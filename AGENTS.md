# Medhealth Claims Platform Guidance

This repository implements a healthcare practice management, claims billing, rules-engine, PMB routing, and audit/evidence platform. Treat it as a claims-platform codebase first, not as a UI-only demo.

## Operating Rules

- Inspect the repository before changing code. Identify the backend service, API surface, UI flow, tests, migrations, and current data model before implementing.
- Preserve server-side RBAC. UI hiding is not sufficient; API endpoints must enforce permissions.
- Keep business decisions out of the UI. The frontend may display decisions, validation summaries, PMB explanations, payload previews, and evidence, but it must not determine claim outcomes.
- Do not invent medical policy content. ICD-10 to PMB mappings, PMB condition metadata, scheme benefit buckets, tariffs, authorisation rules, and evidence requirements are business-owned reference data. Use clearly labelled placeholder configuration only for development.
- Keep PMB logic configuration-driven through mapping rules, policy profiles, and benefit routing rules.
- Every validation failure must expose a machine reason code, user-facing message, remediation guidance, affected fields, and severity.
- Every PMB flag must be explainable: trigger ICD-10, mapping rule, PMB condition, provider PMB indicator, route decision, action taken, and evidence gap.
- Every material lifecycle action must produce audit evidence. Avoid logging unnecessary PHI.
- Preserve immutability: closed billing snapshots and decision bundles are append-only evidence. Corrections should create a new claim version.
- Preserve idempotency for submissions and replayable lifecycle actions where applicable.

## Architecture Boundaries

- Practice Management and EMR: patients, providers, appointments, encounters, notes, attachments.
- Claims Context: drafts, versions, readiness, closure, snapshots, payloads, submissions.
- Rules Engine Context: policy profiles, decision tables, rule hits, decision bundles.
- Coding Context: ICD-10 validation and diagnosis linkage.
- PMB Context: ICD-10 to PMB mappings, PMB condition metadata, PMB detection.
- Benefit Routing Context: normal benefit, PMB benefit, or PMB review routing.
- Billing and Ledger Context: pricing, financial bundles, ledger-style postings.
- Submission Context: direct, switch, batch placeholder, idempotency, transport logs.
- Remittance and Reconciliation Context: advice, matching, partials, exceptions.
- Audit and Evidence Context: audit timeline and evidence packet.

## Validation Workflow

- Run readiness before closure and before payload/submission work.
- Re-check ICD-10 validity and PMB classification during closure and post-closure validation.
- Return structured validation summaries to the UI for action-point popups.
- Do not bypass closure blockers unless an explicit governed override path exists and is audited.

## Local Verification

- Backend syntax: `.\.venv\Scripts\python.exe -B -c "import ast, pathlib; [ast.parse(path.read_text(encoding='utf-8')) for path in [pathlib.Path('medhealth-ui/backend/platform_core.py'), pathlib.Path('medhealth-ui/backend/platform_api.py')]]"`
- Backend tests: `.\.venv\Scripts\python.exe -B -m unittest discover -s .\medhealth-ui\backend\tests -v`
- UI syntax: `node --check .\medhealth-ui\js\app.js`
- API smoke check: `Invoke-WebRequest -UseBasicParsing http://localhost:8001/`

## Current Local App

- Static UI usually runs at `http://localhost:8000/index.html`.
- Backend usually runs at `http://localhost:8001`.
- API docs are at `http://localhost:8001/docs`.
