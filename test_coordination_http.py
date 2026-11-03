import json
import threading
import time
import unittest
import urllib.request
import urllib.error
from unittest.mock import patch
import app

class CoordinationHTTPTests(unittest.TestCase):
    def test_submit_run_poll_report_and_approval_gate(self):
        server=app.HTTPServer(('127.0.0.1',0),app.Handler)
        threading.Thread(target=server.serve_forever,daemon=True).start()
        opener=urllib.request.build_opener(urllib.request.ProxyHandler({}))
        base='http://127.0.0.1:'+str(server.server_port)
        def get(path):
            with opener.open(base+path,timeout=5) as r:return json.load(r)
        def post(path,data,token=app.TOKEN):
            req=urllib.request.Request(base+'/api/'+path,data=json.dumps(data).encode(),headers={'X-Case-Token':token,'Content-Type':'application/json'})
            with opener.open(req,timeout=5) as r:return json.load(r)
        def publish(case):
            with app.STATE_LOCK:app.STATE=case
        try:
            with patch.dict('os.environ',{'FLEET_MODE':'demo'}),patch.object(app,'publish',side_effect=publish):
                self.assertEqual(get('/api/version')['build'], 'impact-v4')
                self.assertEqual(len(get('/api/examples')), 11)
                self.assertEqual(get('/api/state')['build'], 'impact-v4')
                with opener.open(base+'/',timeout=5) as response:
                    self.assertIn(b'Submit a case to the AI Fleet Manager',response.read())
                with opener.open(base+'/sms',timeout=5) as response:
                    self.assertEqual(response.status,200)
                with self.assertRaises(urllib.error.HTTPError) as error:post('run',{},'bad-token')
                self.assertEqual(error.exception.code,403)
                post('submit',dict(reporter_role='Master',reporter_name='Test officer',location='At sea',operating_condition='Steady',problem='Engine condition report',urgency='High'))
                with self.assertRaises(urllib.error.HTTPError) as error:post('approve',dict(name='Reviewer',consultation=True,decision='Request further evidence'))
                self.assertEqual(error.exception.code,400)
                post('run',{})
                deadline=time.monotonic()+10
                while time.monotonic()<deadline:
                    state=get('/api/state')
                    if not state['busy']:break
                    time.sleep(.05)
                self.assertFalse(state['busy'])
                self.assertEqual(state['case']['trace'][0]['phase'],'plan')
                self.assertEqual(state['case']['trace'][-1]['phase'],'final')
                self.assertEqual(state['case']['status'],'Awaiting human review')
                post('approve',dict(name='Reviewer',consultation=True,decision='Request further evidence'))
                self.assertFalse(get('/api/state')['case']['closure'])
        finally:
            server.shutdown()
            server.server_close()
