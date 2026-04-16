# Runtime Proof Before

Date verified: `2026-04-16`

## Runtime Status

`docker compose ps`

```text
NAME                      IMAGE                   COMMAND                  SERVICE    CREATED          STATUS                    PORTS
medhealth-ui-backend-1    medhealth-ui-backend    "/app/docker-entrypo…"   backend    14 seconds ago   Up 12 seconds (healthy)   0.0.0.0:8001->8001/tcp, [::]:8001->8001/tcp
medhealth-ui-db-1         postgres:16-alpine      "docker-entrypoint.s…"   db         21 minutes ago   Up 21 minutes (healthy)   0.0.0.0:5432->5432/tcp, [::]:5432->5432/tcp
medhealth-ui-frontend-1   medhealth-ui-frontend   "python -m http.serv…"   frontend   21 minutes ago   Up 20 minutes (healthy)   0.0.0.0:8000->8000/tcp, [::]:8000->8000/tcp
```

## Fresh Database Before Seeding

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

## Purpose Of The Before Proof

- prove the runtime is healthy
- prove Postgres starts empty on a fresh volume before controlled seeds
- establish the baseline for deterministic UAT replay
