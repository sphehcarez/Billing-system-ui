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

    def test_missing_primary_icd_blocks_readiness_with_navigation_action(self) -> None:
        result = self.store.run_readiness(2, "tester", "Billing Specialist")
        self.assertEqual(result["outcome"], "BLOCK")
        self.assertEqual(self.store.claims[2].status, "blocked")
        self.assertIn("validation_summary", result)
        blocker = result["validation_summary"]["blockers"][0]
        self.assertEqual(blocker["reason_code"], "ICD_MISSING_PRIMARY")
        self.assertEqual(blocker["action"]["type"], "NAVIGATE_DIAGNOSES")
        self.assertEqual(blocker["action"]["target"], "diagnoses")
        self.assertEqual(blocker["action_target"], "diagnoses")
        self.assertFalse(blocker["allowAutoFix"])
        self.assertEqual(result["pmb_decision"]["pmb_status"], "UNKNOWN")

    def test_invalid_icd_blocks_readiness(self) -> None:
        claim = self.store.create_claim(
            {
                "claim_number": "CLM-ICD-BAD",
                "patient_id": 1,
                "provider_id": 1,
                "member_number": "MEM201001",
                "service_date": "2026-04-10",
                "diagnoses": [{"seq": 1, "icd10": "X99", "diagnosis_type": "PRIMARY"}],
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
        result = self.store.run_readiness(claim.id, "tester", "Billing Specialist")
        reason_codes = {item["reason_code"] for item in result["validation_summary"]["blockers"]}
        self.assertEqual(result["outcome"], "BLOCK")
        self.assertIn("ICD_INVALID", reason_codes)

    def test_icd_to_pmb_auto_flags_even_without_provider_indicator(self) -> None:
        result = self.store.run_readiness(1, "tester", "Billing Specialist")
        self.assertEqual(result["pmb_decision"]["matched_icd10"], "I10")
        self.assertFalse(result["pmb_decision"]["provider_marked_pmb"])
        self.assertTrue(result["pmb_decision"]["auto_flagged"])
        self.assertEqual(
            result["pmb_decision"]["condition_name"],
            "Business-owned PMB placeholder hypertension condition",
        )
        self.assertEqual(result["pmb_decision"]["pmb_status"], "CONFIRMED")
        self.assertEqual(result["benefit_routing_decision"]["route"], "PMB_BENEFIT_BUCKET")
        self.assertEqual(self.store.claims[1].pmb_status, "confirmed")

    def test_pmb_missing_evidence_routes_to_review(self) -> None:
        result = self.store.run_readiness(7, "tester", "Billing Specialist")
        pmb_items = result["validation_summary"]["pmb"]
        warning_codes = {item["reason_code"] for item in result["validation_summary"]["warnings"]}
        self.assertIn("PMB_EVIDENCE_REQUIRED", warning_codes)
        self.assertEqual(result["pmb_decision"]["pmb_status"], "REVIEW_REQUIRED")
        self.assertEqual(pmb_items[0]["route"], "PMB_REVIEW_QUEUE")
        self.assertEqual(pmb_items[0]["evidence_missing"], ["MOTIVATION"])

    def test_auto_fix_primary_only_when_safe(self) -> None:
        safe_claim = self.store.create_claim(
            {
                "claim_number": "CLM-AUTOFIX-SAFE",
                "patient_id": 1,
                "provider_id": 1,
                "member_number": "MEM240001",
                "service_date": "2026-04-10",
                "diagnoses": [{"seq": 1, "icd10": "I10", "diagnosis_type": "SECONDARY"}],
                "line_items": [{"line_id": "1", "service_code": "CONS001", "service_description": "Consultation", "quantity": 1, "unit_price": 500, "claimed_amount": 500}],
            },
            actor="tester",
            role="Billing Specialist",
        )
        fixed = self.store.auto_fix_primary_diagnosis(safe_claim.id, "tester", "Billing Specialist")
        self.assertTrue(fixed["fixed"])
        self.assertTrue(fixed["diagnoses"][0]["is_primary"])

        ambiguous_claim = self.store.create_claim(
            {
                "claim_number": "CLM-AUTOFIX-AMB",
                "patient_id": 1,
                "provider_id": 1,
                "member_number": "MEM240002",
                "service_date": "2026-04-10",
                "diagnoses": [
                    {"seq": 1, "icd10": "I10", "diagnosis_type": "SECONDARY"},
                    {"seq": 2, "icd10": "M54.5", "diagnosis_type": "SECONDARY"},
                ],
                "line_items": [{"line_id": "1", "service_code": "CONS001", "service_description": "Consultation", "quantity": 1, "unit_price": 500, "claimed_amount": 500}],
            },
            actor="tester",
            role="Billing Specialist",
        )
        ambiguous = self.store.auto_fix_primary_diagnosis(ambiguous_claim.id, "tester", "Billing Specialist")
        self.assertFalse(ambiguous["fixed"])
        self.assertEqual(ambiguous["reason"], "ambiguous_primary")

    def test_pmb_review_and_costing_preview_after_primary_capture(self) -> None:
        self.store.add_claim_diagnosis(2, {"icd10_code": "I10", "is_primary": True, "source": "UserEntry"}, "tester", "Billing Specialist")
        result = self.store.run_readiness(2, "tester", "Billing Specialist")
        self.assertEqual(result["pmb_decision"]["pmb_status"], "REVIEW_REQUIRED")
        self.assertEqual(result["benefit_routing_decision"]["route"], "PMB_REVIEW_QUEUE")
        self.assertEqual(result["costing_preview"]["pricing_basis"], "NON_DSP_VOLUNTARY")

    def test_south_africa_scope_seed_contains_tenants_practices_and_provider_registry_fields(self) -> None:
        tenants = self.store.list_tenants()
        self.assertGreaterEqual(len(tenants), 2)
        practices = self.store.list_practices(tenant_id="tenant-sa-demo")
        self.assertTrue(practices)
        provider = self.store.get_provider(1)
        self.assertEqual(provider.tenant_id, "tenant-sa-demo")
        self.assertTrue(provider.practice_id)
        self.assertTrue(provider.hpcsa_number)

    def test_claim_creation_blocks_cross_tenant_patient_provider_pairing(self) -> None:
        with self.assertRaises(ValueError) as context:
            self.store.create_claim(
                {
                    "claim_number": "CLM-CROSS-TENANT",
                    "patient_id": 1,
                    "provider_id": 5,
                    "member_number": "MEM999001",
                    "service_date": "2026-04-10",
                    "diagnoses": [{"seq": 1, "icd10": "I10", "diagnosis_type": "PRIMARY"}],
                    "line_items": [{"line_id": "1", "service_code": "CONS001", "service_description": "Consultation", "quantity": 1, "unit_price": 500, "claimed_amount": 500}],
                },
                actor="tester",
                role="Billing Specialist",
                tenant_id="tenant-sa-demo",
        )
        self.assertIn("same tenant", str(context.exception))

    def test_pmb_detection_evaluates_secondary_diagnoses_after_primary(self) -> None:
        claim = self.store.create_claim(
            {
                "claim_number": "CLM-PMB-ORDER",
                "patient_id": 1,
                "provider_id": 1,
                "member_number": "MEM240004",
                "service_date": "2026-04-10",
                "attachments": [
                    {
                        "attachment_type": "MOTIVATION",
                        "file_name": "motivation.pdf",
                        "storage_ref": "motivation.pdf",
                        "file_hash": "demo",
                        "uploaded_by": "tester",
                    }
                ],
                "diagnoses": [
                    {"seq": 1, "icd10": "Z00.0", "diagnosis_type": "PRIMARY"},
                    {"seq": 2, "icd10": "I10", "diagnosis_type": "SECONDARY"},
                ],
                "line_items": [
                    {
                        "line_id": "1",
                        "service_code": "CONS001",
                        "service_description": "Consultation",
                        "quantity": 1,
                        "unit_price": 500,
                        "claimed_amount": 500,
                        "diagnosis_refs": [2],
                    }
                ],
            },
            actor="tester",
            role="Billing Specialist",
        )
        result = self.store.run_readiness(claim.id, "tester", "Billing Specialist")
        self.assertEqual(result["pmb_decision"]["matched_icd10"], "I10")
        self.assertEqual(result["pmb_decision"]["mapping_id"], "PMB-MAP-DEV-I10")
        self.assertIn("Z00.0", result["pmb_decision"]["evaluated_icd10_list"])
        self.assertIn("I10", result["pmb_decision"]["evaluated_icd10_list"])

    def test_costing_preview_respects_dsp_rules_configuration(self) -> None:
        confirmed_dsp = self.store.run_readiness(1, "tester", "Billing Specialist")
        self.assertEqual(confirmed_dsp["costing_preview"]["pricing_basis"], "DSP")
        self.assertEqual(confirmed_dsp["costing_preview"]["member_liability_estimate"], 0.0)
        self.assertEqual(confirmed_dsp["costing_preview"]["pmb_allowed_total"], 900.0)

        non_dsp_claim = self.store.create_claim(
            {
                "claim_number": "CLM-NONDSP-PMB",
                "patient_id": 1,
                "provider_id": 2,
                "provider_is_dsp": False,
                "non_dsp_access_type": "VOLUNTARY",
                "member_number": "MEM240003",
                "service_date": "2026-04-10",
                "diagnoses": [{"seq": 1, "icd10": "I10", "diagnosis_type": "PRIMARY"}],
                "attachments": [{"attachment_type": "MOTIVATION", "file_name": "motivation.pdf", "storage_ref": "motivation.pdf", "file_hash": "demo", "uploaded_by": "tester"}],
                "line_items": [{"line_id": "1", "service_code": "CONS001", "service_description": "Consultation", "quantity": 1, "unit_price": 1200, "claimed_amount": 1200}],
            },
            actor="tester",
            role="Billing Specialist",
        )
        non_dsp = self.store.run_readiness(non_dsp_claim.id, "tester", "Billing Specialist")
        self.assertEqual(non_dsp["pmb_decision"]["pmb_status"], "CONFIRMED")
        self.assertEqual(non_dsp["costing_preview"]["pricing_basis"], "NON_DSP_VOLUNTARY")
        self.assertEqual(non_dsp["costing_preview"]["pmb_allowed_total"], 900.0)
        self.assertEqual(non_dsp["costing_preview"]["member_liability_estimate"], 300.0)

    def test_clean_success_reconciles(self) -> None:
        claim = self.store.claims[1]
        self.assertEqual(claim.status, "reconciled")
        evidence = self.store.get_evidence_packet(1)
        self.assertIsNotNone(evidence["snapshot"])
        self.assertGreaterEqual(len(evidence["decision_bundles"]), 2)
        self.assertGreaterEqual(len(evidence["benefit_route_decisions"]), 1)
        self.assertGreaterEqual(len(evidence["pmb_decisions"]), 1)
        self.assertGreaterEqual(len(evidence["costing_previews"]), 1)
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
                "attachments": [
                    {
                        "attachment_type": "MOTIVATION",
                        "file_name": "motivation.pdf",
                        "storage_ref": "motivation.pdf",
                        "file_hash": "demo",
                        "uploaded_by": "tester",
                    }
                ],
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

    def test_legacy_claim_workflow_metadata_is_backfilled_on_read(self) -> None:
        claim = self.store.claims[1]
        claim.eligible_roles = []
        claim.affected_roles = []
        claim.last_completed_role = None
        claim.role_action_history = []
        claim.state_progression = []

        payload = self.store.get_claim(1)

        self.assertTrue(payload["eligible_roles"])
        self.assertTrue(payload["affected_roles"])
        self.assertTrue(payload["state_progression"])
        self.assertTrue(payload["role_action_history"])
        self.assertIsNotNone(payload["last_completed_role"])
        self.assertEqual(payload["role_action_history"][0]["action"], "CLAIM_CREATED")
        self.assertEqual(payload["role_action_history"][-1]["status"], payload["status"])

    def test_dashboard_summary_is_role_specific(self) -> None:
        finance = self.store.dashboard_summary(tenant_id="tenant-sa-demo", role="Finance Officer")
        provider = self.store.dashboard_summary(tenant_id="tenant-sa-demo", role="Healthcare Provider")
        debtors = self.store.dashboard_summary(tenant_id="tenant-sa-demo", role="Credit Controller")

        self.assertTrue(finance["worklist"])
        self.assertTrue(any(item["status"] == "exception" for item in finance["worklist"]))
        self.assertTrue(all(item["status"] in {"ready_to_submit", "submitted", "acknowledged", "paid", "reconciled", "exception"} for item in finance["worklist"]))
        self.assertTrue(all(item["status"] in {"draft", "blocked", "ready_to_close", "pended", "validation_exception"} for item in provider["worklist"]))
        self.assertTrue(all(item["status"] in {"paid", "reconciled", "exception"} for item in debtors["worklist"]))
        self.assertTrue(finance["ownership_board"])
        self.assertIn("financials", finance)
        self.assertIn("submission_overview", finance)

    def test_seeded_demo_users_cover_expanded_sa_billing_roles(self) -> None:
        expected = {
            "Administrator",
            "Front Office",
            "Billing",
            "Clinical",
            "Finance",
            "Audit",
            "Practice Manager",
            "Bureau Manager",
            "Reception / Patient Access",
            "Billing Specialist",
            "Clinical Coder",
            "Authorisations Coordinator",
            "Healthcare Provider",
            "Finance Officer",
            "Reconciliation Specialist",
            "Credit Controller",
            "Compliance Auditor",
        }
        roles = {record["role"] for record in self.store.auth_users.values()}
        self.assertTrue(expected.issubset(roles))

    def test_patient_statement_reflects_payments_and_invoices(self) -> None:
        claim = self.store.claims[8]
        statement_before = self.store.generate_patient_statement(claim.patient_id, "tester", "Finance Officer")
        payment = self.store.record_patient_payment(
            claim.patient_id,
            5000,
            "EFT",
            "statement-payment-1",
            {"amount_cents": 5000, "method": "EFT"},
        )
        statement_after = self.store.generate_patient_statement(claim.patient_id, "tester", "Finance Officer")

        self.assertGreaterEqual(statement_before["totals"]["outstanding_cents"], 0)
        self.assertTrue(statement_after["payments"])
        self.assertEqual(statement_after["payments"][0]["payment_id"], payment["payment_id"])
        self.assertGreaterEqual(statement_after["totals"]["paid_cents"], 5000)

    def test_reconciliation_exception_can_return_to_billing(self) -> None:
        result = self.store.resolve_reconciliation_exception(
            9,
            "RETURN_TO_BILLING",
            "tester",
            "Finance Officer",
            note="Mismatch needs billing correction.",
        )

        self.assertEqual(self.store.claims[9].status, "ready_to_submit")
        self.assertEqual(result["workflow"]["eligible_roles"][0], "Billing")
        self.assertEqual(result["reconciliation"]["status"], "exception")

    def test_switch_submission_uses_integration_boundary_metadata(self) -> None:
        claim = self.store.create_claim(
            {
                "claim_number": "CLM-SWITCH-BOUNDARY",
                "patient_id": 1,
                "provider_id": 1,
                "member_number": "MEM300001",
                "service_date": "2026-04-10",
                "diagnoses": [{"seq": 1, "icd10": "I10", "diagnosis_type": "PRIMARY"}],
                "attachments": [
                    {
                        "attachment_type": "MOTIVATION",
                        "file_name": "motivation.pdf",
                        "storage_ref": "motivation.pdf",
                        "file_hash": "demo",
                        "uploaded_by": "tester",
                    }
                ],
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
        self.store.run_post_closure_validation(claim.id, "tester", "Billing Specialist")
        result = self.store.submit_claim(
            claim.id,
            ClaimSubmissionRequest(channel="SWITCH", idempotency_key="switch-boundary"),
            "tester",
            "Billing Specialist",
        )

        events = [item["event"] for item in result["transport_logs"]]
        self.assertEqual(result["integration_boundary"]["channel"], "SWITCH")
        self.assertIn("provider", result["integration_boundary"])
        self.assertIn("SWITCH_DISPATCH_PREPARED", events)
        self.assertIn("SWITCH_TRANSFORM", events)


if __name__ == "__main__":
    unittest.main()
