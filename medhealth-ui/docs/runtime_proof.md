# Runtime Proof

Date verified: `2026-04-16`

## Runtime status

`docker compose ps`

```text
NAME                      IMAGE                   COMMAND                  SERVICE    CREATED          STATUS                    PORTS
medhealth-ui-backend-1    medhealth-ui-backend    "/app/docker-entrypo…"   backend    14 seconds ago   Up 12 seconds (healthy)   0.0.0.0:8001->8001/tcp, [::]:8001->8001/tcp
medhealth-ui-db-1         postgres:16-alpine      "docker-entrypoint.s…"   db         21 minutes ago   Up 21 minutes (healthy)   0.0.0.0:5432->5432/tcp, [::]:5432->5432/tcp
medhealth-ui-frontend-1   medhealth-ui-frontend   "python -m http.serv…"   frontend   21 minutes ago   Up 20 minutes (healthy)   0.0.0.0:8000->8000/tcp, [::]:8000->8000/tcp
```

## Before seeding

Fresh Postgres after rebuild, before reference/UAT seeds:

```sql
select count(*) as claims_count from claims;
select count(*) as icd10_count from icd10_reference;
select count(*) as audit_event_count from audit_events;
```

```text
 claims_count
--------------
            0

 icd10_count
-------------
           0

 audit_event_count
-------------------
                 0
```

## Seed outputs

Reference data seed:

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

UAT scenario seed:

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

## After seeding

Reference and audit proof queries:

```sql
select count(*) as claims_count from claims;
select count(*) as icd10_count from icd10_reference;
select condition_id, type, name from pmb_conditions order by condition_id;
select count(*) as audit_event_count from audit_events;
```

```text
 claims_count
--------------
            5

 icd10_count
-------------
           4

 condition_id | type |                name
--------------+------+-------------------------------------
 DEMO_CDL_001 | CDL  | DEMO chronic disease list condition
 DEMO_DTP_001 | DTP  | DEMO diagnosis treatment pair

 audit_event_count
-------------------
               103
```

## Live API proof

The live backend was exercised with a fresh runtime-proof claim created through `/api/claims`, then processed through readiness, closure, post-closure validation, and idempotent submission.

Proof response:

```json
{
  "claim_id": 7,
  "closure": {
    "snapshot_id": "snap-1836a64add45",
    "status": "closed"
  },
  "evidence_counts": {
    "audit_events": 25,
    "benefit_route_decisions": 3,
    "costing_previews": 3,
    "decision_bundles": 3,
    "pmb_decisions": 3
  },
  "health": {
    "db": "ok",
    "status": "ok"
  },
  "post_closure": {
    "outcome": "PASS",
    "validation_status": "valid"
  },
  "readiness": {
    "blockers": null,
    "mapping_id": "DEMO_MAP_I10",
    "member_liability_estimate": 0.0,
    "outcome": "PASS",
    "pmb_status": "CONFIRMED",
    "pricing_basis": "DSP",
    "route": "PMB_BENEFIT_BUCKET"
  },
  "submission": {
    "first_submission_id": "sub-ca6604ae1114",
    "idempotent_replay": true,
    "response_status": "ACK",
    "second_submission_id": "sub-ca6604ae1114"
  }
}
```

## Claim-specific DB proof

The runtime-proof claim persisted the expected artefacts exactly once where required.

```sql
select count(*) as snapshot_count from billing_snapshots where claim_id = 7;
select count(*) as decision_bundle_count from decision_bundles where claim_id = 7;
select count(*) as submission_count from submissions where claim_id = 7;
select count(*) as transport_log_count
from transport_logs tl
join submissions s on s.submission_id = tl.submission_id
where s.claim_id = 7;

select claim_id, stage, route, reason_code
from benefit_routing_decisions
where claim_id = 7
order by created_at;

select claim_id, stage, allowed_total, pmb_allowed_total, member_liability_estimate, pricing_basis
from costing_previews
where claim_id = 7
order by created_at;
```

```text
 snapshot_count
----------------
              1

 decision_bundle_count
-----------------------
                     3

 submission_count
------------------
                1

 transport_log_count
---------------------
                   2

 claim_id |          stage          |       route        |     reason_code
----------+-------------------------+--------------------+---------------------
        7 | READINESS               | PMB_BENEFIT_BUCKET | ROUTE_PMB_CONFIRMED
        7 | CLOSURE_GATE            | PMB_BENEFIT_BUCKET | ROUTE_PMB_CONFIRMED
        7 | POST_CLOSURE_VALIDATION | PMB_BENEFIT_BUCKET | ROUTE_PMB_CONFIRMED

 claim_id |          stage          | allowed_total | pmb_allowed_total | member_liability_estimate | pricing_basis
----------+-------------------------+---------------+-------------------+---------------------------+---------------
        7 | READINESS               |        650.00 |            900.00 |                      0.00 | DSP
        7 | CLOSURE_GATE            |        650.00 |            900.00 |                      0.00 | DSP
        7 | POST_CLOSURE_VALIDATION |        650.00 |            900.00 |                      0.00 | DSP
```

## Test proof

`pytest` result captured through the Docker-backed repo mount:

```text
24 passed, 3 warnings in 47.37s
```

The warnings are from `httpx` deprecating the legacy `app=` shortcut used by `TestClient`; they do not indicate a failing persistence path. The idempotent submission test now also asserts persisted `remittances`, `reconciliations`, and joined `transport_logs`.
