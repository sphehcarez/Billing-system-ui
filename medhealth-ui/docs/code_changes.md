# Code Changes

Date completed: `2026-04-17`

## Backend Persistence And Rules

- `backend/platform_core.py`
  - added persisted claim-line diagnosis linking
  - added patient claim-context and patient timeline assemblers
  - added structured payload tiles
  - added EDI generate, validate, download, and submit flows
  - extended PMB explainability and no-match remediation metadata
- `backend/postgres_store.py`
  - persists line items, diagnosis links, EDI artefacts, PMB explainability fields, and transport artefact references
- `backend/db_schema.py`
  - added `claim_line_items`
  - added `claim_line_diagnosis_links`
  - added `edi_artifacts`
  - extended `pmb_decisions` and `transport_logs`
- `backend/alembic/versions/20260416_0002_pmb_explainability_fields.py`
  - made PMB explainability migration existence-safe
- `backend/alembic/versions/20260416_0003_resolution_paths_payload_edi.py`
  - adds line diagnosis linkage, EDI artefacts, and PMB explainability storage

## API Surface

- `backend/platform_api.py`
  - added patient claim-context and timeline endpoints
  - added line-item diagnosis-link endpoints
  - added structured payload endpoint
  - added EDI generate, validate, download, and submit endpoints
  - added claim transport-log endpoint
  - added PMB mapping simulate and CRUD endpoints

## Seed And Demo Data

- `backend/demo_seed.py`
  - ensures seeded claims carry claim-context basics such as clinical summary and reference mappings

## UI

- `claim_detail.html`
  - added a functional line-items remediation section
  - replaced raw payload code with tile rendering targets
  - replaced passive pseudo-EDI preview with a submission tool panel
- `patients.html`
  - added patient claim-context and timeline containers
- `settings.html`
  - added PMB Mapping Admin controls
- `js/api-client.js`
  - added client methods for the new endpoints
- `js/app.js`
  - wired diagnosis-link remediation
  - rendered patient claim-carry context
  - rendered structured payload tiles
  - enabled EDI actions and transport-log timeline
  - exposed PMB mapping simulation and admin CRUD flows

## Tests

- `backend/tests/test_persistence_runtime.py`
  - covers diagnosis-link remediation, patient claim-context, structured payloads, EDI persistence, and PMB no-match explanation
- `backend/tests/test_platform_core.py`
  - covers PMB evaluation order
- `backend/tests/test_ui_validation_modal.py`
  - keeps the UI contract smoke test and skips cleanly when frontend assets are not present in the backend test image
