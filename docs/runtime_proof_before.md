> Current task proof begins here. Older runtime notes from the previous PMB visibility task remain below for history.

# Runtime Proof BEFORE Changes (Primary ICD, Jump, PMB Decision, Costing Preview)

Date: `2026-04-16`

Observed runtime: patched backend currently running on `http://127.0.0.1:8001`

This proof targets the current implementation before the diagnosis-capture, two-step PMB decision, routing refinement, costing preview, and jump-to-diagnoses work requested in this task.

## 1. UI target proof: no diagnoses jump destination exists

Search result for IDs and `data-field` targets in claim detail:

- `medhealth-ui/claim_detail.html:60` `id="claim-number"`
- `medhealth-ui/claim_detail.html:61` `id="claim-member"`
- `medhealth-ui/claim_detail.html:62` `id="claim-status-chip"`
- `medhealth-ui/claim_detail.html:86` `id="readiness-status"`
- `medhealth-ui/claim_detail.html:87` `id="closure-status"`
- `medhealth-ui/claim_detail.html:88` `id="post-closure-status"`
- `medhealth-ui/claim_detail.html:97` `id="payload-preview"`
- `medhealth-ui/claim_detail.html:106` `id="edi-preview"`

There is no `id="diagnoses"` and no `data-field="diagnoses"` target in the claim detail page.

Current modal jump logic:

- `medhealth-ui/js/app.js:1229-1239`

Exact excerpt:

```javascript
const target =
  document.querySelector(`[data-field="${selectorValue}"]`) ||
  document.getElementById(targetName);
if (target) {
  close();
  target.scrollIntoView({ behavior: "smooth", block: "center" });
}
```

Conclusion:
- the modal can render a jump button
- the current page does not contain a diagnoses destination
- “Jump to diagnoses” is non-functional today

## 2. API proof: missing primary ICD currently blocks readiness

Target claim:
- `CLM-1002`
- seed source: `medhealth-ui/backend/platform_core.py:1073-1081`
- scenario key: `missing_icd_blocks_closure`

### Request

`GET /api/claims/2`

### Response excerpt

```json
{
  "id": 2,
  "claim_number": "CLM-1002",
  "diagnoses": [],
  "latest_benefit_route_decision": {
    "route": "NORMAL_BENEFIT",
    "reason_code": "PMB_NOT_DETECTED",
    "trigger_icd10": null
  }
}
```

### Request

`POST /api/claims/2/readiness`

### Response excerpt

```json
{
  "keys": [
    "claim_id",
    "claim_number",
    "claim_version",
    "status",
    "outcome",
    "decision_bundle",
    "readiness_run",
    "benefit_route_decisions",
    "validation_summary"
  ],
  "outcome": "BLOCK",
  "blockers": [
    {
      "severity": "BLOCK",
      "reason_code": "ICD_MISSING",
      "title": "Primary ICD-10 required",
      "message": "Primary diagnosis missing",
      "remediation": "Capture a valid primary ICD-10 from the MIT and link it to the claim.",
      "affected_fields": ["diagnoses"],
      "jump_target": "diagnoses"
    }
  ]
}
```

Current problems proven by the response:

1. Reason code is `ICD_MISSING`, not the requested `ICD_MISSING_PRIMARY`
2. No action metadata is returned
3. No `allowAutoFix` flag is returned
4. No diagnosis capture endpoint is linked from the response

## 3. PMB proof: missing-primary claim is currently treated as “not detected”

Same readiness response for `CLM-1002`:

```json
{
  "pmb": [
    {
      "reason_code": "PMB_NOT_DETECTED",
      "trigger_icd10": null,
      "mapping_id": null,
      "pmb_condition_id": null,
      "provider_marked_pmb": false,
      "route": "NORMAL_BENEFIT",
      "action": "NO_PMB_MATCH",
      "message": "No configured ICD-10 to PMB mapping matched this claim."
    }
  ]
}
```

This is the wrong state for the requested behaviour:
- there is no primary diagnosis
- PMB should be `UNKNOWN`/blocked or `REVIEW_REQUIRED`
- current code falls through to “not detected” and normal benefit routing

## 4. PMB proof: mapped claim has route details, but no confirmation stage or costing preview

Target claim:
- `CLM-1001`

### Request

`GET /api/claims/1`

### Response excerpt

```json
{
  "claim_number": "CLM-1001",
  "pmb_status": "auto_routed",
  "latest_benefit_route_decision": {
    "trigger_icd10": "I10",
    "mapping_id": "PMB-MAP-DEV-I10",
    "pmb_condition_id": "PMB-CONFIG-001",
    "route": "PMB_BENEFIT",
    "reason_code": "PMB_AUTO_ROUTED"
  }
}
```

### Request

`POST /api/claims/1/readiness`

### Response excerpt

```json
{
  "pmb": [
    {
      "trigger_icd10": "I10",
      "mapping_id": "PMB-MAP-DEV-I10",
      "pmb_condition_id": "PMB-CONFIG-001",
      "route": "PMB_BENEFIT",
      "reason_code": "PMB_AUTO_ROUTED"
    }
  ],
  "has_costing_preview": false
}
```

Current problems proven by the response:

1. There is no two-step PMB state such as `POSSIBLE`, `REVIEW_REQUIRED`, or `CONFIRMED`
2. There is no separate benefit-routing decision object
3. There is no costing preview in readiness

## 5. Evidence packet proof: no costing preview persistence and no PMB confirmation object

### Request

`GET /api/claims/2/evidence`

### Response excerpt

```json
{
  "documents": [
    "snapshot.json",
    "decision_bundles.json",
    "pmb_routing.json",
    "payloads.json",
    "submissions.json",
    "responses.json",
    "remittance.json",
    "reconciliation.json"
  ],
  "benefit_route_decisions": [
    {
      "route": "NORMAL_BENEFIT",
      "reason_code": "PMB_NOT_DETECTED"
    }
  ],
  "financial_bundles": [],
  "audit_event_types": [
    "CLAIM_DRAFT_UPDATED",
    "PMB_DETECTION_AND_BENEFIT_ROUTING",
    "READINESS_RUN"
  ]
}
```

Current problems proven by evidence:

1. No distinct persisted PMB decision object
2. No costing preview persistence
3. No dedicated PMB/routing/costing event taxonomy requested by this task

## 6. First broken links in the chain

### Jump to diagnoses

UI action -> UI modal button -> UI jump handler -> DOM target lookup

First break:
- `medhealth-ui/js/app.js:1233-1235` expects `data-field="diagnoses"` or `id="diagnoses"`
- `medhealth-ui/claim_detail.html:1-117` has no such target

### Primary ICD fix flow

UI action -> API response blocker -> diagnosis capture API -> persistence -> UI refresh

First break:
- no dedicated diagnosis capture endpoints exist in `medhealth-ui/backend/platform_api.py:220-360`
- no diagnosis table exists in `medhealth-ui/backend/migrations/001_initial_schema.sql:1-260`
- no diagnosis editor exists in `medhealth-ui/claim_detail.html:1-117` / `medhealth-ui/js/app.js`

### PMB + costing

Readiness action -> readiness endpoint -> PMB/routing service -> response DTO -> UI modal

First breaks:
- PMB detection path treats missing-primary claims as `PMB_NOT_DETECTED` in `medhealth-ui/backend/platform_core.py:1584-1708`
- no costing preview is computed or returned in readiness/closure/validation
- modal renders only PMB route cards, not confirmation state or costing data

# Runtime Proof (Before Changes)

Date: `2026-04-16`

Target runtime under observation: live localhost backend at `http://localhost:8001`

## 1. Repo/runtime mismatch being tested

- Live root response previously returned `{"message":"Medhealth claims rules platform","docs":"/docs","api":"/api/docs"}`.
- Checked-in code says readiness/closure/validation should return `benefit_route_decisions` and `validation_summary`:
  - `medhealth-ui/backend/platform_core.py:2038-2040`
  - `medhealth-ui/backend/platform_core.py:2056-2057`
  - `medhealth-ui/backend/platform_core.py:2121-2122`
- Live localhost did **not** return those fields.

## 2. Claim seeded for proof

### Request

`POST /api/claims`

```json
{
  "claim_number": "CLM-PMB-BEFORE-001",
  "patient_id": 1,
  "provider_id": 1,
  "member_number": "MEM210001",
  "service_date": "2026-04-16",
  "diagnoses": [
    { "seq": 1, "icd10": "I10", "diagnosis_type": "PRIMARY" }
  ],
  "line_items": [
    {
      "line_id": "1",
      "service_code": "CONS001",
      "service_description": "Consultation",
      "quantity": 1,
      "unit_price": 750,
      "claimed_amount": 750,
      "diagnosis_refs": [1]
    }
  ]
}
```

### Response excerpt

```json
{
  "id": 12,
  "claim_number": "CLM-PMB-BEFORE-001",
  "readiness_status": "pending",
  "validation_status": "pending"
}
```

## 3. Readiness

### Request

`POST /api/claims/12/readiness`

### Live localhost response keys

```json
{
  "keys": [
    "claim_id",
    "claim_number",
    "claim_version",
    "status",
    "outcome",
    "decision_bundle",
    "readiness_run"
  ],
  "benefit_route_decisions": null,
  "validation_summary": null
}
```

### Expected from checked-in service code

```json
{
  "keys": [
    "claim_id",
    "claim_number",
    "claim_version",
    "status",
    "outcome",
    "decision_bundle",
    "readiness_run",
    "benefit_route_decisions",
    "validation_summary"
  ],
  "benefit_route_decisions": [
    {
      "trigger_icd10": "I10",
      "route": "PMB_BENEFIT",
      "reason_code": "PMB_AUTO_ROUTED",
      "provider_marked_pmb": false
    }
  ]
}
```

Source of expected payload:
- `medhealth-ui/backend/platform_core.py:2035-2040`
- verified locally by direct Python invocation of `PlatformStore.run_readiness(...)`

## 4. Closure

### Request

`POST /api/claims/12/close`

### Live localhost response excerpt

```json
{
  "claim_id": 12,
  "claim_number": "CLM-PMB-BEFORE-001",
  "claim_version": 1,
  "status": "closed",
  "snapshot_id": "snap-0a4f364cc8fa",
  "decision_bundle": {
    "stage": "CLOSURE_GATE",
    "outcome": "PASS"
  }
}
```

Observed issue:
- no `benefit_route_decisions`
- no `validation_summary`

## 5. Post-closure validation

### Request

`POST /api/claims/12/validate`

### Live localhost response excerpt

```json
{
  "claim_id": 12,
  "claim_number": "CLM-PMB-BEFORE-001",
  "validation_status": "valid",
  "outcome": "PASS",
  "decision_bundle": {
    "stage": "POST_CLOSURE_VALIDATION",
    "outcome": "PASS"
  }
}
```

Observed issue:
- no `benefit_route_decisions`
- no `validation_summary`

## 6. Submission

### Request

`POST /api/claims/12/submit`

```json
{
  "channel": "DIRECT",
  "idempotency_key": "codex-proof-before-001"
}
```

### Response excerpt

```json
{
  "claim_id": 12,
  "claim_number": "CLM-PMB-BEFORE-001",
  "submission_status": "acknowledged",
  "response": { "status": "ACK" }
}
```

## 7. Evidence packet + audit

### Request

`GET /api/claims/12/evidence`

### Live localhost response excerpt

```json
{
  "documents": [
    "snapshot.json",
    "decision_bundles.json",
    "payloads.json",
    "submissions.json",
    "responses.json",
    "remittance.json",
    "reconciliation.json"
  ],
  "benefit_route_decisions": null
}
```

Observed issue:
- `pmb_routing.json` missing from evidence `documents`
- `benefit_route_decisions` missing/null
- audit timeline for the claim did not contain `PMB_DETECTION_AND_BENEFIT_ROUTING`

## 8. UI notes

Expected UI chain from code:

- `medhealth-ui/js/app.js:712-715` readiness handler opens `showValidationSummaryModal(...)`
- `medhealth-ui/js/app.js:1214` modal consumes `summary.pmb || result.benefit_route_decisions || []`
- `medhealth-ui/js/app.js:1274-1298` renders PMB cards

Actual implication from live localhost responses:

- because readiness/closure/validation responses from localhost omitted both `validation_summary` and `benefit_route_decisions`, the action-point modal has no PMB data to render
- the first break is therefore before UI rendering, at the backend runtime entrypoint / response layer
