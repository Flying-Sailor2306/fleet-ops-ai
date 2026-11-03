import unittest
from copy import deepcopy
from unittest.mock import patch
from examples import examples
from orchestrator import intake, coordinate, rehearsal, parse_response


class GuidanceTests(unittest.TestCase):
    def test_manager_can_cite_validated_specialist_source(self):
        from reference_library import model_context
        source = {'id':'OEM','status':'Text extracted','chunks':[{'id':'OEM-p1','text':'Engine maintenance record review.'}]}
        def selection(role,case,**kwargs):
            context = model_context(role,case,**kwargs)
            if role == 'Fleet Manager':
                context['document_library'] = []
                context['reference_selection']['excerpt_ids'] = []
            return context
        def invoke(role,phase,context,assignment):
            response = rehearsal(role,phase,context,assignment)
            if phase in ('specialist','review','final'):
                response['citations'] = ['OEM-p1']
            return response
        with patch('reference_library.references',return_value=[source]), patch('reference_library.model_context',side_effect=selection):
            result = coordinate(intake(examples()[0]['data']),invoke)
        self.assertIsNone(result['run_error'])
        self.assertIn('OEM-p1',result['trace'][-1]['forwarded_reference_ids'])

    def test_examples_are_distinct_valid_intakes(self):
        items = examples()
        self.assertEqual(len(items), 11)
        self.assertEqual(len({x['label'] for x in items}), 11)
        for item in items:
            case = intake(item['data'])
            self.assertIn('FICTIONAL', case['submission']['observations'])

    def test_guidance_quote_must_exist_in_retrieved_source(self):
        case = {'document_library':[{'chunks':[{'id':'OEM-p1','text':'Inspect the record before assessment.'}]}]}
        result = dict(summary='Guidance', citations=['OEM-p1'], findings=[], uncertainties=[], proposed_actions=[],
            guidance=[dict(instruction='Review record',source_id='OEM-p1',quote='Inspect the record',applicability='Verify engine variant')])
        parse_response(result,'specialist',case,['OEM-p1'])
        bad = deepcopy(result)
        bad['guidance'][0]['quote']='Invented pressure limit'
        with self.assertRaisesRegex(ValueError,'quote'):
            parse_response(bad,'specialist',case,['OEM-p1'])
        with self.assertRaisesRegex(ValueError,'not retrieved'):
            parse_response(result,'specialist',case,[])

    def test_draft_review_and_assignment_search_are_returned(self):
        case = intake(examples()[2]['data'])
        result = coordinate(case,rehearsal)
        self.assertIsNone(result['run_error'])
        self.assertEqual(result['decision_report']['draft_review']['status'],'revision_required')
        self.assertIn('starting', result['trace'][1]['library_search']['query'].lower())
        self.assertIn('vessel_email',result['action_results'][-1]['result'])
        self.assertFalse(result['closure'])
