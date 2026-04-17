import pathlib
import unittest


class UIValidationModalTests(unittest.TestCase):
    def test_claim_action_modal_functions_are_present(self) -> None:
        root = next(
            (
                candidate
                for candidate in pathlib.Path(__file__).resolve().parents
                if (candidate / "js" / "app.js").exists() and (candidate / "claim_detail.html").exists()
            ),
            None,
        )
        if root is None:
            self.skipTest("Frontend assets are not present in this test runtime.")
        app_js = (root / "js" / "app.js").read_text(encoding="utf-8")
        claim_detail_html = (root / "claim_detail.html").read_text(encoding="utf-8")
        self.assertIn("function showValidationSummaryModal", app_js)
        self.assertIn("validationGroupMarkup", app_js)
        self.assertIn("pmbDecisionMarkup", app_js)
        self.assertIn("PMB Detection and Benefit Routing", app_js)
        self.assertIn("PMB cannot be evaluated until primary diagnosis is captured.", app_js)
        self.assertIn("System auto-flagged", app_js)
        self.assertIn('data-action="auto-fix-primary"', app_js)
        self.assertIn("handleApplyLineDiagnosisLinks", app_js)
        self.assertIn("renderStructuredPayload", app_js)
        self.assertIn("handleGenerateEdi", app_js)
        self.assertIn("handleSubmitEdiSwitch", app_js)
        self.assertIn("renderTransportTimeline", app_js)
        self.assertIn("jumpToClaimTarget", app_js)
        self.assertIn("focusDiagnosisSearchInput", app_js)
        self.assertIn("handleAddDiagnosis", app_js)
        self.assertIn("handleRunReadiness", app_js)
        self.assertIn("handleCloseClaim", app_js)
        self.assertIn("handlePostClosureValidation", app_js)
        self.assertIn('id="diagnoses"', claim_detail_html)
        self.assertIn('id="diagnosis-search-input"', claim_detail_html)
        self.assertIn('id="line_items"', claim_detail_html)
        self.assertIn('id="submission_tool"', claim_detail_html)


if __name__ == "__main__":
    unittest.main()
