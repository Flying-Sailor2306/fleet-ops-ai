import unittest
from unittest.mock import patch
from domain import fixture, run, approve, evaluate, ROLES
import meta_client

class WorkflowTests(unittest.TestCase):
    def test_corroborated(self):
        c = run(fixture())
        self.assertIn('corroborates', c['assessment']['diagnosis'])
        self.assertEqual([t['role'] for t in c['trace']], ROLES)
        self.assertEqual(c['assessment']['deviation_bar'], 6)
        self.assertEqual(c['assessment']['alert'], 'OPEN')
        self.assertFalse(c['closure'])

    def test_missing_and_conflicting(self):
        for scenario in ['missing', 'conflicting']:
            c = run(fixture(scenario))
            self.assertIn('unresolved', c['assessment']['diagnosis'])
            self.assertTrue(evaluate(c)['suspected_vs_confirmed'])
            self.assertEqual(c['assessment']['alert'], 'OPEN')

    def test_no_approval_and_invalid_approval(self):
        c = run(fixture())
        self.assertTrue(evaluate(c)['missing_approval'])
        for name, consultation in [('', True), ('Manager', False)]:
            with self.assertRaises(ValueError): approve(c, name, consultation, 'Request stoppage review')
        with self.assertRaises(ValueError): approve(fixture(), 'Manager', True, 'Request stoppage review')

    def test_acknowledgment_cannot_close_case(self):
        c = run(fixture())
        approve(c, 'Demo manager', True, 'Request stoppage review')
        self.assertFalse(c['closure'])
        self.assertFalse(evaluate(c)['missing_approval'])
        self.assertIsNone(run(c)['approval'])

    def test_live_handoffs_share_prior_output(self):
        seen = []
        def generate(role, case):
            seen.append(len(case['trace']))
            return 'Unverified draft citing E1'
        c = run(fixture(), generate)
        self.assertEqual(seen, [0, 1, 2])
        self.assertIn('unverified', c['trace'][0]['provenance'])

    def test_meta_response_parsing_without_network(self):
        with patch.dict('os.environ', {'META_MODEL': 'account-enabled-model'}):
            with patch.object(meta_client, 'request', return_value={'choices':[{'message':{'content':'Draft [E1]'}}]}) as request:
                self.assertEqual(meta_client.generate(ROLES[0], fixture()), 'Draft [E1]')
                self.assertEqual(request.call_args.args[0], '/chat/completions')

if __name__ == '__main__': unittest.main()
