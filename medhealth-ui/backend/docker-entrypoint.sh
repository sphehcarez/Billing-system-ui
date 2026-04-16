#!/bin/sh
set -e

python - <<'PY'
import time
from db_runtime import database_healthcheck

for _ in range(60):
    health = database_healthcheck()
    if health["db"] == "ok":
        break
    time.sleep(1)
else:
    raise SystemExit("Database did not become reachable in time")
PY

alembic upgrade head
exec uvicorn main:app --host 0.0.0.0 --port "${MEDHEALTH_PORT:-8001}"
