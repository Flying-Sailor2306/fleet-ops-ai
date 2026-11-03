import unittest
from benchmark_cases import stress_examples
from orchestrator import intake, coordinate, rehearsal


class StressCaseTests(unittest.TestCase):
    def test_missing_spare_does_not_inherit_six_to_eight_hour_cap(self):
        case=coordinate(intake(stress_examples()[1]['data']),rehearsal)
        self.assertIsNone(case['run_error'])
        self.assertNotIn('max_usd',case['commercial_scenario'])
        self.assertIn('cannot be capped',case['submission']['planning_context'])

    def test_fleet_and_contract_facts_reach_agents_as_case_evidence(self):
        seen=[]
        def invoke(role,phase,context,assignment):
            seen.append(context)
            return rehearsal(role,phase,context,assignment)
        case=coordinate(intake(stress_examples()[0]['data']),invoke)
        self.assertIsNone(case['run_error'])
        for context in seen:
            self.assertIn('Meridian',context['submission']['fleet_context'])
            self.assertIn('At-sea delay does not itself start demurrage',context['submission']['contract_context'])
            self.assertTrue(any(e['title']=='Officer-reported contract context' for e in context['evidence']))
        self.assertEqual(len(case['decision_report']['decision_brief']),7)
