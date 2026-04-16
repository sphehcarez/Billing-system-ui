# Implementation Plan

## Phase 1: Stabilise The Existing Claims Core

- keep Postgres as the only source of truth for claim lifecycle artefacts
- maintain Docker, Alembic, seed scripts, and live runtime proof
- preserve server-side RBAC and structured validation output
- keep PMB/routing/costing logic entirely backend-driven

## Phase 2: Tighten The Existing UX/API Contract

- standardise action metadata for readiness blockers
- widen PMB explainability fields so UI and evidence packets expose:
  - condition name
  - system auto-flagged yes/no
- preserve deterministic tests for readiness, evidence, and idempotent submission

## Phase 3: Add Practice And Clinical Persistence

- introduce first-class practice/clinical tables and models for:
  - membership and consent
  - appointments and waitlist
  - encounters, vitals, notes, prescriptions, documents
  - provider operations such as practices and availability
- expose aggregate patient-record endpoints and search
- close encounters into claim-prep payloads

## Phase 4: Extend Interoperability Simulation

- add HL7 v2 ingest simulator with deterministic parsing
- add simplified C-CDA visit summary generation
- formalise switch/direct connector adapter stubs

## Phase 5: Expand Proof Pack And UI Evidence

- keep `runtime_proof_before.md` and `runtime_proof_after.md` current
- add reproducible UI screenshot or click-path references
- prove any newly added clinical workflow through API plus DB queries

## Phase 6: Lock In Regression Gates

- extend unit tests for any new clinical services
- add integration tests for visit-to-claim preparation
- add UI checks for readiness-to-diagnosis navigation and refreshed PMB panel data

## Minimal-Risk Execution Rules

- evolve schema only through Alembic revisions
- keep new tables additive when possible
- prefer extending the existing `PlatformStore`/`PersistentPlatformStore` seam
- avoid moving claims business logic into the UI
- use demo-labelled reference data whenever business-owned data is unavailable
