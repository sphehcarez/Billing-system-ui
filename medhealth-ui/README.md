Medhealth Claims Platform

- Static HTML/CSS/JS frontend for the claims workflow
- FastAPI backend under `backend/` for RBAC, readiness, PMB routing, and audit-backed actions
- Uses `assets/MedhealthLogo.png`

Run locally:
- `bash wsl_start_system.sh`

Run with Docker:
- `docker compose up --build`

Access points:
- Frontend: `http://localhost:8000`
- Backend API: `http://localhost:8001`
- API docs: `http://localhost:8001/docs`

Note:
- The frontend displays outcomes, but backend APIs must continue to enforce RBAC and business rules.
