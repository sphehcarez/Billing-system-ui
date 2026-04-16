# Runbook

This runbook assumes the repo root is `/mnt/c/pe/MEDHEALTH FINAL/Billing system ui/medhealth-ui`.

## WSL Bash

### 1. Start Docker services

```bash
docker compose up -d
docker compose ps
```

### 2. Export runtime environment

```bash
export DATABASE_URL=postgresql+psycopg://postgres:postgres@localhost:5432/billing
export REDIS_URL=redis://localhost:6379/0
export API_PORT=8001
```

### 3. Run migrations

The backend container already runs Alembic on startup, but this explicit command is useful for manual replays.

```bash
docker compose exec backend alembic -c /app/alembic.ini upgrade head
```

### 4. Seed demo reference data

```bash
docker run --rm \
  --network medhealth-ui_default \
  -e DATABASE_URL=postgresql+psycopg://postgres:postgres@db:5432/billing \
  --mount type=bind,source="$PWD",target=/workspace \
  -w /workspace \
  medhealth-ui-backend \
  python infra/seed/seed_reference_data.py
```

### 5. Seed repeatable UAT scenarios

```bash
docker run --rm \
  --network medhealth-ui_default \
  -e DATABASE_URL=postgresql+psycopg://postgres:postgres@db:5432/billing \
  --mount type=bind,source="$PWD",target=/workspace \
  -w /workspace \
  medhealth-ui-backend \
  python infra/seed/seed_uat_scenarios.py
```

### 6. Start or restart the backend on port 8001

```bash
docker compose up -d backend
docker compose ps
```

### 7. Verify health

```bash
curl http://localhost:8001/health
```

Expected response:

```json
{"status":"ok","db":"ok"}
```

### 8. Call readiness for a seeded claim

Claim `1` is the seeded `CLEAN_SUCCESS` scenario.

```bash
docker compose exec -T backend python - <<'PY'
import json, urllib.request

BASE = "http://localhost:8001"

def req(method, path, data=None, headers=None):
    body = None if data is None else json.dumps(data).encode("utf-8")
    request = urllib.request.Request(BASE + path, data=body, method=method)
    request.add_header("Content-Type", "application/json")
    for key, value in (headers or {}).items():
        request.add_header(key, value)
    with urllib.request.urlopen(request) as response:
        print(response.read().decode("utf-8"))

login_request = urllib.request.Request(
    BASE + "/api/auth/login",
    data=json.dumps({
        "username": "admin",
        "password": "admin123",
        "role": "Administrator",
    }).encode("utf-8"),
    method="POST",
)
login_request.add_header("Content-Type", "application/json")

with urllib.request.urlopen(login_request) as response:
    token = json.loads(response.read().decode("utf-8"))["access_token"]

req("POST", "/api/claims/1/readiness", headers={"Authorization": f"Bearer {token}"})
PY
```

Expected proof points in the JSON:

- `outcome` is `PASS`
- `pmb_decision.pmb_status` is `CONFIRMED`
- `benefit_routing_decision.route` is `PMB_BENEFIT_BUCKET`
- `costing_preview.pricing_basis` is `DSP`

### 9. Query Postgres to prove persistence

```bash
docker compose exec -T db psql -U postgres -d billing -c "select count(*) from claims;"
docker compose exec -T db psql -U postgres -d billing -c "select count(*) from icd10_reference;"
docker compose exec -T db psql -U postgres -d billing -c "select condition_id, type, name from pmb_conditions order by condition_id;"
docker compose exec -T db psql -U postgres -d billing -c "select count(*) from audit_events;"
```

### 10. Run tests

From the repo root:

```bash
pytest
```

If you want the same Docker-backed test path used during verification:

```bash
docker run --rm \
  --network medhealth-ui_default \
  -e DATABASE_URL=postgresql+psycopg://postgres:postgres@db:5432/billing \
  --mount type=bind,source="$PWD",target=/workspace \
  -w /workspace/backend \
  medhealth-ui-backend \
  pytest tests -q
```

## PowerShell

### 1. Start Docker services

```powershell
docker compose up -d
docker compose ps
```

### 2. Export runtime environment

```powershell
$env:DATABASE_URL = "postgresql+psycopg://postgres:postgres@localhost:5432/billing"
$env:REDIS_URL = "redis://localhost:6379/0"
$env:API_PORT = "8001"
```

### 3. Run migrations

```powershell
docker compose exec backend alembic -c /app/alembic.ini upgrade head
```

### 4. Seed demo reference data

```powershell
docker run --rm `
  --network medhealth-ui_default `
  -e DATABASE_URL=postgresql+psycopg://postgres:postgres@db:5432/billing `
  --mount "type=bind,source=${PWD},target=/workspace" `
  -w /workspace `
  medhealth-ui-backend `
  python infra/seed/seed_reference_data.py
```

### 5. Seed repeatable UAT scenarios

```powershell
docker run --rm `
  --network medhealth-ui_default `
  -e DATABASE_URL=postgresql+psycopg://postgres:postgres@db:5432/billing `
  --mount "type=bind,source=${PWD},target=/workspace" `
  -w /workspace `
  medhealth-ui-backend `
  python infra/seed/seed_uat_scenarios.py
```

### 6. Start or restart the backend

```powershell
docker compose up -d backend
docker compose ps
```

### 7. Verify health

```powershell
Invoke-WebRequest -UseBasicParsing http://localhost:8001/health
```

### 8. Call readiness for a seeded claim

```powershell
$login = Invoke-RestMethod `
  -Method Post `
  -Uri http://localhost:8001/api/auth/login `
  -ContentType "application/json" `
  -Body '{"username":"admin","password":"admin123","role":"Administrator"}'

Invoke-RestMethod `
  -Method Post `
  -Uri http://localhost:8001/api/claims/1/readiness `
  -Headers @{ Authorization = "Bearer $($login.access_token)" } `
  -ContentType "application/json"
```

### 9. Query Postgres

```powershell
docker compose exec -T db psql -U postgres -d billing -c "select count(*) from claims;"
docker compose exec -T db psql -U postgres -d billing -c "select count(*) from icd10_reference;"
docker compose exec -T db psql -U postgres -d billing -c "select condition_id, type, name from pmb_conditions order by condition_id;"
docker compose exec -T db psql -U postgres -d billing -c "select count(*) from audit_events;"
```

### 10. Run tests

```powershell
pytest
```
