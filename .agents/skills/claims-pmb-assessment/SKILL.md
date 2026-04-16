---
name: claims-pmb-assessment
description: Use when assessing or modifying this Medhealth healthcare claims platform, especially for ICD-10 validation, ICD-10 to PMB mapping, PMB auto-flagging, benefit routing, readiness or closure validation, claim lifecycle, RBAC, audit evidence, remittance, or reconciliation work.
---

# Claims PMB Assessment

Use this skill for repository work involving the Medhealth practice management, EMR, claims billing, rules-engine, PMB routing, and audit/evidence platform.

## Required Workflow

1. Inspect the repo before changing files. Locate backend domain logic, API endpoints, UI action handlers, tests, migrations, and docs.
2. Identify current behavior for claims intake, readiness, closure, post-closure validation, payload generation, submission, remittance, reconciliation, ICD-10 handling, PMB detection, and audit.
3. Keep boundaries explicit: UI displays decisions, backend services produce decisions, rules/config own policy.
4. Implement highest-value changes directly when asked to build or fix. Do not stop at a design unless the user asks for analysis only.
5. Add or update tests for rule behavior, lifecycle transitions, RBAC, PMB detection, benefit routing, and UI blocker summaries.
6. Run focused verification commands and report results.

## Non-Negotiables

- Do not hard-code PMB logic in controllers or frontend code.
- Do not invent real medical scheme policy. Use labelled placeholder config only when reference data is missing.
- Every validation failure needs severity, machine reason code, message, remediation, and affected fields.
- Every PMB flag needs trigger ICD-10, mapping evidence, provider PMB indicator, route decision, action, and audit evidence.
- Closed snapshots and decision bundles are immutable evidence.
- Server-side RBAC is mandatory; UI restrictions alone are insufficient.
- Avoid unnecessary PHI in logs, audit details, and frontend summaries.

## Preferred Local Commands

- Backend tests: `.\.venv\Scripts\python.exe -B -m unittest discover -s .\medhealth-ui\backend\tests -v`
- Backend parse check: `.\.venv\Scripts\python.exe -B -c "import ast, pathlib; [ast.parse(path.read_text(encoding='utf-8')) for path in [pathlib.Path('medhealth-ui/backend/platform_core.py'), pathlib.Path('medhealth-ui/backend/platform_api.py')]]"`
- Frontend syntax: `node --check .\medhealth-ui\js\app.js`
- Backend smoke: `Invoke-WebRequest -UseBasicParsing http://localhost:8001/`

## Deliverable Shape

For assessment-style requests, respond in this order:

1. Executive summary
2. Current-state analysis
3. Technical gap assessment
4. Target architecture
5. Data model and rules design
6. File-by-file changes
7. Code patches or snippets
8. Test plan and verification
9. Risks, assumptions, and unresolved questions
