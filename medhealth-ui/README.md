Medhealth Claims Platform

- Static HTML/CSS/JS frontend for the claims workflow
- FastAPI backend under `backend/` for RBAC, readiness, PMB routing, and audit-backed actions
- Uses `assets/MedhealthLogo.png`

Run locally:
- Windows: `START_SYSTEM.bat`
- Manual backend: `..\.venv\Scripts\python.exe backend\main.py`
- Manual frontend: `..\.venv\Scripts\python.exe -m http.server 8000`

Run with Docker:
- `docker compose up --build`

Access points:
- Frontend: `http://localhost:8000`
- Backend API: `http://localhost:8001`
- Backend health: `http://localhost:8001/health`
- API docs: `http://localhost:8001/docs`

Note:
- Localhost-only runtime overrides belong in `backend/.env.local`, which is ignored by Git.
- `backend/.env.local.example` shows how to switch between `MEDHEALTH_STORE_MODE=inmemory` and PostgreSQL.
- The frontend displays outcomes, but backend APIs must continue to enforce RBAC and business rules.
