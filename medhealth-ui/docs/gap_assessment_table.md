# Gap Assessment Table

| Capability | Current Implementation | Gap | Fix Direction |
|---|---|---|---|
| Runtime map | Present in `docs/runtime_map.md` | None | Keep current and update as entrypoints evolve |
| Postgres persistence foundation | Implemented with SQLAlchemy Core, Alembic, Docker, Postgres-backed store | None for claims core | Keep extending through the same metadata/store seam |
| Claims lifecycle persistence | Implemented end-to-end | None | Maintain regression coverage |
| Readiness blockers with remediation | Implemented | Action metadata was partially generic | Standardised action contract for diagnosis navigation |
| Jump-to-diagnoses UX | Implemented in UI | Needed a clearer machine action target contract | Preserve `diagnoses` target and `NAVIGATE_DIAGNOSES` action type |
| PMB explainability | Implemented with ICD, mapping, condition id/type, route, costing | Missing persisted `condition_name` and explicit `auto_flagged` field | Added persisted explainability fields and surfaced them in UI |
| Benefit routing | Implemented and persisted | None | Keep proof coverage |
| Costing preview | Implemented and persisted | None | Keep proof coverage |
| Submission idempotency | Implemented and tested | None | Keep proof coverage |
| Remittance and reconciliation persistence | Implemented and tested | None | Keep proof coverage |
| Audit trail and evidence packet | Implemented and persisted/dynamic | Evidence packet artefacts are dynamic rather than separately persisted | Acceptable for now; only persist packets if operational need appears |
| Current-state assessment doc | Missing | No explicit assessment artefact | Added `docs/current_state_assessment.md` |
| Gap assessment doc | Missing | No explicit tracked delta vs target platform | Added this document |
| Target architecture doc | Missing | No explicit bounded-context document | Added `docs/target_architecture.md` |
| Implementation plan doc | Missing | No phased execution document | Added `docs/implementation_plan.md` |
| Proof pack split | Single runtime proof doc | Did not match before/after proof-pack shape | Added `runtime_proof_before.md` and `runtime_proof_after.md` |
| Clinical/practice workflow | Minimal patient/provider CRUD only | No first-class appointment/encounter/clinical record pipeline | Next phase: add practice and encounter contexts persistently |
| Single searchable patient record | Partial through claims and patients | No aggregated clinical search/timeline API | Next phase: add patient record aggregate with clinical artefacts |
| Provider operations | Basic provider CRUD only | No practices, registrations, or availability | Next phase: add provider operations model and endpoints |
| HL7 v2 / C-CDA / connector stubs | Not implemented as first-class modules | Missing interoperability simulation layer | Next phase: add inbound simulator and adapter interface |
