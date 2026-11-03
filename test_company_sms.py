import unittest
from unittest.mock import patch
from company_sms import company, sms_reference, markdown, html_page
from reference_library import attach, model_context
from domain import fixture, run, approve

class CompanySMSTests(unittest.TestCase):
    def test_sms_browser_page_contains_all_sections_and_navigation(self):
        page = html_page()
        self.assertTrue(page.startswith('<!doctype html>'))
        self.assertIn('href="/"', page)
        self.assertIn('href="/sms-download.md"', page)
        self.assertEqual(page.count('<section id="sms-'), 16)
    def test_company_and_sms_available_without_private_library(self):
        with patch('reference_library.LIBRARY') as library:
            library.exists.return_value = False
            c = attach(fixture())
        self.assertEqual(c['company']['name'], 'Aster Tide Marine')
        self.assertIn('Aster Horizon', c['vessel'])
        self.assertEqual(c['document_library'][0]['id'], 'ATM-SMS-001')

    def test_all_roles_receive_nonnegotiable_company_procedures(self):
        c = fixture()
        c['document_library'] = [sms_reference()]
        for role in ['Engineering Superintendent', 'Marine Superintendent', 'Fleet Manager']:
            ids = model_context(role, c)['reference_selection']['excerpt_ids']
            for required in ['ATM-SMS-02', 'ATM-SMS-04', 'ATM-SMS-07', 'ATM-SMS-10', 'ATM-SMS-12']:
                self.assertIn(required, ids)

    def test_demo_handoffs_use_company_sms_without_granting_authority(self):
        c = run(fixture())
        self.assertTrue(all(t['company'] == 'Aster Tide Marine' for t in c['trace']))
        self.assertIn('ATM-SMS-04', c['trace'][0]['note'])
        self.assertIn('ATM-SMS-06', c['trace'][1]['note'])
        self.assertIn('Master retains overriding safety authority', c['trace'][2]['note'])
        approve(c, 'Demo reviewer', True, 'Request stoppage review')
        self.assertFalse(c['closure'])

    def test_manual_has_source_map_and_is_explicitly_fictional(self):
        text = markdown()
        self.assertIn('not a certified SMS', text)
        self.assertIn('ISM-p4', text)
        self.assertEqual(len(sms_reference()['chunks']), 16)

    def test_propulsion_and_case_cylinder_count_match_engine(self):
        c = fixture()
        self.assertEqual(c['company']['main_engine']['cylinders'], 7)
        self.assertEqual(c['company']['main_engine']['model'], '7S50MC-C')
        self.assertIn('Oil tanker', c['company']['main_engine']['propulsion'])
        self.assertIn('units 1–7', c['evidence'][0]['text'])
