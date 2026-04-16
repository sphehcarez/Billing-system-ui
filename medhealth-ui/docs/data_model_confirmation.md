# Data Model Confirmation

## Core Lifecycle

- `claims`
  - current claim version and lifecycle status
  - links to patient, provider, snapshot, submission, remittance, reconciliation, PMB/routing/costing latest rows
- `claim_drafts`
  - latest mutable draft payload for each claim
- `claim_versions`
  - immutable version history plus change summary and stored version payload
- `billing_snapshots`
  - append-only snapshot taken at closure

## Rules And Decisions

- `rule_definitions`
  - rule metadata, severity, decision table JSON
- `policy_profiles`
  - scheme/option configuration and rule activation state
- `decision_bundles`
  - persisted rule outcomes for readiness, closure, and post-closure stages
- `readiness_runs`
  - persisted validation run plus itemized results

## ICD-10 / PMB / Costing Reference

- `icd10_reference`
- `pmb_conditions`
- `icd10_pmb_mappings`
- `benefit_route_rules`
- `tariff_rates`
- `pmb_payment_policies`

## Captured Clinical Coding

- `claim_diagnoses`
  - one-to-many from claims
  - indexed by `(claim_id, is_primary)`

## Persisted Decisions

- `pmb_decisions`
- `benefit_routing_decisions`
- `costing_previews`

## Submission And Financial Flow

- `payloads`
- `submissions`
  - unique `idempotency_key`
- `transport_logs`
- `responses`
- `financial_bundles`
- `remittances`
- `reconciliations`
- `reconciliation_exceptions`
- `ledger_entries`
- `payments`

## Audit / Reporting / Config

- `audit_events`
- `reports`
- `reference_versions`
- `app_settings`

## Key Relationships

- `claims.patient_id -> patients.id`
- `claims.provider_id -> providers.id`
- `claim_drafts.claim_id -> claims.id`
- `claim_versions.claim_id -> claims.id`
- `billing_snapshots.claim_id -> claims.id`
- `claim_diagnoses.claim_id -> claims.id`
- `claim_diagnoses.icd10_code -> icd10_reference.code`
- `icd10_pmb_mappings.icd10_code -> icd10_reference.code`
- `icd10_pmb_mappings.pmb_condition_id -> pmb_conditions.condition_id`
- `pmb_decisions.claim_id -> claims.id`
- `benefit_routing_decisions.pmb_decision_id -> pmb_decisions.decision_id`
- `costing_previews.pmb_decision_id -> pmb_decisions.decision_id`
- `costing_previews.routing_decision_id -> benefit_routing_decisions.decision_id`
- `payloads.snapshot_id -> billing_snapshots.snapshot_id`
- `submissions.claim_id -> claims.id`
- `transport_logs.submission_id -> submissions.submission_id`
- `responses.submission_id -> submissions.submission_id`
- `remittances.claim_id -> claims.id`
- `reconciliations.claim_id -> claims.id`
- `reconciliation_exceptions.reconciliation_id -> reconciliations.reconciliation_id`

## Required Indexes Confirmed In Schema

- `claims(status)`
- `billing_snapshots(claim_id, claim_version)` unique
- `submissions(idempotency_key)` unique
- `claim_diagnoses(claim_id, is_primary)`
- `icd10_pmb_mappings(icd10_code, active, effective_from, effective_to)`
