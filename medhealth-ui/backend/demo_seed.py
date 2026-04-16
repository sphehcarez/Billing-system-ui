from __future__ import annotations

import json
from typing import Any, Dict

from platform_core import ClaimClosureRequest, ClaimSubmissionRequest, PolicyProfile, ReferenceVersion, stable_hash, utc_now
from postgres_store import PersistentPlatformStore


DEMO_SCHEME = "SCHEMEA"
DEMO_OPTION = "OPT1"
DEMO_POLICY_PROFILE = f"{DEMO_SCHEME}:{DEMO_OPTION}"
LEGACY_SCHEME = "SCHEME_A"
LEGACY_OPTION = "OPTION_X"


def seed_reference_data(store: PersistentPlatformStore) -> Dict[str, Any]:
    store.reference_versions["icd10_mit"] = ReferenceVersion(
        reference_key="icd10_mit",
        version="MIT-DEMO-2026-04",
        effective_from="2026-04-01",
    )
    for key, version in {
        "pmb": "PMB-DEMO-2026-04",
        "tariff": "TARIFF-DEMO-2026-04",
        "provider_registry": "PROVIDER-DEMO-2026-04",
        "nappi": "NAPPI-DEMO-2026-04",
    }.items():
        store.reference_versions[key] = ReferenceVersion(reference_key=key, version=version, effective_from="2026-04-01")

    _ensure_demo_users(store)
    _ensure_demo_patients(store)
    _ensure_demo_providers(store)
    _ensure_demo_rules(store)
    _ensure_demo_policy_profile(store)
    _ensure_demo_settings(store)
    _ensure_demo_reference_rows(store)
    store.save()
    return {
        "users": len(store.users),
        "patients": len(store.patients),
        "providers": len(store.providers),
        "icd10_reference": len(store.icd10_codes),
        "pmb_conditions": len(store.pmb_conditions),
        "pmb_mappings": len(store.pmb_mapping_rules),
        "policy_profiles": sum(len(items) for items in store.policy_profiles.values()),
    }


def seed_uat_scenarios(store: PersistentPlatformStore) -> Dict[str, int]:
    scenario_ids: Dict[str, int] = {}
    scenario_ids["CLEAN_SUCCESS"] = _seed_claim(
        store,
        "CLEAN_SUCCESS",
        {
            "claim_number": "UAT-CLM-CLEAN-SUCCESS",
            "claim_reference": "UAT-REF-CLEAN-SUCCESS",
            "invoice_number": "UAT-INV-CLEAN-SUCCESS",
            "patient_id": _patient_id_by_mrn(store, "DEMO-MRN-001"),
            "provider_id": _provider_id_by_practice(store, "DEMO-PRACTICE-001"),
            "provider_is_dsp": True,
            "member_number": "MEM900001",
            "scheme_id": DEMO_SCHEME,
            "plan_option_id": DEMO_OPTION,
            "service_date": "2026-04-16",
            "diagnoses": [{"seq": 1, "icd10": "I10", "diagnosis_type": "PRIMARY"}],
            "attachments": [
                {
                    "attachment_type": "MOTIVATION",
                    "file_name": "demo-clean-success.pdf",
                    "storage_ref": "seed/demo-clean-success.pdf",
                    "file_hash": stable_hash("demo-clean-success"),
                    "uploaded_by": "system",
                }
            ],
            "line_items": [
                {
                    "line_id": "1",
                    "service_code": "CONS001",
                    "service_description": "Consultation",
                    "quantity": 1,
                    "unit_price": 900,
                    "claimed_amount": 900,
                    "diagnosis_refs": [1],
                }
            ],
        },
        actions=["readiness", "close", "validate", "payload", "submit:direct:uat-clean-success"],
    )

    scenario_ids["MISSING_PRIMARY_ICD"] = _seed_claim(
        store,
        "MISSING_PRIMARY_ICD",
        {
            "claim_number": "UAT-CLM-MISSING-PRIMARY",
            "claim_reference": "UAT-REF-MISSING-PRIMARY",
            "invoice_number": "UAT-INV-MISSING-PRIMARY",
            "patient_id": _patient_id_by_mrn(store, "DEMO-MRN-002"),
            "provider_id": _provider_id_by_practice(store, "DEMO-PRACTICE-002"),
            "provider_is_dsp": False,
            "non_dsp_access_type": "VOLUNTARY",
            "member_number": "MEM900002",
            "scheme_id": DEMO_SCHEME,
            "plan_option_id": DEMO_OPTION,
            "service_date": "2026-04-16",
            "diagnoses": [],
            "line_items": [
                {
                    "line_id": "1",
                    "service_code": "CONS001",
                    "service_description": "Consultation",
                    "quantity": 1,
                    "unit_price": 450,
                    "claimed_amount": 450,
                }
            ],
        },
        actions=["readiness"],
    )

    scenario_ids["PMB_REVIEW_REQUIRED"] = _seed_claim(
        store,
        "PMB_REVIEW_REQUIRED",
        {
            "claim_number": "UAT-CLM-PMB-REVIEW",
            "claim_reference": "UAT-REF-PMB-REVIEW",
            "invoice_number": "UAT-INV-PMB-REVIEW",
            "patient_id": _patient_id_by_mrn(store, "DEMO-MRN-003"),
            "provider_id": _provider_id_by_practice(store, "DEMO-PRACTICE-002"),
            "provider_is_dsp": False,
            "non_dsp_access_type": "VOLUNTARY",
            "member_number": "MEM900003",
            "scheme_id": DEMO_SCHEME,
            "plan_option_id": DEMO_OPTION,
            "service_date": "2026-04-16",
            "diagnoses": [{"seq": 1, "icd10": "E11.9", "diagnosis_type": "PRIMARY"}],
            "line_items": [
                {
                    "line_id": "1",
                    "service_code": "MED001",
                    "service_description": "Medication review",
                    "quantity": 1,
                    "unit_price": 650,
                    "claimed_amount": 650,
                    "diagnosis_refs": [1],
                    "requires_attachment": True,
                }
            ],
        },
        actions=["readiness", "close", "validate", "payload", "submit:switch:uat-pmb-review"],
    )

    scenario_ids["PARTIAL_PAYMENT"] = _seed_claim(
        store,
        "PARTIAL_PAYMENT",
        {
            "claim_number": "UAT-CLM-PARTIAL-PAYMENT",
            "claim_reference": "UAT-REF-PARTIAL-PAYMENT",
            "invoice_number": "UAT-INV-PARTIAL-PAYMENT",
            "patient_id": _patient_id_by_mrn(store, "DEMO-MRN-004"),
            "provider_id": _provider_id_by_practice(store, "DEMO-PRACTICE-001"),
            "provider_is_dsp": True,
            "member_number": "MEM900004",
            "scheme_id": DEMO_SCHEME,
            "plan_option_id": DEMO_OPTION,
            "service_date": "2026-04-16",
            "diagnoses": [{"seq": 1, "icd10": "J11.1", "diagnosis_type": "PRIMARY"}],
            "attachments": [
                {
                    "attachment_type": "MOTIVATION",
                    "file_name": "demo-partial-payment.pdf",
                    "storage_ref": "seed/demo-partial-payment.pdf",
                    "file_hash": stable_hash("demo-partial-payment"),
                    "uploaded_by": "system",
                }
            ],
            "line_items": [
                {
                    "line_id": "1",
                    "service_code": "CONS001",
                    "service_description": "Consultation",
                    "quantity": 1,
                    "unit_price": 900,
                    "claimed_amount": 900,
                    "diagnosis_refs": [1],
                }
            ],
        },
        actions=["readiness", "close", "validate", "payload", "submit:direct:uat-partial-payment"],
    )

    scenario_ids["MISMATCH_EXCEPTION"] = _seed_claim(
        store,
        "MISMATCH_EXCEPTION",
        {
            "claim_number": "UAT-CLM-MISMATCH",
            "claim_reference": "UAT-REF-MISMATCH",
            "invoice_number": "UAT-INV-MISMATCH",
            "patient_id": _patient_id_by_mrn(store, "DEMO-MRN-005"),
            "provider_id": _provider_id_by_practice(store, "DEMO-PRACTICE-001"),
            "provider_is_dsp": True,
            "member_number": "MEM900005",
            "scheme_id": DEMO_SCHEME,
            "plan_option_id": DEMO_OPTION,
            "service_date": "2026-04-16",
            "diagnoses": [{"seq": 1, "icd10": "E11.9", "diagnosis_type": "PRIMARY"}],
            "attachments": [
                {
                    "attachment_type": "MOTIVATION",
                    "file_name": "demo-mismatch.pdf",
                    "storage_ref": "seed/demo-mismatch.pdf",
                    "file_hash": stable_hash("demo-mismatch"),
                    "uploaded_by": "system",
                }
            ],
            "line_items": [
                {
                    "line_id": "1",
                    "service_code": "MED001",
                    "service_description": "Medication review",
                    "quantity": 1,
                    "unit_price": 750,
                    "claimed_amount": 750,
                    "diagnosis_refs": [1],
                }
            ],
        },
        actions=["readiness", "close", "validate", "payload", "submit:switch:uat-mismatch-exception"],
    )

    store.save()
    return scenario_ids


def _ensure_demo_users(store: PersistentPlatformStore) -> None:
    demo_users = [
        ("admin", "admin123", "Administrator", "admin@example.com"),
        ("demo.user", "password123", "Billing Specialist", "demo.user@example.com"),
        ("billing", "billing123", "Billing Specialist", "billing@example.com"),
        ("provider", "provider123", "Healthcare Provider", "provider@example.com"),
        ("finance", "finance123", "Finance Officer", "finance@example.com"),
        ("auditor", "auditor123", "Compliance Auditor", "auditor@example.com"),
    ]
    for username, password, role, email in demo_users:
        existing = next((item for item in store.users.values() if item.username == username), None)
        if existing:
            store.users[existing.id] = existing.model_copy(update={"email": email, "role": role})
            store.auth_users[username] = {"password": password, "role": role, "user_id": existing.id, "email": email}
            continue
        store.register_user(username, password, role, email)


def _ensure_demo_patients(store: PersistentPlatformStore) -> None:
    rows = [
        ("DEMO-MRN-001", "Anele Demo", "1986-01-10", "F"),
        ("DEMO-MRN-002", "Mpho Demo", "1984-02-10", "M"),
        ("DEMO-MRN-003", "Naledi Demo", "1990-03-10", "F"),
        ("DEMO-MRN-004", "Tumi Demo", "1988-04-10", "M"),
        ("DEMO-MRN-005", "Buhle Demo", "1992-05-10", "F"),
    ]
    for index, (mrn, name, dob, sex) in enumerate(rows, start=1):
        existing = next((item for item in store.patients.values() if item.mrn == mrn), None)
        payload = {
            "name": name,
            "mrn": mrn,
            "dob": dob,
            "sex": sex,
            "email": f"demo-patient-{index}@example.com",
            "phone": f"+27-82-700-10{index}",
            "status": "active",
            "created_at": existing.created_at if existing else utc_now(),
        }
        if existing:
            store.patients[existing.id] = existing.model_copy(update=payload)
        else:
            from platform_core import Patient

            next_id = store.next_numeric("patient")
            store.patients[next_id] = Patient(id=next_id, **payload)


def _ensure_demo_providers(store: PersistentPlatformStore) -> None:
    rows = [
        ("DEMO-PRACTICE-001", "DEMO-NPI-001", "DSP Demo Provider", True),
        ("DEMO-PRACTICE-002", "DEMO-NPI-002", "Non-DSP Demo Provider", False),
    ]
    for index, (practice_number, npi, name, is_dsp_provider) in enumerate(rows, start=1):
        existing = next((item for item in store.providers.values() if item.practice_number == practice_number), None)
        payload = {
            "name": name,
            "npi": npi,
            "practice_number": practice_number,
            "specialty": "General Practice",
            "discipline": "GP",
            "is_dsp_provider": is_dsp_provider,
            "email": f"demo-provider-{index}@example.com",
            "phone": f"+27-11-700-20{index}",
            "status": "active",
            "created_at": existing.created_at if existing else utc_now(),
        }
        if existing:
            store.providers[existing.id] = existing.model_copy(update=payload)
        else:
            from platform_core import Provider

            next_id = store.next_numeric("provider")
            store.providers[next_id] = Provider(id=next_id, **payload)


def _ensure_demo_rules(store: PersistentPlatformStore) -> None:
    store.rule_definitions.clear()
    store._seed_rules()


def _ensure_demo_policy_profile(store: PersistentPlatformStore) -> None:
    rule_ids = list(store.rule_definitions.keys())
    for scheme_id, option_id in [(DEMO_SCHEME, DEMO_OPTION), (LEGACY_SCHEME, LEGACY_OPTION)]:
        profile_id = f"{scheme_id}:{option_id}"
        store.policy_profiles[profile_id] = [
            PolicyProfile(
                policy_profile_id=profile_id,
                scheme_id=scheme_id,
                plan_option_id=option_id,
                version=1,
                effective_from="2026-04-01",
                status="ACTIVE",
                approved_by="admin",
                approved_at=utc_now(),
                runtime_toggles={
                    "icdEnforcementMode": "BLOCK",
                    "requirePreauthForCodes": ["PROC_PREAUTH", "THEATRE001"],
                    "allowClosureWithWarnings": True,
                    "requireSupervisorOverrideOnWarnings": False,
                    "defaultSubmissionChannel": "DIRECT",
                    "memberNumberRegex": r"^MEM\d{6}$",
                    "autoFlagPMBFromICD10": True,
                    "autoRoutePMBWhenMappingAllows": True,
                    "pmbEvidenceMode": "WARN",
                },
                rule_ids=rule_ids,
            )
        ]


def _ensure_demo_settings(store: PersistentPlatformStore) -> None:
    store.settings.update(
        {
            "scheme": DEMO_SCHEME,
            "option": DEMO_OPTION,
            "policy_profile_id": DEMO_POLICY_PROFILE,
            "policy_version": 1,
            "demo_mode": True,
        }
    )


def _ensure_demo_reference_rows(store: PersistentPlatformStore) -> None:
    version = store.reference_versions["icd10_mit"].version
    for code, description in {
        "J11.1": "DEMO influenza with respiratory manifestations",
        "I10": "DEMO essential hypertension",
        "E11.9": "DEMO type 2 diabetes mellitus without complications",
        "Z00.0": "DEMO general adult medical examination",
    }.items():
        from platform_core import ICD10Code

        store.icd10_codes[code] = ICD10Code(
            code=code,
            description=description,
            version=version,
            active=True,
            effective_from="2026-04-01",
            source="DEMO business-owned production data required",
            status="ACTIVE",
        )

    from platform_core import PMBCondition, PMBMappingRule, BenefitRouteRule, TariffRate, PMBPaymentPolicy

    store.pmb_conditions["DEMO_DTP_001"] = PMBCondition(
        condition_id="DEMO_DTP_001",
        name="DEMO diagnosis treatment pair",
        type="DTP",
        descriptor="DEMO DTP evidence descriptor",
        category="DEMO_ONLY",
        metadata={"dataset_owner": "business-owned in production", "demo": True},
        evidence_requirements=["MOTIVATION"],
        confirmation_flags=["demo_descriptor_present"],
        active=True,
        effective_from="2026-04-01",
        source="DEMO business-owned production data required",
        status="ACTIVE",
    )
    store.pmb_conditions["DEMO_CDL_001"] = PMBCondition(
        condition_id="DEMO_CDL_001",
        name="DEMO chronic disease list condition",
        type="CDL",
        descriptor="DEMO CDL evidence descriptor",
        category="DEMO_ONLY",
        metadata={"dataset_owner": "business-owned in production", "demo": True},
        evidence_requirements=["MOTIVATION"],
        confirmation_flags=["demo_descriptor_present"],
        active=True,
        effective_from="2026-04-01",
        source="DEMO business-owned production data required",
        status="ACTIVE",
    )

    store.pmb_mapping_rules["DEMO_MAP_J111"] = PMBMappingRule(
        mapping_id="DEMO_MAP_J111",
        icd10_code="J11.1",
        pmb_condition_id="DEMO_DTP_001",
        match_type="EXACT",
        version=1,
        effective_from="2026-04-01",
        confidence="HIGH",
        auto_route_allowed=True,
        required_evidence_types=["MOTIVATION"],
        active=True,
        status="ACTIVE",
        source="DEMO business-owned production data required",
    )
    store.pmb_mapping_rules["DEMO_MAP_I10"] = PMBMappingRule(
        mapping_id="DEMO_MAP_I10",
        icd10_code="I10",
        pmb_condition_id="DEMO_DTP_001",
        match_type="EXACT",
        version=1,
        effective_from="2026-04-01",
        confidence="HIGH",
        auto_route_allowed=True,
        required_evidence_types=["MOTIVATION"],
        active=True,
        status="ACTIVE",
        source="DEMO business-owned production data required",
    )
    store.pmb_mapping_rules["DEMO_MAP_E119"] = PMBMappingRule(
        mapping_id="DEMO_MAP_E119",
        icd10_code="E11.9",
        pmb_condition_id="DEMO_CDL_001",
        match_type="PREFIX",
        version=1,
        effective_from="2026-04-01",
        confidence="HIGH",
        auto_route_allowed=True,
        required_evidence_types=["MOTIVATION"],
        active=True,
        status="ACTIVE",
        source="DEMO business-owned production data required",
    )

    for scheme_id, option_id, key_suffix in [
        (DEMO_SCHEME, DEMO_OPTION, "DEMO"),
        (LEGACY_SCHEME, LEGACY_OPTION, "LEGACY"),
    ]:
        store.benefit_route_rules[f"{key_suffix}_ROUTE_RULE"] = BenefitRouteRule(
            rule_id=f"{key_suffix}_ROUTE_RULE",
            scheme_id=scheme_id,
            plan_option_id=option_id,
            route_when_confirmed="PMB_BENEFIT_BUCKET",
            route_when_possible="PMB_REVIEW_QUEUE",
            route_when_missing_evidence="PMB_REVIEW_QUEUE",
            auto_route_possible_matches=False,
            active=True,
            effective_from="2026-04-01",
            source="DEMO business-owned production data required",
        )

        for rate_id, tariff_code, dsp_flag, rate_amount in [
            (f"{key_suffix}_RATE_CONS001_DSP", "CONS001", True, 900),
            (f"{key_suffix}_RATE_CONS001_NONDSP", "CONS001", False, 650),
            (f"{key_suffix}_RATE_MED001_DSP", "MED001", True, 750),
            (f"{key_suffix}_RATE_MED001_NONDSP", "MED001", False, 550),
        ]:
            store.tariff_rates[rate_id] = TariffRate(
                rate_id=rate_id,
                scheme_id=scheme_id,
                plan_option_id=option_id,
                tariff_code=tariff_code,
                dsp_flag=dsp_flag,
                rate_amount=rate_amount,
                unit="PER_SERVICE",
                active=True,
                effective_from="2026-04-01",
                source="DEMO business-owned production data required",
            )

        store.pmb_payment_policies[f"{key_suffix}_PMB_POLICY"] = PMBPaymentPolicy(
            policy_id=f"{key_suffix}_PMB_POLICY",
            scheme_id=scheme_id,
            plan_option_id=option_id,
            pay_in_full_requires_dsp=True,
            voluntary_non_dsp_rate_mode="DSP_RATE",
            involuntary_non_dsp_no_copay=True,
            active=True,
            effective_from="2026-04-01",
            source="DEMO business-owned production data required",
        )


def _seed_claim(store: PersistentPlatformStore, scenario_key: str, payload: Dict[str, Any], actions: list[str]) -> int:
    existing = next((item for item in store.claims.values() if item.claim_number == payload["claim_number"]), None)
    if existing:
        _purge_claim(store, existing.id)

    claim = store.create_claim({**payload, "scenario_key": scenario_key}, actor="system", role="Seeder")
    for action in actions:
        if action == "readiness":
            store.run_readiness(claim.id, "system", "Seeder")
        elif action == "close":
            store.close_claim(claim.id, ClaimClosureRequest(), "system", "Seeder")
        elif action == "validate":
            store.run_post_closure_validation(claim.id, "system", "Seeder")
        elif action == "payload":
            store.build_payload(claim.id, "system", "Seeder")
        elif action.startswith("submit:"):
            _, channel, idem = action.split(":")
            store.submit_claim(
                claim.id,
                ClaimSubmissionRequest(channel=channel, idempotency_key=idem),
                "system",
                "Seeder",
            )
    return claim.id


def _purge_claim(store: PersistentPlatformStore, claim_id: int) -> None:
    claim = store.claims.pop(claim_id, None)
    if claim is None:
        return
    store.claim_versions.pop(claim_id, None)
    for key in [key for key in list(store.claim_history.keys()) if key.startswith(f"{claim_id}:")]:
        del store.claim_history[key]
    store.claim_diagnoses.pop(claim_id, None)
    deleted_readiness_run_ids = []
    deleted_submission_ids = []
    for collection in [
        store.billing_snapshots,
        store.decision_bundles,
        store.pmb_decisions,
        store.benefit_route_decisions,
        store.costing_previews,
        store.payloads,
        store.responses,
        store.financial_bundles,
        store.remittances,
        store.reconciliations,
    ]:
        for item_id in [item_id for item_id, item in collection.items() if getattr(item, "claim_id", None) == claim_id]:
            del collection[item_id]
    for item_id, item in list(store.readiness_runs.items()):
        if item.claim_id == claim_id:
            deleted_readiness_run_ids.append(item_id)
            del store.readiness_runs[item_id]
    for item in list(store.readiness_items.values()):
        if item.claim_id == claim_id:
            store.readiness_items.pop(item.item_id, None)
    for item_id, item in list(store.submissions.items()):
        if item.claim_id == claim_id:
            deleted_submission_ids.append(item_id)
            del store.submissions[item_id]
    for item_id in [
        item_id
        for item_id, item in store.transport_logs.items()
        if item.submission_id in deleted_submission_ids or store.submissions.get(item.submission_id) is None
    ]:
        del store.transport_logs[item_id]
    for idem_key, submission_id in list(store.idempotency_index.items()):
        if submission_id in deleted_submission_ids:
            del store.idempotency_index[idem_key]
    for payment_id in [payment_id for payment_id, item in store.payments.items() if item.claim_id == claim_id]:
        del store.payments[payment_id]
    for ledger_id in [ledger_id for ledger_id, item in store.ledger_entries.items() if item["claim_id"] == claim_id]:
        del store.ledger_entries[ledger_id]
    for audit_id in [audit_id for audit_id, item in store.audit_events.items() if item.entity_type == "claim" and item.entity_id == str(claim_id)]:
        del store.audit_events[audit_id]


def _patient_id_by_mrn(store: PersistentPlatformStore, mrn: str) -> int:
    return next(item.id for item in store.patients.values() if item.mrn == mrn)


def _provider_id_by_practice(store: PersistentPlatformStore, practice_number: str) -> int:
    return next(item.id for item in store.providers.values() if item.practice_number == practice_number)


def dumps_pretty(payload: Dict[str, Any]) -> str:
    return json.dumps(payload, indent=2, sort_keys=True)
