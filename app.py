"""Local single-user hackathon server. Python 3.10+, standard library only."""
import json
import os
import secrets
import socket
import errno
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from threading import RLock, Thread
from copy import deepcopy
from pathlib import Path
from domain import fixture, run, approve, evaluate
import meta_client
from reference_library import attach
from company_sms import markdown, html_page
from orchestrator import intake, prepare, coordinate, rehearsal, SPECIALISTS, MANAGER

meta_client.load_env()
STATE = prepare(fixture())
BUSY = False
TOKEN = secrets.token_urlsafe(24)
STATE_LOCK = RLock()

class HTTPServer(ThreadingHTTPServer):
    """Browsers may open idle speculative sockets; don't let one block all requests."""
    daemon_threads = True
    allow_reuse_address = False

    def server_bind(self):
        if hasattr(socket, 'SO_EXCLUSIVEADDRUSE'):
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_EXCLUSIVEADDRUSE, 1)
        super().server_bind()

class Handler(BaseHTTPRequestHandler):
    def setup(self):
        super().setup()
        self.connection.settimeout(15)

    def reply(self, value, status=200):
        body = json.dumps(value).encode()
        self.send_response(status)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Cache-Control', 'no-store')
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path == '/api/examples':
            from examples import examples
            return self.reply(examples())
        if self.path == '/api/version':
            return self.reply({'build':'impact-v4', 'case_submission':True})
        if self.path in ('/sms', '/sms/', '/sms.md'):
            body = html_page().encode('utf-8')
            self.send_response(200)
            self.send_header('Content-Type', 'text/html; charset=utf-8')
            self.send_header('Cache-Control', 'no-store')
            self.end_headers()
            self.wfile.write(body)
            return
        if self.path == '/sms-download.md':
            body = markdown().encode('utf-8')
            self.send_response(200)
            self.send_header('Content-Type', 'text/markdown; charset=utf-8')
            self.send_header('Content-Disposition', 'attachment; filename="Aster-Tide-Marine-SMS.md"')
            self.end_headers()
            self.wfile.write(body)
            return
        if self.path == '/api/state':
            with STATE_LOCK:
                return self.reply(dict(build='impact-v4', case=STATE, mode=os.environ.get('FLEET_MODE', 'demo'), token=TOKEN, busy=BUSY,
                    models={r:meta_client.configured_model(r) or 'Not configured' for r in (MANAGER,)+SPECIALISTS}))
        if self.path != '/': return self.reply({'error': 'Not found'}, 404)
        body = Path(__file__).with_name('dashboard.html').read_bytes()
        self.send_response(200)
        self.send_header('Content-Type', 'text/html; charset=utf-8')
        self.send_header('Cache-Control', 'no-store')
        self.send_header('Content-Security-Policy', "default-src 'self'; script-src 'unsafe-inline'; style-src 'unsafe-inline'; connect-src 'self'; frame-ancestors 'none'")
        self.end_headers()
        self.wfile.write(body)

    def do_POST(self):
        with STATE_LOCK:
            self.handle_post()

    def handle_post(self):
        global STATE, BUSY
        if self.headers.get('X-Case-Token') != TOKEN: return self.reply({'error': 'Invalid local session token'}, 403)
        try:
            length = int(self.headers.get('Content-Length', 0))
            if length > 100000: raise ValueError('Request too large')
            data = json.loads(self.rfile.read(length) or b'{}')
            if BUSY: return self.reply({'error':'An agent run is in progress; wait for completion.'},409)
            if self.path == '/api/reset':
                if data.get('scenario') not in ('corroborated', 'missing', 'conflicting'): raise ValueError('Invalid scenario')
                STATE = prepare(fixture(data['scenario']))
            elif self.path == '/api/submit':
                STATE = prepare(intake(data))
            elif self.path == '/api/run':
                live = os.environ.get('FLEET_MODE') == 'live'
                if live:
                    if data.get('live_consent') is not True: raise ValueError('Acknowledge external API use first')
                    if not all(meta_client.configured_model(r).startswith('muse-') for r in (MANAGER,)+SPECIALISTS): raise ValueError('Configure an account-enabled Muse model for each role (or META_MODEL).')
                STATE = prepare(STATE)
                STATE['status'] = 'Starting Meta Muse run' if live else 'Starting scripted architecture rehearsal'
                BUSY = True
                Thread(target=run_worker,args=(deepcopy(STATE),live),daemon=True).start()
            elif self.path == '/api/approve':
                if not STATE.get('decision_report') or STATE.get('run_error'): raise ValueError('A completed management report is required before human acknowledgment.')
                approve(STATE, data.get('name', ''), data.get('consultation') is True, data.get('decision'))
            else: return self.reply({'error': 'Not found'}, 404)
            self.reply({'ok': True})
        except ValueError as exc: self.reply({'error': str(exc)}, 400)
        except Exception:
            # Never echo provider responses, headers or credentials to browser/logs.
            self.reply({'error': 'Model request failed. Check local configuration, account access and API status. Previous case preserved; no demo fallback.'}, 502)

def publish(case):
    global STATE
    with STATE_LOCK:
        STATE = case
        # Local last-case snapshot, excluded from Git. Not an authenticated audit log.
        try:
            path = Path(__file__).with_name('local-data')/'last-case.json'
            path.parent.mkdir(exist_ok=True)
            scratch=path.with_suffix('.tmp')
            scratch.write_text(json.dumps(case),encoding='utf-8')
            scratch.replace(path)
        except OSError:
            STATE['storage_warning']='Local snapshot failed; download case before closing.'

def run_worker(case, live):
    global BUSY
    try:
        if live:
            catalog=meta_client.models()
            if any(meta_client.configured_model(r) not in catalog for r in (MANAGER,)+SPECIALISTS):
                raise ValueError('A configured Muse model is not enabled in your account catalog.')
            case['configured_models']={r:meta_client.configured_model(r) for r in (MANAGER,)+SPECIALISTS}
        coordinate(case, meta_client.invoke if live else rehearsal, publish,
            'Meta Muse · unverified AI output' if live else 'Scripted architecture rehearsal — no AI calls')
    except Exception as exc:
        case['status']='Run failed — configuration or API access'
        case['run_error']=str(exc) if isinstance(exc,ValueError) else 'Meta access failed. Check local credentials/account; no rehearsal fallback.'
        publish(case)
    finally:
        with STATE_LOCK: BUSY=False

def create_server(preferred_port):
    try:
        return HTTPServer(('127.0.0.1', preferred_port), Handler)
    except OSError as exc:
        if exc.errno != errno.EADDRINUSE and getattr(exc, 'winerror', None) != 10048:
            raise
        print(f'Port {preferred_port} is already in use. Selecting an available local port.', flush=True)
        # Bind directly to port 0 so Windows reserves a free port without a check/bind race.
        return HTTPServer(('127.0.0.1', 0), Handler)


if __name__ == '__main__':
    server = create_server(int(os.environ.get('FLEET_PORT', '8890')))
    port = server.server_port
    print(f'Fleet Ops AI IMPACT V4 ready: http://127.0.0.1:{port} — keep this window open', flush=True)
    if os.environ.get('FLEET_OPEN_BROWSER') == '1':
        webbrowser.open(f'http://127.0.0.1:{port}/')
    server.serve_forever()
