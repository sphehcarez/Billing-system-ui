# Enforcement Scan

Repo root: `C:\pe\MEDHEALTH FINAL\Billing system ui`

## Step 0

- `pwd` => `C:\pe\MEDHEALTH FINAL\Billing system ui`
- `.git` present at repo root: `C:\pe\MEDHEALTH FINAL\Billing system ui\.git`
- Backend entrypoint documented in repo before patch: `medhealth-ui/backend/main.py` and `medhealth-ui/START_SYSTEM.bat:30`
- Frontend entrypoint: static HTML under `medhealth-ui/`, typically served with `python -m http.server 8000` from `medhealth-ui/`
- UI is served separately from backend, not mounted by FastAPI.

## Readiness / Closure / Validation / Blockers

- `medhealth-ui/backend/platform_api.py:254` `run_readiness`
- `medhealth-ui/backend/platform_api.py:267` `close_claim`
- `medhealth-ui/backend/platform_api.py:279` `post_closure_validate`
- `medhealth-ui/backend/platform_core.py:1723` `_validation_summary`
- `medhealth-ui/backend/platform_core.py:1996` `run_readiness`
- `medhealth-ui/backend/platform_core.py:2043` `close_claim`
- `medhealth-ui/backend/platform_core.py:2097` `run_post_closure_validation`
- `medhealth-ui/js/app.js:712` `handleRunReadiness`
- `medhealth-ui/js/app.js:719` `handleCloseClaim`
- `medhealth-ui/js/app.js:735` `handlePostClosureValidation`
- `medhealth-ui/js/app.js:1190` `showValidationSummaryModal`

## ICD-10 / Diagnosis Capture + Validation

- `medhealth-ui/backend/platform_core.py:96` `Diagnosis`
- `medhealth-ui/backend/platform_core.py:143` `ICD10Code`
- `medhealth-ui/backend/platform_core.py:818` seeded ICD-10 reference
- `medhealth-ui/backend/platform_core.py:874` rule `ICD_PRIMARY_REQUIRED`
- `medhealth-ui/backend/platform_core.py:886` rule `ICD_FORMAT_INVALID`
- `medhealth-ui/backend/platform_core.py:1466` primary diagnosis lookup
- `medhealth-ui/backend/platform_core.py:1499` facts include `invalid_icd_count`
- `medhealth-ui/backend/tests/test_platform_core.py:17` missing ICD blocks readiness
- `medhealth-ui/backend/tests/test_platform_core.py:24` invalid ICD blocks readiness

## PMB Logic / Benefit Routing / Benefit Bucket

- `medhealth-ui/backend/platform_core.py:150` `PMBCondition`
- `medhealth-ui/backend/platform_core.py:159` `PMBMappingRule`
- `medhealth-ui/backend/platform_core.py:171` `BenefitRouteDecision`
- `medhealth-ui/backend/platform_core.py:831` seeded PMB conditions
- `medhealth-ui/backend/platform_core.py:849` seeded PMB mappings
- `medhealth-ui/backend/platform_core.py:1447` `_active_pmb_mappings_for_claim`
- `medhealth-ui/backend/platform_core.py:1455` `_missing_pmb_evidence`
- `medhealth-ui/backend/platform_core.py:1584` `_detect_pmb_and_route`
- `medhealth-ui/backend/platform_core.py:1688` audit event `PMB_DETECTION_AND_BENEFIT_ROUTING`
- `medhealth-ui/backend/platform_core.py:1781` `get_pmb_decisions_for_claim`
- `medhealth-ui/backend/platform_core.py:2510` `get_evidence_packet`
- `medhealth-ui/backend/tests/test_platform_core.py:53` auto-flag without provider indicator
- `medhealth-ui/backend/tests/test_platform_core.py:62` PMB missing evidence routes to review

## Decision Bundles / Reason Codes / Severity

- `medhealth-ui/backend/platform_core.py:193` `RuleHit`
- `medhealth-ui/backend/platform_core.py:206` `DecisionBundle`
- `medhealth-ui/backend/platform_core.py:1418` `_override_severity`
- `medhealth-ui/backend/platform_core.py:1510` `_evaluate_rule`
- `medhealth-ui/backend/platform_core.py:1534` `_aggregate_outcome`
- `medhealth-ui/backend/platform_core.py:1555` `_build_decision_bundle`
- `medhealth-ui/backend/platform_core.py:1733` summary groups blockers/warnings/info

## Audit / Evidence

- `medhealth-ui/backend/platform_core.py:559` `add_audit_event`
- `medhealth-ui/backend/platform_core.py:2030` `READINESS_RUN`
- `medhealth-ui/backend/platform_core.py:2049` `CLOSURE_BLOCKED`
- `medhealth-ui/backend/platform_core.py:2085` `SNAPSHOT_CREATED`
- `medhealth-ui/backend/platform_core.py:2114` `POST_CLOSURE_VALIDATION_DONE`
- `medhealth-ui/backend/platform_core.py:2510` `get_evidence_packet`
- `medhealth-ui/backend/platform_api.py:343` `/api/claims/{claim_id}/evidence`
- `medhealth-ui/backend/platform_api.py:438` `/api/audit-logs`
- `medhealth-ui/backend/platform_api.py:459` `/api/audit/{audit_event_id}`

## UI Action Points / Blocker Rendering

- `medhealth-ui/claim_detail.html:65-75` claim action buttons
- `medhealth-ui/claims.html:68-85` worklist action chips
- `medhealth-ui/js/api-client.js:177-185` readiness/close/validate API calls
- `medhealth-ui/js/app.js:712-738` action handlers call modal
- `medhealth-ui/js/app.js:1190-1338` modal rendering, blocker groups, PMB markup
- `medhealth-ui/js/app.js:1214` modal consumes `summary.pmb || result.benefit_route_decisions || []`

## IR System Search

- No hits for `IR system|IR_system|integration repository|integration-repository|IRSystem`.
- Result: no repository naming mismatch to standardize in current codebase.
