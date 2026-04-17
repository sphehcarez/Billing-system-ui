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
    _ensure_demo_schemes(store)
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


def seed_realistic_scenarios(store: PersistentPlatformStore) -> Dict[str, int]:
    """Seed realistic claim scenarios across SA schemes and providers"""
    scenario_ids: Dict[str, int] = {}
    
    # Scenario 6: Multiple diagnoses claim
    scenario_ids["MULTIPLE_DIAGNOSES"] = _seed_claim(
        store, "MULTIPLE_DIAGNOSES", {
            "claim_number": "REAL-CLM-MULTI-DIA-001",
            "patient_id": _patient_id_by_mrn(store, "DH-MRN-001"),
            "provider_id": _provider_id_by_practice(store, "NPI-ZA-001"),
            "provider_is_dsp": True,
            "member_number": "DH-MEM-001",
            "scheme_id": "DH",
            "plan_option_id": "OPT2",
            "service_date": "2026-04-14",
            "diagnoses": [
                {"seq": 1, "icd10": "I10", "diagnosis_type": "PRIMARY"},
                {"seq": 2, "icd10": "E11.9", "diagnosis_type": "SECONDARY"},
                {"seq": 3, "icd10": "E78.5", "diagnosis_type": "TERTIARY"},
            ],
            "line_items": [
                {"line_id": "1", "service_code": "CONS002", "service_description": "Extended consultation", 
                 "quantity": 1, "unit_price": 1200, "claimed_amount": 1200, "diagnosis_refs": [1, 2, 3]}
            ],
        },
        actions=["readiness", "close", "validate", "payload"],
    )
    
    # Scenario 7: High-value surgical claim
    scenario_ids["HIGH_VALUE_CLAIM"] = _seed_claim(
        store, "HIGH_VALUE_CLAIM", {
            "claim_number": "REAL-CLM-SURGERY-001",
            "patient_id": _patient_id_by_mrn(store, "GEMS-MRN-001"),
            "provider_id": _provider_id_by_practice(store, "NPI-ZA-002"),
            "provider_is_dsp": True,
            "member_number": "GEMS-MEM-001",
            "scheme_id": "GEMS",
            "plan_option_id": "OPT2",
            "service_date": "2026-04-13",
            "diagnoses": [{"seq": 1, "icd10": "I21.9", "diagnosis_type": "PRIMARY"}],
            "line_items": [
                {"line_id": "1", "service_code": "SURG001", "service_description": "Cardiac surgery", 
                 "quantity": 1, "unit_price": 45000, "claimed_amount": 45000, "diagnosis_refs": [1], "requires_attachment": True}
            ],
        },
        actions=["readiness"],
    )
    
    # Scenario 8: Non-DSP voluntary claim
    scenario_ids["NON_DSP_VOLUNTARY"] = _seed_claim(
        store, "NON_DSP_VOLUNTARY", {
            "claim_number": "REAL-CLM-NONDSP-VOL-001",
            "patient_id": _patient_id_by_mrn(store, "BON-MRN-001"),
            "provider_id": _provider_id_by_practice(store, "NPI-ZA-008"),
            "provider_is_dsp": False,
            "non_dsp_access_type": "VOLUNTARY",
            "member_number": "BON-MEM-001",
            "scheme_id": "BON",
            "plan_option_id": "OPT2",
            "service_date": "2026-04-12",
            "diagnoses": [{"seq": 1, "icd10": "J44.9", "diagnosis_type": "PRIMARY"}],
            "line_items": [
                {"line_id": "1", "service_code": "CONS001", "service_description": "Consultation", 
                 "quantity": 1, "unit_price": 400, "claimed_amount": 400, "diagnosis_refs": [1]}
            ],
        },
        actions=["readiness", "close"],
    )
    
    # Scenario 9: Non-DSP involuntary claim
    scenario_ids["NON_DSP_INVOLUNTARY"] = _seed_claim(
        store, "NON_DSP_INVOLUNTARY", {
            "claim_number": "REAL-CLM-NONDSP-INV-001",
            "patient_id": _patient_id_by_mrn(store, "MOM-MRN-001"),
            "provider_id": _provider_id_by_practice(store, "NPI-ZA-009"),
            "provider_is_dsp": False,
            "non_dsp_access_type": "INVOLUNTARY",
            "member_number": "MOM-MEM-001",
            "scheme_id": "MOM",
            "plan_option_id": "OPT2",
            "service_date": "2026-04-11",
            "diagnoses": [{"seq": 1, "icd10": "B34.1", "diagnosis_type": "PRIMARY"}],
            "line_items": [
                {"line_id": "1", "service_code": "CONS001", "service_description": "Emergency consultation", 
                 "quantity": 1, "unit_price": 600, "claimed_amount": 600, "diagnosis_refs": [1]}
            ],
        },
        actions=["readiness"],
    )
    
    # Scenario 10: Attachment required for high-value claim
    scenario_ids["ATTACHMENT_REQUIRED"] = _seed_claim(
        store, "ATTACHMENT_REQUIRED", {
            "claim_number": "REAL-CLM-ATTACH-001",
            "patient_id": _patient_id_by_mrn(store, "FED-MRN-001"),
            "provider_id": _provider_id_by_practice(store, "NPI-ZA-003"),
            "provider_is_dsp": True,
            "member_number": "FED-MEM-001",
            "scheme_id": "FED",
            "plan_option_id": "OPT1",
            "service_date": "2026-04-10",
            "diagnoses": [{"seq": 1, "icd10": "I50.9", "diagnosis_type": "PRIMARY"}],
            "line_items": [
                {"line_id": "1", "service_code": "MED002", "service_description": "Specialist cardiology review", 
                 "quantity": 1, "unit_price": 2500, "claimed_amount": 2500, "diagnosis_refs": [1], "requires_attachment": True}
            ],
            "attachments": [
                {"attachment_type": "REPORT", "file_name": "cardiology-report.pdf", 
                 "storage_ref": "seed/cardiology-report.pdf", "file_hash": stable_hash("cardiology"), "uploaded_by": "system"}
            ],
        },
        actions=["readiness", "close"],
    )
    
    # Scenario 11: Invalid ICD format
    scenario_ids["INVALID_ICD_FORMAT"] = _seed_claim(
        store, "INVALID_ICD_FORMAT", {
            "claim_number": "REAL-CLM-INVALID-ICD-001",
            "patient_id": _patient_id_by_mrn(store, "POL-MRN-001"),
            "provider_id": _provider_id_by_practice(store, "NPI-ZA-004"),
            "provider_is_dsp": True,
            "member_number": "POL-MEM-001",
            "scheme_id": "POL",
            "plan_option_id": "OPT1",
            "service_date": "2026-04-09",
            "diagnoses": [{"seq": 1, "icd10": "INVALID999", "diagnosis_type": "PRIMARY"}],
            "line_items": [
                {"line_id": "1", "service_code": "CONS001", "service_description": "Consultation", 
                 "quantity": 1, "unit_price": 450, "claimed_amount": 450}
            ],
        },
        actions=["readiness"],
    )
    
    # Scenario 12: Member not found (invalid membership)
    scenario_ids["MEMBER_NOT_FOUND"] = _seed_claim(
        store, "MEMBER_NOT_FOUND", {
            "claim_number": "REAL-CLM-MEMBER-NOT-FOUND-001",
            "patient_id": _patient_id_by_mrn(store, "DH-MRN-002"),
            "provider_id": _provider_id_by_practice(store, "NPI-ZA-005"),
            "provider_is_dsp": True,
            "member_number": "INVALID-MEM-999999",  # Invalid format
            "scheme_id": "DH",
            "plan_option_id": "OPT1",
            "service_date": "2026-04-08",
            "diagnoses": [{"seq": 1, "icd10": "M54.5", "diagnosis_type": "PRIMARY"}],
            "line_items": [
                {"line_id": "1", "service_code": "CONS001", "service_description": "Consultation", 
                 "quantity": 1, "unit_price": 450, "claimed_amount": 450, "diagnosis_refs": [1]}
            ],
        },
        actions=["readiness"],
    )
    
    # Scenario 13: Closed with warnings
    scenario_ids["CLOSED_WITH_WARNINGS"] = _seed_claim(
        store, "CLOSED_WITH_WARNINGS", {
            "claim_number": "REAL-CLM-WARNINGS-001",
            "patient_id": _patient_id_by_mrn(store, "GEMS-MRN-002"),
            "provider_id": _provider_id_by_practice(store, "NPI-ZA-006"),
            "provider_is_dsp": True,
            "member_number": "GEMS-MEM-002",
            "scheme_id": "GEMS",
            "plan_option_id": "OPT1",
            "service_date": "2026-04-07",
            "diagnoses": [{"seq": 1, "icd10": "F41.1", "diagnosis_type": "PRIMARY"}],
            "line_items": [
                {"line_id": "1", "service_code": "CONS001", "service_description": "Consultation", 
                 "quantity": 1, "unit_price": 550, "claimed_amount": 550, "diagnosis_refs": [1]}
            ],
        },
        actions=["readiness", "close"],
    )
    
    # Scenario 14: Expedited processing
    scenario_ids["EXPEDITED_PROCESSING"] = _seed_claim(
        store, "EXPEDITED_PROCESSING", {
            "claim_number": "REAL-CLM-EXPEDITED-001",
            "patient_id": _patient_id_by_mrn(store, "BON-MRN-002"),
            "provider_id": _provider_id_by_practice(store, "NPI-ZA-007"),
            "provider_is_dsp": True,
            "member_number": "BON-MEM-002",
            "scheme_id": "BON",
            "plan_option_id": "OPT2",
            "service_date": "2026-04-06",
            "diagnoses": [{"seq": 1, "icd10": "K21.0", "diagnosis_type": "PRIMARY"}],
            "line_items": [
                {"line_id": "1", "service_code": "CONS001", "service_description": "Consultation", 
                 "quantity": 1, "unit_price": 600, "claimed_amount": 600, "diagnosis_refs": [1]}
            ],
        },
        actions=["readiness", "close", "validate", "payload"],
    )
    
    # Scenario 15: Diagnosis link missing scenario
    scenario_ids["DIAGNOSIS_LINK_MISSING"] = _seed_claim(
        store, "DIAGNOSIS_LINK_MISSING", {
            "claim_number": "REAL-CLM-DIAGNOSIS-LINK-001",
            "patient_id": _patient_id_by_mrn(store, "MOM-MRN-002"),
            "provider_id": _provider_id_by_practice(store, "NPI-ZA-010"),
            "provider_is_dsp": False,
            "non_dsp_access_type": "VOLUNTARY",
            "member_number": "MOM-MEM-002",
            "scheme_id": "MOM",
            "plan_option_id": "OPT3",
            "service_date": "2026-04-05",
            "diagnoses": [
                {"seq": 1, "icd10": "M79.3", "diagnosis_type": "PRIMARY"},
                {"seq": 2, "icd10": "M54.5", "diagnosis_type": "SECONDARY"},
            ],
            "line_items": [
                {"line_id": "1", "service_code": "CONS001", "service_description": "Consultation", 
                 "quantity": 1, "unit_price": 500, "claimed_amount": 500},  # No diagnosis_refs
                {"line_id": "2", "service_code": "PHYS001", "service_description": "Physiotherapy", 
                 "quantity": 3, "unit_price": 300, "claimed_amount": 900},  # No diagnosis_refs
            ],
        },
        actions=["readiness"],
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
    # Original 5 demo patients (preserved for UAT scenarios)
    rows = [
        ("DEMO-MRN-001", "Anele Demo", "1986-01-10", "F"),
        ("DEMO-MRN-002", "Mpho Demo", "1984-02-10", "M"),
        ("DEMO-MRN-003", "Naledi Demo", "1990-03-10", "F"),
        ("DEMO-MRN-004", "Tumi Demo", "1988-04-10", "M"),
        ("DEMO-MRN-005", "Buhle Demo", "1992-05-10", "F"),
    ]
    
    # Extended realistic SA patients (30+)
    realistic_patients = [
        # Discovery Health members
        ("DH-MRN-001", "Anele Tshabalala", "1975-03-22", "F"),
        ("DH-MRN-002", "Sipho Nkomo", "1972-07-15", "M"),
        ("DH-MRN-003", "Lindiwe Khumalo", "1980-11-08", "F"),
        ("DH-MRN-004", "Thabo Mthembu", "1968-01-30", "M"),
        ("DH-MRN-005", "Nokuthula Dlamini", "1985-06-17", "F"),
        ("DH-MRN-006", "Lerato Molefe", "1990-09-04", "M"),
        # GEMS members
        ("GEMS-MRN-001", "Buhle Ngcobo", "1978-04-12", "F"),
        ("GEMS-MRN-002", "Sandile Ndaba", "1973-08-26", "M"),
        ("GEMS-MRN-003", "Nomvula Sithole", "1982-02-14", "F"),
        ("GEMS-MRN-004", "Thulani Khoza", "1976-10-19", "M"),
        ("GEMS-MRN-005", "Palesa Mokoena", "1988-05-03", "F"),
        # Bonitas members
        ("BON-MRN-001", "Amahle Nxumalo", "1981-12-07", "F"),
        ("BON-MRN-002", "Mandla Mngomezulu", "1974-06-20", "M"),
        ("BON-MRN-003", "Thandeka Nyathi", "1987-09-11", "F"),
        ("BON-MRN-004", "Sizwe Mthiyane", "1979-03-28", "M"),
        # Momentum members
        ("MOM-MRN-001", "Zandile Mahlangu", "1983-07-13", "F"),
        ("MOM-MRN-002", "Vusi Mavundla", "1970-11-25", "M"),
        ("MOM-MRN-003", "Nandi Zwane", "1986-01-09", "F"),
        ("MOM-MRN-004", "Mthunzi Xaba", "1977-04-22", "M"),
        # Fedhealth members
        ("FED-MRN-001", "Siphiwe Nkosi", "1982-08-16", "F"),
        ("FED-MRN-002", "Piet Venter", "1969-12-03", "M"),
        ("FED-MRN-003", "Grace Okafor", "1984-10-29", "F"),
        ("FED-MRN-004", "Frank Steyn", "1975-02-11", "M"),
        # Polmed members
        ("POL-MRN-001", "Jennifer Wong", "1981-05-20", "F"),
        ("POL-MRN-002", "Rajesh Patel", "1976-09-07", "M"),
        ("POL-MRN-003", "Fatima Hassan", "1988-03-14", "F"),
        ("POL-MRN-004", "Michael Chen", "1973-11-26", "M"),
    ]
    
    all_rows = rows + realistic_patients
    for index, (mrn, name, dob, sex) in enumerate(all_rows, start=1):
        existing = next((item for item in store.patients.values() if item.mrn == mrn), None)
        payload = {
            "name": name,
            "mrn": mrn,
            "dob": dob,
            "sex": sex,
            "email": f"{mrn.lower()}@patient.example.com",
            "phone": f"+27-{index % 2 + 71}-{700 + index:03d}",
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
    
    # Extended realistic SA providers (10+)
    realistic_providers = [
        ("NPI-ZA-001", "NPI-ZA-001", "Dr. Thabo Mthembu", True),
        ("NPI-ZA-002", "NPI-ZA-002", "Dr. Lindiwe Khumalo", True),
        ("NPI-ZA-003", "NPI-ZA-003", "Prof. Sipho Nkomo", True),
        ("NPI-ZA-004", "NPI-ZA-004", "Dr. Naledi Dlamini", True),
        ("NPI-ZA-005", "NPI-ZA-005", "Dr. Thandeka Ngcobo", True),
        ("NPI-ZA-006", "NPI-ZA-006", "Prof. Mandla Khoza", True),
        ("NPI-ZA-007", "NPI-ZA-007", "Dr. Grace Okafor", True),
        ("NPI-ZA-008", "NPI-ZA-008", "Dr. Piet Venter", False),
        ("NPI-ZA-009", "NPI-ZA-009", "Clinic: Soweto Health Centre", False),
        ("NPI-ZA-010", "NPI-ZA-010", "Clinic: Durban Community Medical", False),
    ]
    
    all_rows = rows + realistic_providers
    for index, (practice_number, npi, name, is_dsp_provider) in enumerate(all_rows, start=1):
        existing = next((item for item in store.providers.values() if item.practice_number == practice_number), None)
        payload = {
            "name": name,
            "npi": npi,
            "practice_number": practice_number,
            "specialty": "General Practice" if "Dr." in name or "Prof." in name else "Primary Health Care",
            "discipline": "GP" if "Dr." in name or "Prof." in name else "Clinic",
            "is_dsp_provider": is_dsp_provider,
            "email": f"{practice_number.lower()}@provider.example.com",
            "phone": f"+27-11-555-{1000 + index}",
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


def _ensure_demo_schemes(store: PersistentPlatformStore) -> None:
    """Ensure realistic South African medical scheme options exist"""
    schemes = [
        ("DH", "Discovery Health", [
            ("OPT1", "Classic", 80),
            ("OPT2", "Comprehensive", 90),
            ("OPT3", "Core", 70),
        ]),
        ("GEMS", "GEMS (Gees Everybody Medical Scheme)", [
            ("OPT1", "Standard", 75),
            ("OPT2", "Plus", 85),
        ]),
        ("BON", "Bonitas", [
            ("OPT1", "Option 1", 75),
            ("OPT2", "Option 2", 85),
        ]),
        ("MOM", "Momentum Health", [
            ("OPT1", "Bronze", 70),
            ("OPT2", "Silver", 80),
            ("OPT3", "Gold", 90),
        ]),
        ("FED", "Fedhealth", [
            ("OPT1", "Standard", 75),
        ]),
        ("POL", "Polmed", [
            ("OPT1", "Plan A", 80),
            ("OPT2", "Plan B", 85),
        ]),
    ]
    
    # Store scheme info in settings-like structure (for reference)
    if not hasattr(store, "_scheme_registry"):
        store._scheme_registry = {}
    
    for scheme_id, scheme_name, options in schemes:
        store._scheme_registry[scheme_id] = {
            "name": scheme_name,
            "options": {opt_id: opt_name for opt_id, opt_name, _ in options},
            "coverage_percent": {opt_id: coverage for _, _, coverage in options},
        }


def _ensure_demo_policy_profile(store: PersistentPlatformStore) -> None:
    rule_ids = list(store.rule_definitions.keys())
    
    # Original demo schemes
    base_schemes = [(DEMO_SCHEME, DEMO_OPTION), (LEGACY_SCHEME, LEGACY_OPTION)]
    
    # Extended realistic SA schemes
    sa_schemes = [
        ("DH", "OPT1"), ("DH", "OPT2"), ("DH", "OPT3"),
        ("GEMS", "OPT1"), ("GEMS", "OPT2"),
        ("BON", "OPT1"), ("BON", "OPT2"),
        ("MOM", "OPT1"), ("MOM", "OPT2"), ("MOM", "OPT3"),
        ("FED", "OPT1"),
        ("POL", "OPT1"), ("POL", "OPT2"),
    ]
    
    for scheme_id, option_id in base_schemes + sa_schemes:
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
                    "memberNumberRegex": r"^(MEM\d{6}|[A-Z]{2,3}-MEM-\d{3,6}|[A-Z]{3,5}-MEM-\d{1,6})$",
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
    
    # Extended realistic ICD-10 codes
    icd_codes = {
        "J11.1": "Influenza with respiratory manifestations",
        "I10": "Essential hypertension",
        "E11.9": "Type 2 diabetes mellitus without complications",
        "Z00.0": "General adult medical examination",
        "I50.9": "Unspecified heart failure",
        "J44.9": "Chronic obstructive pulmonary disease, unspecified",
        "E78.5": "Hyperlipidemia, unspecified",
        "F41.1": "Generalized anxiety disorder",
        "M79.3": "Myalgia",
        "K21.0": "Gastro-esophageal reflux disease with esophagitis",
        "M54.5": "Low back pain",
        "N18.3": "Chronic kidney disease, stage 3a",
        "F32.9": "Major depressive disorder, single episode, unspecified",
        "M25.50": "Pain in unspecified shoulder joint",
        "B34.1": "Respiratory syncytial virus infection",
        "E04.9": "Disorder of thyroid, unspecified",
        "I21.9": "Acute myocardial infarction, unspecified",
        "C34.90": "Unspecified malignant neoplasm of unspecified part of lung",
        "J20.9": "Acute bronchitis, unspecified",
        "G89.29": "Other chronic pain",
    }
    
    for code, description in icd_codes.items():
        from platform_core import ICD10Code
        
        store.icd10_codes[code] = ICD10Code(
            code=code,
            description=description,
            version=version,
            active=True,
            effective_from="2026-04-01",
            source="Realistic SA medical scheme data",
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

    claim = store.create_claim(
        {
            **payload,
            "clinical_summary": payload.get("clinical_summary") or f"DEMO clinical summary for {scenario_key}",
            "scenario_key": scenario_key,
        },
        actor="system",
        role="Seeder",
    )
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
