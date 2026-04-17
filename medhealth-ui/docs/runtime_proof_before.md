# Runtime Proof Before

Date captured before this change set: `2026-04-17`

## Observed UI Behaviour

- Post-closure validation showed `DIAGNOSIS_LINK_MISSING` with a passive `Jump to line_items` affordance.
- The PMB panel showed `NOT_DETECTED` with a generic no-match explanation.
- Canonical payload was rendered as raw code.
- Pseudo-EDI was passive text, not an operational tool.
- Patient registry did not expose a claim-ready profile view.

## API Proof Before

Claim `CLM-BEFORE-LINK` was created with a primary `Z00.0` diagnosis and line items without diagnosis references.

Post-closure validation returned a warning, but no persisted remediation path existed:

```json
{
  "validation_summary": {
    "outcome": "WARN",
    "warnings": [
      {
        "reason_code": "DIAGNOSIS_LINK_MISSING",
        "jump_target": "line_items"
      }
    ]
  }
}
```

PMB no-match output was too terse for remediation:

```json
{
  "pmb_decision": {
    "pmb_status": "NOT_DETECTED",
    "reason_code": "PMB_NOT_DETECTED",
    "explainability": "Primary ICD-10 Z00.0 did not match any active PMB mapping."
  }
}
```

Required runtime endpoints were missing:

```text
GET /api/patients/1/claim-context          -> 404 Not Found
GET /api/patients/1/timeline               -> 404 Not Found
GET /api/claims/10/payloads/1/structured   -> 404 Not Found
POST /api/claims/10/payloads/1/edi/generate -> 404 Not Found
```

## Database Proof Before

The required persistence tables did not exist:

```sql
select to_regclass('public.claim_line_items');
select to_regclass('public.claim_line_diagnosis_links');
select to_regclass('public.edi_artifacts');
```

```text
 to_regclass
------------

 to_regclass
------------

 to_regclass
------------
```

Line items were still embedded inside claim payload JSON instead of being first-class persisted rows:

```text
claims.payload_json.line_items existed, but there was no backing claim_line_items table to query or join.
```

## UI Reproduction Notes Before

- `claim_detail.html` could show the warning, but users could not actually link diagnoses to lines from the UI.
- The patient registry page did not provide member, provider, visit, diagnosis, charge, attachment, and claim-timeline data in one place.
- The payload preview and pseudo-EDI panel did not provide an operational submission path.
