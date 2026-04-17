from __future__ import annotations

import json
import os
import random
from typing import Any, Dict, List, Optional

from platform_core import (
    BenefitRouteRule,
    ClaimClosureRequest,
    ClaimSubmissionRequest,
    ICD10Code,
    Patient,
    PMBCondition,
    PMBMappingRule,
    PMBPaymentPolicy,
    PolicyProfile,
    Provider,
    ReferenceVersion,
    TariffRate,
    stable_hash,
    utc_now,
)
from postgres_store import PersistentPlatformStore

# ---------------------------------------------------------------------------
# Fixed random seed – must be at module level so every import is deterministic
# ---------------------------------------------------------------------------
random.seed(20260101)

# ---------------------------------------------------------------------------
# Default scheme constants (Discovery Health as primary platform default)
# ---------------------------------------------------------------------------
DEMO_SCHEME = "DH"           # formerly SCHEMEA; updated to realistic default
DEMO_OPTION = "CLASSIC_COMP" # formerly OPT1; updated to realistic default
DEMO_POLICY_PROFILE = f"{DEMO_SCHEME}:{DEMO_OPTION}"

LEGACY_SCHEME = "SCHEME_A"
LEGACY_OPTION = "OPTION_X"

# ---------------------------------------------------------------------------
# Schemes
# ---------------------------------------------------------------------------
SCHEMES: List[Dict[str, str]] = [
    {"id": "DH",      "display_name": "Discovery Health Medical Scheme"},
    {"id": "GEMS",    "display_name": "Government Employees Medical Scheme (GEMS)"},
    {"id": "BON",     "display_name": "Bonitas Medical Fund"},
    {"id": "MOM",     "display_name": "Momentum Medical Scheme"},
    {"id": "FED",     "display_name": "Fedhealth Medical Scheme"},
    {"id": "POL",     "display_name": "Polmed"},
    {"id": "SCHEMEA", "display_name": "Bestmed Medical Scheme"},  # legacy – keep ID
]

# ---------------------------------------------------------------------------
# Scheme options  (scheme_id, option_id, display_name, coverage_pct)
# ---------------------------------------------------------------------------
SCHEME_OPTIONS: List[Dict[str, Any]] = [
    # Discovery Health
    {"scheme_id": "DH",  "option_id": "CLASSIC_COMP",   "display_name": "Classic Comprehensive",    "coverage_pct": 90},
    {"scheme_id": "DH",  "option_id": "CLASSIC_SAVER",  "display_name": "Classic Saver",             "coverage_pct": 80},
    {"scheme_id": "DH",  "option_id": "KEYCARE_PLUS",   "display_name": "KeyCare Plus",              "coverage_pct": 70},
    # GEMS
    {"scheme_id": "GEMS","option_id": "ONYX",            "display_name": "Onyx",                      "coverage_pct": 75},
    {"scheme_id": "GEMS","option_id": "EMERALD",         "display_name": "Emerald",                   "coverage_pct": 85},
    # Bonitas
    {"scheme_id": "BON", "option_id": "BON_COMP",        "display_name": "BonComprehensive",          "coverage_pct": 88},
    {"scheme_id": "BON", "option_id": "BON_CAP",         "display_name": "BonCap",                    "coverage_pct": 72},
    # Momentum
    {"scheme_id": "MOM", "option_id": "MOM_EXTENDER",   "display_name": "Extender Options",          "coverage_pct": 82},
    {"scheme_id": "MOM", "option_id": "MOM_INCENTIVE",  "display_name": "Incentive",                 "coverage_pct": 75},
    # Fedhealth
    {"scheme_id": "FED", "option_id": "FED_MAXIMA",     "display_name": "Maxima Plus",               "coverage_pct": 90},
    # Polmed
    {"scheme_id": "POL", "option_id": "POL_MARINE",     "display_name": "Marine Plus",               "coverage_pct": 85},
    {"scheme_id": "POL", "option_id": "POL_RUBY",       "display_name": "Ruby",                      "coverage_pct": 78},
    # Bestmed – legacy ID retained for backward compat
    {"scheme_id": "SCHEMEA","option_id": "OPT1",        "display_name": "Bestmed Pace",              "coverage_pct": 75},
]

# ---------------------------------------------------------------------------
# Practices
# ---------------------------------------------------------------------------
PRACTICES: List[Dict[str, str]] = [
    {"practice_number": "0312456", "name": "Glenwood Medical Centre",       "city": "Durban",              "phone": "+27 31 201 4567"},
    {"practice_number": "0312789", "name": "Musgrave Specialist Centre",    "city": "Durban",              "phone": "+27 31 312 8901"},
    {"practice_number": "0312321", "name": "Umhlanga Medical Suites",       "city": "Umhlanga Rocks",      "phone": "+27 31 566 2345"},
    {"practice_number": "0123456", "name": "Hatfield Medical Practice",     "city": "Pretoria",            "phone": "+27 12 362 1122"},
    {"practice_number": "0114567", "name": "Morningside Specialist Centre", "city": "Sandton",             "phone": "+27 11 784 5678"},
    {"practice_number": "0117890", "name": "Rosebank Medical Park",         "city": "Johannesburg",        "phone": "+27 11 447 9012"},
    {"practice_number": "0211234", "name": "Sea Point Medical Centre",      "city": "Cape Town",           "phone": "+27 21 434 5678"},
    {"practice_number": "0217567", "name": "Claremont Health Hub",          "city": "Cape Town",           "phone": "+27 21 683 2345"},
    {"practice_number": "0339012", "name": "Scottsville Medical Centre",    "city": "Pietermaritzburg",    "phone": "+27 33 394 5678"},
    {"practice_number": "0119345", "name": "Midrand Medical Suites",        "city": "Midrand",             "phone": "+27 11 318 9012"},
]

def _practice_slug(practice: Dict[str, str]) -> str:
    return practice["name"].lower().replace(" ", "-").replace(",", "")

# ---------------------------------------------------------------------------
# Providers  (surname, practice_index 0-9, specialty)
# 2 per practice → 20 total; first 14 are DSP, last 6 are not
# ---------------------------------------------------------------------------
_PROVIDER_ROWS: List[tuple] = [
    # (surname, practice_idx, specialty, discipline)
    ("Nkosi",          0, "General Practice", "GP"),
    ("Dlamini",        0, "Internal Medicine", "SPECIALIST"),
    ("Van der Merwe",  1, "Cardiology",        "SPECIALIST"),
    ("Pillay",         1, "General Practice",  "GP"),
    ("Botha",          2, "Orthopaedics",      "SPECIALIST"),
    ("Molefe",         2, "General Practice",  "GP"),
    ("De Bruyn",       3, "Neurology",         "SPECIALIST"),
    ("Khumalo",        3, "General Practice",  "GP"),
    ("Swanepoel",      4, "Dermatology",       "SPECIALIST"),
    ("Sithole",        4, "General Practice",  "GP"),
    ("Mahlangu",       5, "General Practice",  "GP"),
    ("Venter",         5, "Psychiatry",        "SPECIALIST"),
    ("Ndlovu",         6, "General Practice",  "GP"),
    ("Grobler",        6, "Oncology",          "SPECIALIST"),
    # Non-DSP (last 6)
    ("Zulu",           7, "General Practice",  "GP"),
    ("Pretorius",      7, "General Practice",  "GP"),
    ("Mokoena",        8, "General Practice",  "GP"),
    ("Le Roux",        8, "General Practice",  "GP"),
    ("Shabalala",      9, "General Practice",  "GP"),
    ("Jacobs",         9, "General Practice",  "GP"),
]

def _build_providers() -> List[Dict[str, Any]]:
    providers = []
    for idx, (surname, practice_idx, specialty, discipline) in enumerate(_PROVIDER_ROWS):
        practice = PRACTICES[practice_idx]
        reg_id = f"MP{100000 + idx + 1:06d}"
        slug = _practice_slug(practice)
        surname_clean = surname.lower().replace(" ", "").replace("'", "")
        email = f"dr.{surname_clean}@{slug}.co.za"
        is_dsp = idx < 14  # first 14 are DSP
        providers.append({
            "registration_id": reg_id,
            "surname": surname,
            "name": f"Dr. {surname}",
            "practice_number": practice["practice_number"],
            "specialty": specialty,
            "discipline": discipline,
            "is_dsp_provider": is_dsp,
            "email": email,
            "phone": practice["phone"],
        })
    return providers

PROVIDERS_DATA = _build_providers()

# ---------------------------------------------------------------------------
# Patients
# ---------------------------------------------------------------------------
_FEMALE_FIRST = [
    "Thandi", "Nomsa", "Zanele", "Nokwanda", "Buhle", "Lindiwe", "Sipho",
    "Nokuthula", "Ayanda", "Nompumelelo", "Nokubonga", "Sindisiwe", "Fikile",
    "Hlengiwe", "Londiwe", "Phumzile", "Nozipho", "Thandeka", "Siphokazi",
    "Naledi", "Lerato", "Puleng", "Mmapula", "Dineo", "Kedibone", "Mpho",
    "Precious", "Nthabiseng", "Bontle", "Keitumetse",
]
_MALE_FIRST = [
    "Sipho", "Bongani", "Lwazi", "Mthokozisi", "Nkosinathi", "Mandla",
    "Siyanda", "Thabo", "Lungelo", "Muzi", "Sandile", "Msizi", "Sifiso",
    "Tshepo", "Kabelo", "Lethabo", "Kagiso", "Tumelo", "Tlotlo", "Pule",
    "Mpho", "Botshelo", "Tebogo", "Lesego", "Ofentse", "Mogomotsi",
]
_SURNAMES = [
    "Dlamini", "Nkosi", "Mokoena", "Mahlangu", "Khumalo", "Mthembu",
    "Sithole", "Zulu", "Ndlovu", "Baloyi", "Molefe", "Motaung", "Khoza",
    "Mabuza", "Kgosi", "Modise", "Phiri", "Mkhize", "Cele", "Hadebe",
    "Gwala", "Ngubane", "Mthethwa", "Buthelezi", "Ntuli", "Kunene",
    "Mnguni", "Msomi", "Vilakazi", "Nxumalo",
]
_MOBILE_PREFIXES = ["+27 82", "+27 83", "+27 84", "+27 71", "+27 72", "+27 73"]
_SCHEME_IDS     = ["DH", "GEMS", "BON", "MOM", "FED", "POL"]
_SCHEME_OPTIONS_MAP: Dict[str, List[str]] = {
    "DH":   ["CLASSIC_COMP", "CLASSIC_SAVER", "KEYCARE_PLUS"],
    "GEMS": ["ONYX", "EMERALD"],
    "BON":  ["BON_COMP", "BON_CAP"],
    "MOM":  ["MOM_EXTENDER", "MOM_INCENTIVE"],
    "FED":  ["FED_MAXIMA"],
    "POL":  ["POL_MARINE", "POL_RUBY"],
}
_DEP_CODES = ["00", "01", "02", "03"]

def _build_patients() -> List[Dict[str, Any]]:
    rng = random.Random(20260101)  # local RNG for reproducibility within function
    patients = []
    used_names: set = set()

    female_pool = list(_FEMALE_FIRST)
    male_pool   = list(_MALE_FIRST)
    surname_pool = list(_SURNAMES)

    rng.shuffle(female_pool)
    rng.shuffle(male_pool)
    rng.shuffle(surname_pool)

    # build 60 patients: 30 female, 30 male
    combos = []
    for i in range(30):
        fn = female_pool[i % len(female_pool)]
        sn = surname_pool[(i * 2) % len(surname_pool)]
        combos.append((fn, sn, "F"))
    for i in range(30):
        fn = male_pool[i % len(male_pool)]
        sn = surname_pool[(i * 2 + 1) % len(surname_pool)]
        combos.append((fn, sn, "M"))

    rng.shuffle(combos)

    for idx, (first, surname, sex) in enumerate(combos):
        mrn = f"MRN-{idx + 1:06d}"
        # DOB between 1955-01-01 and 2000-12-31
        dob_year  = rng.randint(1955, 2000)
        dob_month = rng.randint(1, 12)
        dob_day   = rng.randint(1, 28)  # safe for all months
        dob = f"{dob_year:04d}-{dob_month:02d}-{dob_day:02d}"
        # Membership: 8-10 digit string
        mem_len = rng.randint(8, 10)
        membership_number = "".join([str(rng.randint(0, 9)) for _ in range(mem_len)])
        # Phone
        prefix = _MOBILE_PREFIXES[idx % len(_MOBILE_PREFIXES)]
        phone_digits = "".join([str(rng.randint(0, 9)) for _ in range(7)])
        phone = f"{prefix} {phone_digits}"
        # Scheme/option
        scheme_id = _SCHEME_IDS[idx % len(_SCHEME_IDS)]
        plan_option_id = rng.choice(_SCHEME_OPTIONS_MAP[scheme_id])
        # Dependency code
        dep_code = _DEP_CODES[idx % len(_DEP_CODES)]

        first_lower   = first.lower()
        surname_lower = surname.lower()
        email = f"{first_lower}.{surname_lower}@gmail.com"

        patients.append({
            "mrn": mrn,
            "name": f"{first} {surname}",
            "first": first,
            "surname": surname,
            "dob": dob,
            "sex": sex,
            "email": email,
            "phone": phone,
            "membership_number": membership_number,
            "scheme_id": scheme_id,
            "plan_option_id": plan_option_id,
            "dependant_code": dep_code,
        })
    return patients

PATIENTS_DATA = _build_patients()

# ---------------------------------------------------------------------------
# ICD-10 codes for claims
# ---------------------------------------------------------------------------
ICD10_CODES: Dict[str, str] = {
    "I10":     "Essential hypertension",
    "E11.9":   "Type 2 diabetes mellitus, without complications",
    "J45.909": "Unspecified asthma, uncomplicated",
    "E78.5":   "Hyperlipidemia, unspecified",
    "M17.11":  "Primary osteoarthritis, right knee",
    "J35.03":  "Chronic tonsillitis and adenoiditis",
    "K02.9":   "Dental caries, unspecified",
    "J06.9":   "Acute upper respiratory infection, unspecified",
    "N39.0":   "Urinary tract infection, site not specified",
    "L20.9":   "Atopic dermatitis, unspecified",
}
# Extra ICD codes used by UAT / realistic scenarios
ICD10_EXTRA: Dict[str, str] = {
    "J11.1":  "Influenza with respiratory manifestations",
    "I50.9":  "Unspecified heart failure",
    "J44.9":  "Chronic obstructive pulmonary disease, unspecified",
    "F41.1":  "Generalized anxiety disorder",
    "M79.3":  "Myalgia",
    "K21.0":  "Gastro-oesophageal reflux disease with oesophagitis",
    "M54.5":  "Low back pain",
    "B34.1":  "Respiratory syncytial virus infection",
    "I21.9":  "Acute myocardial infarction, unspecified",
    "J20.9":  "Acute bronchitis, unspecified",
}

# ---------------------------------------------------------------------------
# Synthetic tariff codes (all amounts in cents)
# ---------------------------------------------------------------------------
TARIFF_CODES: List[Dict[str, Any]] = [
    {"code": "0008", "description": "Consultation",          "unit_price_cents": 85000},
    {"code": "0192", "description": "Arthroscopy",           "unit_price_cents": 420000},
    {"code": "2101", "description": "Theatre fee",           "unit_price_cents": 350000},
    {"code": "0021", "description": "Follow-up consultation","unit_price_cents": 55000},
    {"code": "0055", "description": "Specialist consultation","unit_price_cents": 125000},
]
_TARIFF_BY_CODE: Dict[str, Dict[str, Any]] = {t["code"]: t for t in TARIFF_CODES}

# ---------------------------------------------------------------------------
# Claims configuration
# ---------------------------------------------------------------------------
_CLAIM_ICD_LIST = list(ICD10_CODES.keys())

# Status distribution: 15 DRAFT, 25 SUBMITTED, 20 PAID_FULL(closed), 15 PAID_PARTIAL, 5 REJECTED
_STATUS_POOL = (
    ["draft"] * 15
    + ["submitted"] * 25
    + ["closed"] * 20
    + ["paid_partial"] * 15
    + ["rejected"] * 5
)

# Service dates – spread across 2026
_SERVICE_DATES = [
    f"2026-{m:02d}-{d:02d}"
    for m in range(1, 5)      # Jan–Apr 2026
    for d in (5, 10, 15, 20, 25)
]

# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def seed_reference_data(store: PersistentPlatformStore) -> Dict[str, Any]:
    """Upsert schemes, options, practices, providers, rules, PMB mappings, tariffs."""
    _ensure_reference_versions(store)
    _ensure_demo_users(store)
    _ensure_practices(store)
    _ensure_providers(store)
    _ensure_schemes(store)
    _ensure_rules(store)
    _ensure_policy_profiles(store)
    _ensure_settings(store)
    _ensure_icd10_codes(store)
    _ensure_pmb_data(store)
    _ensure_tariff_rates(store)
    store.save()
    return {
        "users": len(store.users),
        "patients": len(store.patients),
        "providers": len(store.providers),
        "icd10_reference": len(store.icd10_codes),
        "pmb_conditions": len(store.pmb_conditions),
        "pmb_mappings": len(store.pmb_mapping_rules),
        "policy_profiles": sum(len(v) for v in store.policy_profiles.values()),
    }


def seed_uat_scenarios(store: PersistentPlatformStore) -> Dict[str, Any]:
    """Upsert 80 claims with 60 patients and print a JSON summary."""
    # Ensure patients exist (idempotent)
    _ensure_patients(store)

    # Seed legacy UAT named scenarios (preserved for backward compat)
    scenario_ids: Dict[str, int] = {}
    scenario_ids["CLEAN_SUCCESS"] = _seed_named_claim(
        store, "CLEAN_SUCCESS", {
            "claim_number": "UAT-CLM-CLEAN-SUCCESS",
            "claim_reference": "UAT-REF-CLEAN-SUCCESS",
            "invoice_number": "UAT-INV-CLEAN-SUCCESS",
            "patient_id": _patient_id_by_mrn(store, "MRN-000001"),
            "provider_id": _provider_id_by_practice(store, "0312456"),
            "provider_is_dsp": True,
            "member_number": "MEM900001",
            "scheme_id": DEMO_SCHEME,
            "plan_option_id": DEMO_OPTION,
            "service_date": "2026-04-16",
            "diagnoses": [{"seq": 1, "icd10": "I10", "diagnosis_type": "PRIMARY"}],
            "attachments": [{
                "attachment_type": "MOTIVATION",
                "file_name": "motivation-clean-success.pdf",
                "storage_ref": "seed/motivation-clean-success.pdf",
                "file_hash": stable_hash("motivation-clean-success"),
                "uploaded_by": "system",
            }],
            "line_items": [{
                "line_id": "1",
                "service_code": "0008",
                "service_description": "Consultation",
                "quantity": 1,
                "unit_price": 85000,
                "claimed_amount": 85000,
                "diagnosis_refs": [1],
            }],
        },
        actions=["readiness", "close", "validate", "payload", "submit:direct:uat-clean-success"],
    )

    scenario_ids["MISSING_PRIMARY_ICD"] = _seed_named_claim(
        store, "MISSING_PRIMARY_ICD", {
            "claim_number": "UAT-CLM-MISSING-PRIMARY",
            "claim_reference": "UAT-REF-MISSING-PRIMARY",
            "invoice_number": "UAT-INV-MISSING-PRIMARY",
            "patient_id": _patient_id_by_mrn(store, "MRN-000002"),
            "provider_id": _provider_id_by_practice(store, "0312789"),
            "provider_is_dsp": False,
            "non_dsp_access_type": "VOLUNTARY",
            "member_number": "MEM900002",
            "scheme_id": DEMO_SCHEME,
            "plan_option_id": DEMO_OPTION,
            "service_date": "2026-04-16",
            "diagnoses": [],
            "line_items": [{
                "line_id": "1",
                "service_code": "0021",
                "service_description": "Follow-up consultation",
                "quantity": 1,
                "unit_price": 55000,
                "claimed_amount": 55000,
            }],
        },
        actions=["readiness"],
    )

    scenario_ids["PMB_REVIEW_REQUIRED"] = _seed_named_claim(
        store, "PMB_REVIEW_REQUIRED", {
            "claim_number": "UAT-CLM-PMB-REVIEW",
            "claim_reference": "UAT-REF-PMB-REVIEW",
            "invoice_number": "UAT-INV-PMB-REVIEW",
            "patient_id": _patient_id_by_mrn(store, "MRN-000003"),
            "provider_id": _provider_id_by_practice(store, "0312789"),
            "provider_is_dsp": False,
            "non_dsp_access_type": "VOLUNTARY",
            "member_number": "MEM900003",
            "scheme_id": DEMO_SCHEME,
            "plan_option_id": DEMO_OPTION,
            "service_date": "2026-04-16",
            "diagnoses": [{"seq": 1, "icd10": "E11.9", "diagnosis_type": "PRIMARY"}],
            "line_items": [{
                "line_id": "1",
                "service_code": "0055",
                "service_description": "Specialist consultation",
                "quantity": 1,
                "unit_price": 125000,
                "claimed_amount": 125000,
                "diagnosis_refs": [1],
                "requires_attachment": True,
            }],
        },
        actions=["readiness", "close", "validate", "payload", "submit:switch:uat-pmb-review"],
    )

    scenario_ids["PARTIAL_PAYMENT"] = _seed_named_claim(
        store, "PARTIAL_PAYMENT", {
            "claim_number": "UAT-CLM-PARTIAL-PAYMENT",
            "claim_reference": "UAT-REF-PARTIAL-PAYMENT",
            "invoice_number": "UAT-INV-PARTIAL-PAYMENT",
            "patient_id": _patient_id_by_mrn(store, "MRN-000004"),
            "provider_id": _provider_id_by_practice(store, "0312456"),
            "provider_is_dsp": True,
            "member_number": "MEM900004",
            "scheme_id": DEMO_SCHEME,
            "plan_option_id": DEMO_OPTION,
            "service_date": "2026-04-16",
            "diagnoses": [{"seq": 1, "icd10": "J11.1", "diagnosis_type": "PRIMARY"}],
            "attachments": [{
                "attachment_type": "MOTIVATION",
                "file_name": "motivation-partial-payment.pdf",
                "storage_ref": "seed/motivation-partial-payment.pdf",
                "file_hash": stable_hash("motivation-partial-payment"),
                "uploaded_by": "system",
            }],
            "line_items": [{
                "line_id": "1",
                "service_code": "0008",
                "service_description": "Consultation",
                "quantity": 1,
                "unit_price": 85000,
                "claimed_amount": 85000,
                "diagnosis_refs": [1],
            }],
        },
        actions=["readiness", "close", "validate", "payload", "submit:direct:uat-partial-payment"],
    )

    scenario_ids["MISMATCH_EXCEPTION"] = _seed_named_claim(
        store, "MISMATCH_EXCEPTION", {
            "claim_number": "UAT-CLM-MISMATCH",
            "claim_reference": "UAT-REF-MISMATCH",
            "invoice_number": "UAT-INV-MISMATCH",
            "patient_id": _patient_id_by_mrn(store, "MRN-000005"),
            "provider_id": _provider_id_by_practice(store, "0312456"),
            "provider_is_dsp": True,
            "member_number": "MEM900005",
            "scheme_id": DEMO_SCHEME,
            "plan_option_id": DEMO_OPTION,
            "service_date": "2026-04-16",
            "diagnoses": [{"seq": 1, "icd10": "E11.9", "diagnosis_type": "PRIMARY"}],
            "attachments": [{
                "attachment_type": "MOTIVATION",
                "file_name": "motivation-mismatch-exception.pdf",
                "storage_ref": "seed/motivation-mismatch-exception.pdf",
                "file_hash": stable_hash("motivation-mismatch-exception"),
                "uploaded_by": "system",
            }],
            "line_items": [{
                "line_id": "1",
                "service_code": "0055",
                "service_description": "Specialist consultation",
                "quantity": 1,
                "unit_price": 125000,
                "claimed_amount": 125000,
                "diagnosis_refs": [1],
            }],
        },
        actions=["readiness", "close", "validate", "payload", "submit:switch:uat-mismatch-exception"],
    )

    # Seed 80 bulk claims (the named UAT ones are separate, not counted in the 80)
    _seed_bulk_claims(store)

    store.save()

    # ------------------------------------------------------------------
    # Summary JSON to stdout
    # ------------------------------------------------------------------
    all_patient_ids = sorted(store.patients.keys())
    all_claim_ids   = sorted(store.claims.keys())
    total_claimed_cents = sum(
        sum(int(li.claimed_amount) for li in c.line_items)
        for c in store.claims.values()
    )

    summary = {
        "patients": len(store.patients),
        "providers": len(store.providers),
        "claims": len(store.claims),
        "practices": len(PRACTICES),
        "sample_patient_ids": all_patient_ids[:5],
        "sample_claim_ids": all_claim_ids[:5],
        "total_claimed_cents": total_claimed_cents,
    }
    print(json.dumps(summary, indent=2))

    # ------------------------------------------------------------------
    # Write snapshot fixture
    # ------------------------------------------------------------------
    _write_snapshot_fixture(store)

    return scenario_ids


# ---------------------------------------------------------------------------
# Internal helpers – reference data
# ---------------------------------------------------------------------------

def _ensure_reference_versions(store: PersistentPlatformStore) -> None:
    store.reference_versions["icd10_mit"] = ReferenceVersion(
        reference_key="icd10_mit",
        version="ICD10-ZA-2026-Q2",
        effective_from="2026-04-01",
    )
    for key, version in {
        "pmb":               "PMB-ZA-2026-Q2",
        "tariff":            "NHRPL-2026-Q2",
        "provider_registry": "PCNS-2026-Q2",
        "nappi":             "NAPPI-2026-Q2",
    }.items():
        store.reference_versions[key] = ReferenceVersion(
            reference_key=key, version=version, effective_from="2026-04-01"
        )


def _ensure_demo_users(store: PersistentPlatformStore) -> None:
    demo_users = [
        ("admin",     "admin123",    "Administrator",    "admin@example.com"),
        ("demo.user", "password123", "Billing Specialist","demo.user@example.com"),
        ("billing",   "billing123",  "Billing Specialist","billing@example.com"),
        ("provider",  "provider123", "Healthcare Provider","provider@example.com"),
        ("finance",   "finance123",  "Finance Officer",   "finance@example.com"),
        ("auditor",   "auditor123",  "Compliance Auditor","auditor@example.com"),
    ]
    for username, password, role, email in demo_users:
        existing = next(
            (item for item in store.users.values() if item.username == username), None
        )
        if existing:
            store.users[existing.id] = existing.model_copy(
                update={"email": email, "role": role}
            )
            store.auth_users[username] = {
                "password": password, "role": role,
                "user_id": existing.id, "email": email,
            }
        else:
            store.register_user(username, password, role, email)


def _ensure_practices(store: PersistentPlatformStore) -> None:
    """Practices are stored via providers; this is a no-op registry initialiser."""
    if not hasattr(store, "_practice_registry"):
        store._practice_registry = {}
    for p in PRACTICES:
        store._practice_registry[p["practice_number"]] = p


def _ensure_providers(store: PersistentPlatformStore) -> None:
    """Upsert 20 providers by practice_number."""
    for pdata in PROVIDERS_DATA:
        existing = next(
            (item for item in store.providers.values()
             if item.practice_number == pdata["practice_number"]
             and item.name == pdata["name"]),
            None,
        )
        payload = {
            "name":             pdata["name"],
            "npi":              pdata["registration_id"],
            "practice_number":  pdata["practice_number"],
            "specialty":        pdata["specialty"],
            "discipline":       pdata["discipline"],
            "is_dsp_provider":  pdata["is_dsp_provider"],
            "email":            pdata["email"],
            "phone":            pdata["phone"],
            "status":           "active",
        }
        if existing:
            store.providers[existing.id] = existing.model_copy(update=payload)
        else:
            store.create_provider(payload, actor="system", role="Seeder")


def _ensure_patients(store: PersistentPlatformStore) -> None:
    """Upsert 60 patients by MRN."""
    for pdata in PATIENTS_DATA:
        existing = next(
            (item for item in store.patients.values() if item.mrn == pdata["mrn"]),
            None,
        )
        payload = {
            "name":   pdata["name"],
            "mrn":    pdata["mrn"],
            "dob":    pdata["dob"],
            "sex":    pdata["sex"],
            "email":  pdata["email"],
            "phone":  pdata["phone"],
            "status": "active",
        }
        if existing:
            store.patients[existing.id] = existing.model_copy(update=payload)
        else:
            store.create_patient(payload, actor="system", role="Seeder")


def _ensure_schemes(store: PersistentPlatformStore) -> None:
    """Store scheme registry on the store object."""
    if not hasattr(store, "_scheme_registry"):
        store._scheme_registry = {}
    for s in SCHEMES:
        opts = {
            o["option_id"]: {
                "display_name": o["display_name"],
                "coverage_pct": o["coverage_pct"],
            }
            for o in SCHEME_OPTIONS
            if o["scheme_id"] == s["id"]
        }
        store._scheme_registry[s["id"]] = {
            "display_name": s["display_name"],
            "options": opts,
        }


def _ensure_rules(store: PersistentPlatformStore) -> None:
    store.rule_definitions.clear()
    store._seed_rules()


def _ensure_policy_profiles(store: PersistentPlatformStore) -> None:
    rule_ids = list(store.rule_definitions.keys())

    all_combos = [(o["scheme_id"], o["option_id"]) for o in SCHEME_OPTIONS]
    # Also keep legacy
    all_combos += [(LEGACY_SCHEME, LEGACY_OPTION)]

    for scheme_id, option_id in all_combos:
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
                    "requirePreauthForCodes": ["0192", "2101"],
                    "allowClosureWithWarnings": True,
                    "requireSupervisorOverrideOnWarnings": False,
                    "defaultSubmissionChannel": "DIRECT",
                    "memberNumberRegex": r"^\d{8,10}$",
                    "autoFlagPMBFromICD10": True,
                    "autoRoutePMBWhenMappingAllows": True,
                    "pmbEvidenceMode": "WARN",
                },
                rule_ids=rule_ids,
            )
        ]


def _ensure_settings(store: PersistentPlatformStore) -> None:
    store.settings.update({
        "scheme":             DEMO_SCHEME,
        "option":             DEMO_OPTION,
        "policy_profile_id":  DEMO_POLICY_PROFILE,
        "policy_version":     1,
    })


def _ensure_icd10_codes(store: PersistentPlatformStore) -> None:
    version = store.reference_versions["icd10_mit"].version
    all_codes = {**ICD10_CODES, **ICD10_EXTRA}
    for code, description in all_codes.items():
        store.icd10_codes[code] = ICD10Code(
            code=code,
            description=description,
            version=version,
            active=True,
            effective_from="2026-04-01",
            source="Synthetic SA medical scheme reference data – ICD-10-CM",
            status="ACTIVE",
        )


def _ensure_pmb_data(store: PersistentPlatformStore) -> None:
    from platform_core import PMBCondition, PMBMappingRule, BenefitRouteRule, PMBPaymentPolicy

    # PMB Conditions (aligned to SA Prescribed Minimum Benefits framework)
    store.pmb_conditions["PMB_DTP_ZA_001"] = PMBCondition(
        condition_id="PMB_DTP_ZA_001",
        name="Hypertension and cardiovascular disease management",
        type="DTP",
        descriptor="Diagnosis-treatment pair: hypertension, ischaemic heart disease",
        category="CARDIOVASCULAR",
        metadata={"regulatory_basis": "MSA 1998 Schedule 1", "condition_group": "CDL"},
        evidence_requirements=["MOTIVATION"],
        confirmation_flags=["icd10_match", "treatment_protocol_met"],
        active=True,
        effective_from="2026-04-01",
        source="Prescribed Minimum Benefits framework – MSA 1998 Schedule 1",
        status="ACTIVE",
    )
    store.pmb_conditions["PMB_CDL_ZA_001"] = PMBCondition(
        condition_id="PMB_CDL_ZA_001",
        name="Type 2 diabetes mellitus and metabolic conditions",
        type="CDL",
        descriptor="Chronic disease list: diabetes mellitus type 2, hyperlipidaemia",
        category="ENDOCRINE",
        metadata={"regulatory_basis": "MSA 1998 Schedule 1 CDL", "condition_group": "CDL"},
        evidence_requirements=["MOTIVATION"],
        confirmation_flags=["icd10_match", "cdl_condition_confirmed"],
        active=True,
        effective_from="2026-04-01",
        source="Prescribed Minimum Benefits framework – MSA 1998 Schedule 1",
        status="ACTIVE",
    )

    # PMB mapping rules for the claim ICD codes
    _pmb_map = [
        ("PMB_MAP_I10",    "I10",     "PMB_DTP_ZA_001", "EXACT",  True),
        ("PMB_MAP_E119",   "E11.9",   "PMB_CDL_ZA_001", "PREFIX", True),
        ("PMB_MAP_J459",   "J45.909", "PMB_DTP_ZA_001", "EXACT",  True),
        ("PMB_MAP_J111",   "J11.1",   "PMB_DTP_ZA_001", "EXACT",  True),
        ("PMB_MAP_E785",   "E78.5",   "PMB_CDL_ZA_001", "EXACT",  False),
        ("PMB_MAP_M1711",  "M17.11",  "PMB_DTP_ZA_001", "EXACT",  True),
        ("PMB_MAP_J3503",  "J35.03",  "PMB_DTP_ZA_001", "EXACT",  True),
        ("PMB_MAP_N390",   "N39.0",   "PMB_DTP_ZA_001", "EXACT",  False),
    ]
    for map_id, icd, cond, match, auto in _pmb_map:
        store.pmb_mapping_rules[map_id] = PMBMappingRule(
            mapping_id=map_id,
            icd10_code=icd,
            pmb_condition_id=cond,
            match_type=match,
            version=1,
            effective_from="2026-04-01",
            confidence="HIGH",
            auto_route_allowed=auto,
            required_evidence_types=["MOTIVATION"],
            active=True,
            status="ACTIVE",
            source="Prescribed Minimum Benefits framework – MSA 1998 Schedule 1",
        )

    # Benefit route rules + tariff rates + PMB payment policies per scheme/option
    all_combos = [(o["scheme_id"], o["option_id"]) for o in SCHEME_OPTIONS]
    all_combos += [(LEGACY_SCHEME, LEGACY_OPTION)]

    for scheme_id, option_id in all_combos:
        key = f"{scheme_id}_{option_id}"
        store.benefit_route_rules[f"{key}_ROUTE"] = BenefitRouteRule(
            rule_id=f"{key}_ROUTE",
            scheme_id=scheme_id,
            plan_option_id=option_id,
            route_when_confirmed="PMB_BENEFIT_BUCKET",
            route_when_possible="PMB_REVIEW_QUEUE",
            route_when_missing_evidence="PMB_REVIEW_QUEUE",
            auto_route_possible_matches=False,
            active=True,
            effective_from="2026-04-01",
            source="MSA 1998 scheme benefit routing rules",
        )
        store.pmb_payment_policies[f"{key}_PMB_POL"] = PMBPaymentPolicy(
            policy_id=f"{key}_PMB_POL",
            scheme_id=scheme_id,
            plan_option_id=option_id,
            pay_in_full_requires_dsp=True,
            voluntary_non_dsp_rate_mode="DSP_RATE",
            involuntary_non_dsp_no_copay=True,
            active=True,
            effective_from="2026-04-01",
            source="MSA 1998 scheme benefit payment policies",
        )


def _ensure_tariff_rates(store: PersistentPlatformStore) -> None:
    """Add tariff rates for all synthetic codes across all scheme/option combos."""
    all_combos = [(o["scheme_id"], o["option_id"]) for o in SCHEME_OPTIONS]
    all_combos += [(LEGACY_SCHEME, LEGACY_OPTION)]

    for scheme_id, option_id in all_combos:
        key = f"{scheme_id}_{option_id}"
        for tariff in TARIFF_CODES:
            code = tariff["code"]
            base_cents = tariff["unit_price_cents"]
            for dsp_flag, suffix, rate_cents in [
                (True,  "DSP",    base_cents),
                (False, "NONDSP", int(base_cents * 0.80)),  # non-DSP at 80%
            ]:
                rate_id = f"{key}_RATE_{code}_{suffix}"
                store.tariff_rates[rate_id] = TariffRate(
                    rate_id=rate_id,
                    scheme_id=scheme_id,
                    plan_option_id=option_id,
                    tariff_code=code,
                    dsp_flag=dsp_flag,
                    rate_amount=rate_cents,  # stored as integer cents via float field
                    unit="PER_SERVICE",
                    active=True,
                    effective_from="2026-04-01",
                    source="Synthetic NHRPL tariff rates – is_synthetic=True",
                )


# ---------------------------------------------------------------------------
# Bulk claim seeding (80 claims)
# ---------------------------------------------------------------------------

def _seed_bulk_claims(store: PersistentPlatformStore) -> None:
    """Create 80 bulk CLM-2026-MMDD-NNN claims idempotently."""
    rng = random.Random(20260101)

    # Build pools
    patient_ids  = sorted(store.patients.keys())
    provider_ids = sorted(store.providers.keys())

    # Status pool – shuffled deterministically
    status_pool = list(_STATUS_POOL)  # 80 entries
    rng.shuffle(status_pool)

    # ICD pool rotation
    icd_keys = list(_CLAIM_ICD_LIST)

    # Track how many have allowed_total < claimed_total (copay requirement: ≥15)
    copay_count = 0
    copay_target = 15

    for n in range(80):
        seq_num   = n + 1
        date_idx  = n % len(_SERVICE_DATES)
        svc_date  = _SERVICE_DATES[date_idx]
        mm        = svc_date[5:7]
        dd        = svc_date[8:10]
        ref       = f"CLM-2026-{mm}{dd}-{seq_num:03d}"
        inv       = f"INV-2026-{mm}{dd}-{seq_num:03d}"

        # Check idempotency by claim_number
        existing = next(
            (c for c in store.claims.values() if c.claim_number == ref), None
        )
        if existing:
            continue  # already seeded; skip

        patient_id  = patient_ids[n % len(patient_ids)]
        provider_id = provider_ids[n % len(provider_ids)]

        patient   = store.patients[patient_id]
        provider  = store.providers[provider_id]

        # Derive scheme/option from patient data (stored in PATIENTS_DATA by index)
        pdata     = PATIENTS_DATA[n % len(PATIENTS_DATA)]
        scheme_id = pdata["scheme_id"]
        option_id = pdata["plan_option_id"]
        dep_code  = pdata["dependant_code"]
        mem_num   = pdata["membership_number"]

        # ICD code
        primary_icd = icd_keys[n % len(icd_keys)]
        diagnoses = [{"seq": 1, "icd10": primary_icd, "diagnosis_type": "PRIMARY"}]
        # Some claims have secondary diagnosis
        if n % 5 == 0:
            secondary_icd = icd_keys[(n + 3) % len(icd_keys)]
            if secondary_icd != primary_icd:
                diagnoses.append({"seq": 2, "icd10": secondary_icd, "diagnosis_type": "SECONDARY"})

        # Tariff code for line items
        tariff = TARIFF_CODES[n % len(TARIFF_CODES)]
        tariff_code = tariff["code"]
        description = tariff["description"]
        qty = 1

        # Determine copay: first 15 claims (that aren't already done) get copay
        needs_copay = copay_count < copay_target and (n < copay_target or (n % 6 == 0 and copay_count < copay_target))

        # All monetary values in INTEGER CENTS
        unit_price_cents: int = tariff["unit_price_cents"]
        claimed_cents: int    = unit_price_cents * qty

        if needs_copay:
            # allowed < claimed → copay scenario
            allowed_cents = int(claimed_cents * rng.randint(60, 85) / 100)
            copay_count += 1
        else:
            allowed_cents = claimed_cents  # full payment

        member_liability_cents: int = max(0, claimed_cents - allowed_cents)

        line_items = [{
            "line_id": "1",
            "service_code": tariff_code,
            "service_description": description,
            "quantity": qty,
            "unit_price": unit_price_cents,
            "claimed_amount": claimed_cents,
            "diagnosis_refs": [1],
        }]

        status = status_pool[n]
        is_dsp = provider.is_dsp_provider

        claim_payload: Dict[str, Any] = {
            "claim_number":  ref,
            "claim_reference": ref,
            "invoice_number": inv,
            "patient_id":    patient_id,
            "provider_id":   provider_id,
            "provider_is_dsp": is_dsp,
            "member_number": mem_num,
            "dependant_code": dep_code,
            "scheme_id":     scheme_id,
            "plan_option_id": option_id,
            "service_date":  svc_date,
            "diagnoses":     diagnoses,
            "line_items":    line_items,
            "clinical_summary": f"Bulk seed claim {seq_num}: {description} for {patient.name}",
            "scenario_key":  f"BULK_{status.upper()}_{seq_num:03d}",
            "status":        "draft",  # always start draft
        }

        # Non-DSP claims need access type
        if not is_dsp:
            claim_payload["non_dsp_access_type"] = "VOLUNTARY" if n % 2 == 0 else "INVOLUNTARY"

        claim = store.create_claim(claim_payload, actor="system", role="Seeder")

        # Advance to target status
        _advance_claim_status(store, claim.id, status, allowed_cents, claimed_cents, member_liability_cents)


def _advance_claim_status(
    store: PersistentPlatformStore,
    claim_id: int,
    target_status: str,
    allowed_cents: int,
    claimed_cents: int,
    member_liability_cents: int,
) -> None:
    """Drive a claim from draft toward the desired status."""
    if target_status == "draft":
        return  # already draft

    try:
        store.run_readiness(claim_id, "system", "Seeder")
    except Exception:
        return  # if readiness fails, leave as draft

    if target_status in ("submitted", "closed", "paid_partial", "rejected"):
        try:
            store.close_claim(claim_id, ClaimClosureRequest(), "system", "Seeder")
        except Exception:
            return

    if target_status in ("submitted", "paid_partial", "rejected"):
        try:
            store.run_post_closure_validation(claim_id, "system", "Seeder")
            store.build_payload(claim_id, "system", "Seeder")
        except Exception:
            return

    if target_status in ("submitted", "paid_partial", "rejected"):
        try:
            idem = f"bulk-seed-{claim_id}"
            store.submit_claim(
                claim_id,
                ClaimSubmissionRequest(channel="direct", idempotency_key=idem),
                "system", "Seeder",
            )
        except Exception:
            return

    # For paid_partial: mark as acknowledged + apply financial bundle
    # (the store's submit_claim already handles SUBMITTED→ACK/REJ flows internally)


# ---------------------------------------------------------------------------
# Named claim (UAT scenario) helper
# ---------------------------------------------------------------------------

def _seed_named_claim(
    store: PersistentPlatformStore,
    scenario_key: str,
    payload: Dict[str, Any],
    actions: List[str],
) -> int:
    existing = next(
        (item for item in store.claims.values() if item.claim_number == payload["claim_number"]),
        None,
    )
    if existing:
        _purge_claim(store, existing.id)

    claim = store.create_claim(
        {
            **payload,
            "clinical_summary": payload.get("clinical_summary")
                or f"UAT scenario: {scenario_key.replace('_', ' ').title()}",
            "scenario_key": scenario_key,
        },
        actor="system",
        role="Seeder",
    )
    for action in actions:
        try:
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
                    "system", "Seeder",
                )
        except Exception:
            pass  # seed best-effort; don't crash on workflow errors

    return claim.id


# ---------------------------------------------------------------------------
# Snapshot fixture writer
# ---------------------------------------------------------------------------

def _write_snapshot_fixture(store: PersistentPlatformStore) -> None:
    fixtures_dir = os.path.join(
        os.path.dirname(__file__), "tests", "fixtures"
    )
    os.makedirs(fixtures_dir, exist_ok=True)

    # Deterministic: sort by MRN string, take first 5
    mrn_sorted = sorted(
        (p.mrn for p in store.patients.values()),
        key=lambda m: m,
    )
    first5_mrns = mrn_sorted[:5]

    # Claims sorted by claim_number string
    ref_sorted = sorted(
        (c.claim_number for c in store.claims.values()),
        key=lambda r: r,
    )
    first5_refs = ref_sorted[:5]

    fixture = {
        "first_5_patient_mrns": first5_mrns,
        "first_5_claim_refs":   first5_refs,
    }
    path = os.path.join(fixtures_dir, "seed_snapshot.json")
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(fixture, fh, indent=2)


# ---------------------------------------------------------------------------
# Lookup helpers
# ---------------------------------------------------------------------------

def _patient_id_by_mrn(store: PersistentPlatformStore, mrn: str) -> int:
    result = next((item.id for item in store.patients.values() if item.mrn == mrn), None)
    if result is None:
        raise KeyError(f"Patient with MRN {mrn!r} not found; ensure patients are seeded first.")
    return result


def _provider_id_by_practice(store: PersistentPlatformStore, practice_number: str) -> int:
    result = next(
        (item.id for item in store.providers.values() if item.practice_number == practice_number),
        None,
    )
    if result is None:
        raise KeyError(f"Provider with practice_number {practice_number!r} not found.")
    return result


# ---------------------------------------------------------------------------
# Claim purge (used by named UAT scenario upserts)
# ---------------------------------------------------------------------------

def _purge_claim(store: PersistentPlatformStore, claim_id: int) -> None:
    claim = store.claims.pop(claim_id, None)
    if claim is None:
        return
    store.claim_versions.pop(claim_id, None)
    for key in [k for k in list(store.claim_history.keys()) if k.startswith(f"{claim_id}:")]:
        del store.claim_history[key]
    store.claim_diagnoses.pop(claim_id, None)
    deleted_submission_ids: List[str] = []
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
        for item_id in [
            item_id for item_id, item in collection.items()
            if getattr(item, "claim_id", None) == claim_id
        ]:
            del collection[item_id]
    for item_id, item in list(store.readiness_runs.items()):
        if item.claim_id == claim_id:
            del store.readiness_runs[item_id]
    for item in list(store.readiness_items.values()):
        if item.claim_id == claim_id:
            store.readiness_items.pop(item.item_id, None)
    for item_id, item in list(store.submissions.items()):
        if item.claim_id == claim_id:
            deleted_submission_ids.append(item_id)
            del store.submissions[item_id]
    for item_id in [
        item_id for item_id, item in store.transport_logs.items()
        if item.submission_id in deleted_submission_ids
        or store.submissions.get(item.submission_id) is None
    ]:
        del store.transport_logs[item_id]
    for idem_key, submission_id in list(store.idempotency_index.items()):
        if submission_id in deleted_submission_ids:
            del store.idempotency_index[idem_key]
    for payment_id in [
        pid for pid, item in store.payments.items() if item.claim_id == claim_id
    ]:
        del store.payments[payment_id]
    for ledger_id in [
        lid for lid, item in store.ledger_entries.items() if item["claim_id"] == claim_id
    ]:
        del store.ledger_entries[ledger_id]
    for audit_id in [
        aid for aid, item in store.audit_events.items()
        if item.entity_type == "claim" and item.entity_id == str(claim_id)
    ]:
        del store.audit_events[audit_id]


# ---------------------------------------------------------------------------
# Pretty-print helper (used by external callers)
# ---------------------------------------------------------------------------

def dumps_pretty(payload: Dict[str, Any]) -> str:
    return json.dumps(payload, indent=2, sort_keys=True)
