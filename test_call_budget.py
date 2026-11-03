import unittest
from orchestrator import coordinate, intake, rehearsal, MAX_CALLS
from benchmark_cases import benchmark_examples


class BudgetTests(unittest.TestCase):
    def run_with_corrections(self, fail_final=False):
        calls=0
        def invoke(role,phase,context,assignment):
            nonlocal calls
            calls+=1
            if calls % 2 == 1 and (phase!='final' or fail_final):
                return 'Invalid JSON to exercise bounded correction'
            return rehearsal(role,phase,context,assignment)
        case=coordinate(intake(benchmark_examples()[0]['data']),invoke)
        self.assertEqual(calls,case['ai_calls'])
        return case

    def test_seven_different_stages_can_correct_and_finish_at_fifteen(self):
        case=self.run_with_corrections()
        self.assertEqual(case['ai_calls'],15)
        self.assertEqual(len(case['validation_attempts']),7)
        self.assertIsNone(case['run_error'])
        self.assertIsNotNone(case['decision_report'])

    def test_no_sixteenth_call_when_final_cannot_validate(self):
        case=self.run_with_corrections(True)
        self.assertEqual(case['ai_calls'],MAX_CALLS)
        self.assertIn('correction budget',case['run_error'])
        self.assertIsNone(case['decision_report'])
        self.assertFalse(case['closure'])
