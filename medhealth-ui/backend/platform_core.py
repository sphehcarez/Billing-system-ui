from __future__ import annotations

from copy import deepcopy
from datetime import UTC, datetime, timedelta
import hashlib
import json
import re
from typing import Any, Dict, List, Literal, Optional
from uuid import uuid4

from pydantic import BaseModel, Field


StageName = Literal[
    "READINESS",
    "CLOSURE_GATE",
    "POST_CLOSURE_VALIDATION",
    "SUBMISSION_CHECKS",
    "ADJUDICATION_RULES",
]
Severity = Literal["BLOCK", "WARN", "INFO"]
Outcome = Literal["PASS", "WARN", "BLOCK", "REJECT", "PEND"]


def utc_now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def stable_hash(payload: Any) -> str:
    blob = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")
    return "sha256:" + hashlib.sha256(blob).hexdigest()


def new_ref(prefix: str) -> str:
    return f"{prefix}-{uuid4().hex[:12]}"


def to_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        return False
    return str(value).strip().lower() in {"1", "true", "yes", "y", "on"}


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: str


class LoginRequest(BaseModel):
    username: str
    password: str
    role: Optional[str] = None


class Patient(BaseModel):
    id: Optional[int] = None
    name: str
    mrn: str
    dob: str
    sex: str = "U"
    email: str
    phone: str
    status: str = "active"
    created_at: Optional[str] = None


class Provider(BaseModel):
    id: Optional[int] = None
    name: str
    npi: str
    practice_number: str
    specialty: str
    discipline: str = "SPECIALIST"
    is_dsp_provider: bool = True
    email: str
    phone: str
    status: str = "active"
    created_at: Optional[str] = None


class User(BaseModel):
    id: Optional[int] = None
    username: str
    email: str
    role: str
    status: str = "active"
    created_at: Optional[str] = None


class UserCreate(User):
    password: str


class Diagnosis(BaseModel):
    seq: int
    icd10: str = ""
    diagnosis_type: Literal["PRIMARY", "SECONDARY", "REFERRAL"] = "PRIMARY"


class ClaimLineItem(BaseModel):
    line_id: str
    service_code: str
    service_description: str
    quantity: float = 1.0
    unit_price: float = 0.0
    claimed_amount: float = 0.0
    service_date: Optional[str] = None
    diagnosis_refs: List[int] = Field(default_factory=list)
    modifiers: List[str] = Field(default_factory=list)
    nappi_code: Optional[str] = None
    device_id: Optional[str] = None
    rendering_provider_practice_number: Optional[str] = None
    requires_preauth: bool = False
    requires_attachment: bool = False


class AuthorizationRecord(BaseModel):
    auth_number: str
    auth_type: Literal["ADMISSION", "PROCEDURE", "MEDICINE", "OTHER"] = "PROCEDURE"
    valid_from: str
    valid_to: str


class AttachmentRecord(BaseModel):
    attachment_id: str
    attachment_type: Literal["MOTIVATION", "REPORT", "INVOICE", "PROOF_OF_PAYMENT", "OTHER"]
    file_name: str
    storage_ref: str
    file_hash: str
    uploaded_at: str
    uploaded_by: str
    virus_scan_status: Literal["CLEAN", "PENDING"] = "CLEAN"


class ReferenceVersion(BaseModel):
    reference_key: str
    version: str
    effective_from: str


class ICD10Code(BaseModel):
    code: str
    description: str
    version: str
    active: bool = True
    effective_from: Optional[str] = None
    effective_to: Optional[str] = None
    source: str = "development_placeholder_reference_data"
    status: Literal["ACTIVE", "RETIRED"] = "ACTIVE"


class PMBCondition(BaseModel):
    condition_id: str
    name: str
    type: Literal["DTP", "CDL", "EMERGENCY", "UNSPECIFIED"] = "UNSPECIFIED"
    descriptor: str = ""
    category: str
    metadata: Dict[str, Any] = Field(default_factory=dict)
    evidence_requirements: List[str] = Field(default_factory=list)
    confirmation_flags: List[str] = Field(default_factory=list)
    active: bool = True
    effective_from: str = "2026-01-01"
    effective_to: Optional[str] = None
    source: str = "development_placeholder_business_owned_required"
    status: Literal["ACTIVE", "RETIRED"] = "ACTIVE"


class PMBMappingRule(BaseModel):
    mapping_id: str
    icd10_code: str
    pmb_condition_id: str
    match_type: Literal["EXACT", "PREFIX"] = "EXACT"
    version: int
    effective_from: str
    effective_to: Optional[str] = None
    confidence: Literal["HIGH", "MEDIUM", "LOW"] = "LOW"
    auto_route_allowed: bool = False
    required_evidence_types: List[str] = Field(default_factory=list)
    active: bool = True
    status: Literal["DRAFT", "ACTIVE", "RETIRED"] = "ACTIVE"
    source: str = "business_owned_reference_data"


class BenefitRouteRule(BaseModel):
    rule_id: str
    scheme_id: str
    plan_option_id: str
    route_when_confirmed: Literal["PMB_BENEFIT_BUCKET", "PMB_REVIEW_QUEUE", "NORMAL_BENEFIT"] = "PMB_BENEFIT_BUCKET"
    route_when_possible: Literal["PMB_BENEFIT_BUCKET", "PMB_REVIEW_QUEUE", "NORMAL_BENEFIT"] = "PMB_REVIEW_QUEUE"
    route_when_missing_evidence: Literal["PMB_BENEFIT_BUCKET", "PMB_REVIEW_QUEUE", "NORMAL_BENEFIT"] = "PMB_REVIEW_QUEUE"
    auto_route_possible_matches: bool = False
    active: bool = True
    effective_from: str
    effective_to: Optional[str] = None
    source: str = "development_placeholder_business_owned_required"


class TariffRate(BaseModel):
    rate_id: str
    scheme_id: str
    plan_option_id: str
    tariff_code: str
    dsp_flag: bool = True
    rate_amount: float
    unit: str = "PER_SERVICE"
    active: bool = True
    effective_from: str
    effective_to: Optional[str] = None
    source: str = "development_placeholder_business_owned_required"


class PMBPaymentPolicy(BaseModel):
    policy_id: str
    scheme_id: str
    plan_option_id: str
    pay_in_full_requires_dsp: bool = True
    voluntary_non_dsp_rate_mode: Literal["DSP_RATE", "SCHEME_RATE", "CLAIMED_LIMITED"] = "DSP_RATE"
    involuntary_non_dsp_no_copay: bool = True
    active: bool = True
    effective_from: str
    effective_to: Optional[str] = None
    source: str = "development_placeholder_business_owned_required"


class ClaimDiagnosis(BaseModel):
    diagnosis_id: str
    claim_id: int
    seq: int
    icd10_code: str
    is_primary: bool = False
    source: str = "UserEntry"
    captured_by: str
    captured_at: str


class PMBDecision(BaseModel):
    decision_id: str
    claim_id: int
    claim_version: int
    stage: StageName
    pmb_status: Literal["UNKNOWN", "NOT_DETECTED", "POSSIBLE", "REVIEW_REQUIRED", "CONFIRMED"] = "UNKNOWN"
    matched_icd10: Optional[str] = None
    mapping_id: Optional[str] = None
    condition_id: Optional[str] = None
    condition_name: Optional[str] = None
    condition_type: Optional[str] = None
    provider_marked_pmb: bool = False
    auto_flagged: bool = False
    reason_code: str
    message: str
    remediation_hint: str
    explainability: str
    descriptor: Optional[str] = None
    confidence: Literal["HIGH", "MEDIUM", "LOW", "NONE"] = "NONE"
    evidence_required: List[str] = Field(default_factory=list)
    evidence_missing: List[str] = Field(default_factory=list)
    created_at: str


class BenefitRouteDecision(BaseModel):
    decision_id: str
    claim_id: int
    claim_version: int
    stage: StageName
    pmb_decision_id: Optional[str] = None
    pmb_status: Literal["UNKNOWN", "NOT_DETECTED", "POSSIBLE", "REVIEW_REQUIRED", "CONFIRMED"] = "UNKNOWN"
    trigger_icd10: Optional[str] = None
    mapping_id: Optional[str] = None
    pmb_condition_id: Optional[str] = None
    provider_marked_pmb: bool = False
    pmb_detected: bool = False
    route: Literal["NORMAL_BENEFIT", "PMB_BENEFIT_BUCKET", "PMB_REVIEW_QUEUE"] = "NORMAL_BENEFIT"
    action: Literal["NO_PMB_MATCH", "SYSTEM_FLAGGED", "ROUTED_TO_PMB_BUCKET", "ROUTED_TO_PMB_REVIEW"] = "NO_PMB_MATCH"
    confidence: Literal["HIGH", "MEDIUM", "LOW", "NONE"] = "NONE"
    reason_code: str
    message: str
    remediation_hint: str
    evidence_required: List[str] = Field(default_factory=list)
    evidence_missing: List[str] = Field(default_factory=list)
    created_at: str


class CostingPreview(BaseModel):
    preview_id: str
    claim_id: int
    claim_version: int
    stage: StageName
    pmb_decision_id: Optional[str] = None
    routing_decision_id: Optional[str] = None
    claimed_total: float
    allowed_total: float
    pmb_allowed_total: Optional[float] = None
    member_liability_estimate: float
    pricing_basis: Literal["DSP", "NON_DSP_VOLUNTARY", "NON_DSP_INVOLUNTARY", "SCHEME_STANDARD"] = "SCHEME_STANDARD"
    pending_pmb_review: bool = False
    provisional: bool = False
    reason_code: str
    explanation: str
    created_at: str


class RuleHit(BaseModel):
    rule_id: str
    name: str
    category: str
    severity: Severity
    reason_code: str
    message: str
    remediation_hint: str
    affected_fields: List[str] = Field(default_factory=list)
    evaluated_facts: Dict[str, Any] = Field(default_factory=dict)


class DecisionBundle(BaseModel):
    decision_bundle_id: str
    claim_id: int
    claim_version: int
    snapshot_id: Optional[str] = None
    stage: StageName
    policy_profile_id: str
    policy_version: int
    outcome: Outcome
    input_hash: str
    payload_hash: Optional[str] = None
    reference_versions: Dict[str, str]
    rule_hits: List[RuleHit] = Field(default_factory=list)
    explanations: List[str] = Field(default_factory=list)
    created_at: str
    created_by: str


class ReadinessItem(BaseModel):
    item_id: str
    claim_id: int
    claim_version: int
    severity: Severity
    reason_code: str
    message: str
    remediation_hint: str
    affected_fields: List[str] = Field(default_factory=list)


class ReadinessRun(BaseModel):
    readiness_run_id: str
    claim_id: int
    claim_version: int
    decision_bundle_id: str
    outcome: Outcome
    created_at: str
    items: List[ReadinessItem]


class BillingSnapshot(BaseModel):
    snapshot_id: str
    claim_id: int
    claim_version: int
    data: Dict[str, Any]
    input_hash: str
    created_at: str
    created_by: str


class ClaimVersion(BaseModel):
    claim_id: int
    version: int
    snapshot_id: Optional[str] = None
    status: str = "DRAFT"
    previous_version: Optional[int] = None
    change_summary: str = "Initial version"
    created_at: str


class PayloadArtifact(BaseModel):
    payload_id: str
    claim_id: int
    claim_version: int
    snapshot_id: str
    canonical_claim: Dict[str, Any]
    pseudo_edi: str
    phisc_xml: str
    canonical_hash: str
    payload_hash: str
    created_at: str


class Submission(BaseModel):
    submission_id: str
    claim_id: int
    claim_version: int
    channel: Literal["DIRECT", "SWITCH"]
    correlation_id: str
    idempotency_key: str
    status: str
    attempts: int = 1
    created_at: str
    updated_at: str


class TransportLog(BaseModel):
    transport_log_id: str
    submission_id: str
    event: str
    details: Dict[str, Any]
    created_at: str


class ResponseReason(BaseModel):
    level: Literal["HEADER", "LINE"]
    reason_code: str
    message: str
    line_id: Optional[str] = None


class ResponseRecord(BaseModel):
    response_id: str
    submission_id: str
    claim_id: int
    claim_version: int
    status: Literal["ACK", "REJ", "PEND"]
    reasons: List[ResponseReason] = Field(default_factory=list)
    received_at: str


class FinancialLineOutcome(BaseModel):
    line_id: str
    claimed_amount: float
    allowed_amount: float
    paid_amount: float
    member_liability: float
    scheme_liability: float
    reason_codes: List[str] = Field(default_factory=list)


class FinancialBundle(BaseModel):
    financial_bundle_id: str
    claim_id: int
    claim_version: int
    policy_profile_id: str
    policy_version: int
    totals: Dict[str, float]
    line_outcomes: List[FinancialLineOutcome]
    created_at: str


class PaymentRecord(BaseModel):
    id: Optional[int] = None
    claim_id: int
    amount: float
    payment_date: str
    method: str
    status: str = "pending"
    created_at: Optional[str] = None


class RemittanceLine(BaseModel):
    line_id: str
    paid_amount: float
    adjustment_amount: float
    status: Literal["PAID", "PARTIAL", "DENIED"]
    reason_codes: List[str] = Field(default_factory=list)


class RemittanceAdvice(BaseModel):
    remittance_id: str
    claim_id: int
    claim_version: int
    payment_batch_ref: str
    claim_reference: str
    lines: List[RemittanceLine]
    totals: Dict[str, float]
    created_at: str


class ReconciliationRecord(BaseModel):
    reconciliation_id: str
    claim_id: int
    claim_version: int
    status: Literal["RECONCILED", "PARTIAL", "EXCEPTION"]
    exception_reasons: List[str] = Field(default_factory=list)
    created_at: str


class AuditEvent(BaseModel):
    audit_event_id: str
    event_type: str
    actor: str
    role: str
    entity_type: str
    entity_id: str
    policy_profile_id: Optional[str] = None
    policy_version: Optional[int] = None
    hashes: Dict[str, str] = Field(default_factory=dict)
    detail: Dict[str, Any] = Field(default_factory=dict)
    timestamp: str


class RuleDefinition(BaseModel):
    rule_id: str
    name: str
    category: str
    severity: Severity
    reason_code: str
    message: str
    remediation_hint: str
    affected_fields: List[str] = Field(default_factory=list)
    stage_scope: List[StageName]
    enabled: bool = True
    decision_table: Dict[str, Any]


class PolicyProfile(BaseModel):
    policy_profile_id: str
    scheme_id: str
    plan_option_id: str
    version: int
    effective_from: str
    effective_to: Optional[str] = None
    status: Literal["DRAFT", "APPROVED", "ACTIVE", "RETIRED"] = "ACTIVE"
    approved_by: Optional[str] = None
    approved_at: Optional[str] = None
    runtime_toggles: Dict[str, Any] = Field(default_factory=dict)
    rule_ids: List[str] = Field(default_factory=list)


class ClaimRecord(BaseModel):
    id: Optional[int] = None
    version: int = 1
    previous_version: Optional[int] = None
    scenario_key: str = "clean_success"
    status: str = "draft"
    claim_number: str
    claim_reference: str
    batch_reference: Optional[str] = None
    invoice_number: str
    scheme_id: str = "SCHEME_A"
    plan_option_id: str = "OPTION_X"
    member_number: str
    dependant_code: str = "01"
    membership_status: str = "ACTIVE"
    patient_id: int
    provider_id: int
    care_setting: str = "OUTPATIENT"
    service_date: str
    admission_date_time: Optional[str] = None
    discharge_date_time: Optional[str] = None
    diagnoses: List[Diagnosis] = Field(default_factory=list)
    line_items: List[ClaimLineItem] = Field(default_factory=list)
    authorisations: List[AuthorizationRecord] = Field(default_factory=list)
    attachments: List[AttachmentRecord] = Field(default_factory=list)
    clinical_summary: Optional[str] = None
    source_system: str = "UserEntry"
    provider_pmb_indicator: Optional[bool] = None
    provider_is_dsp: Optional[bool] = None
    non_dsp_access_type: Literal["NOT_APPLICABLE", "VOLUNTARY", "INVOLUNTARY"] = "NOT_APPLICABLE"
    pmb_status: str = "not_evaluated"
    readiness_status: str = "pending"
    validation_status: str = "pending"
    payload_status: str = "not_built"
    submission_status: str = "not_submitted"
    submission_channel: Optional[str] = None
    remittance_status: str = "pending"
    reconciliation_status: str = "pending"
    latest_snapshot_id: Optional[str] = None
    latest_payload_id: Optional[str] = None
    latest_submission_id: Optional[str] = None
    latest_response_id: Optional[str] = None
    latest_financial_bundle_id: Optional[str] = None
    latest_remittance_id: Optional[str] = None
    latest_reconciliation_id: Optional[str] = None
    latest_pmb_decision_id: Optional[str] = None
    latest_benefit_route_decision_id: Optional[str] = None
    latest_costing_preview_id: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class Report(BaseModel):
    id: Optional[int] = None
    name: str
    report_type: str
    generated_at: str
    period: str
    summary: Dict[str, Any] = Field(default_factory=dict)


class ClaimSubmissionRequest(BaseModel):
    channel: Literal["DIRECT", "SWITCH", "direct", "switch"]
    idempotency_key: Optional[str] = None


class ClaimClosureRequest(BaseModel):
    supervisor_override: bool = False
    override_note: Optional[str] = None


class PolicyProfilePatch(BaseModel):
    effective_from: Optional[str] = None
    effective_to: Optional[str] = None
    runtime_toggles: Optional[Dict[str, Any]] = None
    status: Optional[str] = None
    approved_by: Optional[str] = None


class RulePatch(BaseModel):
    enabled: Optional[bool] = None
    severity: Optional[Severity] = None
    message: Optional[str] = None
    remediation_hint: Optional[str] = None
    decision_table: Optional[Dict[str, Any]] = None


class ICD10ValidationService:
    def __init__(self, store: PlatformStore) -> None:
        self.store = store

    def validate_code(self, code: str, as_of: Optional[str] = None) -> Optional[str]:
        normalized = code.strip().upper()
        reference = self.store._active_icd10_reference(normalized, as_of)
        if not normalized:
            return "ICD_EMPTY"
        if not self.store._icd10_format_valid(normalized):
            return "ICD_INVALID_FORMAT"
        if not reference:
            return "ICD_NOT_IN_REFERENCE"
        return None

    def evaluate_claim(self, claim: ClaimRecord) -> Dict[str, Any]:
        diagnoses = self.store.get_claim_diagnoses(claim.id)
        primary = next((item for item in diagnoses if item.is_primary), None)
        issues: List[Dict[str, Any]] = []
        invalid_codes: List[str] = []

        if primary is None:
            issues.append(
                {
                    "severity": "BLOCK",
                    "reason_code": "ICD_MISSING_PRIMARY",
                    "message": "Primary ICD-10 required",
                    "remediation": "Capture a valid primary ICD-10 and mark it primary before continuing.",
                }
            )

        for diagnosis in diagnoses:
            error = self.validate_code(diagnosis.icd10_code, claim.service_date)
            if error:
                invalid_codes.append(diagnosis.icd10_code.strip().upper())

        if invalid_codes:
            issues.append(
                {
                    "severity": "BLOCK",
                    "reason_code": "ICD_INVALID",
                    "message": "One or more ICD-10 codes are invalid or inactive in the configured reference.",
                    "remediation": "Select a valid ICD-10 from the configured reference data before continuing.",
                    "invalid_codes": invalid_codes,
                }
            )

        return {
            "diagnoses": diagnoses,
            "primary_diagnosis": primary,
            "invalid_codes": invalid_codes,
            "issues": issues,
        }


class PMBDetectionService:
    def __init__(self, store: PlatformStore) -> None:
        self.store = store

    def evaluate(self, claim: ClaimRecord, stage: StageName) -> PMBDecision:
        validation = self.store.icd10_validation_service.evaluate_claim(claim)
        provider_marked_pmb = bool(claim.provider_pmb_indicator)
        primary = validation["primary_diagnosis"]

        if primary is None:
            return PMBDecision(
                decision_id=new_ref("pmb"),
                claim_id=claim.id,
                claim_version=claim.version,
                stage=stage,
                pmb_status="UNKNOWN",
                provider_marked_pmb=provider_marked_pmb,
                auto_flagged=False,
                reason_code="ICD_MISSING_PRIMARY",
                message="PMB cannot be evaluated until primary diagnosis is captured.",
                remediation_hint="Jump to diagnoses, capture a valid primary ICD-10, and rerun readiness.",
                explainability="No primary diagnosis is present, so PMB identification cannot run safely.",
                created_at=utc_now(),
            )

        mapping = self.store._best_pmb_mapping_for_claim(claim)
        if not mapping:
            return PMBDecision(
                decision_id=new_ref("pmb"),
                claim_id=claim.id,
                claim_version=claim.version,
                stage=stage,
                pmb_status="NOT_DETECTED",
                provider_marked_pmb=provider_marked_pmb,
                auto_flagged=False,
                matched_icd10=primary.icd10_code,
                reason_code="PMB_NOT_DETECTED",
                message="No configured ICD-10 to PMB mapping matched the claim diagnoses.",
                remediation_hint="Continue normal benefit routing unless reference data changes.",
                explainability=f"Primary ICD-10 {primary.icd10_code} did not match any active PMB mapping.",
                created_at=utc_now(),
            )

        condition = self.store.pmb_conditions.get(mapping.pmb_condition_id)
        evidence_required = list(mapping.required_evidence_types or (condition.evidence_requirements if condition else []))
        evidence_missing = self.store._missing_pmb_evidence(claim, mapping)
        status: Literal["UNKNOWN", "NOT_DETECTED", "POSSIBLE", "REVIEW_REQUIRED", "CONFIRMED"] = "POSSIBLE"
        reason_code = "PMB_POSSIBLE_MATCH"
        message = "ICD-10 matched a configured PMB mapping. Confirmation evidence is still required."
        remediation_hint = "Review the PMB mapping and add the configured evidence before treating the claim as confirmed PMB."

        if evidence_required and not evidence_missing:
            status = "CONFIRMED"
            reason_code = "PMB_CONFIRMED"
            message = "ICD-10 matched a configured PMB mapping and all configured evidence is present."
            remediation_hint = "No remediation required unless a reviewer overrides the PMB assessment."
        elif evidence_required and evidence_missing:
            status = "REVIEW_REQUIRED"
            reason_code = "PMB_REVIEW_REQUIRED"
            message = "ICD-10 matched a configured PMB mapping, but confirmation evidence is still missing."
            remediation_hint = "Capture the missing PMB descriptor evidence or route the claim to PMB review."

        explainability = (
            f"ICD-10 {primary.icd10_code} matched mapping {mapping.mapping_id} for condition {mapping.pmb_condition_id}. "
            f"Provider marked PMB: {'yes' if provider_marked_pmb else 'no'}. "
            f"Evidence missing: {', '.join(evidence_missing) if evidence_missing else 'none'}."
        )

        return PMBDecision(
            decision_id=new_ref("pmb"),
            claim_id=claim.id,
            claim_version=claim.version,
            stage=stage,
            pmb_status=status,
            matched_icd10=primary.icd10_code,
            mapping_id=mapping.mapping_id,
            condition_id=mapping.pmb_condition_id,
            condition_name=condition.name if condition else None,
            condition_type=condition.type if condition else None,
            provider_marked_pmb=provider_marked_pmb,
            auto_flagged=True,
            reason_code=reason_code,
            message=message,
            remediation_hint=remediation_hint,
            explainability=explainability,
            descriptor=condition.descriptor if condition else None,
            confidence=mapping.confidence,
            evidence_required=evidence_required,
            evidence_missing=evidence_missing,
            created_at=utc_now(),
        )


class BenefitRoutingService:
    def __init__(self, store: PlatformStore) -> None:
        self.store = store

    def evaluate(self, claim: ClaimRecord, stage: StageName, pmb_decision: PMBDecision) -> BenefitRouteDecision:
        provider_marked_pmb = bool(claim.provider_pmb_indicator)
        rule = self.store._resolve_benefit_route_rule(claim.scheme_id, claim.plan_option_id, claim.service_date)
        route: Literal["NORMAL_BENEFIT", "PMB_BENEFIT_BUCKET", "PMB_REVIEW_QUEUE"] = "NORMAL_BENEFIT"
        action: Literal["NO_PMB_MATCH", "SYSTEM_FLAGGED", "ROUTED_TO_PMB_BUCKET", "ROUTED_TO_PMB_REVIEW"] = "NO_PMB_MATCH"
        reason_code = "ROUTE_NORMAL"
        message = "Claim remains in the normal benefit path."
        remediation_hint = "No PMB routing action is required."

        if pmb_decision.pmb_status == "CONFIRMED":
            route = rule.route_when_confirmed if rule else "PMB_BENEFIT_BUCKET"
            action = "ROUTED_TO_PMB_BUCKET" if route == "PMB_BENEFIT_BUCKET" else "ROUTED_TO_PMB_REVIEW"
            reason_code = "ROUTE_PMB_CONFIRMED"
            message = "Confirmed PMB claim routed according to the active benefit routing rule."
            remediation_hint = "Verify the PMB benefit bucket or review queue assignment if needed."
        elif pmb_decision.pmb_status == "POSSIBLE":
            route = (
                rule.route_when_confirmed
                if rule and rule.auto_route_possible_matches
                else (rule.route_when_possible if rule else "PMB_REVIEW_QUEUE")
            )
            action = "ROUTED_TO_PMB_BUCKET" if route == "PMB_BENEFIT_BUCKET" else "ROUTED_TO_PMB_REVIEW"
            reason_code = "ROUTE_PMB_REVIEW"
            message = "Possible PMB claim routed conservatively pending confirmation."
            remediation_hint = "Review PMB confirmation evidence before finalising payment treatment."
        elif pmb_decision.pmb_status in {"REVIEW_REQUIRED", "UNKNOWN"}:
            route = rule.route_when_missing_evidence if rule else "PMB_REVIEW_QUEUE"
            action = "ROUTED_TO_PMB_REVIEW" if route == "PMB_REVIEW_QUEUE" else "ROUTED_TO_PMB_BUCKET"
            reason_code = "ROUTE_PMB_REVIEW"
            message = "PMB review is required before the claim can be treated as confirmed PMB."
            remediation_hint = "Capture the missing PMB evidence or resolve the diagnosis blocker."

        if pmb_decision.pmb_status in {"POSSIBLE", "REVIEW_REQUIRED", "CONFIRMED"} and not provider_marked_pmb:
            message = (
                "Provider did not mark PMB, but the system identified a PMB mapping and applied configured routing."
            )

        return BenefitRouteDecision(
            decision_id=new_ref("brd"),
            claim_id=claim.id,
            claim_version=claim.version,
            stage=stage,
            pmb_decision_id=pmb_decision.decision_id,
            pmb_status=pmb_decision.pmb_status,
            trigger_icd10=pmb_decision.matched_icd10,
            mapping_id=pmb_decision.mapping_id,
            pmb_condition_id=pmb_decision.condition_id,
            provider_marked_pmb=provider_marked_pmb,
            pmb_detected=pmb_decision.pmb_status in {"POSSIBLE", "REVIEW_REQUIRED", "CONFIRMED"},
            route=route,
            action=action,
            confidence=pmb_decision.confidence,
            reason_code=reason_code,
            message=message,
            remediation_hint=remediation_hint,
            evidence_required=pmb_decision.evidence_required,
            evidence_missing=pmb_decision.evidence_missing,
            created_at=utc_now(),
        )


class CostingPreviewService:
    def __init__(self, store: PlatformStore) -> None:
        self.store = store

    def evaluate(
        self,
        claim: ClaimRecord,
        stage: StageName,
        pmb_decision: PMBDecision,
        routing_decision: BenefitRouteDecision,
    ) -> CostingPreview:
        policy = self.store._resolve_pmb_payment_policy(claim.scheme_id, claim.plan_option_id, claim.service_date)
        claimed_total = round(sum(item.claimed_amount for item in claim.line_items), 2)
        allowed_total = round(sum(self._line_allowed(item, claim, False) for item in claim.line_items), 2)
        provider_is_dsp = self.store._claim_provider_is_dsp(claim)
        access_type = claim.non_dsp_access_type
        pricing_basis: Literal["DSP", "NON_DSP_VOLUNTARY", "NON_DSP_INVOLUNTARY", "SCHEME_STANDARD"] = "DSP" if provider_is_dsp else (
            "NON_DSP_VOLUNTARY" if access_type == "VOLUNTARY" else ("NON_DSP_INVOLUNTARY" if access_type == "INVOLUNTARY" else "SCHEME_STANDARD")
        )
        provisional = pmb_decision.pmb_status in {"POSSIBLE", "REVIEW_REQUIRED"}
        pending_pmb_review = provisional
        pmb_allowed_total: Optional[float] = None
        member_liability = max(0.0, round(claimed_total - allowed_total, 2))
        reason_code = "COSTING_SCHEME_STANDARD"
        explanation = "Standard scheme tariff preview applied."

        if pmb_decision.pmb_status == "CONFIRMED":
            pmb_allowed_total = round(self._confirmed_pmb_allowed(claim, claimed_total, allowed_total, policy, provider_is_dsp), 2)
            member_liability = 0.0 if self._member_liability_waived(claim, policy, provider_is_dsp) else max(0.0, round(claimed_total - pmb_allowed_total, 2))
            reason_code = "COSTING_PMB_CONFIRMED"
            explanation = "Confirmed PMB costing preview computed using the active DSP payment policy."
        elif provisional:
            pmb_allowed_total = round(self._confirmed_pmb_allowed(claim, claimed_total, allowed_total, policy, provider_is_dsp), 2)
            member_liability = 0.0 if self._member_liability_waived(claim, policy, provider_is_dsp) else max(0.0, round(claimed_total - pmb_allowed_total, 2))
            reason_code = "COSTING_PMB_PROVISIONAL"
            explanation = "Provisional PMB costing preview computed pending PMB review confirmation."

        return CostingPreview(
            preview_id=new_ref("cost"),
            claim_id=claim.id,
            claim_version=claim.version,
            stage=stage,
            pmb_decision_id=pmb_decision.decision_id,
            routing_decision_id=routing_decision.decision_id,
            claimed_total=claimed_total,
            allowed_total=allowed_total,
            pmb_allowed_total=pmb_allowed_total,
            member_liability_estimate=round(member_liability, 2),
            pricing_basis=pricing_basis,
            pending_pmb_review=pending_pmb_review,
            provisional=provisional,
            reason_code=reason_code,
            explanation=explanation,
            created_at=utc_now(),
        )

    def _line_allowed(self, line_item: ClaimLineItem, claim: ClaimRecord, dsp_flag: bool) -> float:
        rate = self.store._resolve_tariff_rate(claim.scheme_id, claim.plan_option_id, line_item.service_code, dsp_flag, claim.service_date)
        if not rate:
            return line_item.claimed_amount
        if rate.unit == "PER_SERVICE":
            return min(line_item.claimed_amount, rate.rate_amount * line_item.quantity)
        return min(line_item.claimed_amount, rate.rate_amount)

    def _member_liability_waived(self, claim: ClaimRecord, policy: Optional[PMBPaymentPolicy], provider_is_dsp: bool) -> bool:
        if provider_is_dsp:
            return True
        return bool(policy and claim.non_dsp_access_type == "INVOLUNTARY" and policy.involuntary_non_dsp_no_copay)

    def _confirmed_pmb_allowed(
        self,
        claim: ClaimRecord,
        claimed_total: float,
        allowed_total: float,
        policy: Optional[PMBPaymentPolicy],
        provider_is_dsp: bool,
    ) -> float:
        if provider_is_dsp:
            return claimed_total
        if claim.non_dsp_access_type == "INVOLUNTARY":
            return claimed_total if policy and policy.involuntary_non_dsp_no_copay else allowed_total
        if not policy:
            return allowed_total
        if policy.voluntary_non_dsp_rate_mode == "CLAIMED_LIMITED":
            return min(claimed_total, allowed_total)
        if policy.voluntary_non_dsp_rate_mode == "SCHEME_RATE":
            return allowed_total
        dsp_total = round(sum(self._line_allowed(item, claim, True) for item in claim.line_items), 2)
        return dsp_total

class PlatformStore:
    def __init__(self) -> None:
        self.patients: Dict[int, Patient] = {}
        self.providers: Dict[int, Provider] = {}
        self.users: Dict[int, User] = {}
        self.auth_users: Dict[str, Dict[str, Any]] = {}
        self.claims: Dict[int, ClaimRecord] = {}
        self.claim_versions: Dict[int, List[ClaimVersion]] = {}
        self.claim_history: Dict[str, Dict[str, Any]] = {}
        self.billing_snapshots: Dict[str, BillingSnapshot] = {}
        self.reference_versions: Dict[str, ReferenceVersion] = {}
        self.icd10_codes: Dict[str, ICD10Code] = {}
        self.claim_diagnoses: Dict[int, List[ClaimDiagnosis]] = {}
        self.pmb_conditions: Dict[str, PMBCondition] = {}
        self.pmb_mapping_rules: Dict[str, PMBMappingRule] = {}
        self.benefit_route_rules: Dict[str, BenefitRouteRule] = {}
        self.tariff_rates: Dict[str, TariffRate] = {}
        self.pmb_payment_policies: Dict[str, PMBPaymentPolicy] = {}
        self.pmb_decisions: Dict[str, PMBDecision] = {}
        self.benefit_route_decisions: Dict[str, BenefitRouteDecision] = {}
        self.costing_previews: Dict[str, CostingPreview] = {}
        self.rule_definitions: Dict[str, RuleDefinition] = {}
        self.policy_profiles: Dict[str, List[PolicyProfile]] = {}
        self.readiness_runs: Dict[str, ReadinessRun] = {}
        self.readiness_items: Dict[str, ReadinessItem] = {}
        self.decision_bundles: Dict[str, DecisionBundle] = {}
        self.payloads: Dict[str, PayloadArtifact] = {}
        self.submissions: Dict[str, Submission] = {}
        self.transport_logs: Dict[str, TransportLog] = {}
        self.responses: Dict[str, ResponseRecord] = {}
        self.financial_bundles: Dict[str, FinancialBundle] = {}
        self.payments: Dict[int, PaymentRecord] = {}
        self.remittances: Dict[str, RemittanceAdvice] = {}
        self.reconciliations: Dict[str, ReconciliationRecord] = {}
        self.audit_events: Dict[str, AuditEvent] = {}
        self.reports: Dict[int, Report] = {}
        self.idempotency_index: Dict[str, str] = {}
        self.settings: Dict[str, Any] = {
            "api_version": "2.0.0",
            "demo_mode": True,
            "database": "in-memory",
            "rbac_enabled": True,
            "audit_logging": True,
            "throughput_target": {
                "claims_per_day": "UNSPECIFIED",
                "peak_claims_per_hour": "UNSPECIFIED",
                "max_payload_size": "UNSPECIFIED",
            },
            "retention": {
                "decision_bundles": "7 years",
                "audit_events": "7 years",
                "claims_and_snapshots": "7 years",
                "remittance_and_reconciliation": "7 years",
            },
            "schema_registry": self._default_schema_registry(),
            "retention_matrix": self._default_retention_matrix(),
        }
        self.counters = {"patient": 1, "provider": 1, "user": 1, "claim": 1, "report": 1, "payment": 1}
        self.icd10_validation_service = ICD10ValidationService(self)
        self.pmb_detection_service = PMBDetectionService(self)
        self.benefit_routing_service = BenefitRoutingService(self)
        self.costing_preview_service = CostingPreviewService(self)
        self.seed()

    def next_numeric(self, key: str) -> int:
        current = self.counters[key]
        self.counters[key] += 1
        return current

    def add_audit_event(
        self,
        actor: str,
        role: str,
        event_type: str,
        entity_type: str,
        entity_id: str,
        detail: Dict[str, Any],
        policy_profile_id: Optional[str] = None,
        policy_version: Optional[int] = None,
        hashes: Optional[Dict[str, str]] = None,
    ) -> AuditEvent:
        event = AuditEvent(
            audit_event_id=new_ref("audit"),
            event_type=event_type,
            actor=actor,
            role=role,
            entity_type=entity_type,
            entity_id=entity_id,
            policy_profile_id=policy_profile_id,
            policy_version=policy_version,
            hashes=hashes or {},
            detail=detail,
            timestamp=utc_now(),
        )
        self.audit_events[event.audit_event_id] = event
        return event

    def _as_of_date(self, value: Optional[str]) -> str:
        return (value or utc_now())[:10]

    def _is_effective_record(
        self,
        *,
        active: bool = True,
        effective_from: Optional[str] = None,
        effective_to: Optional[str] = None,
        status: str = "ACTIVE",
        as_of: Optional[str] = None,
    ) -> bool:
        check_date = self._as_of_date(as_of)
        if not active or status.upper() == "RETIRED":
            return False
        if effective_from and self._as_of_date(effective_from) > check_date:
            return False
        if effective_to and self._as_of_date(effective_to) < check_date:
            return False
        return True

    def _active_icd10_reference(self, code: str, as_of: Optional[str] = None) -> Optional[ICD10Code]:
        item = self.icd10_codes.get(code.strip().upper())
        if not item:
            return None
        if not self._is_effective_record(
            active=item.active,
            effective_from=item.effective_from,
            effective_to=item.effective_to,
            status=item.status,
            as_of=as_of,
        ):
            return None
        return item

    def _resolve_benefit_route_rule(
        self,
        scheme_id: str,
        plan_option_id: str,
        as_of: Optional[str] = None,
    ) -> Optional[BenefitRouteRule]:
        rules = [
            item
            for item in self.benefit_route_rules.values()
            if item.scheme_id == scheme_id
            and item.plan_option_id == plan_option_id
            and self._is_effective_record(
                active=item.active,
                effective_from=item.effective_from,
                effective_to=item.effective_to,
                as_of=as_of,
            )
        ]
        return sorted(rules, key=lambda item: item.effective_from)[-1] if rules else None

    def _resolve_tariff_rate(
        self,
        scheme_id: str,
        plan_option_id: str,
        tariff_code: str,
        dsp_flag: bool,
        as_of: Optional[str] = None,
    ) -> Optional[TariffRate]:
        matches = [
            item
            for item in self.tariff_rates.values()
            if item.scheme_id == scheme_id
            and item.plan_option_id == plan_option_id
            and item.tariff_code.upper() == tariff_code.upper()
            and item.dsp_flag == dsp_flag
            and self._is_effective_record(
                active=item.active,
                effective_from=item.effective_from,
                effective_to=item.effective_to,
                as_of=as_of,
            )
        ]
        return sorted(matches, key=lambda item: item.effective_from)[-1] if matches else None

    def _resolve_pmb_payment_policy(
        self,
        scheme_id: str,
        plan_option_id: str,
        as_of: Optional[str] = None,
    ) -> Optional[PMBPaymentPolicy]:
        matches = [
            item
            for item in self.pmb_payment_policies.values()
            if item.scheme_id == scheme_id
            and item.plan_option_id == plan_option_id
            and self._is_effective_record(
                active=item.active,
                effective_from=item.effective_from,
                effective_to=item.effective_to,
                as_of=as_of,
            )
        ]
        return sorted(matches, key=lambda item: item.effective_from)[-1] if matches else None

    def _claim_provider_is_dsp(self, claim: ClaimRecord) -> bool:
        if claim.provider_is_dsp is not None:
            return claim.provider_is_dsp
        provider = self.providers.get(claim.provider_id)
        return bool(provider.is_dsp_provider) if provider else True

    def _sync_claim_diagnoses_from_claim(
        self,
        claim: ClaimRecord,
        actor: str,
        source: Optional[str] = None,
    ) -> None:
        existing = {
            (item.seq, item.icd10_code.upper()): item
            for item in self.claim_diagnoses.get(claim.id, [])
        }
        records: List[ClaimDiagnosis] = []
        for index, item in enumerate(claim.diagnoses, start=1):
            key = (index, item.icd10.strip().upper())
            previous = existing.get(key)
            records.append(
                ClaimDiagnosis(
                    diagnosis_id=previous.diagnosis_id if previous else new_ref("dx"),
                    claim_id=claim.id,
                    seq=index,
                    icd10_code=item.icd10.strip().upper(),
                    is_primary=item.diagnosis_type == "PRIMARY",
                    source=source or (previous.source if previous else claim.source_system),
                    captured_by=previous.captured_by if previous else actor,
                    captured_at=previous.captured_at if previous else utc_now(),
                )
            )
        self.claim_diagnoses[claim.id] = records

    def _apply_claim_diagnosis_records_to_claim(self, claim: ClaimRecord) -> None:
        records = sorted(
            self.claim_diagnoses.get(claim.id, []),
            key=lambda item: (0 if item.is_primary else 1, item.seq, item.captured_at),
        )
        claim.diagnoses = [
            Diagnosis(
                seq=index,
                icd10=item.icd10_code,
                diagnosis_type="PRIMARY" if index == 1 and item.is_primary else ("PRIMARY" if item.is_primary else "SECONDARY"),
            )
            for index, item in enumerate(records, start=1)
        ]
        for index, record in enumerate(records, start=1):
            record.seq = index

    def get_claim_diagnoses(self, claim_id: int) -> List[ClaimDiagnosis]:
        claim = self.claims[claim_id]
        if claim_id not in self.claim_diagnoses:
            self._sync_claim_diagnoses_from_claim(claim, actor="system", source=claim.source_system)
        return [item.model_copy(deep=True) for item in sorted(self.claim_diagnoses.get(claim_id, []), key=lambda item: item.seq)]

    def _safe_primary_autofix_available(self, claim_id: int) -> bool:
        diagnoses = self.get_claim_diagnoses(claim_id)
        return len(diagnoses) == 1 and not any(item.is_primary for item in diagnoses)

    def register_user(self, username: str, password: str, role: str, email: str) -> User:
        user = User(
            id=self.next_numeric("user"),
            username=username,
            email=email,
            role=role,
            created_at=utc_now(),
        )
        self.users[user.id] = user
        self.auth_users[username] = {"password": password, "role": role, "user_id": user.id, "email": email}
        return user

    def _default_schema_registry(self) -> Dict[str, Any]:
        return {
            "fields": [
                {
                    "category": "membership",
                    "field": "member_number",
                    "draft": True,
                    "snapshot": True,
                    "canonical_claim": True,
                    "payload": True,
                    "required_stages": ["READINESS", "SUBMISSION_CHECKS"],
                    "integrations": ["UserEntry", "PMS", "EligibilityAPI"],
                },
                {
                    "category": "diagnosis",
                    "field": "diagnoses.primary.icd10",
                    "draft": True,
                    "snapshot": True,
                    "canonical_claim": True,
                    "payload": True,
                    "required_stages": ["READINESS", "CLOSURE_GATE"],
                    "integrations": ["PMS", "EMR", "UserEntry"],
                },
                {
                    "category": "pmb",
                    "field": "pmb_mapping_rules[].icd10_code",
                    "draft": False,
                    "snapshot": False,
                    "canonical_claim": True,
                    "payload": True,
                    "required_stages": ["READINESS", "CLOSURE_GATE", "POST_CLOSURE_VALIDATION"],
                    "integrations": ["BusinessOwnedReferenceData"],
                },
                {
                    "category": "benefit_routing",
                    "field": "benefit_route_decision.route",
                    "draft": False,
                    "snapshot": True,
                    "canonical_claim": True,
                    "payload": True,
                    "required_stages": ["CLOSURE_GATE", "SUBMISSION_CHECKS"],
                    "integrations": ["RulesEngine", "SchemeConfiguration"],
                },
                {
                    "category": "authorisation",
                    "field": "authorisations.auth_number",
                    "draft": True,
                    "snapshot": True,
                    "canonical_claim": True,
                    "payload": True,
                    "required_stages": ["READINESS", "CLOSURE_GATE"],
                    "integrations": ["SchemeAPI", "UserEntry"],
                },
                {
                    "category": "billing",
                    "field": "line_items[].claimed_amount",
                    "draft": True,
                    "snapshot": True,
                    "canonical_claim": True,
                    "payload": True,
                    "required_stages": ["POST_CLOSURE_VALIDATION", "ADJUDICATION_RULES"],
                    "integrations": ["PMS", "HIS", "UserEntry"],
                },
            ]
        }

    def _default_retention_matrix(self) -> List[Dict[str, str]]:
        return [
            {
                "artifact": "decision_bundles",
                "storage_type": "application_store",
                "retention": "7 years",
                "purge_behavior": "configurable anonymise or purge",
                "audit_exceptions": "retention changes are audited",
            },
            {
                "artifact": "audit_events",
                "storage_type": "append_only_store",
                "retention": "7 years",
                "purge_behavior": "retained unless legal override",
                "audit_exceptions": "none",
            },
            {
                "artifact": "claim_snapshots",
                "storage_type": "application_store",
                "retention": "7 years",
                "purge_behavior": "anonymise where contract allows",
                "audit_exceptions": "snapshot hash retained",
            },
            {
                "artifact": "remittance_reconciliation",
                "storage_type": "application_store",
                "retention": "7 years",
                "purge_behavior": "configurable anonymise or purge",
                "audit_exceptions": "financial references retained",
            },
            {
                "artifact": "pmb_mapping_and_benefit_route_decisions",
                "storage_type": "configuration_and_application_store",
                "retention": "7 years",
                "purge_behavior": "retain decision evidence; retire mapping versions rather than deleting",
                "audit_exceptions": "mapping activation and manual overrides are audited",
            },
        ]

    def _record_claim_version(self, claim: ClaimRecord, change_summary: str) -> None:
        version = ClaimVersion(
            claim_id=claim.id,
            version=claim.version,
            snapshot_id=claim.latest_snapshot_id,
            status=claim.status,
            previous_version=claim.previous_version,
            change_summary=change_summary,
            created_at=utc_now(),
        )
        versions = [item for item in self.claim_versions.get(claim.id, []) if item.version != claim.version]
        versions.append(version)
        versions.sort(key=lambda item: item.version)
        self.claim_versions[claim.id] = versions
        self.claim_history[f"{claim.id}:{claim.version}"] = self._claim_payload(claim)

    def seed(self) -> None:
        self.reference_versions["icd10_mit"] = ReferenceVersion(
            reference_key="icd10_mit",
            version="MIT-2026-01",
            effective_from="2026-01-01",
        )
        self.reference_versions["pmb"] = ReferenceVersion(
            reference_key="pmb",
            version="PMB-2026-01",
            effective_from="2026-01-01",
        )
        self.reference_versions["nappi"] = ReferenceVersion(
            reference_key="nappi",
            version="NAPPI-2026-01",
            effective_from="2026-01-01",
        )
        self.reference_versions["tariff"] = ReferenceVersion(
            reference_key="tariff",
            version="TARIFF-2026-04",
            effective_from="2026-04-01",
        )
        self.reference_versions["provider_registry"] = ReferenceVersion(
            reference_key="provider_registry",
            version="PCNS-2026-04",
            effective_from="2026-04-01",
        )
        self._seed_coding_and_pmb_reference()

        self.register_user("admin", "admin123", "Administrator", "admin@example.com")
        self.register_user("demo.user", "password123", "Billing Specialist", "demo.user@example.com")
        self.register_user("billing", "billing123", "Billing Specialist", "billing@example.com")
        self.register_user("provider", "provider123", "Healthcare Provider", "provider@example.com")
        self.register_user("finance", "finance123", "Finance Officer", "finance@example.com")
        self.register_user("auditor", "auditor123", "Compliance Auditor", "auditor@example.com")

        patient_names = [
            "Anele Nkosi",
            "Mpho Dlamini",
            "Naledi Mokoena",
            "Kamo Maseko",
            "Buhle Khumalo",
            "Lerato Mthembu",
            "Siyabonga Zulu",
            "Palesa Motaung",
            "Tumi Radebe",
            "Nandi Sibiya",
        ]
        for index, name in enumerate(patient_names, start=1):
            patient = Patient(
                id=self.next_numeric("patient"),
                name=name,
                mrn=f"MRN{1200 + index}",
                dob=f"198{index % 10}-0{(index % 9) + 1}-1{index % 8}",
                sex="F" if index % 2 else "M",
                email=f"patient{index}@example.com",
                phone=f"+27-82-555-01{index:02d}",
                created_at=utc_now(),
            )
            self.patients[patient.id] = patient

        provider_rows = [
            ("Cardiology Provider 1", "Cardiology", "SPECIALIST", True),
            ("General Practice Provider 2", "General Practice", "GP", False),
            ("Orthopaedics Provider 3", "Orthopaedics", "SPECIALIST", True),
            ("Hospitalist Provider 4", "Hospital", "SPECIALIST", True),
            ("Pathology Provider 5", "Pathology", "SPECIALIST", False),
            ("Dental Surgery Provider 6", "Dental Surgery", "SPECIALIST", True),
        ]
        for index, (name, specialty, discipline, is_dsp_provider) in enumerate(provider_rows, start=1):
            provider = Provider(
                id=self.next_numeric("provider"),
                name=name,
                npi=f"NPI{9000 + index}",
                practice_number=f"01234{index:02d}",
                specialty=specialty,
                discipline=discipline,
                is_dsp_provider=is_dsp_provider,
                email=f"provider{index}@example.com",
                phone=f"+27-11-700-0{index:02d}",
                created_at=utc_now(),
            )
            self.providers[provider.id] = provider

        self._seed_rules()
        self._seed_policy_profiles()
        self.settings.update(
            {
                "scheme": "SCHEME_A",
                "option": "OPTION_X",
                "policy_profile_id": "SCHEME_A:OPTION_X",
                "policy_version": 2,
            }
        )
        self._seed_claims()
        self.generate_report("summary", "Seeded UAT")

    def _seed_coding_and_pmb_reference(self) -> None:
        mit_version = self.reference_versions["icd10_mit"].version
        for code, description in {
            "I10": "Configured ICD-10 development reference",
            "S72.0": "Configured ICD-10 development reference",
            "M54.5": "Configured ICD-10 development reference",
            "J11.1": "Configured ICD-10 development reference",
            "K02.1": "Configured ICD-10 development reference",
            "C50.9": "Configured ICD-10 development reference",
            "I11.0": "Configured ICD-10 development reference",
            "E11.9": "Configured ICD-10 development reference",
            "H52.4": "Configured ICD-10 development reference",
            "Z00.0": "Configured ICD-10 development reference",
        }.items():
            self.icd10_codes[code] = ICD10Code(
                code=code,
                description=description,
                version=mit_version,
                effective_from="2026-01-01",
                source="development_placeholder_business_owned_required",
            )

        self.pmb_conditions["PMB-CONFIG-001"] = PMBCondition(
            condition_id="PMB-CONFIG-001",
            name="Business-owned PMB placeholder hypertension condition",
            type="CDL",
            descriptor="Development placeholder PMB descriptor evidence required",
            category="UNSPECIFIED_REFERENCE_DATA",
            metadata={
                "note": "Development seed only. Replace with CMS/scheme-owned PMB condition metadata.",
            },
            evidence_requirements=["MOTIVATION"],
            confirmation_flags=["descriptor_motivation_present"],
        )
        self.pmb_conditions["PMB-CONFIG-002"] = PMBCondition(
            condition_id="PMB-CONFIG-002",
            name="Business-owned PMB placeholder condition B",
            type="DTP",
            descriptor="Development placeholder oncology evidence descriptor",
            category="UNSPECIFIED_REFERENCE_DATA",
            metadata={
                "note": "Development seed only. Replace with CMS/scheme-owned PMB condition metadata.",
            },
            evidence_requirements=["MOTIVATION"],
            confirmation_flags=["descriptor_motivation_present"],
        )
        for mapping in [
            PMBMappingRule(
                mapping_id="PMB-MAP-DEV-I10",
                icd10_code="I10",
                pmb_condition_id="PMB-CONFIG-001",
                match_type="EXACT",
                version=1,
                effective_from="2026-01-01",
                confidence="HIGH",
                auto_route_allowed=False,
                source="development_placeholder_business_owned_required",
                required_evidence_types=["MOTIVATION"],
            ),
            PMBMappingRule(
                mapping_id="PMB-MAP-DEV-C509",
                icd10_code="C50.9",
                pmb_condition_id="PMB-CONFIG-002",
                match_type="EXACT",
                version=1,
                effective_from="2026-01-01",
                confidence="MEDIUM",
                auto_route_allowed=False,
                required_evidence_types=["MOTIVATION"],
                source="development_placeholder_business_owned_required",
            ),
        ]:
            self.pmb_mapping_rules[mapping.mapping_id] = mapping

        self.benefit_route_rules["BRR-SCHEME_A-OPTION_X"] = BenefitRouteRule(
            rule_id="BRR-SCHEME_A-OPTION_X",
            scheme_id="SCHEME_A",
            plan_option_id="OPTION_X",
            route_when_confirmed="PMB_BENEFIT_BUCKET",
            route_when_possible="PMB_REVIEW_QUEUE",
            route_when_missing_evidence="PMB_REVIEW_QUEUE",
            auto_route_possible_matches=False,
            effective_from="2026-01-01",
        )
        for rate in [
            TariffRate(
                rate_id="TAR-DEMO-DSP-CONS001",
                scheme_id="SCHEME_A",
                plan_option_id="OPTION_X",
                tariff_code="CONS001",
                dsp_flag=True,
                rate_amount=900,
                unit="PER_SERVICE",
                effective_from="2026-01-01",
            ),
            TariffRate(
                rate_id="TAR-DEMO-SCHEME-CONS001",
                scheme_id="SCHEME_A",
                plan_option_id="OPTION_X",
                tariff_code="CONS001",
                dsp_flag=False,
                rate_amount=600,
                unit="PER_SERVICE",
                effective_from="2026-01-01",
            ),
        ]:
            self.tariff_rates[rate.rate_id] = rate

        self.pmb_payment_policies["PMP-SCHEME_A-OPTION_X"] = PMBPaymentPolicy(
            policy_id="PMP-SCHEME_A-OPTION_X",
            scheme_id="SCHEME_A",
            plan_option_id="OPTION_X",
            pay_in_full_requires_dsp=True,
            voluntary_non_dsp_rate_mode="DSP_RATE",
            involuntary_non_dsp_no_copay=True,
            effective_from="2026-01-01",
        )

    def _seed_rules(self) -> None:
        self.rule_definitions["ICD_PRIMARY_REQUIRED"] = RuleDefinition(
            rule_id="ICD_PRIMARY_REQUIRED",
            name="Primary ICD-10 required",
            category="ICD10_VALIDATION",
            severity="BLOCK",
            reason_code="ICD_MISSING_PRIMARY",
            message="Primary ICD-10 is required before closure.",
            remediation_hint="Capture a valid primary ICD-10 from the MIT and link it to the claim.",
            affected_fields=["diagnoses"],
            stage_scope=["READINESS", "CLOSURE_GATE", "POST_CLOSURE_VALIDATION"],
            decision_table={"rows": [{"when": [{"path": "facts.primary_icd_missing", "op": "eq", "value": True}]}]},
        )
        self.rule_definitions["ICD_FORMAT_INVALID"] = RuleDefinition(
            rule_id="ICD_FORMAT_INVALID",
            name="ICD-10 code invalid or not in configured MIT",
            category="ICD10_VALIDATION",
            severity="BLOCK",
            reason_code="ICD_INVALID",
            message="One or more ICD-10 codes are invalid or unavailable in the configured MIT reference.",
            remediation_hint="Select a valid ICD-10 from the configured MIT version before continuing.",
            affected_fields=["diagnoses"],
            stage_scope=["READINESS", "CLOSURE_GATE", "POST_CLOSURE_VALIDATION"],
            decision_table={
                "rows": [{"when": [{"path": "facts.invalid_icd_count", "op": "gt", "value": 0}]}]
            },
        )
        self.rule_definitions["INPATIENT_DISCHARGE_REQUIRED"] = RuleDefinition(
            rule_id="INPATIENT_DISCHARGE_REQUIRED",
            name="Inpatient discharge required before closure",
            category="TECHNICAL",
            severity="BLOCK",
            reason_code="DISCHARGE_MISSING",
            message="Inpatient claims need a discharge date before closure.",
            remediation_hint="Capture discharge date and time from the HIS before closing the file.",
            affected_fields=["discharge_date_time"],
            stage_scope=["READINESS", "CLOSURE_GATE"],
            decision_table={
                "rows": [
                    {
                        "when": [
                            {"path": "facts.is_inpatient", "op": "eq", "value": True},
                            {"path": "facts.discharge_missing", "op": "eq", "value": True},
                        ]
                    }
                ]
            },
        )
        self.rule_definitions["PREAUTH_REQUIRED"] = RuleDefinition(
            rule_id="PREAUTH_REQUIRED",
            name="Required preauthorisation missing",
            category="PREAUTH",
            severity="BLOCK",
            reason_code="PREAUTH_MISSING",
            message="A preauthorisation is required for one or more billed services.",
            remediation_hint="Capture a valid preauthorisation covering the service date.",
            affected_fields=["authorisations"],
            stage_scope=["READINESS", "CLOSURE_GATE"],
            decision_table={"rows": [{"when": [{"path": "facts.missing_preauth_count", "op": "gt", "value": 0}]}]},
        )
        self.rule_definitions["ATTACHMENT_RECOMMENDED"] = RuleDefinition(
            rule_id="ATTACHMENT_RECOMMENDED",
            name="Supporting attachment recommended",
            category="TECHNICAL",
            severity="WARN",
            reason_code="ATTACHMENT_REQUIRED",
            message="An attachment or motivation is expected for this claim.",
            remediation_hint="Upload a motivation or report before submission to avoid a pend.",
            affected_fields=["attachments"],
            stage_scope=["READINESS", "CLOSURE_GATE"],
            decision_table={
                "rows": [{"when": [{"path": "facts.missing_attachment_count", "op": "gt", "value": 0}]}]
            },
        )
        self.rule_definitions["PMB_EVIDENCE_REQUIRED"] = RuleDefinition(
            rule_id="PMB_EVIDENCE_REQUIRED",
            name="PMB evidence required before automatic routing",
            category="PMB",
            severity="WARN",
            reason_code="PMB_EVIDENCE_REQUIRED",
            message="A configured ICD-10 to PMB mapping was detected, but supporting PMB evidence is missing.",
            remediation_hint="Upload the configured evidence or route the claim to PMB review before submission.",
            affected_fields=["attachments", "diagnoses"],
            stage_scope=["READINESS", "CLOSURE_GATE", "POST_CLOSURE_VALIDATION"],
            decision_table={
                "rows": [{"when": [{"path": "facts.missing_pmb_evidence_count", "op": "gt", "value": 0}]}]
            },
        )
        self.rule_definitions["MODIFIER_SEQUENCE_INVALID"] = RuleDefinition(
            rule_id="MODIFIER_SEQUENCE_INVALID",
            name="Modifier sequence invalid",
            category="MODIFIERS",
            severity="BLOCK",
            reason_code="MODIFIER_SEQUENCE_INVALID",
            message="Modifier sequencing is invalid for one or more claim lines.",
            remediation_hint="Ensure modifiers follow a valid base tariff line in the configured sequence.",
            affected_fields=["line_items"],
            stage_scope=["POST_CLOSURE_VALIDATION"],
            decision_table={
                "rows": [{"when": [{"path": "facts.modifier_sequence_invalid", "op": "eq", "value": True}]}]
            },
        )
        self.rule_definitions["AMOUNT_MISMATCH"] = RuleDefinition(
            rule_id="AMOUNT_MISMATCH",
            name="Claimed amount mismatch",
            category="TECHNICAL",
            severity="BLOCK",
            reason_code="AMOUNT_MISMATCH",
            message="Claimed amount does not match quantity multiplied by unit price.",
            remediation_hint="Correct the billed amount or adjust quantity and unit price.",
            affected_fields=["line_items"],
            stage_scope=["POST_CLOSURE_VALIDATION"],
            decision_table={
                "rows": [{"when": [{"path": "facts.amount_mismatch_count", "op": "gt", "value": 0}]}]
            },
        )
        self.rule_definitions["DIAGNOSIS_LINKAGE_WARNING"] = RuleDefinition(
            rule_id="DIAGNOSIS_LINKAGE_WARNING",
            name="Diagnosis linkage incomplete",
            category="ICD10_VALIDATION",
            severity="WARN",
            reason_code="DIAGNOSIS_LINK_MISSING",
            message="One or more claim lines are missing diagnosis references.",
            remediation_hint="Link each billed line to the applicable diagnosis sequence.",
            affected_fields=["line_items"],
            stage_scope=["POST_CLOSURE_VALIDATION"],
            decision_table={
                "rows": [
                    {"when": [{"path": "facts.diagnosis_link_missing_count", "op": "gt", "value": 0}]}
                ]
            },
        )

    def _seed_policy_profiles(self) -> None:
        rule_ids = list(self.rule_definitions.keys())
        self.policy_profiles["SCHEME_A:OPTION_X"] = [
            PolicyProfile(
                policy_profile_id="SCHEME_A:OPTION_X",
                scheme_id="SCHEME_A",
                plan_option_id="OPTION_X",
                version=1,
                effective_from="2026-01-01",
                status="APPROVED",
                approved_by="admin",
                approved_at=utc_now(),
                runtime_toggles={
                    "icdEnforcementMode": "WARN",
                    "requirePreauthForCodes": ["PROC_PREAUTH"],
                    "allowClosureWithWarnings": True,
                    "requireSupervisorOverrideOnWarnings": False,
                    "defaultSubmissionChannel": "DIRECT",
                    "memberNumberRegex": r"^MEM\d{6}$",
                    "autoFlagPMBFromICD10": True,
                    "autoRoutePMBWhenMappingAllows": True,
                    "pmbEvidenceMode": "WARN",
                },
                rule_ids=rule_ids,
            ),
            PolicyProfile(
                policy_profile_id="SCHEME_A:OPTION_X",
                scheme_id="SCHEME_A",
                plan_option_id="OPTION_X",
                version=2,
                effective_from="2026-04-01",
                status="ACTIVE",
                approved_by="admin",
                approved_at=utc_now(),
                runtime_toggles={
                    "icdEnforcementMode": "BLOCK",
                    "requirePreauthForCodes": ["PROC_PREAUTH", "THEATRE001"],
                    "allowClosureWithWarnings": True,
                    "requireSupervisorOverrideOnWarnings": True,
                    "defaultSubmissionChannel": "SWITCH",
                    "memberNumberRegex": r"^MEM\d{6}$",
                    "reasonCodeMappings": {"ICD_MISSING": "Primary diagnosis missing"},
                    "autoFlagPMBFromICD10": True,
                    "autoRoutePMBWhenMappingAllows": True,
                    "pmbEvidenceMode": "WARN",
                },
                rule_ids=rule_ids,
            ),
        ]

    def _seed_claims(self) -> None:
        service_date = (datetime.now(UTC) - timedelta(days=5)).date().isoformat()
        scenarios = [
            {
                "scenario_key": "clean_success",
                "claim_number": "CLM-1001",
                "claim_reference": "REF-1001",
                "invoice_number": "INV-1001",
                "member_number": "MEM100001",
                "patient_id": 1,
                "provider_id": 1,
                "provider_is_dsp": True,
                "non_dsp_access_type": "NOT_APPLICABLE",
                "service_date": service_date,
                "diagnoses": [{"seq": 1, "icd10": "I10", "diagnosis_type": "PRIMARY"}],
                "attachments": [
                    {
                        "attachment_type": "MOTIVATION",
                        "file_name": "demo-pmb-motivation.pdf",
                        "storage_ref": "seed/demo-pmb-motivation.pdf",
                        "file_hash": stable_hash("demo-pmb-motivation"),
                        "uploaded_by": "system",
                    }
                ],
                "line_items": [{"line_id": "1", "service_code": "CONS001", "service_description": "Consultation", "quantity": 1, "unit_price": 900, "claimed_amount": 900, "diagnosis_refs": [1]}],
                "actions": ["readiness", "close", "validate", "payload", "submit:direct:seed-clean-success"],
            },
            {
                "scenario_key": "missing_icd_blocks_closure",
                "claim_number": "CLM-1002",
                "claim_reference": "REF-1002",
                "invoice_number": "INV-1002",
                "member_number": "MEM100002",
                "patient_id": 2,
                "provider_id": 2,
                "provider_is_dsp": False,
                "non_dsp_access_type": "VOLUNTARY",
                "service_date": service_date,
                "diagnoses": [],
                "line_items": [{"line_id": "1", "service_code": "CONS001", "service_description": "Consultation", "quantity": 1, "unit_price": 450, "claimed_amount": 450}],
                "actions": ["readiness"],
            },
            {
                "scenario_key": "missing_discharge_blocks_inpatient",
                "claim_number": "CLM-1003",
                "claim_reference": "REF-1003",
                "invoice_number": "INV-1003",
                "member_number": "MEM100003",
                "patient_id": 3,
                "provider_id": 4,
                "care_setting": "INPATIENT",
                "service_date": service_date,
                "admission_date_time": f"{service_date}T08:00:00",
                "diagnoses": [{"seq": 1, "icd10": "S72.0", "diagnosis_type": "PRIMARY"}],
                "line_items": [{"line_id": "1", "service_code": "WARD001", "service_description": "Ward stay", "quantity": 2, "unit_price": 1200, "claimed_amount": 2400, "diagnosis_refs": [1]}],
                "actions": ["readiness"],
            },
            {
                "scenario_key": "missing_authorisation_toggle",
                "claim_number": "CLM-1004",
                "claim_reference": "REF-1004",
                "invoice_number": "INV-1004",
                "member_number": "MEM100004",
                "patient_id": 4,
                "provider_id": 3,
                "service_date": service_date,
                "diagnoses": [{"seq": 1, "icd10": "M54.5", "diagnosis_type": "PRIMARY"}],
                "line_items": [{"line_id": "1", "service_code": "PROC_PREAUTH", "service_description": "Authorised procedure", "quantity": 1, "unit_price": 3200, "claimed_amount": 3200, "diagnosis_refs": [1], "requires_preauth": True}],
                "actions": ["readiness"],
            },
            {
                "scenario_key": "invalid_membership_format_rejects_submission",
                "claim_number": "CLM-1005",
                "claim_reference": "REF-1005",
                "invoice_number": "INV-1005",
                "member_number": "ABC123",
                "patient_id": 5,
                "provider_id": 2,
                "service_date": service_date,
                "diagnoses": [{"seq": 1, "icd10": "J11.1", "diagnosis_type": "PRIMARY"}],
                "line_items": [{"line_id": "1", "service_code": "CONS001", "service_description": "Consultation", "quantity": 1, "unit_price": 700, "claimed_amount": 700, "diagnosis_refs": [1]}],
                "actions": ["readiness", "close", "validate", "payload", "submit:direct:seed-invalid-member"],
            },
            {
                "scenario_key": "modifier_sequence_error_rejects",
                "claim_number": "CLM-1006",
                "claim_reference": "REF-1006",
                "invoice_number": "INV-1006",
                "member_number": "MEM100006",
                "patient_id": 6,
                "provider_id": 2,
                "service_date": service_date,
                "diagnoses": [{"seq": 1, "icd10": "K02.1", "diagnosis_type": "PRIMARY"}],
                "line_items": [{"line_id": "1", "service_code": "ORPHANMOD", "service_description": "Modifier without base line", "quantity": 1, "unit_price": 250, "claimed_amount": 250, "modifiers": ["M1"], "diagnosis_refs": [1]}],
                "actions": ["readiness", "close", "validate"],
            },
            {
                "scenario_key": "pending_attachment_motivation",
                "claim_number": "CLM-1007",
                "claim_reference": "REF-1007",
                "invoice_number": "INV-1007",
                "member_number": "MEM100007",
                "patient_id": 7,
                "provider_id": 5,
                "service_date": service_date,
                "diagnoses": [{"seq": 1, "icd10": "C50.9", "diagnosis_type": "PRIMARY"}],
                "line_items": [{"line_id": "1", "service_code": "ONC001", "service_description": "Oncology review", "quantity": 1, "unit_price": 1800, "claimed_amount": 1800, "diagnosis_refs": [1], "requires_attachment": True}],
                "actions": ["readiness", "close", "validate", "payload", "submit:switch:seed-pend-attachment"],
            },
            {
                "scenario_key": "partial_payment_remittance",
                "claim_number": "CLM-1008",
                "claim_reference": "REF-1008",
                "invoice_number": "INV-1008",
                "member_number": "MEM100008",
                "patient_id": 8,
                "provider_id": 1,
                "service_date": service_date,
                "diagnoses": [{"seq": 1, "icd10": "I11.0", "diagnosis_type": "PRIMARY"}],
                "line_items": [{"line_id": "1", "service_code": "CARD001", "service_description": "Cardiology review", "quantity": 1, "unit_price": 1100, "claimed_amount": 1100, "diagnosis_refs": [1]}],
                "actions": ["readiness", "close", "validate", "payload", "submit:direct:seed-partial-payment"],
            },
            {
                "scenario_key": "reconciliation_mismatch_exception",
                "claim_number": "CLM-1009",
                "claim_reference": "REF-1009",
                "invoice_number": "INV-1009",
                "member_number": "MEM100009",
                "patient_id": 9,
                "provider_id": 1,
                "service_date": service_date,
                "diagnoses": [{"seq": 1, "icd10": "E11.9", "diagnosis_type": "PRIMARY"}],
                "line_items": [{"line_id": "1", "service_code": "ENDO001", "service_description": "Endocrine review", "quantity": 1, "unit_price": 980, "claimed_amount": 980, "diagnosis_refs": [1]}],
                "actions": ["readiness", "close", "validate", "payload", "submit:switch:seed-recon-mismatch"],
            },
            {
                "scenario_key": "rejected_v1_corrected_to_v2_paid",
                "claim_number": "CLM-1010",
                "claim_reference": "REF-1010",
                "invoice_number": "INV-1010",
                "member_number": "BAD-010",
                "patient_id": 10,
                "provider_id": 2,
                "service_date": service_date,
                "diagnoses": [{"seq": 1, "icd10": "H52.4", "diagnosis_type": "PRIMARY"}],
                "line_items": [{"line_id": "1", "service_code": "OPT001", "service_description": "Optometry consult", "quantity": 1, "unit_price": 560, "claimed_amount": 560, "diagnosis_refs": [1]}],
                "actions": ["readiness", "close", "validate", "payload", "submit:direct:seed-v1-rejected"],
            },
        ]

        for payload in scenarios:
            actions = payload.pop("actions")
            claim = self.create_claim(payload, actor="system", role="system")
            for action in actions:
                if action == "readiness":
                    self.run_readiness(claim.id, "system", "system")
                elif action == "close":
                    self.close_claim(claim.id, ClaimClosureRequest(supervisor_override=True), "system", "system")
                elif action == "validate":
                    self.run_post_closure_validation(claim.id, "system", "system")
                elif action == "payload":
                    self.build_payload(claim.id, "system", "system")
                elif action.startswith("submit:"):
                    _, channel, idem = action.split(":")
                    self.submit_claim(
                        claim.id,
                        ClaimSubmissionRequest(channel=channel, idempotency_key=idem),
                        "system",
                        "system",
                    )

        corrected = self.claims[10]
        self.update_claim(
            corrected.id,
            {
                "member_number": "MEM100010",
                "scenario_key": "corrected_v2_paid",
                "claim_number": "CLM-1010-V2",
                "invoice_number": "INV-1010-V2",
            },
            actor="system",
            role="system",
            change_summary="Corrected member number after submission rejection.",
        )
        self.run_readiness(corrected.id, "system", "system")
        self.close_claim(corrected.id, ClaimClosureRequest(supervisor_override=True), "system", "system")
        self.run_post_closure_validation(corrected.id, "system", "system")
        self.build_payload(corrected.id, "system", "system")
        self.submit_claim(
            corrected.id,
            ClaimSubmissionRequest(channel="DIRECT", idempotency_key="seed-v2-corrected"),
            "system",
            "system",
        )

    def _normalize_line_item(self, data: Dict[str, Any], index: int, service_date: str) -> ClaimLineItem:
        quantity = float(data.get("quantity", 1) or 1)
        unit_price = float(data.get("unit_price", data.get("claimed_amount", 0)) or 0)
        claimed_amount = float(data.get("claimed_amount", quantity * unit_price) or 0)
        return ClaimLineItem(
            line_id=str(data.get("line_id") or index),
            service_code=str(data.get("service_code") or "CONS001"),
            service_description=str(data.get("service_description") or "Consultation"),
            quantity=quantity,
            unit_price=unit_price,
            claimed_amount=claimed_amount,
            service_date=data.get("service_date") or service_date,
            diagnosis_refs=list(data.get("diagnosis_refs") or []),
            modifiers=list(data.get("modifiers") or []),
            nappi_code=data.get("nappi_code"),
            device_id=data.get("device_id"),
            rendering_provider_practice_number=data.get("rendering_provider_practice_number"),
            requires_preauth=to_bool(data.get("requires_preauth", False)),
            requires_attachment=to_bool(data.get("requires_attachment", False)),
        )

    def _normalize_claim(self, data: Dict[str, Any]) -> ClaimRecord:
        service_date = data.get("service_date") or datetime.now(UTC).date().isoformat()
        claim_id = self.next_numeric("claim")
        line_source = (
            data["line_items"]
            if "line_items" in data
            else [
                {
                    "line_id": "1",
                    "service_code": data.get("service_code", "CONS001"),
                    "service_description": data.get("service_description", "Consultation"),
                    "quantity": 1,
                    "unit_price": float(data.get("amount", 0) or 0),
                    "claimed_amount": float(data.get("amount", 0) or 0),
                }
            ]
        )
        line_items = [
            self._normalize_line_item(item, index, service_date)
            for index, item in enumerate(
                line_source,
                start=1,
            )
        ]
        diagnosis_source = data["diagnoses"] if "diagnoses" in data else [{"seq": 1, "icd10": "I10"}]
        diagnoses = [Diagnosis(**item) for item in diagnosis_source]
        authorisations = [AuthorizationRecord(**item) for item in (data.get("authorisations") or [])]
        attachments = [
            AttachmentRecord(
                attachment_id=item.get("attachment_id") or new_ref("att"),
                attachment_type=item.get("attachment_type", "OTHER"),
                file_name=item.get("file_name", "attachment.dat"),
                storage_ref=item.get("storage_ref", item.get("file_name", "attachment.dat")),
                file_hash=item.get("file_hash", stable_hash(item)),
                uploaded_at=item.get("uploaded_at", utc_now()),
                uploaded_by=item.get("uploaded_by", data.get("created_by", "seed")),
                virus_scan_status=item.get("virus_scan_status", "CLEAN"),
            )
            for item in (data.get("attachments") or [])
        ]
        now = utc_now()
        return ClaimRecord(
            id=claim_id,
            version=int(data.get("version", 1)),
            previous_version=data.get("previous_version"),
            scenario_key=str(data.get("scenario_key") or "clean_success"),
            status=str(data.get("status") or "draft"),
            claim_number=str(data.get("claim_number") or f"CLM-{1000 + claim_id}"),
            claim_reference=str(data.get("claim_reference") or f"REF-{claim_id:04d}"),
            batch_reference=data.get("batch_reference"),
            invoice_number=str(data.get("invoice_number") or f"INV-{claim_id:04d}"),
            scheme_id=str(data.get("scheme_id") or data.get("scheme") or "SCHEME_A"),
            plan_option_id=str(data.get("plan_option_id") or data.get("option") or "OPTION_X"),
            member_number=str(data.get("member_number") or f"MEM{100000 + claim_id}"),
            dependant_code=str(data.get("dependant_code") or "01"),
            membership_status=str(data.get("membership_status") or "ACTIVE"),
            patient_id=int(data["patient_id"]),
            provider_id=int(data["provider_id"]),
            care_setting=str(data.get("care_setting") or "OUTPATIENT"),
            service_date=service_date,
            admission_date_time=data.get("admission_date_time"),
            discharge_date_time=data.get("discharge_date_time"),
            diagnoses=diagnoses,
            line_items=line_items,
            authorisations=authorisations,
            attachments=attachments,
            clinical_summary=data.get("clinical_summary"),
            source_system=str(data.get("source_system") or "UserEntry"),
            provider_pmb_indicator=data.get("provider_pmb_indicator"),
            provider_is_dsp=data.get("provider_is_dsp"),
            non_dsp_access_type=str(data.get("non_dsp_access_type") or "NOT_APPLICABLE").upper(),
            created_at=now,
            updated_at=now,
        )

    def _claim_amount(self, claim: ClaimRecord) -> float:
        return round(sum(item.claimed_amount for item in claim.line_items), 2)

    def _claim_payload(self, claim: ClaimRecord) -> Dict[str, Any]:
        payload = claim.model_dump()
        payload["amount"] = self._claim_amount(claim)
        payload["scheme"] = claim.scheme_id
        payload["option"] = claim.plan_option_id
        return payload

    def _claim_decision_input(self, claim: ClaimRecord) -> Dict[str, Any]:
        payload = self._claim_payload(claim)
        for key in [
            "status",
            "readiness_status",
            "validation_status",
            "payload_status",
            "submission_status",
            "pmb_status",
            "remittance_status",
            "reconciliation_status",
            "latest_snapshot_id",
            "latest_payload_id",
            "latest_submission_id",
            "latest_response_id",
            "latest_financial_bundle_id",
            "latest_remittance_id",
            "latest_reconciliation_id",
            "latest_pmb_decision_id",
            "latest_benefit_route_decision_id",
            "latest_costing_preview_id",
            "created_at",
            "updated_at",
        ]:
            payload.pop(key, None)
        return payload

    def _resolve_policy(self, scheme_id: str, plan_option_id: str) -> PolicyProfile:
        versions = self.policy_profiles.get(f"{scheme_id}:{plan_option_id}") or []
        active = [item for item in versions if item.status == "ACTIVE"]
        if active:
            return sorted(active, key=lambda item: item.version)[-1]
        if versions:
            return sorted(versions, key=lambda item: item.version)[-1]
        raise KeyError(f"No policy profile configured for {scheme_id}:{plan_option_id}")

    def _reference_version_map(self) -> Dict[str, str]:
        return {key: value.version for key, value in self.reference_versions.items()}

    def _resolve_path(self, payload: Dict[str, Any], path: str) -> Any:
        current: Any = payload
        for segment in path.split("."):
            if isinstance(current, list):
                try:
                    current = current[int(segment)]
                except (ValueError, IndexError):
                    return None
                continue
            if not isinstance(current, dict):
                return None
            current = current.get(segment)
        return current

    def _match_condition(self, actual: Any, op: str, expected: Any) -> bool:
        if op == "eq":
            return actual == expected
        if op == "ne":
            return actual != expected
        if op == "gt":
            return (actual or 0) > expected
        if op == "gte":
            return (actual or 0) >= expected
        if op == "lt":
            return (actual or 0) < expected
        if op == "lte":
            return (actual or 0) <= expected
        if op == "empty":
            return actual in {None, "", [], {}}
        if op == "not_empty":
            return actual not in {None, "", [], {}}
        if op == "in":
            return actual in (expected or [])
        if op == "not_in":
            return actual not in (expected or [])
        if op == "regex":
            return bool(re.match(str(expected), str(actual or "")))
        return False

    def _override_severity(self, rule: RuleDefinition, policy: PolicyProfile) -> Severity:
        if rule.rule_id == "ICD_PRIMARY_REQUIRED":
            mode = str(policy.runtime_toggles.get("icdEnforcementMode", rule.severity)).upper()
            if mode in {"WARN", "BLOCK"}:
                return mode  # type: ignore[return-value]
        if rule.rule_id == "PMB_EVIDENCE_REQUIRED":
            mode = str(policy.runtime_toggles.get("pmbEvidenceMode", rule.severity)).upper()
            if mode in {"INFO", "WARN", "BLOCK"}:
                return mode  # type: ignore[return-value]
        return rule.severity

    def _icd10_codes_for_claim(self, claim: ClaimRecord) -> List[str]:
        codes = []
        diagnoses = self.get_claim_diagnoses(claim.id) if claim.id in self.claims else []
        if not diagnoses:
            diagnoses = [
                ClaimDiagnosis(
                    diagnosis_id=f"tmp-{item.seq}",
                    claim_id=claim.id or 0,
                    seq=item.seq,
                    icd10_code=item.icd10.strip().upper(),
                    is_primary=item.diagnosis_type == "PRIMARY",
                    source=claim.source_system,
                    captured_by="system",
                    captured_at=utc_now(),
                )
                for item in claim.diagnoses
            ]
        for item in diagnoses:
            code = item.icd10_code.strip().upper()
            if code:
                codes.append(code)
        return codes

    def _icd10_format_valid(self, code: str) -> bool:
        return bool(re.match(r"^[A-Z][0-9]{2}(?:\.[0-9A-Z]{1,4})?$", code))

    def _invalid_icd10_codes(self, claim: ClaimRecord) -> List[str]:
        invalid = []
        for code in self._icd10_codes_for_claim(claim):
            if not self._icd10_format_valid(code) or not self._active_icd10_reference(code, claim.service_date):
                invalid.append(code)
        return invalid

    def _mapping_matches_code(self, code: str, mapping: PMBMappingRule) -> bool:
        normalized_code = code.strip().upper()
        mapping_code = mapping.icd10_code.strip().upper()
        if mapping.match_type == "PREFIX":
            return normalized_code.startswith(mapping_code)
        return normalized_code == mapping_code

    def _active_pmb_mappings_for_claim(self, claim: ClaimRecord) -> List[PMBMappingRule]:
        codes = self._icd10_codes_for_claim(claim)
        return [
            item
            for item in self.pmb_mapping_rules.values()
            if self._is_effective_record(
                active=item.active,
                effective_from=item.effective_from,
                effective_to=item.effective_to,
                status=item.status,
                as_of=claim.service_date,
            )
            and any(self._mapping_matches_code(code, item) for code in codes)
        ]

    def _best_pmb_mapping_for_claim(self, claim: ClaimRecord) -> Optional[PMBMappingRule]:
        diagnoses = self.get_claim_diagnoses(claim.id)
        primary = next((item for item in diagnoses if item.is_primary), None)
        mappings = self._active_pmb_mappings_for_claim(claim)
        if not mappings:
            return None

        def sort_key(item: PMBMappingRule) -> tuple[int, int, int]:
            primary_match = 0
            if primary and self._mapping_matches_code(primary.icd10_code, item):
                primary_match = 1
            confidence = {"HIGH": 3, "MEDIUM": 2, "LOW": 1}.get(item.confidence, 0)
            exact = 1 if item.match_type == "EXACT" else 0
            return (primary_match, exact, confidence)

        return sorted(mappings, key=sort_key, reverse=True)[0]

    def _missing_pmb_evidence(self, claim: ClaimRecord, mapping: PMBMappingRule) -> List[str]:
        available_types = {item.attachment_type.upper() for item in claim.attachments if item.virus_scan_status == "CLEAN"}
        condition = self.pmb_conditions.get(mapping.pmb_condition_id)
        required = set(mapping.required_evidence_types or (condition.evidence_requirements if condition else []))
        return sorted(item for item in required if item.upper() not in available_types)

    def _pmb_evidence_gap_count(self, claim: ClaimRecord) -> int:
        return sum(len(self._missing_pmb_evidence(claim, mapping)) for mapping in self._active_pmb_mappings_for_claim(claim))

    def _facts_for_claim(self, claim: ClaimRecord, policy: PolicyProfile) -> Dict[str, Any]:
        diagnosis_records = self.get_claim_diagnoses(claim.id)
        primary = next((item for item in diagnosis_records if item.is_primary and item.icd10_code), None)
        required_preauth_codes = set(policy.runtime_toggles.get("requirePreauthForCodes", []))
        amount_mismatch_count = 0
        diagnosis_link_missing_count = 0
        missing_preauth_count = 0
        missing_attachment_count = 0
        modifier_sequence_invalid = False

        for item in claim.line_items:
            if round(item.claimed_amount, 2) != round(item.quantity * item.unit_price, 2):
                amount_mismatch_count += 1
            if not item.diagnosis_refs:
                diagnosis_link_missing_count += 1
            if (item.requires_preauth or item.service_code in required_preauth_codes) and not claim.authorisations:
                missing_preauth_count += 1
            if item.requires_attachment and not claim.attachments:
                missing_attachment_count += 1
            if item.modifiers and item.service_code.upper().startswith("ORPHANMOD"):
                modifier_sequence_invalid = True

        regex_value = str(policy.runtime_toggles.get("memberNumberRegex", r"^MEM\d{6}$"))
        return {
            "claim_total": self._claim_amount(claim),
            "primary_icd_missing": primary is None,
            "is_inpatient": claim.care_setting.upper() == "INPATIENT",
            "discharge_missing": claim.care_setting.upper() == "INPATIENT" and not claim.discharge_date_time,
            "missing_preauth_count": missing_preauth_count,
            "missing_attachment_count": missing_attachment_count,
            "amount_mismatch_count": amount_mismatch_count,
            "diagnosis_link_missing_count": diagnosis_link_missing_count,
            "modifier_sequence_invalid": modifier_sequence_invalid,
            "member_format_valid": bool(re.match(regex_value, claim.member_number or "")),
            "invalid_icd_count": len(self._invalid_icd10_codes(claim)),
            "invalid_icd_codes": self._invalid_icd10_codes(claim),
            "pmb_mapping_count": len(self._active_pmb_mappings_for_claim(claim)),
            "missing_pmb_evidence_count": self._pmb_evidence_gap_count(claim),
        }

    def _evaluate_rule(self, rule: RuleDefinition, claim: ClaimRecord, policy: PolicyProfile) -> List[RuleHit]:
        facts = {"claim": self._claim_payload(claim), "facts": self._facts_for_claim(claim, policy)}
        hits: List[RuleHit] = []
        for row in rule.decision_table.get("rows", []):
            evaluated_facts: Dict[str, Any] = {}
            matched = True
            for condition in row.get("when", []):
                actual = self._resolve_path(facts, condition["path"])
                evaluated_facts[condition["path"]] = actual
                if not self._match_condition(actual, condition["op"], condition.get("value")):
                    matched = False
                    break
            if matched:
                hits.append(
                    RuleHit(
                        rule_id=rule.rule_id,
                        name=rule.name,
                        category=rule.category,
                        severity=self._override_severity(rule, policy),
                        reason_code=rule.reason_code,
                        message=policy.runtime_toggles.get("reasonCodeMappings", {}).get(rule.reason_code, rule.message),
                        remediation_hint=rule.remediation_hint,
                        affected_fields=rule.affected_fields,
                        evaluated_facts=evaluated_facts,
                    )
                )
        return hits

    def _aggregate_outcome(self, rule_hits: List[RuleHit]) -> Outcome:
        if any(item.severity == "BLOCK" for item in rule_hits):
            return "BLOCK"
        if any(item.severity == "WARN" for item in rule_hits):
            return "WARN"
        return "PASS"

    def _compat_status(self, outcome: Outcome, stage: StageName) -> str:
        if stage in {"READINESS", "CLOSURE_GATE"}:
            return "blocked" if outcome == "BLOCK" else ("warning" if outcome == "WARN" else "validated")
        if stage == "POST_CLOSURE_VALIDATION":
            return "invalid" if outcome == "BLOCK" else ("warning" if outcome == "WARN" else "valid")
        return outcome.lower()

    def _build_decision_bundle(
        self,
        claim: ClaimRecord,
        stage: StageName,
        actor: str,
        snapshot_id: Optional[str] = None,
        payload_hash: Optional[str] = None,
    ) -> DecisionBundle:
        policy = self._resolve_policy(claim.scheme_id, claim.plan_option_id)
        rule_hits: List[RuleHit] = []
        for rule_id in policy.rule_ids:
            rule = self.rule_definitions[rule_id]
            if stage not in rule.stage_scope or not rule.enabled:
                continue
            rule_hits.extend(self._evaluate_rule(rule, claim, policy))
        evaluated_payload = self.billing_snapshots[snapshot_id].data if snapshot_id else self._claim_decision_input(claim)
        bundle = DecisionBundle(
            decision_bundle_id=new_ref("db"),
            claim_id=claim.id,
            claim_version=claim.version,
            snapshot_id=snapshot_id,
            stage=stage,
            policy_profile_id=policy.policy_profile_id,
            policy_version=policy.version,
            outcome=self._aggregate_outcome(rule_hits),
            input_hash=stable_hash(evaluated_payload),
            payload_hash=payload_hash,
            reference_versions=self._reference_version_map(),
            rule_hits=rule_hits,
            explanations=[f"{item.reason_code}: {item.message}" for item in rule_hits],
            created_at=utc_now(),
            created_by=actor,
        )
        self.decision_bundles[bundle.decision_bundle_id] = bundle
        return bundle

    def _detect_pmb_and_route(
        self,
        claim: ClaimRecord,
        stage: StageName,
        actor: str,
        role: str,
    ) -> Dict[str, Any]:
        policy = self._resolve_policy(claim.scheme_id, claim.plan_option_id)
        pmb_decision = self.pmb_detection_service.evaluate(claim, stage)
        route_decision = self.benefit_routing_service.evaluate(claim, stage, pmb_decision)
        costing_preview = self.costing_preview_service.evaluate(claim, stage, pmb_decision, route_decision)

        self.pmb_decisions[pmb_decision.decision_id] = pmb_decision
        self.benefit_route_decisions[route_decision.decision_id] = route_decision
        self.costing_previews[costing_preview.preview_id] = costing_preview

        claim.latest_pmb_decision_id = pmb_decision.decision_id
        claim.latest_benefit_route_decision_id = route_decision.decision_id
        claim.latest_costing_preview_id = costing_preview.preview_id
        claim.pmb_status = pmb_decision.pmb_status.lower()

        pmb_event_type = {
            "NOT_DETECTED": "PMB_NOT_DETECTED",
            "REVIEW_REQUIRED": "PMB_REVIEW_REQUIRED",
            "CONFIRMED": "PMB_DETECTED",
            "POSSIBLE": "PMB_DETECTED",
            "UNKNOWN": "PMB_EVALUATION_BLOCKED",
        }[pmb_decision.pmb_status]
        self.add_audit_event(
            actor,
            role,
            pmb_event_type,
            "claim",
            str(claim.id),
            {
                "stage": stage,
                "pmb_decision_id": pmb_decision.decision_id,
                "pmb_status": pmb_decision.pmb_status,
                "matched_icd10": pmb_decision.matched_icd10,
                "mapping_id": pmb_decision.mapping_id,
                "condition_id": pmb_decision.condition_id,
                "reason_code": pmb_decision.reason_code,
                "evidence_missing": pmb_decision.evidence_missing,
            },
            policy.policy_profile_id,
            policy.version,
        )
        if pmb_decision.pmb_status in {"POSSIBLE", "REVIEW_REQUIRED", "CONFIRMED"} and not pmb_decision.provider_marked_pmb:
            self.add_audit_event(
                actor,
                role,
                "PMB_PROVIDER_NOT_MARKED",
                "claim",
                str(claim.id),
                {
                    "stage": stage,
                    "pmb_decision_id": pmb_decision.decision_id,
                    "matched_icd10": pmb_decision.matched_icd10,
                    "mapping_id": pmb_decision.mapping_id,
                },
                policy.policy_profile_id,
                policy.version,
            )
        self.add_audit_event(
            actor,
            role,
            f"BENEFIT_ROUTED_{route_decision.route}",
            "claim",
            str(claim.id),
            {
                "stage": stage,
                "routing_decision_id": route_decision.decision_id,
                "pmb_decision_id": pmb_decision.decision_id,
                "route": route_decision.route,
                "reason_code": route_decision.reason_code,
            },
            policy.policy_profile_id,
            policy.version,
        )
        self.add_audit_event(
            actor,
            role,
            "COSTING_PREVIEW_COMPUTED",
            "claim",
            str(claim.id),
            {
                "stage": stage,
                "costing_preview_id": costing_preview.preview_id,
                "pricing_basis": costing_preview.pricing_basis,
                "allowed_total": costing_preview.allowed_total,
                "pmb_allowed_total": costing_preview.pmb_allowed_total,
                "member_liability_estimate": costing_preview.member_liability_estimate,
            },
            policy.policy_profile_id,
            policy.version,
        )
        self.add_audit_event(
            actor,
            role,
            "PMB_DETECTION_AND_BENEFIT_ROUTING",
            "claim",
            str(claim.id),
            {
                "stage": stage,
                "pmb_decision": pmb_decision.model_dump(),
                "benefit_routing_decision": route_decision.model_dump(),
                "costing_preview": costing_preview.model_dump(),
            },
            policy.policy_profile_id,
            policy.version,
        )
        return {
            "pmb_decision": pmb_decision,
            "benefit_routing_decision": route_decision,
            "benefit_route_decisions": [route_decision],
            "costing_preview": costing_preview,
        }

    def _summary_item_from_hit(self, hit: RuleHit, claim_id: Optional[int] = None) -> Dict[str, Any]:
        item = {
            "severity": hit.severity,
            "reason_code": hit.reason_code,
            "title": hit.name,
            "message": hit.message,
            "remediation": hit.remediation_hint,
            "affected_fields": hit.affected_fields,
            "jump_target": hit.affected_fields[0] if hit.affected_fields else None,
        }
        if claim_id and hit.reason_code == "ICD_MISSING_PRIMARY":
            item["action"] = {"type": "NAVIGATE_DIAGNOSES", "target": "diagnoses", "claimId": claim_id}
            item["action_target"] = "diagnoses"
            item["allowAutoFix"] = self._safe_primary_autofix_available(claim_id)
        return item

    def _validation_summary(
        self,
        bundle: Optional[DecisionBundle],
        claim_id: Optional[int] = None,
        pmb_decision: Optional[PMBDecision] = None,
        route_decision: Optional[BenefitRouteDecision] = None,
        costing_preview: Optional[CostingPreview] = None,
        error: Optional[str] = None,
    ) -> Dict[str, Any]:
        blockers: List[Dict[str, Any]] = []
        warnings: List[Dict[str, Any]] = []
        info: List[Dict[str, Any]] = []
        if bundle:
            for hit in bundle.rule_hits:
                target = blockers if hit.severity == "BLOCK" else (warnings if hit.severity == "WARN" else info)
                target.append(self._summary_item_from_hit(hit, claim_id))
        if error:
            blockers.append(
                {
                    "severity": "BLOCK",
                    "reason_code": "ACTION_BLOCKED",
                    "title": "Action blocked",
                    "message": error,
                    "remediation": "Resolve the prerequisite workflow step and retry the action.",
                    "affected_fields": [],
                    "jump_target": None,
                    "action_target": None,
                }
            )
        pmb_items = []
        if route_decision:
            pmb_items.append(
                {
                    "reason_code": route_decision.reason_code,
                    "trigger_icd10": route_decision.trigger_icd10,
                    "mapping_id": route_decision.mapping_id,
                    "pmb_condition_id": route_decision.pmb_condition_id,
                    "provider_marked_pmb": route_decision.provider_marked_pmb,
                    "route": route_decision.route,
                    "action": route_decision.action,
                    "message": route_decision.message,
                    "remediation": route_decision.remediation_hint,
                    "evidence_required": route_decision.evidence_required,
                    "evidence_missing": route_decision.evidence_missing,
                }
            )
        if blockers:
            summary_message = f"{len(blockers)} blocker(s) must be resolved before continuing."
        elif warnings:
            summary_message = f"{len(warnings)} warning(s) require review before continuing."
        else:
            summary_message = "No blockers detected."
        return {
            "outcome": bundle.outcome if bundle else ("BLOCK" if blockers else "PASS"),
            "summary_message": summary_message,
            "blockers": blockers,
            "warnings": warnings,
            "info": info,
            "pmb": pmb_items,
            "pmb_decision": pmb_decision.model_dump() if pmb_decision else None,
            "benefit_routing_decision": route_decision.model_dump() if route_decision else None,
            "costing_preview": costing_preview.model_dump() if costing_preview else None,
            "can_continue": not blockers,
        }

    def get_pmb_decisions_for_claim(self, claim_id: int) -> List[Dict[str, Any]]:
        return [
            item.model_dump()
            for item in sorted(
                [value for value in self.pmb_decisions.values() if value.claim_id == claim_id],
                key=lambda value: value.created_at,
            )
        ]

    def get_benefit_route_decisions_for_claim(self, claim_id: int) -> List[Dict[str, Any]]:
        return [
            item.model_dump()
            for item in sorted(
                [value for value in self.benefit_route_decisions.values() if value.claim_id == claim_id],
                key=lambda value: value.created_at,
            )
        ]

    def get_costing_previews_for_claim(self, claim_id: int) -> List[Dict[str, Any]]:
        return [
            item.model_dump()
            for item in sorted(
                [value for value in self.costing_previews.values() if value.claim_id == claim_id],
                key=lambda value: value.created_at,
            )
        ]

    def list_icd10_reference(self) -> List[Dict[str, Any]]:
        return [
            item.model_dump()
            for item in sorted(
                [value for value in self.icd10_codes.values() if value.active],
                key=lambda value: value.code,
            )
        ]

    def list_pmb_mapping_reference(self) -> Dict[str, Any]:
        return {
            "conditions": [item.model_dump() for item in sorted(self.pmb_conditions.values(), key=lambda value: value.condition_id)],
            "mappings": [item.model_dump() for item in sorted(self.pmb_mapping_rules.values(), key=lambda value: value.mapping_id)],
            "benefit_route_rules": [item.model_dump() for item in sorted(self.benefit_route_rules.values(), key=lambda value: value.rule_id)],
            "tariff_rates": [item.model_dump() for item in sorted(self.tariff_rates.values(), key=lambda value: value.rate_id)],
            "pmb_payment_policies": [
                item.model_dump() for item in sorted(self.pmb_payment_policies.values(), key=lambda value: value.policy_id)
            ],
            "business_data_required": [
                "Official ICD-10 MIT version and valid code set",
                "Business-owned ICD-10 to PMB condition mapping with effective dates",
                "Scheme/plan PMB benefit bucket and evidence requirements",
                "Scheme tariff standards with DSP and non-DSP rates",
                "PMB payment policies for DSP, voluntary non-DSP, and involuntary non-DSP",
                "Approval and rollback governance for mapping activation",
            ],
        }

    def list_patients(self) -> List[Dict[str, Any]]:
        return [item.model_dump() for item in self.patients.values()]

    def get_patient(self, patient_id: int) -> Patient:
        return self.patients[patient_id]

    def create_patient(self, data: Dict[str, Any], actor: str, role: str) -> Dict[str, Any]:
        patient = Patient(
            id=self.next_numeric("patient"),
            name=data["name"],
            mrn=data["mrn"],
            dob=data["dob"],
            sex=data.get("sex", "U"),
            email=data["email"],
            phone=data["phone"],
            status=data.get("status", "active"),
            created_at=utc_now(),
        )
        self.patients[patient.id] = patient
        self.add_audit_event(actor, role, "PATIENT_CREATED", "patient", str(patient.id), patient.model_dump())
        return patient.model_dump()

    def update_patient(self, patient_id: int, data: Dict[str, Any], actor: str, role: str) -> Dict[str, Any]:
        updated = self.patients[patient_id].model_copy(update={**data, "id": patient_id})
        self.patients[patient_id] = updated
        self.add_audit_event(actor, role, "PATIENT_UPDATED", "patient", str(patient_id), updated.model_dump())
        return updated.model_dump()

    def delete_patient(self, patient_id: int, actor: str, role: str) -> None:
        del self.patients[patient_id]
        self.add_audit_event(actor, role, "PATIENT_DELETED", "patient", str(patient_id), {})

    def list_providers(self) -> List[Dict[str, Any]]:
        return [item.model_dump() for item in self.providers.values()]

    def get_provider(self, provider_id: int) -> Provider:
        return self.providers[provider_id]

    def create_provider(self, data: Dict[str, Any], actor: str, role: str) -> Dict[str, Any]:
        provider = Provider(
            id=self.next_numeric("provider"),
            name=data["name"],
            npi=data["npi"],
            practice_number=str(data.get("practice_number") or data["npi"]),
            specialty=data.get("specialty", "General Practice"),
            discipline=data.get("discipline", "SPECIALIST"),
            email=data["email"],
            phone=data["phone"],
            status=data.get("status", "active"),
            created_at=utc_now(),
        )
        self.providers[provider.id] = provider
        self.add_audit_event(actor, role, "PROVIDER_CREATED", "provider", str(provider.id), provider.model_dump())
        return provider.model_dump()

    def update_provider(self, provider_id: int, data: Dict[str, Any], actor: str, role: str) -> Dict[str, Any]:
        payload = {**self.providers[provider_id].model_dump(), **data, "id": provider_id}
        if not payload.get("practice_number"):
            payload["practice_number"] = payload.get("npi")
        updated = Provider(**payload)
        self.providers[provider_id] = updated
        self.add_audit_event(actor, role, "PROVIDER_UPDATED", "provider", str(provider_id), updated.model_dump())
        return updated.model_dump()

    def delete_provider(self, provider_id: int, actor: str, role: str) -> None:
        del self.providers[provider_id]
        self.add_audit_event(actor, role, "PROVIDER_DELETED", "provider", str(provider_id), {})

    def list_users(self) -> List[Dict[str, Any]]:
        return [item.model_dump() for item in self.users.values()]

    def get_user(self, user_id: int) -> User:
        return self.users[user_id]

    def create_user(self, data: Dict[str, Any], actor: str, role: str) -> Dict[str, Any]:
        user = self.register_user(data["username"], data["password"], data["role"], data["email"])
        self.add_audit_event(actor, role, "USER_CREATED", "user", str(user.id), user.model_dump())
        return user.model_dump()

    def update_user(self, user_id: int, data: Dict[str, Any], actor: str, role: str) -> Dict[str, Any]:
        previous = self.users[user_id]
        updated = previous.model_copy(update={**data, "id": user_id})
        self.users[user_id] = updated
        auth_record = self.auth_users.get(previous.username)
        if auth_record:
            if updated.username != previous.username:
                self.auth_users[updated.username] = auth_record
                del self.auth_users[previous.username]
            auth_record["role"] = updated.role
            auth_record["email"] = updated.email
        self.add_audit_event(actor, role, "USER_UPDATED", "user", str(user_id), updated.model_dump())
        return updated.model_dump()

    def delete_user(self, user_id: int, actor: str, role: str) -> None:
        user = self.users[user_id]
        self.auth_users.pop(user.username, None)
        del self.users[user_id]
        self.add_audit_event(actor, role, "USER_DELETED", "user", str(user_id), {})

    def create_claim(self, data: Dict[str, Any], actor: str, role: str) -> ClaimRecord:
        claim = self._normalize_claim(data)
        self.claims[claim.id] = claim
        self._sync_claim_diagnoses_from_claim(claim, actor, source=claim.source_system)
        self._record_claim_version(claim, "Initial version")
        self.add_audit_event(actor, role, "CLAIM_DRAFT_UPDATED", "claim", str(claim.id), self._claim_payload(claim))
        return claim

    def list_claims(self) -> List[Dict[str, Any]]:
        return [self._claim_payload(item) for item in sorted(self.claims.values(), key=lambda item: item.id)]

    def get_claim(self, claim_id: int) -> Dict[str, Any]:
        claim = self.claims[claim_id]
        payload = self._claim_payload(claim)
        payload["diagnoses"] = [item.model_dump() for item in self.get_claim_diagnoses(claim_id)]
        payload["version_chain"] = [item.model_dump() for item in self.claim_versions.get(claim_id, [])]
        payload["current_policy"] = self._resolve_policy(claim.scheme_id, claim.plan_option_id).model_dump()
        payload["latest_snapshot"] = self.billing_snapshots[claim.latest_snapshot_id].model_dump() if claim.latest_snapshot_id else None
        payload["latest_payload"] = self.payloads[claim.latest_payload_id].model_dump() if claim.latest_payload_id else None
        payload["latest_response"] = self.responses[claim.latest_response_id].model_dump() if claim.latest_response_id else None
        payload["latest_remittance"] = self.remittances[claim.latest_remittance_id].model_dump() if claim.latest_remittance_id else None
        payload["latest_reconciliation"] = self.reconciliations[claim.latest_reconciliation_id].model_dump() if claim.latest_reconciliation_id else None
        payload["latest_pmb_decision"] = (
            self.pmb_decisions[claim.latest_pmb_decision_id].model_dump()
            if claim.latest_pmb_decision_id
            else None
        )
        payload["latest_benefit_route_decision"] = (
            self.benefit_route_decisions[claim.latest_benefit_route_decision_id].model_dump()
            if claim.latest_benefit_route_decision_id
            else None
        )
        payload["latest_costing_preview"] = (
            self.costing_previews[claim.latest_costing_preview_id].model_dump()
            if claim.latest_costing_preview_id
            else None
        )
        payload["pmb_decisions"] = self.get_pmb_decisions_for_claim(claim_id)
        payload["benefit_route_decisions"] = self.get_benefit_route_decisions_for_claim(claim_id)
        payload["costing_previews"] = self.get_costing_previews_for_claim(claim_id)
        return payload

    def update_claim(
        self,
        claim_id: int,
        data: Dict[str, Any],
        actor: str,
        role: str,
        change_summary: str = "Draft updated",
    ) -> Dict[str, Any]:
        claim = self.claims[claim_id]
        frozen_statuses = {"closed", "ready_to_submit", "submitted", "acknowledged", "rejected", "pended", "adjudicated", "paid", "reconciled", "validation_exception", "exception"}
        if claim.status in frozen_statuses or claim.latest_snapshot_id:
            next_claim = claim.model_copy(deep=True)
            next_claim.previous_version = claim.version
            next_claim.version = claim.version + 1
            next_claim.status = "draft"
            next_claim.readiness_status = "pending"
            next_claim.validation_status = "pending"
            next_claim.payload_status = "not_built"
            next_claim.submission_status = "not_submitted"
            next_claim.submission_channel = None
            next_claim.remittance_status = "pending"
            next_claim.reconciliation_status = "pending"
            next_claim.latest_snapshot_id = None
            next_claim.latest_payload_id = None
            next_claim.latest_submission_id = None
            next_claim.latest_response_id = None
            next_claim.latest_financial_bundle_id = None
            next_claim.latest_remittance_id = None
            next_claim.latest_reconciliation_id = None
            next_claim.latest_pmb_decision_id = None
            next_claim.latest_benefit_route_decision_id = None
            next_claim.latest_costing_preview_id = None
            next_claim.pmb_status = "not_evaluated"
            for key, value in data.items():
                if hasattr(next_claim, key):
                    setattr(next_claim, key, value)
            next_claim.updated_at = utc_now()
            self.claims[claim_id] = next_claim
            if "diagnoses" in data:
                self._sync_claim_diagnoses_from_claim(next_claim, actor, source=next_claim.source_system)
            self._record_claim_version(next_claim, change_summary)
            self.add_audit_event(actor, role, "CLAIM_VERSION_CREATED", "claim", str(claim_id), {"version": next_claim.version, "previous_version": claim.version, "change_summary": change_summary})
            return self.get_claim(claim_id)

        payload = {**claim.model_dump(), **data, "id": claim_id, "updated_at": utc_now()}
        if "line_items" in data:
            payload["line_items"] = [
                self._normalize_line_item(item, index, payload.get("service_date", claim.service_date))
                for index, item in enumerate(data["line_items"], start=1)
            ]
        if "diagnoses" in data:
            payload["diagnoses"] = [Diagnosis(**item) for item in data["diagnoses"]]
        if "authorisations" in data:
            payload["authorisations"] = [AuthorizationRecord(**item) for item in data["authorisations"]]
        if "attachments" in data:
            payload["attachments"] = [AttachmentRecord(**item) for item in data["attachments"]]
        updated = ClaimRecord(**payload)
        self.claims[claim_id] = updated
        if "diagnoses" in data:
            self._sync_claim_diagnoses_from_claim(updated, actor, source=updated.source_system)
        self._record_claim_version(updated, change_summary)
        self.add_audit_event(actor, role, "CLAIM_DRAFT_UPDATED", "claim", str(claim_id), self._claim_payload(updated))
        return self.get_claim(claim_id)

    def _persist_claim_diagnosis_records(
        self,
        claim_id: int,
        records: List[ClaimDiagnosis],
        actor: str,
        role: str,
        change_summary: str,
    ) -> Dict[str, Any]:
        normalized_records: List[ClaimDiagnosis] = []
        primary_seen = False
        for index, item in enumerate(records, start=1):
            is_primary = bool(item.is_primary and not primary_seen)
            if is_primary:
                primary_seen = True
            normalized_records.append(
                item.model_copy(
                    update={
                        "claim_id": claim_id,
                        "seq": index,
                        "icd10_code": item.icd10_code.strip().upper(),
                        "is_primary": is_primary,
                    }
                )
            )
        diagnosis_payload = [
            {
                "seq": index,
                "icd10": item.icd10_code,
                "diagnosis_type": "PRIMARY" if item.is_primary else "SECONDARY",
            }
            for index, item in enumerate(normalized_records, start=1)
        ]
        self.update_claim(claim_id, {"diagnoses": diagnosis_payload}, actor, role, change_summary)
        self.claim_diagnoses[claim_id] = normalized_records
        self._apply_claim_diagnosis_records_to_claim(self.claims[claim_id])
        return {
            "claim_id": claim_id,
            "claim_version": self.claims[claim_id].version,
            "diagnoses": [item.model_dump() for item in self.get_claim_diagnoses(claim_id)],
        }

    def add_claim_diagnosis(self, claim_id: int, data: Dict[str, Any], actor: str, role: str) -> Dict[str, Any]:
        claim = self.claims[claim_id]
        icd10_code = str(data.get("icd10_code") or data.get("icd10") or "").strip().upper()
        validation_error = self.icd10_validation_service.validate_code(icd10_code, claim.service_date)
        if validation_error:
            raise ValueError(f"ICD-10 code is not valid for capture: {validation_error}")

        records = self.get_claim_diagnoses(claim_id)
        is_primary = to_bool(data.get("is_primary", False)) or (not records and str(data.get("diagnosis_type") or "PRIMARY").upper() == "PRIMARY")
        if is_primary:
            records = [item.model_copy(update={"is_primary": False}) for item in records]
        records.append(
            ClaimDiagnosis(
                diagnosis_id=new_ref("dx"),
                claim_id=claim_id,
                seq=len(records) + 1,
                icd10_code=icd10_code,
                is_primary=is_primary,
                source=str(data.get("source") or claim.source_system),
                captured_by=actor,
                captured_at=utc_now(),
            )
        )
        result = self._persist_claim_diagnosis_records(claim_id, records, actor, role, "Diagnosis captured")
        self.add_audit_event(actor, role, "CLAIM_DIAGNOSIS_CAPTURED", "claim", str(claim_id), {"icd10_code": icd10_code, "is_primary": is_primary})
        return result

    def make_primary_diagnosis(self, claim_id: int, diagnosis_id: str, actor: str, role: str) -> Dict[str, Any]:
        records = self.get_claim_diagnoses(claim_id)
        found = False
        updated_records: List[ClaimDiagnosis] = []
        for item in records:
            make_primary = item.diagnosis_id == diagnosis_id
            if make_primary:
                found = True
            updated_records.append(item.model_copy(update={"is_primary": make_primary}))
        if not found:
            raise KeyError(f"Diagnosis {diagnosis_id} not found for claim {claim_id}")
        result = self._persist_claim_diagnosis_records(claim_id, updated_records, actor, role, "Primary diagnosis updated")
        self.add_audit_event(actor, role, "CLAIM_PRIMARY_DIAGNOSIS_SET", "claim", str(claim_id), {"diagnosis_id": diagnosis_id})
        return result

    def auto_fix_primary_diagnosis(self, claim_id: int, actor: str, role: str) -> Dict[str, Any]:
        records = self.get_claim_diagnoses(claim_id)
        if len(records) == 1 and not any(item.is_primary for item in records):
            fixed_record = records[0].model_copy(update={"is_primary": True})
            result = self._persist_claim_diagnosis_records(claim_id, [fixed_record], actor, role, "Primary diagnosis auto-fixed")
            self.add_audit_event(actor, role, "CLAIM_PRIMARY_DIAGNOSIS_AUTO_FIXED", "claim", str(claim_id), {"diagnosis_id": fixed_record.diagnosis_id})
            result["fixed"] = True
            return result
        return {
            "claim_id": claim_id,
            "fixed": False,
            "reason": "ambiguous_primary",
            "message": "Automatic primary ICD-10 fix is only safe when exactly one diagnosis exists and none is primary.",
            "diagnoses": [item.model_dump() for item in records],
        }

    def get_decision_bundles_for_claim(self, claim_id: int) -> List[DecisionBundle]:
        return sorted(
            [item for item in self.decision_bundles.values() if item.claim_id == claim_id],
            key=lambda item: item.created_at,
        )

    def run_readiness(self, claim_id: int, actor: str, role: str) -> Dict[str, Any]:
        claim = self.claims[claim_id]
        pmb_context = self._detect_pmb_and_route(claim, "READINESS", actor, role)
        bundle = self._build_decision_bundle(claim, "READINESS", actor)
        claim.readiness_status = self._compat_status(bundle.outcome, "READINESS")
        claim.status = "ready_to_close" if bundle.outcome in {"PASS", "WARN"} else "blocked"
        claim.updated_at = utc_now()

        items = []
        for hit in bundle.rule_hits:
            item = ReadinessItem(
                item_id=new_ref("ri"),
                claim_id=claim.id,
                claim_version=claim.version,
                severity=hit.severity,
                reason_code=hit.reason_code,
                message=hit.message,
                remediation_hint=hit.remediation_hint,
                affected_fields=hit.affected_fields,
            )
            self.readiness_items[item.item_id] = item
            items.append(item)

        run = ReadinessRun(
            readiness_run_id=new_ref("rr"),
            claim_id=claim.id,
            claim_version=claim.version,
            decision_bundle_id=bundle.decision_bundle_id,
            outcome=bundle.outcome,
            created_at=utc_now(),
            items=items,
        )
        self.readiness_runs[run.readiness_run_id] = run
        policy = self._resolve_policy(claim.scheme_id, claim.plan_option_id)
        self.add_audit_event(actor, role, "READINESS_RUN", "claim", str(claim_id), {"decision_bundle_id": bundle.decision_bundle_id, "outcome": bundle.outcome}, policy.policy_profile_id, policy.version, {"input_hash": bundle.input_hash})
        return {
            "claim_id": claim.id,
            "claim_number": claim.claim_number,
            "claim_version": claim.version,
            "status": claim.readiness_status,
            "outcome": bundle.outcome,
            "decision_bundle": bundle.model_dump(),
            "readiness_run": run.model_dump(),
            "pmb_decision": pmb_context["pmb_decision"].model_dump(),
            "benefit_routing_decision": pmb_context["benefit_routing_decision"].model_dump(),
            "benefit_route_decisions": [item.model_dump() for item in pmb_context["benefit_route_decisions"]],
            "costing_preview": pmb_context["costing_preview"].model_dump(),
            "validation_summary": self._validation_summary(
                bundle,
                claim.id,
                pmb_context["pmb_decision"],
                pmb_context["benefit_routing_decision"],
                pmb_context["costing_preview"],
            ),
        }

    def close_claim(self, claim_id: int, request: ClaimClosureRequest, actor: str, role: str) -> Dict[str, Any]:
        claim = self.claims[claim_id]
        pmb_context = self._detect_pmb_and_route(claim, "CLOSURE_GATE", actor, role)
        bundle = self._build_decision_bundle(claim, "CLOSURE_GATE", actor)
        policy = self._resolve_policy(claim.scheme_id, claim.plan_option_id)
        if bundle.outcome == "BLOCK":
            self.add_audit_event(actor, role, "CLOSURE_BLOCKED", "claim", str(claim_id), {"decision_bundle_id": bundle.decision_bundle_id, "reasons": [item.reason_code for item in bundle.rule_hits]}, policy.policy_profile_id, policy.version, {"input_hash": bundle.input_hash})
            return {
                "claim_id": claim.id,
                "claim_number": claim.claim_number,
                "status": "blocked",
                "outcome": bundle.outcome,
                "decision_bundle": bundle.model_dump(),
                "pmb_decision": pmb_context["pmb_decision"].model_dump(),
                "benefit_routing_decision": pmb_context["benefit_routing_decision"].model_dump(),
                "benefit_route_decisions": [item.model_dump() for item in pmb_context["benefit_route_decisions"]],
                "costing_preview": pmb_context["costing_preview"].model_dump(),
                "validation_summary": self._validation_summary(
                    bundle,
                    claim.id,
                    pmb_context["pmb_decision"],
                    pmb_context["benefit_routing_decision"],
                    pmb_context["costing_preview"],
                ),
            }
        if bundle.outcome == "WARN" and to_bool(policy.runtime_toggles.get("requireSupervisorOverrideOnWarnings")) and not request.supervisor_override:
            self.add_audit_event(actor, role, "CLOSURE_OVERRIDE_REQUIRED", "claim", str(claim_id), {"decision_bundle_id": bundle.decision_bundle_id}, policy.policy_profile_id, policy.version)
            return {
                "claim_id": claim.id,
                "claim_number": claim.claim_number,
                "status": "override_required",
                "outcome": bundle.outcome,
                "decision_bundle": bundle.model_dump(),
                "pmb_decision": pmb_context["pmb_decision"].model_dump(),
                "benefit_routing_decision": pmb_context["benefit_routing_decision"].model_dump(),
                "benefit_route_decisions": [item.model_dump() for item in pmb_context["benefit_route_decisions"]],
                "costing_preview": pmb_context["costing_preview"].model_dump(),
                "validation_summary": self._validation_summary(
                    bundle,
                    claim.id,
                    pmb_context["pmb_decision"],
                    pmb_context["benefit_routing_decision"],
                    pmb_context["costing_preview"],
                ),
            }

        snapshot = BillingSnapshot(
            snapshot_id=new_ref("snap"),
            claim_id=claim.id,
            claim_version=claim.version,
            data=self._claim_payload(claim),
            input_hash=stable_hash(self._claim_payload(claim)),
            created_at=utc_now(),
            created_by=actor,
        )
        self.billing_snapshots[snapshot.snapshot_id] = snapshot
        claim.latest_snapshot_id = snapshot.snapshot_id
        claim.status = "closed"
        claim.updated_at = utc_now()
        self._record_claim_version(claim, request.override_note or "Snapshot created and claim closed.")
        self.add_audit_event(actor, role, "SNAPSHOT_CREATED", "claim", str(claim_id), {"snapshot_id": snapshot.snapshot_id, "claim_version": claim.version}, policy.policy_profile_id, policy.version, {"input_hash": snapshot.input_hash})
        return {
            "claim_id": claim.id,
            "claim_number": claim.claim_number,
            "claim_version": claim.version,
            "status": claim.status,
            "snapshot_id": snapshot.snapshot_id,
            "decision_bundle": bundle.model_dump(),
            "pmb_decision": pmb_context["pmb_decision"].model_dump(),
            "benefit_routing_decision": pmb_context["benefit_routing_decision"].model_dump(),
            "benefit_route_decisions": [item.model_dump() for item in pmb_context["benefit_route_decisions"]],
            "costing_preview": pmb_context["costing_preview"].model_dump(),
            "validation_summary": self._validation_summary(
                bundle,
                claim.id,
                pmb_context["pmb_decision"],
                pmb_context["benefit_routing_decision"],
                pmb_context["costing_preview"],
            ),
        }

    def run_post_closure_validation(self, claim_id: int, actor: str, role: str) -> Dict[str, Any]:
        claim = self.claims[claim_id]
        if not claim.latest_snapshot_id:
            error = "Claim must be closed before validation."
            return {
                "claim_id": claim.id,
                "claim_number": claim.claim_number,
                "validation_status": "pending",
                "error": error,
                "validation_summary": self._validation_summary(None, claim.id, error=error),
            }
        pmb_context = self._detect_pmb_and_route(claim, "POST_CLOSURE_VALIDATION", actor, role)
        bundle = self._build_decision_bundle(claim, "POST_CLOSURE_VALIDATION", actor, claim.latest_snapshot_id)
        claim.validation_status = self._compat_status(bundle.outcome, "POST_CLOSURE_VALIDATION")
        claim.status = "validation_exception" if bundle.outcome == "BLOCK" else "ready_to_submit"
        claim.updated_at = utc_now()
        policy = self._resolve_policy(claim.scheme_id, claim.plan_option_id)
        self.add_audit_event(actor, role, "POST_CLOSURE_VALIDATION_DONE", "claim", str(claim_id), {"decision_bundle_id": bundle.decision_bundle_id, "outcome": bundle.outcome}, policy.policy_profile_id, policy.version, {"input_hash": bundle.input_hash})
        return {
            "claim_id": claim.id,
            "claim_number": claim.claim_number,
            "validation_status": claim.validation_status,
            "outcome": bundle.outcome,
            "decision_bundle": bundle.model_dump(),
            "pmb_decision": pmb_context["pmb_decision"].model_dump(),
            "benefit_routing_decision": pmb_context["benefit_routing_decision"].model_dump(),
            "benefit_route_decisions": [item.model_dump() for item in pmb_context["benefit_route_decisions"]],
            "costing_preview": pmb_context["costing_preview"].model_dump(),
            "validation_summary": self._validation_summary(
                bundle,
                claim.id,
                pmb_context["pmb_decision"],
                pmb_context["benefit_routing_decision"],
                pmb_context["costing_preview"],
            ),
        }

    def _canonical_claim(self, claim: ClaimRecord, snapshot_id: str) -> Dict[str, Any]:
        provider = self.providers[claim.provider_id]
        return {
            "claim_id": claim.id,
            "claim_number": claim.claim_number,
            "version": claim.version,
            "snapshot_id": snapshot_id,
            "scheme_id": claim.scheme_id,
            "plan_option_id": claim.plan_option_id,
            "member": {"member_number": claim.member_number, "dependant_code": claim.dependant_code, "membership_status": claim.membership_status},
            "provider": {"practice_number": provider.practice_number, "name": provider.name, "discipline": provider.discipline},
            "encounter": {"care_setting": claim.care_setting, "service_date": claim.service_date, "admission_date_time": claim.admission_date_time, "discharge_date_time": claim.discharge_date_time},
            "diagnoses": [
                {
                    "diagnosis_id": item.diagnosis_id,
                    "seq": item.seq,
                    "icd10": item.icd10_code,
                    "icd10_code": item.icd10_code,
                    "type": "PRIMARY" if item.is_primary else "SECONDARY",
                    "is_primary": item.is_primary,
                    "source": item.source,
                    "captured_at": item.captured_at,
                }
                for item in self.get_claim_diagnoses(claim.id)
            ],
            "line_items": [{"line_id": item.line_id, "service_code": item.service_code, "quantity": item.quantity, "unit_price": item.unit_price, "claimed_amount": item.claimed_amount, "diagnosis_refs": item.diagnosis_refs, "modifiers": item.modifiers, "nappi_code": item.nappi_code} for item in claim.line_items],
            "pmb": {
                "provider_pmb_indicator": claim.provider_pmb_indicator,
                "status": claim.pmb_status,
                "pmb_decision": (
                    self.pmb_decisions[claim.latest_pmb_decision_id].model_dump()
                    if claim.latest_pmb_decision_id
                    else None
                ),
                "benefit_route_decision": (
                    self.benefit_route_decisions[claim.latest_benefit_route_decision_id].model_dump()
                    if claim.latest_benefit_route_decision_id
                    else None
                ),
                "costing_preview": (
                    self.costing_previews[claim.latest_costing_preview_id].model_dump()
                    if claim.latest_costing_preview_id
                    else None
                ),
            },
            "attachments": [item.model_dump() for item in claim.attachments],
            "totals": {"claimed": self._claim_amount(claim)},
        }

    def _pseudo_edi(self, claim: ClaimRecord, canonical: Dict[str, Any]) -> str:
        lines = [
            f"UNH+{claim.claim_number}+MEDCLM:1:1:PHISC'",
            f"BGM+340+{claim.invoice_number}+9'",
            f"DTM+137:{claim.service_date.replace('-', '')}:102'",
            f"NAD+MS+{claim.scheme_id}'",
            f"NAD+PR+{self.providers[claim.provider_id].practice_number}:PCNS'",
            f"RFF+MB:{claim.member_number}'",
        ]
        for diagnosis in canonical["diagnoses"]:
            lines.append(f"RFF+ICD:{diagnosis.get('icd10') or diagnosis.get('icd10_code')}:{diagnosis['seq']}'")
        for index, line in enumerate(canonical["line_items"], start=1):
            lines.extend([f"LIN+{index}++{line['service_code']}:SA'", f"QTY+47:{line['quantity']}'", f"MOA+203:{line['claimed_amount']:.2f}'"])
        lines.append(f"UNT+{len(lines) + 1}+{claim.claim_number}'")
        return "\n".join(lines)

    def _phisc_xml(self, claim: ClaimRecord, canonical: Dict[str, Any]) -> str:
        diagnoses_xml = "".join(
            f"<Diagnosis seq=\"{item['seq']}\" type=\"{item['type']}\">{item.get('icd10') or item.get('icd10_code')}</Diagnosis>"
            for item in canonical["diagnoses"]
        )
        lines_xml = "".join(f"<Line id=\"{item['line_id']}\"><Code>{item['service_code']}</Code><Quantity>{item['quantity']}</Quantity><ClaimedAmount>{item['claimed_amount']:.2f}</ClaimedAmount></Line>" for item in canonical["line_items"])
        return (
            f"<Claim id=\"{claim.claim_number}\" scheme=\"{claim.scheme_id}\" option=\"{claim.plan_option_id}\">"
            f"<Member number=\"{claim.member_number}\" dependant=\"{claim.dependant_code}\" />"
            f"<Provider practiceNumber=\"{self.providers[claim.provider_id].practice_number}\" />"
            f"<Encounter careSetting=\"{claim.care_setting}\" serviceDate=\"{claim.service_date}\" />"
            f"<Diagnoses>{diagnoses_xml}</Diagnoses><Lines>{lines_xml}</Lines><Totals claimed=\"{self._claim_amount(claim):.2f}\" /></Claim>"
        )

    def build_payload(self, claim_id: int, actor: str, role: str) -> Dict[str, Any]:
        claim = self.claims[claim_id]
        if not claim.latest_snapshot_id:
            error = "Claim must be closed before payload generation."
            return {
                "claim_id": claim.id,
                "claim_number": claim.claim_number,
                "status": "blocked",
                "error": error,
                "validation_summary": self._validation_summary(None, error=error),
            }
        if claim.validation_status not in {"valid", "warning"}:
            error = "Claim must pass post-closure validation before payload generation."
            return {
                "claim_id": claim.id,
                "claim_number": claim.claim_number,
                "status": "blocked",
                "error": error,
                "validation_summary": self._validation_summary(None, error=error),
            }
        canonical = self._canonical_claim(claim, claim.latest_snapshot_id)
        payload = PayloadArtifact(
            payload_id=new_ref("payload"),
            claim_id=claim.id,
            claim_version=claim.version,
            snapshot_id=claim.latest_snapshot_id,
            canonical_claim=canonical,
            pseudo_edi=self._pseudo_edi(claim, canonical),
            phisc_xml=self._phisc_xml(claim, canonical),
            canonical_hash=stable_hash(canonical),
            payload_hash=stable_hash({"canonical": canonical, "claim_number": claim.claim_number}),
            created_at=utc_now(),
        )
        self.payloads[payload.payload_id] = payload
        claim.latest_payload_id = payload.payload_id
        claim.payload_status = "built"
        claim.updated_at = utc_now()
        policy = self._resolve_policy(claim.scheme_id, claim.plan_option_id)
        self.add_audit_event(actor, role, "PAYLOAD_BUILT", "claim", str(claim_id), {"payload_id": payload.payload_id}, policy.policy_profile_id, policy.version, {"canonical_hash": payload.canonical_hash, "payload_hash": payload.payload_hash})
        return {
            "claim_id": claim.id,
            "claim_number": claim.claim_number,
            "payload_id": payload.payload_id,
            "payload_hash": payload.payload_hash,
            "canonical_claim": canonical,
            "pseudo_edi": payload.pseudo_edi,
            "phisc_xml": payload.phisc_xml,
        }

    def _add_transport_log(self, submission_id: str, event: str, details: Dict[str, Any]) -> TransportLog:
        log = TransportLog(
            transport_log_id=new_ref("tlog"),
            submission_id=submission_id,
            event=event,
            details=details,
            created_at=utc_now(),
        )
        self.transport_logs[log.transport_log_id] = log
        return log

    def _simulate_response(self, claim: ClaimRecord, submission: Submission) -> ResponseRecord:
        reasons: List[ResponseReason] = []
        status: Literal["ACK", "REJ", "PEND"] = "ACK"
        member_regex = str(self._resolve_policy(claim.scheme_id, claim.plan_option_id).runtime_toggles.get("memberNumberRegex", r"^MEM\d{6}$"))
        if not re.match(member_regex, claim.member_number):
            status = "REJ"
            reasons.append(ResponseReason(level="HEADER", reason_code="MEMBER_INVALID", message="Member number failed scheme format validation."))
        elif claim.scenario_key in {"pending_attachment_motivation", "PMB_REVIEW_REQUIRED"}:
            status = "PEND"
            reasons.append(ResponseReason(level="HEADER", reason_code="ATTACHMENT_REQUIRED", message="Additional motivation is required before adjudication."))
        response = ResponseRecord(
            response_id=new_ref("rsp"),
            submission_id=submission.submission_id,
            claim_id=claim.id,
            claim_version=claim.version,
            status=status,
            reasons=reasons,
            received_at=utc_now(),
        )
        self.responses[response.response_id] = response
        return response

    def adjudicate(self, claim_id: int, actor: str, role: str) -> FinancialBundle:
        claim = self.claims[claim_id]
        policy = self._resolve_policy(claim.scheme_id, claim.plan_option_id)
        line_outcomes: List[FinancialLineOutcome] = []
        total_claimed = 0.0
        total_allowed = 0.0
        total_paid = 0.0
        total_member = 0.0
        for item in claim.line_items:
            claimed_amount = round(item.claimed_amount, 2)
            if claim.scenario_key in {"partial_payment_remittance", "PARTIAL_PAYMENT"}:
                allowed_amount = round(claimed_amount * 0.9, 2)
                paid_amount = round(claimed_amount * 0.7, 2)
            else:
                allowed_amount = claimed_amount
                paid_amount = claimed_amount
            member_liability = round(claimed_amount - paid_amount, 2)
            total_claimed += claimed_amount
            total_allowed += allowed_amount
            total_paid += paid_amount
            total_member += member_liability
            line_outcomes.append(
                FinancialLineOutcome(
                    line_id=item.line_id,
                    claimed_amount=claimed_amount,
                    allowed_amount=allowed_amount,
                    paid_amount=paid_amount,
                    member_liability=member_liability,
                    scheme_liability=paid_amount,
                    reason_codes=[] if paid_amount == claimed_amount else ["PARTIAL_PAYMENT"],
                )
            )
        bundle = FinancialBundle(
            financial_bundle_id=new_ref("fin"),
            claim_id=claim.id,
            claim_version=claim.version,
            policy_profile_id=policy.policy_profile_id,
            policy_version=policy.version,
            totals={"claimed": round(total_claimed, 2), "allowed": round(total_allowed, 2), "paid": round(total_paid, 2), "member_liability": round(total_member, 2), "provider_liability": 0.0},
            line_outcomes=line_outcomes,
            created_at=utc_now(),
        )
        self.financial_bundles[bundle.financial_bundle_id] = bundle
        claim.latest_financial_bundle_id = bundle.financial_bundle_id
        claim.status = "adjudicated"
        self.add_audit_event(actor, role, "ADJUDICATED", "claim", str(claim_id), {"financial_bundle_id": bundle.financial_bundle_id, "totals": bundle.totals}, policy.policy_profile_id, policy.version)
        return bundle

    def generate_remittance(self, claim_id: int, actor: str, role: str) -> RemittanceAdvice:
        claim = self.claims[claim_id]
        bundle = self.financial_bundles[claim.latest_financial_bundle_id]
        lines: List[RemittanceLine] = []
        total_paid = 0.0
        total_adjustments = 0.0
        for item in bundle.line_outcomes:
            paid_amount = item.paid_amount
            adjustment_amount = round(item.claimed_amount - paid_amount, 2)
            status: Literal["PAID", "PARTIAL", "DENIED"] = "PAID"
            reason_codes = list(item.reason_codes)
            if claim.scenario_key in {"partial_payment_remittance", "PARTIAL_PAYMENT"}:
                status = "PARTIAL"
            if claim.scenario_key in {"reconciliation_mismatch_exception", "MISMATCH_EXCEPTION"}:
                paid_amount = round(item.paid_amount - 100, 2)
                adjustment_amount = round(item.claimed_amount - paid_amount, 2)
                status = "PARTIAL"
                reason_codes = ["TOTALS_MISMATCH"]
            total_paid += paid_amount
            total_adjustments += adjustment_amount
            lines.append(RemittanceLine(line_id=item.line_id, paid_amount=paid_amount, adjustment_amount=adjustment_amount, status=status, reason_codes=reason_codes))
        remittance = RemittanceAdvice(
            remittance_id=new_ref("rmt"),
            claim_id=claim.id,
            claim_version=claim.version,
            payment_batch_ref=new_ref("batch"),
            claim_reference=claim.claim_reference,
            lines=lines,
            totals={"claimed": bundle.totals["claimed"], "paid": round(total_paid, 2), "adjustments": round(total_adjustments, 2)},
            created_at=utc_now(),
        )
        self.remittances[remittance.remittance_id] = remittance
        claim.latest_remittance_id = remittance.remittance_id
        claim.remittance_status = "partial" if any(item.status == "PARTIAL" for item in lines) else "received"
        claim.status = "paid" if claim.remittance_status == "received" else "exception"
        payment = PaymentRecord(
            id=self.next_numeric("payment"),
            claim_id=claim.id,
            amount=remittance.totals["paid"],
            payment_date=utc_now()[:10],
            method="EFT",
            status="completed" if remittance.totals["paid"] > 0 else "pending",
            created_at=utc_now(),
        )
        self.payments[payment.id] = payment
        self.add_audit_event(actor, role, "REMITTED", "claim", str(claim_id), {"remittance_id": remittance.remittance_id, "payment_id": payment.id})
        return remittance

    def reconcile(self, claim_id: int, actor: str, role: str) -> ReconciliationRecord:
        claim = self.claims[claim_id]
        bundle = self.financial_bundles[claim.latest_financial_bundle_id]
        remittance = self.remittances[claim.latest_remittance_id]
        exception_reasons: List[str] = []
        status: Literal["RECONCILED", "PARTIAL", "EXCEPTION"] = "RECONCILED"
        if claim.scenario_key in {"partial_payment_remittance", "PARTIAL_PAYMENT"}:
            status = "PARTIAL"
            exception_reasons.append("Short paid against adjudicated amount.")
        elif claim.scenario_key in {"reconciliation_mismatch_exception", "MISMATCH_EXCEPTION"}:
            status = "EXCEPTION"
            exception_reasons.append("Remittance totals do not align to adjudication bundle.")
        elif round(remittance.totals["paid"], 2) != round(bundle.totals["paid"], 2):
            status = "EXCEPTION"
            exception_reasons.append("Unexpected paid total mismatch.")
        record = ReconciliationRecord(
            reconciliation_id=new_ref("rec"),
            claim_id=claim.id,
            claim_version=claim.version,
            status=status,
            exception_reasons=exception_reasons,
            created_at=utc_now(),
        )
        self.reconciliations[record.reconciliation_id] = record
        claim.latest_reconciliation_id = record.reconciliation_id
        claim.reconciliation_status = status.lower()
        claim.status = "reconciled" if status == "RECONCILED" else "exception"
        self.add_audit_event(actor, role, "RECONCILED" if status == "RECONCILED" else "RECONCILIATION_EXCEPTION", "claim", str(claim_id), record.model_dump())
        return record

    def submit_claim(self, claim_id: int, request: ClaimSubmissionRequest, actor: str, role: str) -> Dict[str, Any]:
        claim = self.claims[claim_id]
        if not claim.latest_payload_id:
            payload_result = self.build_payload(claim_id, actor, role)
            if payload_result.get("status") == "blocked":
                return payload_result
        idempotency_key = request.idempotency_key or f"{claim.id}:{claim.version}:{str(request.channel).upper()}"
        if idempotency_key in self.idempotency_index:
            submission_id = self.idempotency_index[idempotency_key]
            response = next((item for item in self.responses.values() if item.submission_id == submission_id), None)
            submission = self.submissions[submission_id]
            return {"claim_id": claim.id, "claim_number": claim.claim_number, "channel": submission.channel, "submission_status": claim.submission_status, "submission_id": submission.submission_id, "correlation_id": submission.correlation_id, "response": response.model_dump() if response else None, "idempotent_replay": True}

        channel = str(request.channel).upper()
        submission = Submission(
            submission_id=new_ref("sub"),
            claim_id=claim.id,
            claim_version=claim.version,
            channel=channel,  # type: ignore[arg-type]
            correlation_id=new_ref("corr"),
            idempotency_key=idempotency_key,
            status="SUBMITTED",
            attempts=1,
            created_at=utc_now(),
            updated_at=utc_now(),
        )
        self.submissions[submission.submission_id] = submission
        self.idempotency_index[idempotency_key] = submission.submission_id
        claim.latest_submission_id = submission.submission_id
        claim.submission_channel = channel.lower()
        claim.submission_status = "submitted"
        claim.status = "submitted"
        self._add_transport_log(submission.submission_id, "ENQUEUED", {"channel": channel, "idempotency_key": idempotency_key})
        if channel == "SWITCH":
            self._add_transport_log(submission.submission_id, "SWITCH_TRANSFORM", {"payload_id": claim.latest_payload_id, "mode": "PHISC simulation"})
        self._add_transport_log(submission.submission_id, "SENT", {"correlation_id": submission.correlation_id, "payload_id": claim.latest_payload_id})

        response = self._simulate_response(claim, submission)
        claim.latest_response_id = response.response_id
        if response.status == "ACK":
            claim.submission_status = "acknowledged"
            claim.status = "acknowledged"
            self.adjudicate(claim_id, actor, role)
            self.generate_remittance(claim_id, actor, role)
            self.reconcile(claim_id, actor, role)
        elif response.status == "REJ":
            claim.submission_status = "rejected"
            claim.status = "rejected"
        else:
            claim.submission_status = "pended"
            claim.status = "pended"

        self.add_audit_event(actor, role, "CLAIM_SUBMITTED", "claim", str(claim_id), {"submission_id": submission.submission_id, "channel": channel, "response_status": response.status})
        self.add_audit_event(actor, role, "RESPONSE_RECEIVED", "claim", str(claim_id), {"response_id": response.response_id, "status": response.status})
        return {
            "claim_id": claim.id,
            "claim_number": claim.claim_number,
            "channel": channel,
            "submission_status": claim.submission_status,
            "submission_id": submission.submission_id,
            "correlation_id": submission.correlation_id,
            "response": response.model_dump(),
            "transport_logs": [item.model_dump() for item in self.get_transport_logs_for_submission(submission.submission_id)],
        }

    def get_transport_logs_for_submission(self, submission_id: str) -> List[TransportLog]:
        return sorted(
            [item for item in self.transport_logs.values() if item.submission_id == submission_id],
            key=lambda item: item.created_at,
        )

    def get_claim_remittance(self, claim_id: int) -> Dict[str, Any]:
        claim = self.claims[claim_id]
        if not claim.latest_remittance_id:
            return {"claim_id": claim.id, "status": claim.remittance_status, "reference": "PENDING", "remittance": None}
        remittance = self.remittances[claim.latest_remittance_id]
        return {"claim_id": claim.id, "status": claim.remittance_status, "reference": remittance.payment_batch_ref, "remittance": remittance.model_dump()}

    def get_claim_reconciliation(self, claim_id: int) -> Dict[str, Any]:
        claim = self.claims[claim_id]
        if not claim.latest_reconciliation_id:
            return {"claim_id": claim.id, "status": claim.reconciliation_status, "reconciliation": None}
        record = self.reconciliations[claim.latest_reconciliation_id]
        return {"claim_id": claim.id, "status": claim.reconciliation_status, "reconciliation": record.model_dump()}

    def list_payments(self) -> List[Dict[str, Any]]:
        return [item.model_dump() for item in sorted(self.payments.values(), key=lambda item: item.id or 0)]

    def get_payment(self, payment_id: int) -> PaymentRecord:
        return self.payments[payment_id]

    def create_payment(self, data: Dict[str, Any], actor: str, role: str) -> Dict[str, Any]:
        payment = PaymentRecord(
            id=self.next_numeric("payment"),
            claim_id=int(data["claim_id"]),
            amount=float(data["amount"]),
            payment_date=data["payment_date"],
            method=data.get("method", "EFT"),
            status=data.get("status", "pending"),
            created_at=utc_now(),
        )
        self.payments[payment.id] = payment
        self.add_audit_event(actor, role, "PAYMENT_CREATED", "payment", str(payment.id), payment.model_dump())
        return payment.model_dump()

    def update_payment(self, payment_id: int, data: Dict[str, Any], actor: str, role: str) -> Dict[str, Any]:
        updated = self.payments[payment_id].model_copy(update={**data, "id": payment_id})
        self.payments[payment_id] = updated
        self.add_audit_event(actor, role, "PAYMENT_UPDATED", "payment", str(payment_id), updated.model_dump())
        return updated.model_dump()

    def get_claim_diff(self, claim_id: int) -> Dict[str, Any]:
        versions = self.claim_versions.get(claim_id, [])
        if len(versions) < 2:
            return {"changed_fields": [], "from_version": None, "to_version": versions[-1].version if versions else None}
        previous = self.claim_history.get(f"{claim_id}:{versions[-2].version}", {})
        current = self.claim_history.get(f"{claim_id}:{versions[-1].version}", {})
        changed_fields = []
        for key in sorted(set(previous) | set(current)):
            if previous.get(key) != current.get(key):
                changed_fields.append({"field": key, "from": previous.get(key), "to": current.get(key)})
        return {"from_version": versions[-2].version, "to_version": versions[-1].version, "changed_fields": changed_fields}

    def get_evidence_packet(self, claim_id: int) -> Dict[str, Any]:
        claim = self.claims[claim_id]
        return {
            "claim": self.get_claim(claim_id),
            "documents": ["snapshot.json", "decision_bundles.json", "pmb_decision.json", "pmb_routing.json", "costing_preview.json", "payloads.json", "submissions.json", "responses.json", "remittance.json", "reconciliation.json"],
            "snapshot": self.billing_snapshots[claim.latest_snapshot_id].model_dump() if claim.latest_snapshot_id else None,
            "decision_bundles": [item.model_dump() for item in self.get_decision_bundles_for_claim(claim_id)],
            "pmb_decisions": self.get_pmb_decisions_for_claim(claim_id),
            "benefit_route_decisions": self.get_benefit_route_decisions_for_claim(claim_id),
            "costing_previews": self.get_costing_previews_for_claim(claim_id),
            "payloads": [item.model_dump() for item in self.payloads.values() if item.claim_id == claim_id],
            "submissions": [item.model_dump() for item in self.submissions.values() if item.claim_id == claim_id],
            "transport_logs": [item.model_dump() for item in self.transport_logs.values() if self.submissions[item.submission_id].claim_id == claim_id],
            "responses": [item.model_dump() for item in self.responses.values() if item.claim_id == claim_id],
            "financial_bundles": [item.model_dump() for item in self.financial_bundles.values() if item.claim_id == claim_id],
            "remittances": [item.model_dump() for item in self.remittances.values() if item.claim_id == claim_id],
            "reconciliations": [item.model_dump() for item in self.reconciliations.values() if item.claim_id == claim_id],
            "audit_events": [item.model_dump() for item in self.audit_events.values() if item.entity_type == "claim" and item.entity_id == str(claim_id)],
            "version_diff": self.get_claim_diff(claim_id),
        }

    def get_payload_for_claim_version(self, claim_id: int, version: int) -> Dict[str, Any]:
        payloads = [
            item
            for item in self.payloads.values()
            if item.claim_id == claim_id and item.claim_version == version
        ]
        if not payloads:
            raise KeyError(f"No payload found for claim {claim_id} version {version}")
        return sorted(payloads, key=lambda item: item.created_at)[-1].model_dump()

    def list_audit_events(self) -> List[Dict[str, Any]]:
        events = sorted(self.audit_events.values(), key=lambda item: item.timestamp, reverse=True)
        return [{"id": item.audit_event_id, "action": item.event_type, "resource": f"{item.entity_type}:{item.entity_id}", "username": item.actor, "user_id": item.actor, "timestamp": item.timestamp, "details": json.dumps(item.detail, default=str), "policy_profile_id": item.policy_profile_id, "policy_version": item.policy_version} for item in events]

    def get_audit_event(self, audit_event_id: str) -> Dict[str, Any]:
        return self.audit_events[audit_event_id].model_dump()

    def list_policy_profiles(self) -> List[Dict[str, Any]]:
        rows = []
        for items in self.policy_profiles.values():
            rows.extend(item.model_dump() for item in sorted(items, key=lambda value: value.version))
        return rows

    def create_policy_version(self, policy_profile_id: str, actor: str, role: str) -> Dict[str, Any]:
        latest = sorted(self.policy_profiles[policy_profile_id], key=lambda item: item.version)[-1]
        draft = latest.model_copy(update={"version": latest.version + 1, "status": "DRAFT", "approved_by": None, "approved_at": None})
        self.policy_profiles[policy_profile_id].append(draft)
        self.add_audit_event(actor, role, "POLICY_VERSION_CREATED", "policy_profile", policy_profile_id, {"version": draft.version})
        return draft.model_dump()

    def update_policy_profile(self, policy_profile_id: str, version: int, patch: PolicyProfilePatch, actor: str, role: str) -> Dict[str, Any]:
        versions = self.policy_profiles[policy_profile_id]
        for index, item in enumerate(versions):
            if item.version != version:
                continue
            payload = item.model_dump()
            changes = patch.model_dump(exclude_none=True)
            if "runtime_toggles" in changes:
                payload["runtime_toggles"] = {**payload["runtime_toggles"], **changes["runtime_toggles"]}
                del changes["runtime_toggles"]
            payload.update(changes)
            if payload.get("approved_by") and not payload.get("approved_at"):
                payload["approved_at"] = utc_now()
            updated = PolicyProfile(**payload)
            versions[index] = updated
            self.add_audit_event(actor, role, "POLICY_PROFILE_UPDATED", "policy_profile", f"{policy_profile_id}:v{version}", updated.model_dump())
            return updated.model_dump()
        raise KeyError(f"Policy profile version not found: {policy_profile_id} v{version}")

    def activate_policy_profile(self, policy_profile_id: str, version: int, actor: str, role: str) -> Dict[str, Any]:
        activated = None
        for index, item in enumerate(self.policy_profiles[policy_profile_id]):
            if item.version == version:
                activated = item.model_copy(update={"status": "ACTIVE"})
                self.policy_profiles[policy_profile_id][index] = activated
            elif item.status == "ACTIVE":
                self.policy_profiles[policy_profile_id][index] = item.model_copy(update={"status": "APPROVED"})
        if activated is None:
            raise KeyError(f"Policy profile version not found: {policy_profile_id} v{version}")
        self.settings["policy_profile_id"] = policy_profile_id
        self.settings["policy_version"] = version
        self.add_audit_event(actor, role, "POLICY_PROFILE_ACTIVATED", "policy_profile", f"{policy_profile_id}:v{version}", activated.model_dump())
        return activated.model_dump()

    def list_rules(self) -> List[Dict[str, Any]]:
        return [item.model_dump() for item in self.rule_definitions.values()]

    def update_rule(self, rule_id: str, patch: RulePatch, actor: str, role: str) -> Dict[str, Any]:
        updated = self.rule_definitions[rule_id].model_copy(update=patch.model_dump(exclude_none=True))
        self.rule_definitions[rule_id] = updated
        self.add_audit_event(actor, role, "RULE_UPDATED", "rule", rule_id, updated.model_dump())
        return updated.model_dump()

    def list_reports(self) -> Dict[str, Any]:
        reports = [item.model_dump() for item in sorted(self.reports.values(), key=lambda item: item.generated_at, reverse=True)]
        return {"reports": reports}

    def generate_report(self, report_type: str, period: str) -> Dict[str, Any]:
        if report_type == "audit":
            summary: Dict[str, Any] = {}
            for event in self.audit_events.values():
                summary[event.event_type] = summary.get(event.event_type, 0) + 1
        elif report_type == "reconciliation":
            summary = {"reconciled": 0, "partial": 0, "exception": 0}
            for item in self.reconciliations.values():
                summary[item.status.lower()] += 1
        elif report_type == "rule_hits":
            summary = {}
            for bundle in self.decision_bundles.values():
                for hit in bundle.rule_hits:
                    summary[hit.reason_code] = summary.get(hit.reason_code, 0) + 1
        else:
            summary = {
                "claims_total": len(self.claims),
                "ready_to_close": sum(1 for item in self.claims.values() if item.status == "ready_to_close"),
                "blocked": sum(1 for item in self.claims.values() if item.status == "blocked"),
                "rejected_or_pended": sum(1 for item in self.claims.values() if item.status in {"rejected", "pended"}),
                "reconciliation_exceptions": sum(1 for item in self.claims.values() if item.reconciliation_status == "exception"),
            }
        report = Report(id=self.next_numeric("report"), name=f"{report_type}-{period}", report_type=report_type, generated_at=utc_now(), period=period, summary=summary)
        self.reports[report.id] = report
        return report.model_dump()

    def get_report(self, report_id: int) -> Dict[str, Any]:
        return self.reports[report_id].model_dump()

    def list_worklist(self) -> List[Dict[str, Any]]:
        items = []
        for claim in self.claims.values():
            if claim.status not in {"rejected", "pended", "validation_exception", "blocked", "exception"}:
                continue
            reasons = [hit.reason_code for bundle in self.get_decision_bundles_for_claim(claim.id) for hit in bundle.rule_hits if bundle.claim_version == claim.version]
            if claim.latest_response_id:
                reasons.extend(reason.reason_code for reason in self.responses[claim.latest_response_id].reasons)
            items.append({"claim_id": claim.id, "claim_number": claim.claim_number, "status": claim.status, "reasons": sorted(set(reasons)), "next_action": self._next_action(claim)})
        return items

    def _next_action(self, claim: ClaimRecord) -> str:
        if claim.status == "blocked":
            return "Resolve readiness blockers and rerun readiness."
        if claim.status == "validation_exception":
            return "Correct draft data and create a new claim version."
        if claim.status == "rejected":
            return "Review scheme rejection reasons and resubmit a corrected version."
        if claim.status == "pended":
            return "Upload supporting evidence or motivation and resubmit."
        if claim.status == "exception":
            return "Review remittance and reconcile financial mismatches."
        return "Review claim."

    def get_settings(self) -> Dict[str, Any]:
        settings = deepcopy(self.settings)
        settings["policy_profiles"] = self.list_policy_profiles()
        settings["rule_definitions"] = self.list_rules()
        return settings

    def update_settings(self, payload: Dict[str, Any], actor: str, role: str) -> Dict[str, Any]:
        if "retention" in payload and isinstance(payload["retention"], dict):
            self.settings["retention"].update(payload["retention"])
        if "throughput_target" in payload and isinstance(payload["throughput_target"], dict):
            self.settings["throughput_target"].update(payload["throughput_target"])
        for key in {"scheme", "option", "policy_profile_id", "policy_version", "demo_mode"}:
            if key in payload:
                self.settings[key] = payload[key]
        self.add_audit_event(actor, role, "SETTINGS_UPDATED", "settings", "global", payload)
        return self.get_settings()

    def dashboard_summary(self) -> Dict[str, Any]:
        claims = list(self.claims.values())
        top_rule_hits: Dict[str, int] = {}
        for bundle in self.decision_bundles.values():
            for hit in bundle.rule_hits:
                top_rule_hits[hit.reason_code] = top_rule_hits.get(hit.reason_code, 0) + 1
        return {
            "ready_to_close": sum(1 for item in claims if item.status == "ready_to_close"),
            "ready_to_submit": sum(1 for item in claims if item.status == "ready_to_submit"),
            "rejected_or_pended": sum(1 for item in claims if item.status in {"rejected", "pended"}),
            "reconciliation_exceptions": sum(1 for item in claims if item.reconciliation_status == "exception"),
            "top_rule_hits": top_rule_hits,
            "worklist": self.list_worklist()[:6],
            "active_policy": {"profile": self.settings.get("policy_profile_id"), "version": self.settings.get("policy_version")},
        }
