from __future__ import annotations

from sqlalchemy import text

from db_runtime import create_session
from demo_seed import DEMO_OPTION, DEMO_SCHEME


def test_pmb_detection_service_matches_mapping_from_database(reference_store):
    claim = reference_store.create_claim(
        {
            "claim_number": "TEST-DB-MAP-001",
            "claim_reference": "TEST-DB-MAP-001",
            "invoice_number": "TEST-INV-001",
            "patient_id": 1,
            "provider_id": 1,
            "member_number": "MEM910001",
            "scheme_id": DEMO_SCHEME,
            "plan_option_id": DEMO_OPTION,
            "service_date": "2026-04-16",
            "diagnoses": [{"seq": 1, "icd10": "I10", "diagnosis_type": "PRIMARY"}],
            "attachments": [
                {
                    "attachment_type": "MOTIVATION",
                    "file_name": "db-map-proof.pdf",
                    "storage_ref": "seed/db-map-proof.pdf",
                    "file_hash": "demo",
                    "uploaded_by": "tester",
                }
            ],
            "line_items": [{"line_id": "1", "service_code": "CONS001", "service_description": "Consultation", "quantity": 1, "unit_price": 900, "claimed_amount": 900, "diagnosis_refs": [1]}],
        },
        "tester",
        "Billing Specialist",
    )
    readiness = reference_store.run_readiness(claim.id, "tester", "Billing Specialist")
    assert readiness["pmb_decision"]["mapping_id"] == "DEMO_MAP_I10"
    assert readiness["pmb_decision"]["condition_id"] == "DEMO_DTP_001"
    assert readiness["pmb_decision"]["pmb_status"] == "CONFIRMED"


def test_costing_preview_service_uses_tariff_and_payment_policy(reference_store):
    claim = reference_store.create_claim(
        {
            "claim_number": "TEST-COST-001",
            "claim_reference": "TEST-COST-001",
            "invoice_number": "TEST-COST-001",
            "patient_id": 2,
            "provider_id": 2,
            "provider_is_dsp": False,
            "non_dsp_access_type": "VOLUNTARY",
            "member_number": "MEM910002",
            "scheme_id": DEMO_SCHEME,
            "plan_option_id": DEMO_OPTION,
            "service_date": "2026-04-16",
            "diagnoses": [{"seq": 1, "icd10": "E11.9", "diagnosis_type": "PRIMARY"}],
            "attachments": [
                {
                    "attachment_type": "MOTIVATION",
                    "file_name": "cost-proof.pdf",
                    "storage_ref": "seed/cost-proof.pdf",
                    "file_hash": "demo",
                    "uploaded_by": "tester",
                }
            ],
            "line_items": [{"line_id": "1", "service_code": "MED001", "service_description": "Medication review", "quantity": 1, "unit_price": 850, "claimed_amount": 850, "diagnosis_refs": [1]}],
        },
        "tester",
        "Billing Specialist",
    )
    readiness = reference_store.run_readiness(claim.id, "tester", "Billing Specialist")
    assert readiness["costing_preview"]["pricing_basis"] == "NON_DSP_VOLUNTARY"
    assert readiness["costing_preview"]["pmb_allowed_total"] == 750.0
    assert readiness["costing_preview"]["member_liability_estimate"] == 100.0


def test_readiness_endpoint_writes_decision_bundle_and_audit_event(client, admin_headers, reference_store):
    claim = reference_store.create_claim(
        {
            "claim_number": "TEST-ENDPOINT-READY-001",
            "claim_reference": "TEST-ENDPOINT-READY-001",
            "invoice_number": "TEST-ENDPOINT-READY-001",
            "patient_id": 1,
            "provider_id": 1,
            "member_number": "MEM910003",
            "service_date": "2026-04-16",
            "diagnoses": [{"seq": 1, "icd10": "I10", "diagnosis_type": "PRIMARY"}],
            "attachments": [
                {
                    "attachment_type": "MOTIVATION",
                    "file_name": "ready-proof.pdf",
                    "storage_ref": "seed/ready-proof.pdf",
                    "file_hash": "demo",
                    "uploaded_by": "tester",
                }
            ],
            "line_items": [{"line_id": "1", "service_code": "CONS001", "service_description": "Consultation", "quantity": 1, "unit_price": 900, "claimed_amount": 900, "diagnosis_refs": [1]}],
        },
        "tester",
        "Billing Specialist",
    )

    response = client.post(f"/api/claims/{claim.id}/readiness", headers=admin_headers)
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["pmb_decision"]["pmb_status"] == "CONFIRMED"

    session = create_session()
    try:
        bundle_count = session.execute(
            text("select count(*) from decision_bundles where claim_id = :claim_id and stage = 'READINESS'"),
            {"claim_id": claim.id},
        ).scalar_one()
        audit_count = session.execute(
            text("select count(*) from audit_events where entity_type = 'claim' and entity_id = :claim_id and event_type = 'READINESS_RUN'"),
            {"claim_id": str(claim.id)},
        ).scalar_one()
    finally:
        session.close()

    assert bundle_count == 1
    assert audit_count == 1


def test_evidence_packet_contains_persisted_pmb_mapping_routing_and_costing(client, admin_headers, uat_context):
    claim_id = uat_context["claim_ids"]["CLEAN_SUCCESS"]
    response = client.get(f"/api/audit/claims/{claim_id}/evidence-packet", headers=admin_headers)
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["pmb_decisions"]
    assert body["benefit_route_decisions"]
    assert body["costing_previews"]
    assert body["pmb_decisions"][0]["mapping_id"] == "DEMO_MAP_I10"
    assert body["benefit_route_decisions"][0]["route"] == "PMB_BENEFIT_BUCKET"


def test_idempotent_submission_returns_same_submission_id(client, admin_headers, reference_store):
    claim = reference_store.create_claim(
        {
            "claim_number": "TEST-IDEMPOTENT-001",
            "claim_reference": "TEST-IDEMPOTENT-001",
            "invoice_number": "TEST-IDEMPOTENT-001",
            "patient_id": 1,
            "provider_id": 1,
            "member_number": "MEM910004",
            "service_date": "2026-04-16",
            "diagnoses": [{"seq": 1, "icd10": "J11.1", "diagnosis_type": "PRIMARY"}],
            "attachments": [
                {
                    "attachment_type": "MOTIVATION",
                    "file_name": "idem-proof.pdf",
                    "storage_ref": "seed/idem-proof.pdf",
                    "file_hash": "demo",
                    "uploaded_by": "tester",
                }
            ],
            "line_items": [{"line_id": "1", "service_code": "CONS001", "service_description": "Consultation", "quantity": 1, "unit_price": 900, "claimed_amount": 900, "diagnosis_refs": [1]}],
        },
        "tester",
        "Billing Specialist",
    )
    client.post(f"/api/claims/{claim.id}/readiness", headers=admin_headers)
    client.post(f"/api/claims/{claim.id}/closure/confirm", headers=admin_headers, json={})
    client.post(f"/api/claims/{claim.id}/validation/post-closure", headers=admin_headers)

    first = client.post(
        f"/api/submissions/claims/{claim.id}",
        params={"channel": "DIRECT", "idempotency_key": "proof-idempotency-key"},
        headers=admin_headers,
    )
    second = client.post(
        f"/api/submissions/claims/{claim.id}",
        params={"channel": "DIRECT", "idempotency_key": "proof-idempotency-key"},
        headers=admin_headers,
    )
    assert first.status_code == 200, first.text
    assert second.status_code == 200, second.text
    assert first.json()["submission_id"] == second.json()["submission_id"]
    assert second.json()["idempotent_replay"] is True

    session = create_session()
    try:
        submission_count = session.execute(
            text("select count(*) from submissions where claim_id = :claim_id"),
            {"claim_id": claim.id},
        ).scalar_one()
        remittance_count = session.execute(
            text("select count(*) from remittances where claim_id = :claim_id"),
            {"claim_id": claim.id},
        ).scalar_one()
        reconciliation_count = session.execute(
            text("select count(*) from reconciliations where claim_id = :claim_id"),
            {"claim_id": claim.id},
        ).scalar_one()
        transport_log_count = session.execute(
            text(
                """
                select count(*)
                from transport_logs tl
                join submissions s on s.submission_id = tl.submission_id
                where s.claim_id = :claim_id
                """
            ),
            {"claim_id": claim.id},
        ).scalar_one()
    finally:
        session.close()

    assert submission_count == 1
    assert remittance_count == 1
    assert reconciliation_count == 1
    assert transport_log_count >= 2
