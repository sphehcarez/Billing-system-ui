# Current-State Assessment

## What Exists Today

- Docker-backed runtime with:
  - `frontend` on port `8000`
  - `backend` on port `8001`
  - `db` on port `5432`
- Postgres-backed persistence for the core claims platform:
  - claims, drafts, versions, immutable billing snapshots
  - ICD-10 reference, PMB conditions, ICD10 to PMB mappings
  - benefit routing rules, tariff rates, PMB payment policies
  - decision bundles, readiness runs, PMB decisions, routing decisions, costing previews
  - submissions, transport logs, responses
  - remittances, reconciliations, reconciliation exceptions, ledger entries
  - audit events and dynamic evidence packets
- Backend API coverage for:
  - patients, providers, users
  - claims lifecycle, diagnoses CRUD, readiness, closure, post-closure validation
  - payload generation, submissions, remittance, reconciliation
  - policies, rules, reports, audit, settings, reference data
- UI coverage for:
  - claim detail diagnosis capture
  - readiness modal with blockers/warnings/info
  - jump-to-diagnoses behaviour
  - PMB/routing/costing display
- Deterministic seed support:
  - demo reference data
  - repeatable UAT scenarios
- Docker-backed verification:
  - `/health` checks DB connectivity
  - `pytest` passes against live Postgres

## What Is Implemented Well

- Readiness blockers are structured and already include machine reason codes, remediation, and a navigation action for the primary ICD blocker.
- PMB detection, benefit routing, and costing preview are driven from persisted reference/config data rather than UI logic.
- Idempotent claim submission is persisted and proven.
- Remittance and reconciliation persistence is present and tested.
- Audit evidence is emitted across the major claims lifecycle transitions.

## What Is Still Thin Or Missing

- Clinical/practice workflow breadth:
  - no first-class appointment scheduling, waitlist, encounter, vitals, notes, prescription, or document persistence model yet
  - no persistent patient-wide clinical timeline/search surface
- Provider operations breadth:
  - no first-class practices, provider registrations, or availability calendar model
- Formal proof-pack split:
  - proof existed in a single runtime document, not separate before/after proof-pack files
- Architecture/program docs:
  - runtime map existed, but current-state, gap table, target architecture, and phased implementation docs were not yet present
- Interoperability stubs:
  - no HL7 v2 ingest simulator
  - no C-CDA visit summary generator
  - no explicit switch connector abstraction beyond the current simulated submission flow

## Repository Shape

- Backend domain logic lives primarily in `backend/platform_core.py`
- API surface lives in `backend/platform_api.py`
- Postgres persistence wrapper lives in `backend/postgres_store.py`
- Schema metadata lives in `backend/db_schema.py`
- Runtime DB config lives in `backend/db_runtime.py`
- Demo seed logic lives in `backend/demo_seed.py` and `infra/seed/`
- UI claim workflow lives in `js/app.js`, `js/api-client.js`, and `claim_detail.html`

## Net Assessment

The repo is no longer a UI-only or in-memory prototype. It already behaves like a persistent claims platform for the claim lifecycle, PMB/routing/costing, submission, remittance, reconciliation, and audit trail. The remaining work is mainly to widen the platform into the upstream clinical/practice workflow and interoperability layers, while preserving the current deterministic claims core.
