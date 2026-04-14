import pathlib
import sys
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from platform_core import ClaimClosureRequest, ClaimSubmissionRequest, PlatformStore  # noqa: E402


class PlatformCoreTests(unittest.TestCase):
    def setUp(self) -> None:
        self.store = PlatformStore()

    def test_missing_icd_blocks_readiness(self) -> None:
        result = self.store.run_readiness(2, "tester", "Billing Specialist")
        self.assertEqual(result["outcome"], "BLOCK")
        self.assertEqual(self.store.claims[2].status, "blocked")

    def test_clean_success_reconciles(self) -> None:
        claim = self.store.claims[1]
        self.assertEqual(claim.status, "reconciled")
        evidence = self.store.get_evidence_packet(1)
        self.assertIsNotNone(evidence["snapshot"])
        self.assertGreaterEqual(len(evidence["decision_bundles"]), 2)
        self.assertGreaterEqual(len(evidence["remittances"]), 1)

    def test_idempotent_submission_reuses_original_record(self) -> None:
        first = self.store.submit_claim(
            1,
            ClaimSubmissionRequest(channel="DIRECT", idempotency_key="seed-clean-success"),
            "tester",
            "Billing Specialist",
        )
        second = self.store.submit_claim(
            1,
            ClaimSubmissionRequest(channel="DIRECT", idempotency_key="seed-clean-success"),
            "tester",
            "Billing Specialist",
        )
        self.assertTrue(second["idempotent_replay"])
        self.assertEqual(first["submission_id"], second["submission_id"])

    def test_corrected_claim_creates_version_chain(self) -> None:
        claim = self.store.claims[10]
        self.assertEqual(claim.version, 2)
        diff = self.store.get_claim_diff(10)
        changed_fields = {item["field"] for item in diff["changed_fields"]}
        self.assertIn("member_number", changed_fields)

    def test_manual_claim_lifecycle(self) -> None:
        claim = self.store.create_claim(
            {
                "claim_number": "CLM-2001",
                "patient_id": 1,
                "provider_id": 1,
                "member_number": "MEM200001",
                "service_date": "2026-04-10",
                "diagnoses": [{"seq": 1, "icd10": "I10", "diagnosis_type": "PRIMARY"}],
                "line_items": [
                    {
                        "line_id": "1",
                        "service_code": "CONS001",
                        "service_description": "Consultation",
                        "quantity": 1,
                        "unit_price": 500,
                        "claimed_amount": 500,
                        "diagnosis_refs": [1],
                    }
                ],
            },
            actor="tester",
            role="Billing Specialist",
        )
        self.store.run_readiness(claim.id, "tester", "Billing Specialist")
        self.store.close_claim(claim.id, ClaimClosureRequest(supervisor_override=True), "tester", "Billing Specialist")
        validation = self.store.run_post_closure_validation(claim.id, "tester", "Billing Specialist")
        payload = self.store.build_payload(claim.id, "tester", "Billing Specialist")
        submission = self.store.submit_claim(
            claim.id,
            ClaimSubmissionRequest(channel="DIRECT", idempotency_key="manual-claim"),
            "tester",
            "Billing Specialist",
        )
        self.assertEqual(validation["validation_status"], "valid")
        self.assertIn("payload_id", payload)
        self.assertEqual(submission["response"]["status"], "ACK")


if __name__ == "__main__":
    unittest.main()
