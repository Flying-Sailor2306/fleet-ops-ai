import unittest
from orchestrator import intake, coordinate, rehearsal, prepare


class ActionTests(unittest.TestCase):
    def test_completed_documents_do_not_complete_external_work(self):
        case = intake(dict(reporter_role='Chief Engineer', reporter_name='Demo',
            location='At sea', operating_condition='Steady load', problem='Unverified compression reading', urgency='High'))
        result = coordinate(case, rehearsal)
        self.assertEqual(len(result['action_results']), 3)
        self.assertEqual(result['action_results'][0]['result']['report_id'], 'ENG-R2')
        self.assertTrue(all(a['status'].startswith('Pending') for a in result['pending_actions']))
        self.assertFalse(result['closure'])
        self.assertIsNone(result['approval'])
        reset = prepare(result)
        self.assertEqual(reset['action_results'], [])
        self.assertEqual(reset['pending_actions'], [])
