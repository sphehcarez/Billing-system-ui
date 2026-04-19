import pathlib
import sys
import unittest
from uuid import uuid4


ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import main as backend_entrypoint  # noqa: E402
import platform_api  # noqa: E402
from platform_core import ClaimClosureRequest, LoginRequest  # noqa: E402


class MainEntrypointApiTests(unittest.TestCase):
    def _current_user(self) -> dict[str, str]:
        token_payload = platform_api.login(LoginRequest(username="demo.user", password="password123"))
        self.assertIn("access_token", token_payload)
        return platform_api.get_current_user(f"Bearer {token_payload['access_token']}")

    def _create_claim(self, claim_number: str) -> tuple[dict[str, str], dict]:
        current_user = self._current_user()
        claim = platform_api.create_claim(
            {
                "claim_number": claim_number,
                "patient_id": 1,
                "provider_id": 1,
                "member_number": "MEM220001",
                "service_date": "2026-04-16",
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
                        "unit_price": 750,
                        "claimed_amount": 750,
                        "diagnosis_refs": [1],
                    }
                ],
            },
            current_user=current_user,
        )
        return current_user, claim

    def test_readiness_response_includes_pmb_and_validation_summary(self) -> None:
        self.assertIs(backend_entrypoint.app, platform_api.app)
        current_user, claim = self._create_claim(f"CLM-ENTRYPOINT-{uuid4().hex[:8]}")
        payload = platform_api.run_readiness(claim["id"], current_user=current_user)
        self.assertIn("pmb_decision", payload)
        self.assertIn("benefit_routing_decision", payload)
        self.assertIn("benefit_route_decisions", payload)
        self.assertIn("costing_preview", payload)
        self.assertIn("validation_summary", payload)
        self.assertTrue(payload["benefit_route_decisions"])
        self.assertEqual(payload["pmb_decision"]["pmb_status"], "CONFIRMED")
        self.assertTrue(payload["pmb_decision"]["auto_flagged"])
        self.assertEqual(
            payload["pmb_decision"]["condition_name"],
            "Business-owned PMB placeholder hypertension condition",
        )
        self.assertEqual(payload["benefit_route_decisions"][0]["route"], "PMB_BENEFIT_BUCKET")
        self.assertFalse(payload["benefit_route_decisions"][0]["provider_marked_pmb"])
        self.assertEqual(payload["validation_summary"]["pmb"][0]["trigger_icd10"], "I10")
        self.assertEqual(payload["costing_preview"]["pricing_basis"], "DSP")

    def test_closure_validation_and_evidence_include_pmb_details(self) -> None:
        self.assertIs(backend_entrypoint.app, platform_api.app)
        current_user, claim = self._create_claim(f"CLM-ENTRYPOINT-{uuid4().hex[:8]}")

        readiness = platform_api.run_readiness(claim["id"], current_user=current_user)
        self.assertIn("pmb_decision", readiness)
        self.assertIn("benefit_route_decisions", readiness)
        self.assertIn("costing_preview", readiness)

        closure = platform_api.close_claim(
            claim["id"],
            request=ClaimClosureRequest(),
            current_user=current_user,
        )
        self.assertIn("pmb_decision", closure)
        self.assertIn("benefit_route_decisions", closure)
        self.assertIn("costing_preview", closure)
        self.assertIn("validation_summary", closure)

        validation = platform_api.post_closure_validate(claim["id"], current_user=current_user)
        self.assertIn("pmb_decision", validation)
        self.assertIn("benefit_route_decisions", validation)
        self.assertIn("costing_preview", validation)
        self.assertIn("validation_summary", validation)

        claim_detail = platform_api.get_claim(claim["id"], current_user=current_user)
        self.assertEqual(claim_detail["pmb_status"], "confirmed")
        self.assertIsNotNone(claim_detail["latest_pmb_decision"])
        self.assertIsNotNone(claim_detail["latest_benefit_route_decision"])
        self.assertIsNotNone(claim_detail["latest_costing_preview"])

        evidence_payload = platform_api.claim_evidence(claim["id"], current_user=current_user)
        self.assertTrue(evidence_payload["documents"])
        self.assertTrue(evidence_payload["pmb_decisions"])
        self.assertTrue(evidence_payload["benefit_route_decisions"])
        self.assertIn(
            "PMB_DETECTION_AND_BENEFIT_ROUTING",
            {item["event_type"] for item in evidence_payload["audit_events"]},
        )
        self.assertIn(
            "BENEFIT_ROUTED_PMB_BENEFIT_BUCKET",
            {item["event_type"] for item in evidence_payload["audit_events"]},
        )
        self.assertIn(
            "COSTING_PREVIEW_COMPUTED",
            {item["event_type"] for item in evidence_payload["audit_events"]},
        )

    def test_diagnosis_endpoints_unblock_primary_icd_flow(self) -> None:
        current_user = self._current_user()
        claim = platform_api.create_claim(
            {
                "claim_number": f"CLM-DIAG-{uuid4().hex[:8]}",
                "patient_id": 1,
                "provider_id": 2,
                "provider_is_dsp": False,
                "non_dsp_access_type": "VOLUNTARY",
                "member_number": "MEM220002",
                "service_date": "2026-04-16",
                "diagnoses": [],
                "line_items": [
                    {
                        "line_id": "1",
                        "service_code": "CONS001",
                        "service_description": "Consultation",
                        "quantity": 1,
                        "unit_price": 500,
                        "claimed_amount": 500,
                    }
                ],
            },
            current_user=current_user,
        )
        readiness = platform_api.run_readiness(claim["id"], current_user=current_user)
        blocker = readiness["validation_summary"]["blockers"][0]
        self.assertEqual(blocker["reason_code"], "ICD_MISSING_PRIMARY")
        self.assertEqual(blocker["action"]["type"], "NAVIGATE_DIAGNOSES")
        self.assertEqual(blocker["action"]["target"], "diagnoses")
        self.assertEqual(blocker["action_target"], "diagnoses")

        add_result = platform_api.add_claim_diagnosis(
            claim["id"],
            {"icd10_code": "I10", "is_primary": True, "source": "UserEntry"},
            current_user=current_user,
        )
        self.assertEqual(add_result["diagnoses"][0]["icd10_code"], "I10")
        diagnoses = platform_api.get_claim_diagnoses(claim["id"], current_user=current_user)
        self.assertTrue(diagnoses[0]["is_primary"])

        updated_readiness = platform_api.run_readiness(claim["id"], current_user=current_user)
        self.assertEqual(updated_readiness["pmb_decision"]["pmb_status"], "REVIEW_REQUIRED")
        self.assertEqual(updated_readiness["benefit_routing_decision"]["route"], "PMB_REVIEW_QUEUE")
        self.assertEqual(updated_readiness["costing_preview"]["pricing_basis"], "NON_DSP_VOLUNTARY")

    def test_login_scope_filters_tenants_practices_and_provider_directory(self) -> None:
        medhealth = self._current_user()
        self.assertEqual(medhealth["tenant_id"], "tenant-sa-demo")
        medhealth_tenants = platform_api.list_tenants(current_user=medhealth)
        self.assertEqual(len(medhealth_tenants), 1)
        self.assertEqual(medhealth_tenants[0]["id"], "tenant-sa-demo")
        medhealth_practices = platform_api.list_practices(current_user=medhealth)
        self.assertTrue(medhealth_practices)
        medhealth_providers = platform_api.list_providers(current_user=medhealth)
        self.assertTrue(medhealth_providers)
        self.assertTrue(all(item["tenant_id"] == "tenant-sa-demo" for item in medhealth_providers))

        coastal_payload = platform_api.login(LoginRequest(username="auditor", password="auditor123"))
        coastal = platform_api.get_current_user(f"Bearer {coastal_payload['access_token']}")
        self.assertEqual(coastal["tenant_id"], "tenant-coastal-care")
        coastal_providers = platform_api.list_providers(current_user=coastal)
        self.assertTrue(coastal_providers)
        self.assertTrue(all(item["tenant_id"] == "tenant-coastal-care" for item in coastal_providers))

    def test_provider_onboarding_can_attach_doctor_to_new_practice(self) -> None:
        current_user = self._current_user()
        practice = platform_api.create_practice(
            {
                "practice_number": "0198765",
                "name": "Johannesburg Oncology Centre",
                "city": "Johannesburg",
                "province": "Gauteng",
                "phone": "+27 11 555 0101",
                "email": "admin@jocentre.co.za",
            },
            current_user=current_user,
        )
        provider = platform_api.create_provider(
            {
                "name": "Dr. S Khanyile",
                "npi": "MP200001",
                "hpcsa_number": "MP200001",
                "practice_id": practice["id"],
                "practice_number": practice["practice_number"],
                "specialty": "Oncology",
                "discipline": "SPECIALIST",
                "email": "dr.khanyile@jocentre.co.za",
                "phone": "+27 11 555 0102",
                "onboarding_status": "verified",
            },
            current_user=current_user,
        )
        self.assertEqual(provider["tenant_id"], current_user["tenant_id"])
        self.assertEqual(provider["practice_id"], practice["id"])
        self.assertEqual(provider["onboarding_status"], "verified")
        listed = platform_api.list_providers(current_user=current_user)
        self.assertTrue(any(item["id"] == provider["id"] for item in listed))

    def test_get_claim_includes_workflow_and_onboarding_metadata(self) -> None:
        current_user, claim = self._create_claim(f"CLM-WORKFLOW-{uuid4().hex[:8]}")

        retrieved = platform_api.get_claim(claim["id"], current_user=current_user)

        self.assertIn("eligible_roles", retrieved)
        self.assertIn("last_completed_role", retrieved)
        self.assertIn("role_action_history", retrieved)
        self.assertIn("affected_roles", retrieved)
        self.assertIn("state_progression", retrieved)
        self.assertIn("onboarding_status", retrieved)
        self.assertIn("onboarding_blockers", retrieved)
        self.assertIn("onboarding_actions", retrieved)
        self.assertTrue(isinstance(retrieved["state_progression"], list))

    def test_run_readiness_returns_workflow_and_onboarding_metadata(self) -> None:
        current_user, claim = self._create_claim(f"CLM-READYFLOW-{uuid4().hex[:8]}")

        readiness = platform_api.run_readiness(claim["id"], current_user=current_user)

        self.assertIn("affected_roles", readiness)
        self.assertIn("state_progression", readiness)
        self.assertTrue(isinstance(readiness.get("affected_roles"), list))
        self.assertTrue(isinstance(readiness.get("state_progression"), list))
        self.assertIn("onboarding_blockers", readiness)
        self.assertIn("onboarding_actions", readiness)

    def test_provider_onboarding_appears_in_claim_context(self) -> None:
        current_user = self._current_user()
        provider = platform_api.create_provider(
            {
                "name": "Dr. Test Pending",
                "npi": f"TEST-{uuid4().hex[:6]}",
                "hpcsa_number": f"HP-{uuid4().hex[:6]}",
                "practice_id": current_user.get("practice_id"),
                "practice_number": "0198765",
                "email": "test@example.com",
                "phone": "+27 11 555 0001",
                "onboarding_status": "pending_review",
            },
            current_user=current_user,
        )

        claim = platform_api.create_claim(
            {
                "claim_number": f"CLM-ONBOARD-{uuid4().hex[:8]}",
                "patient_id": 1,
                "provider_id": provider["id"],
                "member_number": "MEM220099",
                "service_date": "2026-04-16",
                "diagnoses": [{"seq": 1, "icd10": "I10", "diagnosis_type": "PRIMARY"}],
                "line_items": [
                    {
                        "line_id": "1",
                        "service_code": "CONS001",
                        "service_description": "Consultation",
                        "quantity": 1,
                        "unit_price": 1500,
                        "claimed_amount": 1500,
                        "diagnosis_refs": [1],
                    }
                ],
            },
            current_user=current_user,
        )

        retrieved = platform_api.get_claim(claim["id"], current_user=current_user)
        self.assertTrue(len(retrieved.get("onboarding_blockers", [])) > 0)
        self.assertTrue(any(item["type"] == "PROVIDER_ONBOARDING" for item in retrieved["onboarding_blockers"]))

    def test_multi_user_claim_update_scenario(self) -> None:
        user_a_payload = platform_api.login(LoginRequest(username="demo.user", password="password123"))
        user_b_payload = platform_api.login(LoginRequest(username="finance", password="finance123"))
        user_a = platform_api.get_current_user(f"Bearer {user_a_payload['access_token']}")
        user_b = platform_api.get_current_user(f"Bearer {user_b_payload['access_token']}")

        claim = platform_api.create_claim(
            {
                "claim_number": f"CLM-MULTI-{uuid4().hex[:8]}",
                "patient_id": 1,
                "provider_id": 1,
                "member_number": "MEM220111",
                "service_date": "2026-04-16",
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
                        "unit_price": 750,
                        "claimed_amount": 750,
                        "diagnosis_refs": [1],
                    }
                ],
            },
            current_user=user_a,
        )

        initial_claim_b = platform_api.get_claim(claim["id"], current_user=user_b)
        self.assertEqual(initial_claim_b["status"], "draft")

        platform_api.run_readiness(claim["id"], current_user=user_a)
        platform_api.close_claim(claim["id"], request=ClaimClosureRequest(), current_user=user_a)

        updated_claim_b = platform_api.get_claim(claim["id"], current_user=user_b)
        self.assertEqual(updated_claim_b["status"], "closed")
        self.assertTrue(len(updated_claim_b.get("state_progression", [])) > 0)
