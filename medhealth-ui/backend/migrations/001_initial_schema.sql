CREATE TABLE claims (
    id INTEGER PRIMARY KEY,
    version INTEGER NOT NULL,
    previous_version INTEGER,
    scenario_key TEXT NOT NULL,
    status TEXT NOT NULL,
    claim_number TEXT NOT NULL,
    claim_reference TEXT NOT NULL,
    invoice_number TEXT NOT NULL,
    scheme_id TEXT NOT NULL,
    plan_option_id TEXT NOT NULL,
    member_number TEXT NOT NULL,
    dependant_code TEXT NOT NULL,
    membership_status TEXT NOT NULL,
    patient_id INTEGER NOT NULL,
    provider_id INTEGER NOT NULL,
    care_setting TEXT NOT NULL,
    service_date TEXT NOT NULL,
    admission_date_time TEXT,
    discharge_date_time TEXT,
    provider_pmb_indicator INTEGER,
    pmb_status TEXT NOT NULL DEFAULT 'not_evaluated',
    latest_snapshot_id TEXT,
    latest_payload_id TEXT,
    latest_submission_id TEXT,
    latest_response_id TEXT,
    latest_financial_bundle_id TEXT,
    latest_remittance_id TEXT,
    latest_reconciliation_id TEXT,
    latest_benefit_route_decision_id TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE claim_versions (
    claim_id INTEGER NOT NULL,
    version INTEGER NOT NULL,
    snapshot_id TEXT,
    status TEXT NOT NULL,
    previous_version INTEGER,
    change_summary TEXT NOT NULL,
    created_at TEXT NOT NULL,
    PRIMARY KEY (claim_id, version)
);

CREATE TABLE billing_snapshots (
    snapshot_id TEXT PRIMARY KEY,
    claim_id INTEGER NOT NULL,
    claim_version INTEGER NOT NULL,
    data_json TEXT NOT NULL,
    input_hash TEXT NOT NULL,
    created_at TEXT NOT NULL,
    created_by TEXT NOT NULL
);

CREATE TABLE decision_bundles (
    decision_bundle_id TEXT PRIMARY KEY,
    claim_id INTEGER NOT NULL,
    claim_version INTEGER NOT NULL,
    snapshot_id TEXT,
    stage TEXT NOT NULL,
    policy_profile_id TEXT NOT NULL,
    policy_version INTEGER NOT NULL,
    outcome TEXT NOT NULL,
    input_hash TEXT NOT NULL,
    payload_hash TEXT,
    reference_versions_json TEXT NOT NULL,
    rule_hits_json TEXT NOT NULL,
    explanations_json TEXT NOT NULL,
    created_at TEXT NOT NULL,
    created_by TEXT NOT NULL
);

CREATE TABLE readiness_runs (
    readiness_run_id TEXT PRIMARY KEY,
    claim_id INTEGER NOT NULL,
    claim_version INTEGER NOT NULL,
    decision_bundle_id TEXT NOT NULL,
    outcome TEXT NOT NULL,
    created_at TEXT NOT NULL
);

CREATE TABLE policy_profiles (
    policy_profile_id TEXT NOT NULL,
    version INTEGER NOT NULL,
    scheme_id TEXT NOT NULL,
    plan_option_id TEXT NOT NULL,
    effective_from TEXT NOT NULL,
    effective_to TEXT,
    status TEXT NOT NULL,
    approved_by TEXT,
    approved_at TEXT,
    runtime_toggles_json TEXT NOT NULL,
    rule_ids_json TEXT NOT NULL,
    PRIMARY KEY (policy_profile_id, version)
);

CREATE TABLE rule_definitions (
    rule_id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    category TEXT NOT NULL,
    severity TEXT NOT NULL,
    reason_code TEXT NOT NULL,
    message TEXT NOT NULL,
    remediation_hint TEXT NOT NULL,
    affected_fields_json TEXT NOT NULL,
    stage_scope_json TEXT NOT NULL,
    enabled INTEGER NOT NULL,
    decision_table_json TEXT NOT NULL
);

CREATE TABLE icd10_codes (
    code TEXT PRIMARY KEY,
    description TEXT NOT NULL,
    version TEXT NOT NULL,
    status TEXT NOT NULL
);

CREATE TABLE pmb_conditions (
    condition_id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    category TEXT NOT NULL,
    metadata_json TEXT NOT NULL,
    evidence_requirements_json TEXT NOT NULL,
    status TEXT NOT NULL
);

CREATE TABLE pmb_mapping_rules (
    mapping_id TEXT PRIMARY KEY,
    icd10_code TEXT NOT NULL,
    pmb_condition_id TEXT NOT NULL,
    version INTEGER NOT NULL,
    effective_from TEXT NOT NULL,
    effective_to TEXT,
    confidence TEXT NOT NULL,
    auto_route_allowed INTEGER NOT NULL,
    required_evidence_types_json TEXT NOT NULL,
    status TEXT NOT NULL,
    source TEXT NOT NULL
);

CREATE TABLE benefit_route_decisions (
    decision_id TEXT PRIMARY KEY,
    claim_id INTEGER NOT NULL,
    claim_version INTEGER NOT NULL,
    stage TEXT NOT NULL,
    trigger_icd10 TEXT,
    mapping_id TEXT,
    pmb_condition_id TEXT,
    provider_marked_pmb INTEGER NOT NULL,
    pmb_detected INTEGER NOT NULL,
    route TEXT NOT NULL,
    action TEXT NOT NULL,
    confidence TEXT NOT NULL,
    reason_code TEXT NOT NULL,
    message TEXT NOT NULL,
    remediation_hint TEXT NOT NULL,
    evidence_required_json TEXT NOT NULL,
    evidence_missing_json TEXT NOT NULL,
    created_at TEXT NOT NULL
);

CREATE TABLE submissions (
    submission_id TEXT PRIMARY KEY,
    claim_id INTEGER NOT NULL,
    claim_version INTEGER NOT NULL,
    channel TEXT NOT NULL,
    correlation_id TEXT NOT NULL,
    idempotency_key TEXT NOT NULL UNIQUE,
    status TEXT NOT NULL,
    attempts INTEGER NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE transport_logs (
    transport_log_id TEXT PRIMARY KEY,
    submission_id TEXT NOT NULL,
    event TEXT NOT NULL,
    details_json TEXT NOT NULL,
    created_at TEXT NOT NULL
);

CREATE TABLE responses (
    response_id TEXT PRIMARY KEY,
    submission_id TEXT NOT NULL,
    claim_id INTEGER NOT NULL,
    claim_version INTEGER NOT NULL,
    status TEXT NOT NULL,
    reasons_json TEXT NOT NULL,
    received_at TEXT NOT NULL
);

CREATE TABLE financial_bundles (
    financial_bundle_id TEXT PRIMARY KEY,
    claim_id INTEGER NOT NULL,
    claim_version INTEGER NOT NULL,
    policy_profile_id TEXT NOT NULL,
    policy_version INTEGER NOT NULL,
    totals_json TEXT NOT NULL,
    line_outcomes_json TEXT NOT NULL,
    created_at TEXT NOT NULL
);

CREATE TABLE payments (
    id INTEGER PRIMARY KEY,
    claim_id INTEGER NOT NULL,
    amount NUMERIC NOT NULL,
    payment_date TEXT NOT NULL,
    method TEXT NOT NULL,
    status TEXT NOT NULL,
    created_at TEXT NOT NULL
);

CREATE TABLE remittances (
    remittance_id TEXT PRIMARY KEY,
    claim_id INTEGER NOT NULL,
    claim_version INTEGER NOT NULL,
    payment_batch_ref TEXT NOT NULL,
    claim_reference TEXT NOT NULL,
    lines_json TEXT NOT NULL,
    totals_json TEXT NOT NULL,
    created_at TEXT NOT NULL
);

CREATE TABLE reconciliations (
    reconciliation_id TEXT PRIMARY KEY,
    claim_id INTEGER NOT NULL,
    claim_version INTEGER NOT NULL,
    status TEXT NOT NULL,
    exception_reasons_json TEXT NOT NULL,
    created_at TEXT NOT NULL
);

CREATE TABLE audit_events (
    audit_event_id TEXT PRIMARY KEY,
    event_type TEXT NOT NULL,
    actor TEXT NOT NULL,
    role TEXT NOT NULL,
    entity_type TEXT NOT NULL,
    entity_id TEXT NOT NULL,
    policy_profile_id TEXT,
    policy_version INTEGER,
    hashes_json TEXT NOT NULL,
    detail_json TEXT NOT NULL,
    timestamp TEXT NOT NULL
);
