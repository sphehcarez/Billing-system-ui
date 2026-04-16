# Runtime Proof AFTER Changes

Date: `2026-04-16`

Runtime under proof:
- backend restarted from `medhealth-ui/backend/main.py`
- live HTTP verification on `http://127.0.0.1:8001`

## 1. Root response

`GET /`

```json
{
  "message": "Medhealth claims rules platform",
  "docs": "/docs",
  "api": "/api/docs"
}
```

## 2. Missing-primary claim proves blocker + jump + PMB gating

Claim created for proof:
- `claim_id=13`
- non-DSP provider
- no diagnoses at creation time

### Request

`POST /api/claims/13/readiness`

### Response excerpt

```json
{
  "outcome": "BLOCK",
  "validation_summary": {
    "blockers": [
      {
        "reason_code": "ICD_MISSING_PRIMARY",
        "action": {
          "type": "NAVIGATE",
          "target": "diagnoses",
          "claimId": 13
        },
        "allowAutoFix": false
      }
    ]
  },
  "pmb_decision": {
    "pmb_status": "UNKNOWN",
    "reason_code": "ICD_MISSING_PRIMARY"
  },
  "benefit_routing_decision": {
    "route": "PMB_REVIEW_QUEUE"
  },
  "costing_preview": {
    "pricing_basis": "NON_DSP_VOLUNTARY"
  }
}
```

Runtime proof:
- the blocker reason code is now `ICD_MISSING_PRIMARY`
- the response carries action metadata for `target=diagnoses`
- PMB is no longer mislabeled as `NOT_DETECTED` when primary ICD is missing

## 3. Diagnosis capture endpoint clears the blocker and re-evaluates PMB

### Request

`POST /api/claims/13/diagnoses`

```json
{
  "icd10_code": "I10",
  "is_primary": true,
  "source": "UserEntry"
}
```

### Response excerpt

```json
{
  "diagnoses": [
    {
      "icd10_code": "I10",
      "is_primary": true,
      "source": "UserEntry"
    }
  ]
}
```

### Request

`POST /api/claims/13/readiness`

### Response excerpt

```json
{
  "outcome": "WARN",
  "pmb_decision": {
    "pmb_status": "REVIEW_REQUIRED",
    "reason_code": "PMB_REVIEW_REQUIRED",
    "matched_icd10": "I10",
    "mapping_id": "PMB-MAP-DEV-I10",
    "condition_id": "PMB-CONFIG-001"
  },
  "benefit_routing_decision": {
    "route": "PMB_REVIEW_QUEUE",
    "reason_code": "ROUTE_PMB_REVIEW"
  },
  "costing_preview": {
    "pricing_basis": "NON_DSP_VOLUNTARY",
    "allowed_total": 450.0,
    "pmb_allowed_total": 450.0,
    "member_liability_estimate": 0.0,
    "pending_pmb_review": true
  }
}
```

Result:
- readiness now re-runs PMB identification after diagnosis capture
- PMB moves from `UNKNOWN` to `REVIEW_REQUIRED`
- routing moves to `PMB_REVIEW_QUEUE`
- costing preview is returned at the action point, not only after adjudication

## 4. Persistence proof on the same claim

### Request

`GET /api/claims/13`

### Response excerpt

```json
{
  "pmb_status": "review_required",
  "latest_pmb_decision": {
    "pmb_status": "REVIEW_REQUIRED",
    "reason_code": "PMB_REVIEW_REQUIRED"
  },
  "latest_benefit_route_decision": {
    "route": "PMB_REVIEW_QUEUE",
    "reason_code": "ROUTE_PMB_REVIEW"
  },
  "latest_costing_preview": {
    "pricing_basis": "NON_DSP_VOLUNTARY",
    "pending_pmb_review": true
  }
}
```

Result:
- PMB decision persistence is visible on the claim DTO
- routing decision persistence is visible on the claim DTO
- costing preview persistence is visible on the claim DTO

## 5. Confirmed PMB proof including closure and post-closure validation

Confirmed claim created for proof:
- `claim_id=14`
- DSP provider
- primary ICD `I10`
- placeholder PMB evidence attachment `MOTIVATION`

### Readiness

`POST /api/claims/14/readiness`

```json
{
  "pmb_decision": {
    "pmb_status": "CONFIRMED"
  },
  "benefit_routing_decision": {
    "route": "PMB_BENEFIT_BUCKET"
  },
  "costing_preview": {
    "pricing_basis": "DSP",
    "pmb_allowed_total": 900.0,
    "member_liability_estimate": 0.0
  }
}
```

### Closure

`POST /api/claims/14/close`

```json
{
  "status": "closed",
  "snapshot_id": "snap-6bd0e39508d6",
  "pmb_decision": {
    "pmb_status": "CONFIRMED"
  },
  "benefit_routing_decision": {
    "route": "PMB_BENEFIT_BUCKET"
  }
}
```

### Post-closure validation

`POST /api/claims/14/validate`

```json
{
  "validation_status": "valid",
  "pmb_decision": {
    "pmb_status": "CONFIRMED"
  },
  "benefit_routing_decision": {
    "route": "PMB_BENEFIT_BUCKET"
  }
}
```

Result:
- readiness, closure, and post-closure validation all re-run PMB/routing/costing
- confirmed PMB on a DSP claim previews full payment with zero member liability

## 6. Evidence packet proof

### Request

`GET /api/claims/14/evidence`

### Response excerpt

```json
{
  "documents": [
    "snapshot.json",
    "decision_bundles.json",
    "pmb_decision.json",
    "pmb_routing.json",
    "costing_preview.json"
  ],
  "pmb_decisions": [
    {
      "pmb_status": "CONFIRMED",
      "matched_icd10": "I10",
      "mapping_id": "PMB-MAP-DEV-I10",
      "condition_id": "PMB-CONFIG-001",
      "reason_code": "PMB_CONFIRMED"
    }
  ],
  "benefit_route_decisions": [
    {
      "route": "PMB_BENEFIT_BUCKET",
      "reason_code": "ROUTE_PMB_CONFIRMED"
    }
  ],
  "costing_previews": [
    {
      "pricing_basis": "DSP",
      "allowed_total": 600.0,
      "pmb_allowed_total": 900.0,
      "member_liability_estimate": 0.0,
      "reason_code": "COSTING_PMB_CONFIRMED"
    }
  ]
}
```

Audit events returned in the same evidence packet:

```json
[
  "BENEFIT_ROUTED_PMB_BENEFIT_BUCKET",
  "COSTING_PREVIEW_COMPUTED",
  "PMB_DETECTED",
  "PMB_DETECTION_AND_BENEFIT_ROUTING",
  "PMB_PROVIDER_NOT_MARKED",
  "READINESS_RUN",
  "SNAPSHOT_CREATED",
  "POST_CLOSURE_VALIDATION_DONE"
]
```

Result:
- evidence packet now includes PMB decision, routing decision, and costing preview artifacts
- audit includes distinct PMB, routing, and costing preview events

## 7. UI action-point proof

Terminal session cannot capture a browser screenshot, so UI proof is shown from the checked-in runtime wiring:

- readiness modal blocker jump uses `medhealth-ui/js/app.js:1421-1434` `jumpToClaimTarget`
- diagnosis focus uses `medhealth-ui/js/app.js:836-844` `focusDiagnosisSearchInput`
- diagnosis add/save re-runs readiness via `medhealth-ui/js/app.js:855-875` and `:877-892`
- diagnoses section exists at `medhealth-ui/claim_detail.html:95-131`
- PMB panel rendering uses `medhealth-ui/js/app.js:1469-1527`

This means the action-point chain is now:

`modal blocker -> jump to diagnoses -> focus ICD search -> capture/set primary -> POST /claims/{id}/diagnoses -> rerun readiness -> modal reopens with PMB panel and costing preview`
