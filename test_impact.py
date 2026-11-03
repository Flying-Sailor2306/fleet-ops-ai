import unittest
from orchestrator import intake, coordinate, rehearsal, SPECIALISTS
from examples import examples
from impact import exposure, validate


class ImpactTests(unittest.TestCase):
    def test_what_if_exposure_does_not_invent_engineering_duration(self):
        case=coordinate(intake(examples()[0]['data']),rehearsal)
        self.assertIsNone(case['reports'][SPECIALISTS[0]][-1]['impact']['downtime']['min_hours'])
        calculated=case['commercial_scenario']
        self.assertEqual(calculated['min_usd'],24000)
        self.assertEqual(calculated['max_usd'],48000)
        self.assertIn('what-if',calculated['duration_origin'])

    def test_new_case_does_not_inherit_old_demo_diagnosis_or_costs(self):
        case=intake(examples()[-1]['data'])
        self.assertEqual(case['assumptions'],{})
        self.assertEqual(case['references'],[])
        self.assertEqual(case['pending'],[])

    def test_marine_waits_for_engineering_and_uses_revised_report(self):
        seen=[]
        def invoke(role,phase,context,assignment):
            result=rehearsal(role,phase,context,assignment)
            if phase=='plan': result['assignments'].reverse()
            if role==SPECIALISTS[0] and phase=='specialist':
                result['impact']['downtime'].update(min_hours=24,max_hours=48,basis='Explicit test planning assumption')
            if role==SPECIALISTS[1] and phase=='specialist':
                seen.append(context['commercial_scenario'])
            return result
        case=coordinate(intake(examples()[0]['data']),invoke)
        self.assertIsNone(case['run_error'])
        self.assertEqual([x['engineering_report_id'] for x in seen],['ENG-R1','ENG-R2'])
        self.assertEqual(seen[-1]['min_usd'],24000)
        self.assertEqual(seen[-1]['max_usd'],48000)
        self.assertEqual(case['reports'][SPECIALISTS[1]][-1]['impact']['engineering_report_id'],'ENG-R2')

    def test_missing_rate_is_not_zero_cost(self):
        c=intake(examples()[0]['data']);c['submission']['daily_cost_usd']=''
        c=coordinate(c,rehearsal)
        self.assertNotIn('min_usd',exposure(c))

    def test_invalid_rate_rejected(self):
        for value in ('nan','inf','-1'):
            data=examples()[0]['data'];data['daily_cost_usd']=value
            with self.assertRaises(ValueError):intake(data)
