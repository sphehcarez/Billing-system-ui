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
    assert readiness["pmb_decision"]["condition_name"] == "DEMO diagnosis treatment pair"
    assert readiness["pmb_decision"]["auto_flagged"] is True
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


def test_post_closure_diagnosis_link_warning_is_resolvable_and_persisted(client, admin_headers, reference_store):
    claim = reference_store.create_claim(
        {
            "claim_number": "TEST-LINK-FIX-001",
            "claim_reference": "TEST-LINK-FIX-001",
            "invoice_number": "TEST-LINK-FIX-001",
            "patient_id": 1,
            "provider_id": 1,
            "member_number": "MEM910005",
            "service_date": "2026-04-16",
            "diagnoses": [{"seq": 1, "icd10": "I10", "diagnosis_type": "PRIMARY"}],
            "attachments": [
                {
                    "attachment_type": "MOTIVATION",
                    "file_name": "link-fix.pdf",
                    "storage_ref": "seed/link-fix.pdf",
                    "file_hash": "demo",
                    "uploaded_by": "tester",
                }
            ],
            "line_items": [{"line_id": "1", "service_code": "CONS001", "service_description": "Consultation", "quantity": 1, "unit_price": 900, "claimed_amount": 900, "diagnosis_refs": []}],
        },
        "tester",
        "Billing Specialist",
    )
    client.post(f"/api/claims/{claim.id}/readiness", headers=admin_headers)
    client.post(f"/api/claims/{claim.id}/closure/confirm", headers=admin_headers, json={})
    warned = client.post(f"/api/claims/{claim.id}/validation/post-closure", headers=admin_headers)
    assert warned.status_code == 200, warned.text
    assert warned.json()["validation_summary"]["warnings"][0]["reason_code"] == "DIAGNOSIS_LINK_MISSING"

    diagnoses = client.get(f"/api/claims/{claim.id}/diagnoses", headers=admin_headers).json()
    diagnosis_id = diagnoses[0]["diagnosis_id"]
    fixed = client.put(
        f"/api/claims/{claim.id}/line-items/1/diagnosis-links",
        headers=admin_headers,
        json={"diagnosis_ids": [diagnosis_id]},
    )
    assert fixed.status_code == 200, fixed.text
    validation = fixed.json()["post_closure_validation"]
    assert validation["validation_summary"]["warnings"] == []

    session = create_session()
    try:
        line_count = session.execute(
            text("select count(*) from claim_line_items where claim_id = :claim_id"),
            {"claim_id": claim.id},
        ).scalar_one()
        link_count = session.execute(
            text("select count(*) from claim_line_diagnosis_links where claim_id = :claim_id"),
            {"claim_id": claim.id},
        ).scalar_one()
        audit_count = session.execute(
            text(
                "select count(*) from audit_events where entity_type = 'claim' and entity_id = :claim_id and event_type = 'DIAGNOSIS_LINK_UPDATED'"
            ),
            {"claim_id": str(claim.id)},
        ).scalar_one()
    finally:
        session.close()

    assert line_count >= 1
    assert link_count == 1
    assert audit_count == 1


def test_patient_claim_context_endpoint_returns_claim_ready_dataset(client, admin_headers, uat_context):
    store = uat_context["store"]
    claim_id = uat_context["claim_ids"]["CLEAN_SUCCESS"]
    patient_id = store.claims[claim_id].patient_id
    response = client.get(f"/api/patients/{patient_id}/claim-context", headers=admin_headers)
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["claim_ready_profile"]["member_number"] == "MEM900001"
    assert body["claim_ready_profile"]["scheme_id"] == DEMO_SCHEME
    assert body["claim_ready_profile"]["plan_option_id"] == DEMO_OPTION
    assert body["claim_ready_profile"]["charge_capture"]["tariff_codes"] == ["CONS001"]
    assert body["claim_ready_profile"]["consent"]["status"] == "CAPTURED"


def test_structured_payload_tiles_expose_stage_completeness(client, admin_headers, uat_context):
    claim_id = uat_context["claim_ids"]["CLEAN_SUCCESS"]
    response = client.get(f"/api/claims/{claim_id}/payloads/1/structured", headers=admin_headers)
    assert response.status_code == 200, response.text
    body = response.json()
    tiles = {item["stage_id"]: item for item in body["structured_tiles"]}
    assert tiles["diagnoses"]["status"] == "complete"
    assert tiles["line_items"]["status"] == "complete"
    assert tiles["routing"]["status"] == "complete"


def test_edi_submit_writes_artifact_and_transport_logs(client, admin_headers, reference_store):
    claim = reference_store.create_claim(
        {
            "claim_number": "TEST-EDI-001",
            "claim_reference": "TEST-EDI-001",
            "invoice_number": "TEST-EDI-001",
            "patient_id": 1,
            "provider_id": 1,
            "member_number": "MEM910006",
            "service_date": "2026-04-16",
            "diagnoses": [{"seq": 1, "icd10": "J11.1", "diagnosis_type": "PRIMARY"}],
            "attachments": [
                {
                    "attachment_type": "MOTIVATION",
                    "file_name": "edi-proof.pdf",
                    "storage_ref": "seed/edi-proof.pdf",
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

    response = client.post(
        f"/api/claims/{claim.id}/payloads/1/edi/submit",
        params={"channel": "SWITCH", "idempotency_key": "edi-submit-proof"},
        headers=admin_headers,
    )
    assert response.status_code == 200, response.text
    body = response.json()
    events = {item["event"] for item in body["transport_logs"]}
    assert {"EDI_GENERATED", "EDI_VALIDATED", "EDI_SUBMITTED"}.issubset(events)

    session = create_session()
    try:
        artifact_count = session.execute(
            text("select count(*) from edi_artifacts where claim_id = :claim_id"),
            {"claim_id": claim.id},
        ).scalar_one()
        transport_log_count = session.execute(
            text("select count(*) from transport_logs where claim_id = :claim_id and event like 'EDI_%'"),
            {"claim_id": claim.id},
        ).scalar_one()
    finally:
        session.close()

    assert artifact_count >= 1
    assert transport_log_count >= 3


def test_pmb_not_detected_includes_explanation_and_admin_action(reference_store):
    claim = reference_store.create_claim(
        {
            "claim_number": "TEST-PMB-NOMATCH-001",
            "claim_reference": "TEST-PMB-NOMATCH-001",
            "invoice_number": "TEST-PMB-NOMATCH-001",
            "patient_id": 1,
            "provider_id": 1,
            "member_number": "MEM910007",
            "service_date": "2026-04-16",
            "diagnoses": [{"seq": 1, "icd10": "Z00.0", "diagnosis_type": "PRIMARY"}],
            "line_items": [{"line_id": "1", "service_code": "CONS001", "service_description": "Consultation", "quantity": 1, "unit_price": 900, "claimed_amount": 900, "diagnosis_refs": []}],
        },
        "tester",
        "Billing Specialist",
    )
    readiness = reference_store.run_readiness(claim.id, "tester", "Billing Specialist")
    assert readiness["pmb_decision"]["pmb_status"] == "NOT_DETECTED"
    assert readiness["pmb_decision"]["detection_reason"] == "NO_MATCH"
    assert readiness["pmb_decision"]["evaluated_icd10_list"] == ["Z00.0"]
    assert readiness["pmb_decision"]["action"]["target"] == "PMB_MAPPING_ADMIN"
