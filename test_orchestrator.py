import unittest
from copy import deepcopy
from orchestrator import intake, coordinate, rehearsal, MANAGER, SPECIALISTS

class CoordinationTests(unittest.TestCase):
    def case(self):
        return intake(dict(reporter_role='Chief Engineer',reporter_name='Fictional reporter',location='At sea',operating_condition='Steady load',problem='Low compression on unit 2',urgency='High',observations='Unverified readings',actions_taken='None',assistance_requested='Assess'))
    def test_intake_never_invents_physical_confirmation(self):
        c=self.case()
        self.assertEqual(c['scenario'],'submitted')
        self.assertNotIn('Physical inspection identifies',str(c['evidence']))
        with self.assertRaises(ValueError): intake({'reporter_role':'AI'})
    def test_manager_delegates_reviews_revises_and_reports(self):
        snapshots=[]
        c=coordinate(self.case(),rehearsal,lambda c:snapshots.append(c))
        phases=[(x['role'],x['phase']) for x in c['trace']]
        self.assertEqual(phases[0],(MANAGER,'plan'))
        self.assertEqual(phases[-1],(MANAGER,'final'))
        self.assertEqual(len(c['reports'][SPECIALISTS[0]]),2)
        self.assertEqual(len(c['reviews']),2)
        self.assertEqual(c['status'],'Awaiting human review')
        self.assertFalse(c['closure'])
        self.assertIsNone(c['approval'])
        self.assertGreater(len(snapshots),len(c['trace']))
    def test_invalid_citation_halts_without_final_report(self):
        def bad(role,phase,ctx,task):
            result=rehearsal(role,phase,ctx,task)
            result['citations']=['FABRICATED-p99']
            return result
        c=coordinate(self.case(),bad)
        self.assertIn('failed',c['status'])
        self.assertIsNone(c['decision_report'])
        self.assertFalse(c['closure'])
    def test_invalid_delegation_halts(self):
        def bad(role,phase,ctx,task):
            result=rehearsal(role,phase,ctx,task)
            result['assignments'][0]['role']='Procurement Agent'
            return result
        self.assertIn('failed',coordinate(self.case(),bad)['status'])
    def test_followup_loop_is_bounded_and_unresolved_preserved(self):
        def persistent(role,phase,ctx,task):
            response=rehearsal(role,phase,ctx,task)
            if phase=='review': response['followups']=[dict(role=r,question='Need corroboration') for r in SPECIALISTS]
            return response
        c=coordinate(self.case(),persistent)
        self.assertEqual(c['ai_calls'],8)
        self.assertEqual(len(c['unresolved_followups']),2)
        self.assertIsNotNone(c['decision_report'])
    def test_provider_error_preserves_partial_trace_no_fallback(self):
        def failing(role,phase,ctx,task):
            if phase=='specialist':raise RuntimeError('secret-provider-detail')
            return rehearsal(role,phase,ctx,task)
        c=coordinate(self.case(),failing)
        self.assertEqual(len(c['trace']),1)
        self.assertNotIn('secret-provider-detail',c['run_error'])
        self.assertIsNone(c['decision_report'])
