import unittest
import urllib.error
from unittest.mock import patch, MagicMock
import meta_client


class ApiErrorTests(unittest.TestCase):
    def test_high_reasoning_gets_longer_timeout(self):
        response=MagicMock()
        response.__enter__.return_value.read.return_value=b'{}'
        with patch.dict('os.environ',{'MODEL_API_KEY':'test-private-key'}),patch('urllib.request.urlopen',return_value=response) as opener:
            meta_client.request('/chat/completions',{'model':'test'})
            self.assertEqual(opener.call_args.kwargs['timeout'],180)
            meta_client.request('/models')
            self.assertEqual(opener.call_args.kwargs['timeout'],30)

    def test_failures_are_specific_and_do_not_expose_provider_details(self):
        failures=[(TimeoutError('private-request'), '180 seconds'),
            (urllib.error.URLError('private-network-detail'),'connect'),
            (urllib.error.HTTPError('private-url',429,'private-body',{},None),'429'),
            (urllib.error.HTTPError('private-url',401,'private-body',{},None),'401')]
        for error, expected in failures:
            with self.subTest(error=expected),patch.dict('os.environ',{'MODEL_API_KEY':'test-private-key'}),patch('urllib.request.urlopen',side_effect=error) as opener:
                with self.assertRaises(ValueError) as caught:meta_client.request('/chat/completions',{})
                self.assertIn(expected,str(caught.exception))
                self.assertNotIn('private',str(caught.exception))
                self.assertEqual(opener.call_count,1)
