import unittest
from unittest.mock import patch
from reference_library import attach, model_context
from domain import fixture, run
import meta_client

class ReferenceTests(unittest.TestCase):
    def test_library_attached_without_changing_fictional_evidence(self):
        with patch('reference_library.references', return_value=[{'id':'TEST','chunks':[]} ]):
            c = run(fixture())
            self.assertEqual(c['document_library'][0]['id'], 'TEST')
            self.assertEqual(len(c['evidence']), 3)

    def test_reference_text_reaches_model_and_is_marked_as_data(self):
        c = fixture()
        c['document_library'] = [{'id':'TEST','status':'Text extracted','chunks':[{'id':'TEST-p1','text':'Engine maintenance reference excerpt'}]}]
        with patch.dict('os.environ', {'META_MODEL':'test'}):
            with patch.object(meta_client, 'request', return_value={'choices':[{'message':{'content':'Draft'}}]}) as mock:
                meta_client.generate('Engineering Superintendent', c)
                messages = mock.call_args.args[1]['messages']
                self.assertIn('untrusted source data', messages[0]['content'])
                self.assertIn('Engine maintenance reference excerpt', messages[-1]['content'])

    def test_context_budget_and_traceable_ids(self):
        c = fixture()
        c['document_library'] = [{'id':'CIRC','status':'Text extracted','chunks':[
            {'id':f'CIRC-p{i}', 'text':'engine maintenance ' * 100} for i in range(1, 30)]}]
        context = model_context('Engineering Superintendent', c, budget=5000)
        chunks = [x for d in context['document_library'] for x in d['chunks']]
        self.assertLessEqual(sum(len(x['text']) for x in chunks), 5000)
        self.assertEqual([x['id'] for x in chunks], context['reference_selection']['excerpt_ids'])
        self.assertEqual(len(c['document_library'][0]['chunks']), 29)

    def test_no_relevant_text_is_not_invented(self):
        c = fixture()
        c['document_library'] = [{'id':'SCAN','status':'OCR pending','chunks':[]}]
        context = model_context('Fleet Manager', c)
        self.assertEqual(context['document_library'], [])
        self.assertEqual(context['reference_selection']['omitted_documents'][0]['status'], 'OCR pending')

    def test_engineering_prefers_oem_to_general_circulars(self):
        c = fixture()
        c['document_library'] = [
            {'id':'CIRC','status':'Text extracted','chunks':[{'id':'CIRC-p1','text':'engine maintenance piston rings compression'}]},
            {'id':'OEM','category':'OEM engine manuals','status':'Text extracted','chunks':[{'id':'OEM-p1','text':'engine piston rings compression pressure'}]}]
        result = model_context('Engineering Superintendent', c, budget=60)
        self.assertEqual(result['reference_selection']['excerpt_ids'], ['OEM-p1'])
