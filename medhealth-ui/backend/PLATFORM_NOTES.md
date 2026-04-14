# Medhealth Claims Rules Platform

This backend now follows a rules-driven lifecycle rather than UI-driven claim outcomes.

## Lifecycle

1. Draft claim capture
2. Readiness rules and checklist
3. Closure gate and immutable billing snapshot
4. Post-closure validation
5. Canonical claim + pseudo-EDI + PHISC XML payload generation
6. Submission with idempotency and transport logs
7. ACK / REJ / PEND response persistence
8. Adjudication and financial bundle creation
9. Remittance generation
10. Reconciliation and exception management
11. Evidence packet export

## Runtime governance

- Rule definitions are stored as decision-table metadata.
- Policy profiles are versioned and activated at runtime.
- The active policy controls ICD enforcement, preauth rules, warning overrides, member format rules, and default routing.
- Every lifecycle stage writes immutable decision bundles and audit events.

## Seeded scenarios

- Clean success to reconciled
- Missing ICD blocks readiness and closure
- Missing discharge blocks inpatient closure
- Missing authorisation blocks under active policy
- Invalid member format rejects on submission
- Modifier sequencing fails post-closure validation
- Missing attachment pends after submission
- Partial payment remittance
- Reconciliation mismatch exception
- Rejected v1 corrected to v2 and paid

## Schema and retention

- `migrations/001_initial_schema.sql` provides the relational schema scaffold.
- The live API exposes `schema_registry` and `retention_matrix` via `/api/settings`.
- Default retention is 7 years for evidence-bearing artifacts unless overridden by contract or legal policy.
