# Verification Checklist

Date completed: `2026-04-17`

- [x] `DIAGNOSIS_LINK_MISSING` returns `reason_code`, user message, remediation hint, affected line IDs, and actionable navigation metadata.
- [x] Line-item diagnosis-link updates persist to Postgres and write `DIAGNOSIS_LINK_UPDATED` audit evidence.
- [x] Post-closure validation automatically reruns after diagnosis-link remediation and clears the warning when all billable lines are linked.
- [x] Patient registry exposes a claim-ready profile with membership, provider, visit, diagnoses, charge capture, attachments, consent, and claim status timeline.
- [x] Structured payload endpoint returns stage tiles with completeness state and remediation actions.
- [x] Pseudo-EDI supports generate, validate, download, and submit.
- [x] EDI actions persist artefacts and write transport logs.
- [x] PMB detection uses configured Postgres mappings and returns explanation for both match and no-match paths.
- [x] No-match PMB responses expose evaluated ICD-10s, mapping version, effective date, and PMB mapping admin navigation metadata.
- [x] PMB mapping reference data exists in Postgres and simulation is callable through the admin endpoint.
- [x] Runtime proof includes API responses and direct Postgres queries.
- [x] Backend regression suite passes in Docker.
