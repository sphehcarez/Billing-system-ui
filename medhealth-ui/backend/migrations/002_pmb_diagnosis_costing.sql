CREATE TABLE icd10_reference (
    code TEXT PRIMARY KEY,
    description TEXT NOT NULL,
    active BOOLEAN NOT NULL DEFAULT TRUE,
    effective_from DATE NOT NULL,
    effective_to DATE,
    source TEXT NOT NULL DEFAULT 'development_placeholder_business_owned_required'
);

CREATE TABLE pmb_condition (
    condition_id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    type TEXT NOT NULL CHECK (type IN ('DTP', 'CDL', 'EMERGENCY', 'UNSPECIFIED')),
    descriptor TEXT NOT NULL DEFAULT '',
    active BOOLEAN NOT NULL DEFAULT TRUE,
    effective_from DATE NOT NULL,
    effective_to DATE,
    source TEXT NOT NULL DEFAULT 'development_placeholder_business_owned_required'
);

CREATE TABLE icd10_pmb_mapping (
    mapping_id TEXT PRIMARY KEY,
    icd10_code TEXT NOT NULL REFERENCES icd10_reference(code),
    condition_id TEXT NOT NULL REFERENCES pmb_condition(condition_id),
    match_type TEXT NOT NULL CHECK (match_type IN ('EXACT', 'PREFIX')),
    confidence TEXT NOT NULL,
    active BOOLEAN NOT NULL DEFAULT TRUE,
    effective_from DATE NOT NULL,
    effective_to DATE,
    source TEXT NOT NULL DEFAULT 'development_placeholder_business_owned_required'
);

CREATE TABLE benefit_route_rule (
    rule_id TEXT PRIMARY KEY,
    scheme_id TEXT NOT NULL,
    plan_option_id TEXT NOT NULL,
    route_when_confirmed TEXT NOT NULL,
    route_when_possible TEXT NOT NULL,
    route_when_missing_evidence TEXT NOT NULL,
    active BOOLEAN NOT NULL DEFAULT TRUE,
    effective_from DATE NOT NULL,
    effective_to DATE,
    source TEXT NOT NULL DEFAULT 'development_placeholder_business_owned_required'
);

CREATE TABLE tariff_rate (
    rate_id TEXT PRIMARY KEY,
    scheme_id TEXT NOT NULL,
    plan_option_id TEXT NOT NULL,
    tariff_code TEXT NOT NULL,
    dsp_flag BOOLEAN NOT NULL DEFAULT TRUE,
    rate_amount NUMERIC(12,2) NOT NULL,
    unit TEXT NOT NULL,
    effective_from DATE NOT NULL,
    effective_to DATE,
    source TEXT NOT NULL DEFAULT 'development_placeholder_business_owned_required'
);

CREATE TABLE pmb_payment_policy (
    policy_id TEXT PRIMARY KEY,
    scheme_id TEXT NOT NULL,
    plan_option_id TEXT NOT NULL,
    pay_in_full_requires_dsp BOOLEAN NOT NULL DEFAULT TRUE,
    voluntary_non_dsp_rate_mode TEXT NOT NULL CHECK (voluntary_non_dsp_rate_mode IN ('DSP_RATE', 'SCHEME_RATE', 'CLAIMED_LIMITED')),
    involuntary_non_dsp_no_copay BOOLEAN NOT NULL DEFAULT TRUE,
    effective_from DATE NOT NULL,
    effective_to DATE,
    source TEXT NOT NULL DEFAULT 'development_placeholder_business_owned_required'
);

CREATE TABLE claim_diagnosis (
    diagnosis_id TEXT PRIMARY KEY,
    claim_id INTEGER NOT NULL REFERENCES claims(id),
    icd10_code TEXT NOT NULL REFERENCES icd10_reference(code),
    is_primary BOOLEAN NOT NULL DEFAULT FALSE,
    source TEXT NOT NULL,
    captured_by TEXT NOT NULL,
    captured_at TIMESTAMP NOT NULL
);

CREATE TABLE pmb_decision (
    decision_id TEXT PRIMARY KEY,
    claim_id INTEGER NOT NULL REFERENCES claims(id),
    claim_version INTEGER NOT NULL,
    stage TEXT NOT NULL,
    pmb_status TEXT NOT NULL,
    matched_icd10 TEXT,
    mapping_id TEXT,
    condition_id TEXT,
    provider_marked_pmb BOOLEAN NOT NULL DEFAULT FALSE,
    reason_code TEXT NOT NULL,
    message TEXT NOT NULL,
    remediation_hint TEXT NOT NULL,
    explainability TEXT NOT NULL,
    created_at TIMESTAMP NOT NULL
);

CREATE TABLE benefit_routing_decision (
    decision_id TEXT PRIMARY KEY,
    claim_id INTEGER NOT NULL REFERENCES claims(id),
    claim_version INTEGER NOT NULL,
    stage TEXT NOT NULL,
    pmb_decision_id TEXT REFERENCES pmb_decision(decision_id),
    route TEXT NOT NULL,
    reason_code TEXT NOT NULL,
    message TEXT NOT NULL,
    remediation_hint TEXT NOT NULL,
    created_at TIMESTAMP NOT NULL
);

CREATE TABLE costing_preview (
    preview_id TEXT PRIMARY KEY,
    claim_id INTEGER NOT NULL REFERENCES claims(id),
    claim_version INTEGER NOT NULL,
    stage TEXT NOT NULL,
    pmb_decision_id TEXT REFERENCES pmb_decision(decision_id),
    routing_decision_id TEXT REFERENCES benefit_routing_decision(decision_id),
    claimed_total NUMERIC(12,2) NOT NULL,
    allowed_total NUMERIC(12,2) NOT NULL,
    pmb_allowed_total NUMERIC(12,2),
    member_liability_estimate NUMERIC(12,2) NOT NULL,
    pricing_basis TEXT NOT NULL,
    pending_pmb_review BOOLEAN NOT NULL DEFAULT FALSE,
    provisional BOOLEAN NOT NULL DEFAULT FALSE,
    reason_code TEXT NOT NULL,
    explanation TEXT NOT NULL,
    created_at TIMESTAMP NOT NULL
);
