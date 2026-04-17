# Patch Plan

Date executed: `2026-04-17`

## Minimal-Risk Order

1. Persistence foundation
   - Add `claim_line_items`, `claim_line_diagnosis_links`, and `edi_artifacts`.
   - Extend PMB decision persistence for explainability fields.
2. Backend remediation paths
   - Add diagnosis-link CRUD and patient claim-context assemblers.
   - Keep PMB and routing decisions server-side and DB-driven.
3. UI resolution flows
   - Make `Jump to line_items` functional.
   - Render patient claim context, structured payload tiles, and actionable EDI controls.
4. PMB admin and no-match explanation
   - Add mapping simulation and CRUD endpoints.
   - Return explicit no-match explanation plus admin action metadata.
5. Proof and regression coverage
   - Add backend tests first.
   - Capture live API proof and direct Postgres proof after runtime seeding.

## Why This Order

- It prevented the UI from depending on unstable or incomplete backend contracts.
- It preserved the existing claim lifecycle while adding new persisted artefacts incrementally.
- It let post-closure remediation reuse the existing claim versioning and snapshot model instead of bypassing it.
