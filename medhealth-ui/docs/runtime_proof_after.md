# Runtime Proof After

Date verified: `2026-04-17`

## Runtime Health And Seed Proof

Health:

```json
{
  "status": "ok",
  "db": "ok"
}
```

Reference and UAT seeds were rerun against the Docker runtime before capture:

```json
{
  "result": {
    "icd10_reference": 4,
    "patients": 5,
    "pmb_conditions": 2,
    "pmb_mappings": 3,
    "policy_profiles": 2,
    "providers": 2,
    "users": 6
  },
  "seed": "reference_data"
}
```

```json
{
  "claim_ids": {
    "CLEAN_SUCCESS": 1,
    "MISMATCH_EXCEPTION": 5,
    "MISSING_PRIMARY_ICD": 2,
    "PARTIAL_PAYMENT": 4,
    "PMB_REVIEW_REQUIRED": 3
  },
  "seed": "uat_scenarios"
}
```

## API Proof: Diagnosis Linkage Resolution

Runtime proof claim: `claim_id = 19`

Post-closure validation now returns a fully actionable warning contract before remediation:

```json
{
  "outcome": "WARN",
  "warnings": [
    {
      "reason_code": "DIAGNOSIS_LINK_MISSING",
      "message": "One or more claim lines are missing diagnosis references.",
      "remediation_hint": "Link each billed line to the applicable diagnosis sequence.",
      "affected_line_ids": [
        "1"
      ],
      "action": {
        "type": "NAVIGATE",
        "target": "line_items",
        "claimId": 19,
        "highlightMissingDiagnosis": true,
        "line_ids": [
          "1"
        ]
      },
      "action_target": "line_items"
    }
  ]
}
```

The line-item API exposes linkage state:

```json
[
  {
    "claim_line_item_id": "19:1:1",
    "line_id": "1",
    "diagnosis_refs": [],
    "diagnosis_link_status": "MISSING",
    "missing_diagnosis_link": true
  }
]
```

After `PUT /api/claims/19/line-items/1/diagnosis-links`, the relink is persisted, a new claim version is created, and post-closure validation clears:

```json
{
  "claim_version": 2,
  "post_closure_validation": {
    "outcome": "PASS",
    "warnings": []
  },
  "line_item": {
    "line_id": "1",
    "diagnosis_refs": [
      1
    ],
    "diagnosis_codes": [
      "J11.1"
    ],
    "diagnosis_link_status": "LINKED",
    "missing_diagnosis_link": false
  }
}
```

## API Proof: Patient Registry Claim-Carry

`GET /api/patients/1/claim-context` now returns a patient-centric claim-ready profile:

```json
{
  "patient_id": 1,
  "claim_ready_missing": [
    "preauthorisation"
  ],
  "latest_claim_status": "reconciled",
  "claims_count": 9,
  "patient_missing_indicators": [
    "preauthorisation"
  ],
  "evidence_packet_url": "/api/audit/claims/19/evidence-packet"
}
```

`GET /api/patients/1/timeline` now returns claim and submission activity against the patient:

```json
[
  {
    "event_type": "ADJUDICATED",
    "claim_id": 19
  },
  {
    "event_type": "REMITTED",
    "claim_id": 19
  },
  {
    "event_type": "RECONCILED",
    "claim_id": 19
  },
  {
    "event_type": "CLAIM_SUBMITTED",
    "claim_id": 19
  },
  {
    "event_type": "EDI_VALIDATED",
    "claim_id": 19
  }
]
```

## API Proof: Structured Payload Tiles

`GET /api/claims/19/payloads/2/structured` now returns stage-based tiles instead of a raw-only payload view:

```json
{
  "claim_version": 2,
  "tile_statuses": [
    {
      "stage_id": "parties",
      "status": "complete",
      "missing_fields": []
    },
    {
      "stage_id": "visit",
      "status": "complete",
      "missing_fields": []
    },
    {
      "stage_id": "diagnoses",
      "status": "complete",
      "missing_fields": []
    },
    {
      "stage_id": "line_items",
      "status": "complete",
      "missing_fields": []
    },
    {
      "stage_id": "routing",
      "status": "complete",
      "missing_fields": []
    },
    {
      "stage_id": "submission",
      "status": "missing",
      "missing_fields": [
        {
          "field": "submission_metadata",
          "action": {
            "label": "Submit claim",
            "target": "submission_tool",
            "type": "NAVIGATE"
          }
        }
      ]
    }
  ]
}
```

## API Proof: Functional Pseudo-EDI

EDI actions now work as operational endpoints:

```json
{
  "generated_artifact_id": "edi-dbecca94ddb7",
  "valid": true,
  "validated_errors": [],
  "download_preview": [
    "UNH+AFTER-LINK-1776400446+MEDCLM:1:1:PHISC'",
    "BGM+340+AFTER-LINK-1776400446+9'",
    "DTM+137:20260417:102'",
    "NAD+MS+SCHEMEA'",
    "NAD+PR+DEMO-PRACTICE-001:PCNS'"
  ],
  "submission_id": "sub-2acab9087bd7",
  "response_status": "ACK",
  "transport_events": [
    "EDI_GENERATED",
    "EDI_VALIDATED",
    "EDI_VALIDATED",
    "ENQUEUED",
    "SWITCH_TRANSFORM",
    "SENT",
    "EDI_SUBMITTED"
  ]
}
```

## API Proof: PMB Match And No-Match

Mapped claim outcome:

```json
{
  "claim_id": 19,
  "outcome": "PASS",
  "pmb_status": "CONFIRMED",
  "mapping_id": "DEMO_MAP_J111",
  "route": "PMB_BENEFIT_BUCKET",
  "pricing_basis": "DSP",
  "line_level_evaluation_limited": true
}
```

After diagnosis linkage is fixed, the rerun PMB decision keeps the same mapping but clears the line-level limitation:

```json
{
  "claim_version": 2,
  "pmb_status": "CONFIRMED",
  "mapping_id": "DEMO_MAP_J111",
  "line_level_evaluation_limited": false
}
```

No-match claim: `claim_id = 20`

```json
{
  "pmb_status": "NOT_DETECTED",
  "reason_code": "PMB_NOT_DETECTED",
  "detection_reason": "NO_MATCH",
  "evaluated_icd10_list": [
    "Z00.0"
  ],
  "mapping_table_version": "PMB-DEMO-2026-04",
  "effective_date_used": "2026-04-17",
  "action": {
    "type": "NAVIGATE",
    "target": "PMB_MAPPING_ADMIN",
    "location": "settings.html#pmb-mapping-admin",
    "allowed_roles": [
      "Administrator"
    ]
  }
}
```

PMB mapping simulation confirms the current no-match state while showing impacted claims:

```json
{
  "icd10_code": "Z00.0",
  "matches": [],
  "impacted_claims": [
    {
      "claim_id": 20,
      "claim_number": "AFTER-NOMATCH-1776400446",
      "current_pmb_status": "not_detected"
    }
  ]
}
```

## Database Proof

Reference mappings are present:

```sql
select count(*) as mapping_count from icd10_pmb_mappings where active = true;
```

```text
 mapping_count
---------------
             3
```

Line-item diagnosis linkage is persisted for claim `19`:

```sql
select item.claim_id, item.claim_version, item.line_id,
       array_remove(array_agg(link.diagnosis_id order by link.sequence), null) as diagnosis_ids
from claim_line_items item
left join claim_line_diagnosis_links link on link.claim_line_item_id = item.claim_line_item_id
where item.claim_id = 19
group by item.claim_id, item.claim_version, item.line_id
order by item.line_id;
```

```text
 claim_id | claim_version | line_id |   diagnosis_ids
----------+---------------+---------+-------------------
       19 |             2 | 1       | {dx-93c7bde0dfd4}
```

Audit evidence for the remediation exists:

```sql
select event_type, detail_json, timestamp
from audit_events
where entity_type = 'claim'
  and entity_id = '19'
  and event_type = 'DIAGNOSIS_LINK_UPDATED'
order by timestamp desc
limit 1;
```

```text
       event_type       |                                  detail_json                                  |      timestamp
------------------------+-------------------------------------------------------------------------------+----------------------
 DIAGNOSIS_LINK_UPDATED | {"line_ids": ["1"], "claim_version": 2, "diagnosis_ids": ["dx-93c7bde0dfd4"]} | 2026-04-17T04:34:10Z
```

EDI artefact persistence exists:

```sql
select artifact_id, claim_id, claim_version, format, content_hash
from edi_artifacts
where claim_id = 19
order by artifact_id desc
limit 1;
```

```text
   artifact_id    | claim_id | claim_version |   format   |                              content_hash
------------------+----------+---------------+------------+-------------------------------------------------------------------------
 edi-dbecca94ddb7 |       19 |             2 | PSEUDO_EDI | sha256:c7fc883eb62ac22f36d5bccaf6c454030e16a5345328523bc5bd17a2da1bbb15
```

Transport evidence exists for the EDI flow:

```sql
select event, count(*) as event_count
from transport_logs
where claim_id = 19
group by event
order by event;
```

```text
      event       | event_count
------------------+-------------
 EDI_GENERATED    |           1
 EDI_SUBMITTED    |           1
 EDI_VALIDATED    |           2
 ENQUEUED         |           1
 SENT             |           1
 SWITCH_TRANSFORM |           1
```

PMB match and no-match outcomes are persisted:

```sql
select claim_id, claim_version, pmb_status, reason_code, detection_reason, evaluated_icd10_list_json
from pmb_decisions
where claim_id in (19,20)
order by claim_id, claim_version, created_at;
```

```text
 claim_id | claim_version |  pmb_status  |   reason_code    | detection_reason | evaluated_icd10_list_json
----------+---------------+--------------+------------------+------------------+---------------------------
       19 |             1 | CONFIRMED    | PMB_CONFIRMED    | MATCH_FOUND      | ["J11.1"]
       19 |             1 | CONFIRMED    | PMB_CONFIRMED    | MATCH_FOUND      | ["J11.1"]
       19 |             1 | CONFIRMED    | PMB_CONFIRMED    | MATCH_FOUND      | ["J11.1"]
       19 |             2 | CONFIRMED    | PMB_CONFIRMED    | MATCH_FOUND      | ["J11.1"]
       19 |             2 | CONFIRMED    | PMB_CONFIRMED    | MATCH_FOUND      | ["J11.1"]
       19 |             2 | CONFIRMED    | PMB_CONFIRMED    | MATCH_FOUND      | ["J11.1"]
       20 |             1 | NOT_DETECTED | PMB_NOT_DETECTED | NO_MATCH         | ["Z00.0"]
```

## UI Notes

- `claim_detail.html?id=19`
  - open Post-closure Validation
  - click `Jump to line_items`
  - the line item row is highlighted and now exposes diagnosis-link controls
  - save the link and the modal reruns validation automatically
- The claim page now shows stage tiles instead of a raw canonical-only block.
- The submission tool now exposes Generate, Validate, Download, and Submit actions with a transport timeline.
- `patients.html` now exposes the patient claim-ready profile and patient timeline.
- `settings.html#pmb-mapping-admin` now provides PMB mapping admin and simulation controls.

## Test Proof

Docker-backed regression run:

```text
29 passed, 1 skipped, 7 warnings in 152.37s (0:02:32)
```
