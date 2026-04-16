import pathlib
import unittest


class UIValidationModalTests(unittest.TestCase):
    def test_claim_action_modal_functions_are_present(self) -> None:
        root = pathlib.Path(__file__).resolve().parents[2]
        app_js = (root / "js" / "app.js").read_text(encoding="utf-8")
        claim_detail_html = (root / "claim_detail.html").read_text(encoding="utf-8")
        self.assertIn("function showValidationSummaryModal", app_js)
        self.assertIn("validationGroupMarkup", app_js)
        self.assertIn("pmbDecisionMarkup", app_js)
        self.assertIn("PMB Detection and Benefit Routing", app_js)
        self.assertIn("PMB cannot be evaluated until primary diagnosis is captured.", app_js)
        self.assertIn("System auto-flagged", app_js)
        self.assertIn('data-action="auto-fix-primary"', app_js)
        self.assertIn("jumpToClaimTarget", app_js)
        self.assertIn("focusDiagnosisSearchInput", app_js)
        self.assertIn("handleAddDiagnosis", app_js)
        self.assertIn("handleRunReadiness", app_js)
        self.assertIn("handleCloseClaim", app_js)
        self.assertIn("handlePostClosureValidation", app_js)
        self.assertIn('id="diagnoses"', claim_detail_html)
        self.assertIn('id="diagnosis-search-input"', claim_detail_html)


if __name__ == "__main__":
    unittest.main()
