# Codex Repo-First Implementation Prompt

Use this prompt in a new Codex thread from the repository root.

```text
Project: Med Directory Practice Management + EMR + Billing + Rules Engine + Scheme Claims

ROLE
You are Codex running inside VS Code as a senior healthcare claims-platform engineer and enterprise architect. Work repo-first. Apply changes directly to this existing repository. Do not generate an unrelated greenfield project unless the repo is empty.

FIRST ACTIONS
1. Detect and read repo guidance before changing files:
   - AGENTS.md
   - .agents/skills/claims-pmb-assessment/SKILL.md if available
   - Any README, API testing, deployment, backend notes, migrations, and tests
2. Report briefly which guidance files were detected.
3. Inspect the current backend, UI, API surface, migrations, tests, and seed/demo data.
4. Identify what already exists and what is missing before editing.

PRIMARY OBJECTIVE
Upgrade the existing healthcare claims platform into a production-grade Practice Management + EMR + Billing + Rules Engine + Scheme Claims platform with:
- provider discovery and booking
- patient onboarding and intake
- queue management
- EMR encounters and clinical notes
- ICD-10 validation
- ICD-10 to PMB auto-flagging
- PMB benefit routing
- readiness and closure validation
- billing snapshot and claim versioning
- payload generation
- direct/switch submission with idempotency
- ACK/REJ/PEND response handling
- remittance and reconciliation
- reporting
- drillable audit and evidence packet
- minimal polished role-based UI

NON-NEGOTIABLES
- Apply changes to the existing codebase. Do not just describe the design.
- All business outcomes must come from backend services, not frontend hard-coding.
- Do not hard-code PMB logic in UI components or controllers.
- Do not invent real medical scheme policy. If PMB mappings, tariffs, benefit buckets, scheme constraints, or authorisation rules are missing, create clearly labelled placeholder configuration and document the required business-owned reference data.
- Enforce server-side RBAC. UI permissions are secondary.
- Every validation failure must return:
  - severity
  - machine-readable reason code
  - user-facing message
  - remediation guidance
  - affected fields
- Every PMB flag must explain:
  - trigger ICD-10
  - mapping rule
  - PMB condition
  - whether the provider marked PMB
  - route decision
  - action taken
  - evidence gaps
- Every material lifecycle transition must write an audit event.
- Preserve immutability: decision bundles and closed billing snapshots are append-only evidence.
- Re-submissions or corrections must create claim versions rather than overwriting historical evidence.
- Preserve idempotency for submissions.
- Avoid unnecessary PHI in logs, audit events, UI summaries, and transport logs.

TARGET STACK
Use the existing stack unless there is a compelling reason to change it:
- Python 3.11-compatible FastAPI backend
- Pydantic v2 models where applicable
- SQLAlchemy 2.0 and Alembic migrations if persistence exists or is introduced
- PostgreSQL-ready schema
- Redis/Celery scaffold only if practical in the current repo
- Static HTML/CSS/JS UI served locally
- JWT auth and server-side RBAC

ARCHITECTURE BOUNDARIES
Maintain clear bounded contexts even in a modular monolith:
- Clinical Context: EMR, encounters, notes, vitals, prescriptions, attachments
- Directory Context: providers, practices, specialties, availability
- Booking Context: appointments, queue entries, reminders placeholder
- Claims Context: claim drafts, versions, readiness, closure, snapshots, payloads
- Rules Engine Context: policy profiles, decision tables, rule hits, decision bundles
- Coding Context: ICD-10 validation and diagnosis linkage
- PMB Context: ICD-10 to PMB mapping, PMB flags, evidence requirements
- Benefit Routing Context: PMB benefit, normal benefit, or PMB review path
- Billing Context: tariff pricing, totals, financial bundles, ledger entries
- Submission Context: direct/switch/batch, idempotency, correlation IDs, transport logs
- Remittance/Reconciliation Context: remittance advice, matching, partials, exceptions
- Audit/Evidence Context: audit events, drilldown, evidence packet

DOMAIN MODULES TO IMPLEMENT OR COMPLETE
Inspect existing files first, then implement missing minimum viable functionality:
1. Medical Directory
2. Booking and Scheduling
3. Queue Management
4. Patient Onboarding and Intake
5. EMR patient file and encounters
6. Clinical notes and AI-assist placeholder with human approval required
7. eScript placeholder storing prescriptions
8. ICD-10 and diagnosis support
9. PMB detection and routing
10. Billing and claims management
11. Direct/Switch/Batch submission and response handling
12. Payments, remittance advice, reconciliation, exceptions
13. Reporting and analytics
14. Audit and evidence packet

MINIMUM ENTITIES
Add or validate models/tables for:
- User, Role
- Provider, Practice, Speciality, ProviderAvailability
- Patient, Member, Dependant, Consent
- Appointment, QueueEntry
- Encounter, ClinicalNote, VitalSigns, Attachment, LabResult, Referral, Letter
- Prescription
- ICD10CodeSelection, DiagnosisLink
- PMBFlag, PMBEvidence
- TariffCode, PriceList, BenefitOption, EligibilityRecord
- ClaimDraft, ClaimVersion, BillingSnapshot
- ReadinessRun, ReadinessItemResult
- PolicyProfile, RuleDefinition, PolicyVersionApproval
- CanonicalClaim, PseudoEDIMessage
- Submission, TransportLog, ResponseMessage
- RemittanceAdvice, RemittanceLine
- ReconciliationRecord, ReconciliationException
- LedgerEntry
- AuditEvent, EvidencePacket

CLAIM LIFECYCLE STATE MACHINE
Implement or align to one coherent model:
OPEN
→ READY_TO_CLOSE
→ CLOSED_FOR_BILLING or CLOSED_FOR_BILLING_WITH_WARNINGS
→ READY_TO_SUBMIT
→ SUBMITTED
→ ACKNOWLEDGED / REJECTED / PENDED
→ ADJUDICATED
→ REMITTED
→ PAID / PARTIALLY_PAID
→ RECONCILED / RECONCILIATION_EXCEPTION

RULES ENGINE REQUIREMENTS
Implement or strengthen a policy-driven rules engine:
- Policy profiles per scheme and plan option
- Policy versioning and effective dating
- Rule definitions as decision tables stored as JSON/config
- Rule fields:
  ruleId, stage, category, severity, reasonCode, message, remediationHint, affectedFields, enabled
- Deterministic evaluator producing DecisionBundle with:
  outcome, rule hits, input hash, reference versions, created timestamp, actor/service
- Stages:
  intake completeness
  clinical closure gate
  billing readiness
  PMB detection and evidence requirements
  submission validation
  post-submission response routing
- Persist DecisionBundles and link them to claim, claim version, and snapshot where applicable.
- Overrides require approver, reason, and audit event.

ICD-10 AND PMB REQUIREMENTS
Implement or complete:
- ICD-10 required for readiness/closure
- ICD-10 format validation
- ICD-10 configured reference membership validation
- Primary/secondary diagnosis handling where supported
- Diagnosis linkage to claim lines where required
- ICD-10 to PMB mapping repository with versioning/effective dates
- PMB condition metadata repository
- PMB auto-flagging even when provider_pmb_indicator is false or absent
- Benefit routing decision:
  - PMB_BENEFIT when safe and configured
  - PMB_REVIEW when evidence is missing or mapping confidence/route is unsafe
  - NORMAL_BENEFIT when no PMB mapping matches
- Persist PMB/benefit route decisions and include them in audit and evidence packet.

BILLING SERVICE REQUIREMENTS
Billing must:
- Trigger from encounter/claim closure and readiness success
- Create immutable billing snapshot
- Create claim lines from clinical-to-billable mapping or explicit claim draft lines
- Apply tariff pricing and totals from configurable price lists
- Generate CanonicalClaim and Pseudo-EDI payloads
- Support versioning and resubmission
- Create immutable ledger entries for postings and adjustments

SUBMISSION SERVICE REQUIREMENTS
Implement:
- Direct submission path
- Switch submission path with intermediary transform/log step
- Batch submission placeholder
- Idempotency key enforcement
- Correlation ID generation
- Transport logs per step
- Response handling for ACK, REJ, and PEND

RESPONSE SIMULATOR
Use deterministic UAT behavior:
- ACK for clean claims
- REJ for blocking rule failures or invalid submission dataset
- PEND for warnings requiring evidence
- Generate simulated adjudication and remittance where applicable

REMITTANCE AND RECONCILIATION
Implement:
- Remittance advice model and retrieval/ingestion placeholder
- Line-level and total-level remittance details
- Paid, partially paid, and mismatch exception scenarios
- Reconciliation matching by claim reference, member number, provider/practice reference, and amount

AUDIT AND EVIDENCE
Implement:
- AuditEvent service/table/model
- Audit event for readiness, closure, snapshot, validation, PMB detection, benefit routing, submission, response, remittance, reconciliation, and overrides
- Audit list and detail APIs
- Evidence packet endpoint bundling:
  draft, snapshot, decision bundles, PMB routing decisions, payloads, submissions/logs, responses, remittance, reconciliation, audit timeline

FRONTEND UI REQUIREMENTS
Use the existing UI unless a page is missing.
Implement or complete:
- Login with demo credentials and role selection
- Role-based navigation
- Dashboard with KPIs
- Claims list
- Claim detail cockpit:
  Run readiness, Close file, Post-closure validate, Payload preview, Submit Direct, Submit Switch, View remittance, Evidence packet
- On-screen action-point modal summaries for readiness/closure/validation failures:
  blockers, warnings, info, reason code, message, remediation, affected fields, PMB route explanation
- Payments view
- Audit view
- Reports view
- Settings/rules/policy profile view
- Branded CSS and logo support

API REQUIREMENTS
Expose or align endpoints:
Auth:
- POST /auth/token or existing login equivalent

Claims lifecycle:
- POST /claims/{id}/readiness/run
- POST /claims/{id}/closure/confirm
- POST /claims/{id}/validation/post-closure
- GET /claims/{id}/payloads/{version}

Submission:
- POST /submissions/claims/{id}?channel=DIRECT|SWITCH&idempotency_key=...
- GET /submissions/{submission_id}/logs

Payments:
- GET /payments/claims/{id}/remittance
- GET /payments/claims/{id}/reconciliation

Audit:
- GET /audit?entity_type=...&entity_id=...
- GET /audit/{audit_event_id}
- GET /audit/claims/{id}/evidence-packet

Directory/Booking/EMR:
- CRUD endpoints for providers, appointments, patients, encounters, notes, ICD-10 selections, and prescriptions.

MIGRATIONS AND SEED DATA
Add or update migrations/schema for all introduced tables.
Seed deterministic UAT scenarios:
1. CLEAN_SUCCESS: ACK → Paid → Reconciled
2. MISSING_ICD_BLOCKS: blocked at readiness/closure
3. MODIFIER_ORPHAN_BLOCKS: blocked at closure/post-closure
4. MEMBERSHIP_INVALID_REJECT: fails post-closure or submission validation
5. PMB_PEND_MISSING_EVIDENCE: PMB detected, evidence missing, PEND/review
6. PARTIAL_PAYMENT: ACK but partially paid
7. MISMATCH_EXCEPTION: ACK but reconciliation exception

Seeds must print or expose demo record IDs where possible.

QUALITY GATES
Add or update tests for:
- Rules evaluator
- Readiness and closure lifecycle
- ICD-10 invalid/missing behavior
- PMB auto-flagging when provider did not mark PMB
- Benefit routing decisions
- Idempotent submission
- Audit events per lifecycle step
- UI modal wiring for validation summaries
- RBAC denial paths

Run verification:
- Backend tests
- Backend syntax/AST parse
- Frontend JS syntax check
- API smoke check if server can run locally

DELIVERABLE RESPONSE ORDER
1. Executive summary
2. Guidance files detected
3. Current-state analysis with key file pointers
4. Technical gap assessment
5. Target architecture and data flow
6. File-by-file changes made
7. Tests added/updated
8. Verification results
9. Remaining production risks and required business-owned reference data

START NOW
Scan the repo, read detected guidance, apply the changes directly, run verification, and report results in the required order.
```
