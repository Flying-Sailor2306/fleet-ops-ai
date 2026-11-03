import unittest
from unittest.mock import patch
import meta_client


class RoutingTests(unittest.TestCase):
    def test_api_payload_uses_role_model(self):
        with patch.dict('os.environ', {}, clear=True), patch.object(meta_client, 'request', return_value={'choices':[{'message':{'content':'Test response'}}]}) as request:
            for role, expected in meta_client.DEFAULT_MODELS.items():
                meta_client.generate(role, {'reference_selection':{'excerpt_ids':[]}})
                self.assertEqual(request.call_args.args[0], '/chat/completions')
                self.assertEqual(request.call_args.args[1]['model'], expected)
                self.assertEqual(request.call_args.args[1]['reasoning_effort'], 'high')

    def test_explicit_role_override_precedes_shared_model(self):
        with patch.dict('os.environ', {'META_MODEL':'shared','META_MANAGER_MODEL':'manager'}, clear=True):
            self.assertEqual(meta_client.configured_model('Fleet Manager'), 'manager')
            self.assertEqual(meta_client.configured_model('Marine Superintendent'), 'shared')
