import unittest
from orchestrator import coordinate, intake, rehearsal
from examples import examples


class QuoteRecoveryTests(unittest.TestCase):
    def run_case(self, fail_twice=False):
        attempts=0
        def invoke(role,phase,context,assignment):
            nonlocal attempts
            self.assertNotIn('validation_attempts',context)
            response=rehearsal(role,phase,context,assignment)
            if role=='Engineering Superintendent' and phase=='specialist':
                attempts+=1
                chunk=context['document_library'][0]['chunks'][0]
                bad=attempts==1 or fail_twice
                response['guidance']=[dict(instruction='Review reference applicability',source_id=chunk['id'],
                    quote='UNSUPPORTED QUOTATION 987654' if bad else chunk['text'][:80],applicability='Fictional test')]
                if attempts==2:self.assertIn('_validation_feedback',context)
            return response
        return coordinate(intake(examples()[0]['data']),invoke)

    def test_one_bad_quote_is_corrected_without_propagating_it(self):
        case=self.run_case()
        self.assertIsNone(case['run_error'])
        self.assertEqual(case['ai_calls'],9)
        self.assertEqual(case['validation_attempts'][0]['status'],'Corrected response passed validation')
        self.assertNotIn('UNSUPPORTED QUOTATION',str(case['trace']))

    def test_second_bad_quote_halts_and_preserves_failed_attempt(self):
        case=self.run_case(True)
        self.assertEqual(case['ai_calls'],3)
        self.assertIsNone(case['decision_report'])
        self.assertEqual(case['reports'],{})
        self.assertEqual(case['validation_attempts'][0]['status'],'Correction failed; run halted')
