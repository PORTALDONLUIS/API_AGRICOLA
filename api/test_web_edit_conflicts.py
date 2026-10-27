import unittest
from api.services.web_edit_conflicts import web_edit_conflict

class WebEditConflictTests(unittest.TestCase):
    def test_known_sql_errors_are_explained(self):
        for error in ('SQL: (51012)', 'SQL: (51010)', 'El lote fue corregido en WEB'):
            self.assertIn('DonTec Web', web_edit_conflict(Exception(error)))
    def test_other_failures_are_not_hidden(self):
        for error in ('database unavailable','duplicate row 51012','timeout',''):
            self.assertIsNone(web_edit_conflict(Exception(error)))
