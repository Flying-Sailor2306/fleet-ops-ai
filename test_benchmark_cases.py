import unittest
from benchmark_cases import benchmark_examples
from orchestrator import intake, coordinate, rehearsal, SPECIALISTS


class BenchmarkCaseTests(unittest.TestCase):
    def test_all_three_cases_complete_rehearsal_with_unsent_commercial_draft(self):
        for example in benchmark_examples():
            with self.subTest(case=example['id']):
                case=coordinate(intake(example['data']),rehearsal)
                self.assertIsNone(case['run_error'])
                draft=case['reports'][SPECIALISTS[1]][-1]['impact']['commercial_notification']
                self.assertEqual(draft['send_status'],'draft_not_sent')
                self.assertFalse(case['closure'])
                self.assertIsNone(case['approval'])

    def test_changeout_sensitivity_and_survey_delay_stay_separate(self):
        engine=coordinate(intake(benchmark_examples()[0]['data']),rehearsal)
        survey=coordinate(intake(benchmark_examples()[2]['data']),rehearsal)
        self.assertEqual((engine['commercial_scenario']['min_usd'],engine['commercial_scenario']['max_usd']),(6000,8000))
        self.assertEqual((survey['commercial_scenario']['min_usd'],survey['commercial_scenario']['max_usd']),(0,0))
        self.assertIn('what-if',engine['commercial_scenario']['duration_origin'])
