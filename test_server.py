import socket
import threading
import unittest
import urllib.request
from app import HTTPServer, Handler, create_server
from unittest.mock import patch

class BrowserConnectionTests(unittest.TestCase):
    def test_busy_port_opens_v3_on_a_different_port(self):
        occupied = HTTPServer(('127.0.0.1', 0), Handler)
        fallback = None
        try:
            fallback = create_server(occupied.server_port)
            self.assertNotEqual(fallback.server_port, occupied.server_port)
            self.assertEqual(fallback.server_address[0], '127.0.0.1')
            threading.Thread(target=fallback.serve_forever, daemon=True).start()
            opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
            with opener.open('http://127.0.0.1:%d/api/version' % fallback.server_port, timeout=2) as response:
                self.assertIn(b'impact-v4', response.read())
        finally:
            if fallback:
                fallback.shutdown()
                fallback.server_close()
            occupied.server_close()

    def test_other_startup_errors_are_not_hidden(self):
        with patch('app.HTTPServer', side_effect=PermissionError('Access denied')) as constructor:
            with self.assertRaises(PermissionError):
                create_server(8890)
            self.assertEqual(constructor.call_count, 1)

    def test_idle_browser_connection_does_not_block_dashboard(self):
        server = HTTPServer(('127.0.0.1', 0), Handler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        idle = socket.create_connection(server.server_address, timeout=2)
        try:
            opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
            with opener.open('http://127.0.0.1:%d/' % server.server_port, timeout=2) as response:
                self.assertEqual(response.status, 200)
                self.assertIn(b'Fleet Ops AI', response.read())
        finally:
            idle.close()
            server.shutdown()
            server.server_close()
