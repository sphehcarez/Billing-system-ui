# Repo Root Confirmation and Run Instructions

## Repo Root

- Working directory: `C:\pe\MEDHEALTH FINAL\Billing system ui`
- Git root: `C:\pe\MEDHEALTH FINAL\Billing system ui\.git`

## Backend

- Framework: FastAPI + Uvicorn
- Current runtime entrypoint: `C:\pe\MEDHEALTH FINAL\Billing system ui\medhealth-ui\backend\main.py`

Actual code references:
- `medhealth-ui/backend/main.py:1-9`
- `medhealth-ui/backend/platform_api.py:81`
- `medhealth-ui/backend/platform_api.py:556-563`

Backend run commands:

```powershell
cd "C:\pe\MEDHEALTH FINAL\Billing system ui\medhealth-ui\backend"
..\..\.venv\Scripts\python.exe main.py
```

Equivalent direct run:

```powershell
cd "C:\pe\MEDHEALTH FINAL\Billing system ui\medhealth-ui\backend"
..\..\.venv\Scripts\python.exe platform_api.py
```

Resolved backend behaviour:
- `medhealth-ui/backend/main.py` imports `platform_api.app`
- `platform_api.py` exposes the live FastAPI app and can run directly under `if __name__ == "__main__"`

## Frontend

- UI type: static HTML + vanilla JS
- Entry page: `medhealth-ui/index.html`
- Claim action page: `medhealth-ui/claim_detail.html`
- API client: `medhealth-ui/js/api-client.js`
- UI controller: `medhealth-ui/js/app.js`

Frontend run command:

```powershell
cd "C:\pe\MEDHEALTH FINAL\Billing system ui\medhealth-ui"
python -m http.server 8000
```

## Served Architecture

- UI is served separately as static files on `http://localhost:8000`
- Backend API is served separately on `http://localhost:8001`
- UI is not mounted inside FastAPI

## Current Local URLs

- UI: `http://localhost:8000/index.html`
- Backend: `http://localhost:8001/`
- Swagger: `http://localhost:8001/docs`
