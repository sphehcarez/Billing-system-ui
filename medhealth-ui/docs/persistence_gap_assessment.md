# Persistence Gap Assessment

## Before This Change

- `backend/platform_api.py` instantiated `PlatformStore()` as a process-global in-memory object.
- Core artefacts lived in Python dictionaries:
  - claims, versions, drafts, diagnoses
  - billing snapshots
  - policy profiles and rule definitions
  - ICD-10 and PMB mapping reference data
  - PMB/routing/costing decisions
  - submissions, transport logs, responses
  - remittances, reconciliations, payments
  - audit events and evidence packet sources
- `backend/migrations/*.sql` existed only as reference SQL drafts. They were not part of a runtime migration system.
- Docker only started the frontend/backend app containers; there was no database service, no migration runner, and no Postgres-backed source of truth.

## Runtime Risks That Existed

- Backend restarts erased claim lifecycle state.
- Docker did not provide durable storage for claim evidence or transport history.
- API reads and writes were not replayable against a database.
- Seed/UAT state was implicit inside code, not repeatable as standalone scripts.
- Health checks could not prove database reachability because there was no runtime DB integration.

## Current Direction

- Postgres is now the intended system of record through:
  - SQLAlchemy engine/session config in `backend/db_runtime.py`
  - schema metadata in `backend/db_schema.py`
  - Alembic migration setup under `backend/alembic/`
  - a Postgres-backed store wrapper in `backend/postgres_store.py`
- Docker Compose now includes:
  - `db` for PostgreSQL
  - `redis` for optional background processing
  - backend startup that runs Alembic before serving traffic
