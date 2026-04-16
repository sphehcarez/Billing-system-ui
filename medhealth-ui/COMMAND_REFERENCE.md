# ⚡ COMMAND REFERENCE

## 🎯 Quick Commands

### Start Frontend (Port 8000)
```bash
cd medhealth-ui
python -m http.server 8000
```

### Start Backend (Port 8001)
```bash
cd medhealth-ui/backend
python main.py
```

### Windows: Automated Start
```bash
START_SYSTEM.bat
```

---

## 🌐 Access URLs

| Service | URL |
|---------|-----|
| Frontend | http://localhost:8000 |
| Backend | http://localhost:8001 |
| API Docs | http://localhost:8001/docs |
| Health | http://localhost:8001/ |

---

## 🔑 Demo Logins

```
admin / admin123
demo.user / password123
billing / billing123
provider / provider123
finance / finance123
auditor / auditor123
```

---

## 🛠️ Installation

```bash
# Install dependencies
pip install -r backend/requirements.txt

# Run backend
python backend/main.py

# In another terminal, run frontend
python -m http.server 8000
```

---

## 📋 API Endpoints (Summary)

```
POST   /api/auth/login              - Login
GET    /api/patients
POST   /api/patients
PUT    /api/patients/{id}
DELETE /api/patients/{id}
GET    /api/providers
POST   /api/providers
PUT    /api/providers/{id}
GET    /api/claims
POST   /api/claims
PUT    /api/claims/{id}
POST   /api/claims/{id}/readiness   - Readiness check
POST   /api/claims/{id}/close       - Close claim
POST   /api/claims/{id}/validate    - Post-closure validate
GET    /api/payments
POST   /api/payments
GET    /api/users
POST   /api/users
GET    /api/reports
POST   /api/reports/generate
GET    /api/audit-logs
GET    /api/settings
PUT    /api/settings
```

---

## 🔐 Default Permissions

### Administrator
✅ All access

### Billing Specialist
✅ Dashboard, Patients, Providers, Claims, Payments

### Healthcare Provider
✅ Dashboard, Patients, Claims

### Finance Officer
✅ Dashboard, Payments, Reports

### Compliance Auditor
✅ Dashboard, Reports, Audit

---

## 🗂️ File Locations

```
medhealth-ui/
├── index.html              (Login)
├── dashboard.html          (Main)
├── backend/main.py         (API Server)
├── js/api-client.js        (API Library)
├── js/app.js               (Main Logic)
├── QUICKSTART.md
├── SYSTEM_README.md
├── API_TESTING.md
└── DEPLOYMENT_SUMMARY.md
```

---

## 🧪 Test Claim Workflow

```bash
# 1. Login
curl -X POST "http://localhost:8001/api/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123","role":"Administrator"}'

# 2. Get token from response, then list claims
curl "http://localhost:8001/api/claims?token=TOKEN"

# 3. Run readiness
curl -X POST "http://localhost:8001/api/claims/1/readiness?token=TOKEN"

# 4. Close claim
curl -X POST "http://localhost:8001/api/claims/1/close?token=TOKEN"

# 5. Validate
curl -X POST "http://localhost:8001/api/claims/1/validate?token=TOKEN"
```

---

## 🛑 Troubleshooting

### Port Already in Use
```bash
# Kill process on port
# Windows:
netstat -ano | findstr :8000
taskkill /PID <PID> /F

# Linux/Mac:
lsof -ti:8000 | xargs kill -9
```

### Module Not Found
```bash
pip install -r backend/requirements.txt
```

### Can't Connect
- Check both servers are running
- Verify ports 8000 and 8001 are available
- Check firewall settings

---

## 📚 Documentation

| File | Purpose |
|------|---------|
| QUICKSTART.md | 5-minute setup |
| SYSTEM_README.md | Complete docs |
| API_TESTING.md | cURL examples |
| DEPLOYMENT_SUMMARY.md | System overview |
| COMMAND_REFERENCE.md | This file |

---

## 🔄 Common Tasks

### View Current Claims
```
http://localhost:8000/claims.html
```

### Create New Claim
```
Claims → Create New → Fill form → Submit
```

### Check Audit Trail
```
Audit → View → See all actions
```

### Test API
```
http://localhost:8001/docs
→ Authorize button
→ Enter demo credentials
→ Test endpoints
```

---

## 📊 System Info

```
Frontend: HTML5/CSS3/JavaScript
Backend: FastAPI + Uvicorn
Auth: JWT Tokens
DB: In-Memory (configurable)
RBAC: 5 roles, server-enforced
Audit: Complete logging
```

---

## ✅ Launch Checklist

- [ ] Python 3.8+ installed
- [ ] Dependencies installed: `pip install -r requirements.txt`
- [ ] Backend running: port 8001
- [ ] Frontend running: port 8000
- [ ] Can access http://localhost:8000
- [ ] Can login with demo credentials
- [ ] Can create records
- [ ] API docs accessible

---

**Everything configured and ready!** 🚀
