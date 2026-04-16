# Target Architecture

## Bounded Contexts

### Practice And Clinical

- patients, membership, dependants, consents
- providers, practices, registrations, availability
- appointments, intake, waitlist
- encounters, vitals, notes, prescriptions, documents

### Claims Context

- claim draft capture
- immutable versions and billing snapshots
- diagnoses and line-level coding links
- readiness, closure, post-closure validation

### Rules And Policy

- policy profiles
- rule definitions
- decision bundles
- readiness items and rule execution evidence

### PMB And Benefit Routing

- ICD-10 reference
- PMB conditions
- ICD10 to PMB mapping
- benefit routing rules
- PMB payment policy
- persisted PMB/routing/costing decisions

### Submission And Switching

- canonical claim payloads
- pseudo-EDI/XML builders
- direct and switch submission channels
- idempotency envelope
- transport logs and responses

### Financials

- financial bundles
- remittances
- reconciliations and exceptions
- immutable ledger entries
- payments and patient balance artefacts

### Audit And Evidence

- audit events
- dynamic evidence packet assembler
- retention and traceability controls

## Event Flow

1. Practice intake creates or updates the patient record.
2. Visit workflow captures encounter facts, diagnoses, prescriptions, and supporting documents.
3. Encounter close prepares claim draft inputs.
4. Readiness runs against persisted claim and reference data.
5. PMB detection, routing, and costing persist explainable decisions.
6. Closure writes an immutable billing snapshot.
7. Post-closure validation confirms the frozen claim state.
8. Payload generation builds canonical and transport artefacts.
9. Submission persists idempotency, correlation, logs, and responses.
10. ACK outcomes flow to remittance simulation and reconciliation.
11. Audit and evidence services assemble the full trail from Postgres.

## Persistence Pattern

- Domain logic remains in `platform_core.py`
- `postgres_store.py` is the persistence-backed orchestration layer
- `db_schema.py` owns SQLAlchemy Core table definitions
- Alembic revisions evolve the schema
- API controllers stay thin and delegate to the store
- UI never computes PMB mappings, benefit routing, or tariff logic

## UI Contract

- UI receives structured validation summaries
- blockers include:
  - `reason_code`
  - `message`
  - `remediation`
  - machine action metadata for navigation
- PMB panel receives:
  - status
  - matched ICD-10
  - mapping id
  - condition id and name
  - provider marked PMB yes/no
  - system auto-flagged yes/no
  - benefit route and reason
  - costing preview and pricing basis

## Deterministic UAT Pattern

- one reference seed script
- one scenario seed script
- seeded natural keys and upsert behaviour
- repeatable docker runtime
- proof pack built from real API calls and `psql` queries
