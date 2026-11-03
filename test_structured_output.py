import unittest
from unittest.mock import patch
import meta_client
from orchestrator import coordinate,intake,rehearsal
from benchmark_cases import benchmark_examples


class StructuredOutputTests(unittest.TestCase):
    def test_actual_api_request_has_role_schema(self):
        with patch.dict('os.environ',{'META_MODEL':'test'}),patch.object(meta_client,'request',return_value={'choices':[{'message':{'content':'{}'}}]}) as request:
            meta_client.invoke('Engineering Superintendent','specialist',{'reference_selection':{}},'Assess')
        schema=request.call_args.args[1]['response_format']['json_schema']['schema']
        self.assertIn('impact',schema['required'])
        duration=schema['properties']['impact']['properties']['downtime']
        self.assertEqual(duration['properties']['min_hours']['type'],['number','null'])
        self.assertFalse(schema['additionalProperties'])

    def test_malformed_marine_response_repaired_once(self):
        attempts=0
        def invoke(role,phase,context,assignment):
            nonlocal attempts
            if role=='Marine Superintendent' and phase=='specialist':
                attempts+=1
                if attempts==1:return '{"summary": "incomplete'
                if attempts==2:self.assertIn('_validation_feedback',context)
            return rehearsal(role,phase,context,assignment)
        case=coordinate(intake(benchmark_examples()[0]['data']),invoke)
        self.assertIsNone(case['run_error'])
        self.assertEqual(case['ai_calls'],9)
        self.assertEqual(case['validation_attempts'][0]['source_id'],'response-format')

    def test_repeated_invalid_json_halts(self):
        def invoke(role,phase,context,assignment):
            return 'not JSON' if phase=='specialist' else rehearsal(role,phase,context,assignment)
        case=coordinate(intake(benchmark_examples()[0]['data']),invoke)
        self.assertEqual(case['ai_calls'],3)
        self.assertIsNone(case['decision_report'])
