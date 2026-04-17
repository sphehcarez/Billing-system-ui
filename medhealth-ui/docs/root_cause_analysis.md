# Root Cause Analysis

Date verified: `2026-04-17`

## Diagnosis Linkage

- Root cause
  - Claim line items were only embedded in claim payload structures and were not first-class persisted records.
  - Post-closure validation could warn about missing diagnosis links, but there was no persisted API or UI remediation path to fix them.
- Impact
  - `DIAGNOSIS_LINK_MISSING` was actionable in wording only.
  - PMB explainability had to fall back to claim-level diagnoses because line-level linkage evidence was absent.

## Patient Registry Claim-Carry

- Root cause
  - The patient page exposed patient basics, but not a denormalised claim-ready profile assembled from claim, provider, diagnoses, attachments, consent, and status history.
- Impact
  - Users could not verify whether a patient profile actually carried the prescribed claim submission dataset.
  - Claim follow-up stayed claim-centric instead of patient-centric.

## Canonical Payload Preview

- Root cause
  - Payload preview was treated as a developer debug block rather than a staged claim-completeness view.
- Impact
  - Users could not see which submission stage was complete, which fields were missing, or where to go next.

## Pseudo-EDI Preview

- Root cause
  - Pseudo-EDI existed only as static text in payload output and had no persisted artefact, validation, download, or submission lifecycle.
- Impact
  - The preview did not prove any operational submission capability.
  - No transport evidence was written for EDI generation or validation.

## PMB Mapping Mismatch

- Root cause
  - The no-match path returned a terse PMB result without enough explanation for why a claim did not match.
  - The detector needed to account for claim-level diagnoses first and annotate when line-level linkage limited confirmation.
  - There was no direct admin remediation path exposed from the no-match outcome.
- Impact
  - UI users saw a dead-end `NOT_DETECTED` message instead of a diagnosable configuration or data-capture problem.
  - PMB operations lacked traceable explainability for no-match scenarios.
