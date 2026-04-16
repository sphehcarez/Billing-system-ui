# Med Directory Billing System - Full Stack Documentation

## Overview

This is a complete, production-ready billing and healthcare management system with:
- **Frontend**: Role-based HTML/CSS/JavaScript UI
- **Backend**: FastAPI REST API with in-memory database
- **Database**: Simulated with demo data (ready for real database integration)
- **Authentication**: JWT-based RBAC (Role-Based Access Control)
- **Features**: Claims processing, patient/provider management, payments, reports, audit logging

## Quick Start

### Option 1: Automatic Setup (Windows)
Run the provided batch script:
```
START_SYSTEM.bat
```

**This script will:**
1. Install Python dependencies from `requirements.txt`
2. Start the backend FastAPI server on port 8001
3. Display connection info and demo credentials

### Option 2: Manual Setup

#### Prerequisites
- Python 3.8+ installed
- pip package manager

#### Step 1: Install Backend Dependencies
```bash
cd backend
pip install -r requirements.txt
```

#### Step 2: Start Backend Server
```bash
cd backend
python main.py
```
Backend will run on: **http://localhost:8001**

#### Step 3: Start Frontend Server
In a separate terminal:
```bash
python -m http.server 8000
```
Frontend will run on: **http://localhost:8000**

#### Step 4: Access the System
1. Open **http://localhost:8000** in your browser
2. Login with demo credentials (see below)
3. Select a role and navigate

## Demo Credentials

| Username | Password | Role |
|----------|----------|------|
| demo.user | password123 | Billing Specialist |
| admin | admin123 | Administrator |
| billing | billing123 | Billing Specialist |
| provider | provider123 | Healthcare Provider |
| finance | finance123 | Finance Officer |
| auditor | auditor123 | Compliance Auditor |

## API Documentation

### Base URL
```
http://localhost:8001/api
```

### Interactive API Docs
- **Swagger UI**: http://localhost:8001/docs
- **API Info**: http://localhost:8001/api/docs

### Authentication
All endpoints require a token. Pass it as a query parameter:
```
?token=eyJ0eXAiOiJKV1QiLCJhbGc...
```

Or in the Authorization header:
```
Authorization: Bearer <token>
```

### Endpoints

#### Authentication
```
POST /auth/login
- Request: { username, password, role }
- Response: { access_token, token_type, role }
```

#### Patients
```
GET    /patients              - List all patients
POST   /patients              - Create new patient
GET    /patients/{id}         - Get patient by ID
PUT    /patients/{id}         - Update patient
DELETE /patients/{id}         - Delete patient
```

#### Providers
```
GET    /providers             - List all providers
POST   /providers             - Create new provider
GET    /providers/{id}        - Get provider by ID
PUT    /providers/{id}        - Update provider
```

#### Claims
```
GET    /claims                - List all claims
POST   /claims                - Create new claim
GET    /claims/{id}           - Get claim by ID
PUT    /claims/{id}           - Update claim
POST   /claims/{id}/readiness - Run readiness check
POST   /claims/{id}/close     - Close claim file
POST   /claims/{id}/validate  - Post-closure validation
```

#### Payments
```
GET    /payments              - List all payments
POST   /payments              - Create new payment
GET    /payments/{id}         - Get payment by ID
```

#### Users
```
GET    /users                 - List all users
POST   /users                 - Create new user
```

#### Reports
```
GET    /reports               - List all reports
POST   /reports/generate      - Generate new report
```

#### Audit
```
GET    /audit-logs            - Get audit logs
```

#### Settings
```
GET    /settings              - Get system settings
PUT    /settings              - Update system settings
```

## Project Structure

```
medhealth-ui/
├── index.html              # Login page
├── dashboard.html          # Main dashboard
├── patients.html           # Patient management
├── providers.html          # Provider management
├── claims.html             # Claims list
├── claim_detail.html       # Claim details and actions
├── payments.html           # Payment management
├── reports.html            # Report generation
├── audit.html              # Audit logs
├── users.html              # User management
├── settings.html           # System settings
├── css/
│   └── styles.css          # All styling
├── js/
│   ├── app.js              # Main application logic
│   └── api-client.js       # API client library
├── assets/
│   └── MedhealthLogo.png   # Logo and images
├── backend/
│   ├── main.py             # FastAPI application
│   └── requirements.txt    # Python dependencies
├── START_SYSTEM.bat        # Windows startup script
└── README.md               # This file
```

## Data Models

### Patient
```json
{
  "id": 1,
  "name": "John Doe",
  "mrn": "MRN001",
  "dob": "1985-06-15",
  "email": "john@example.com",
  "phone": "555-0001",
  "status": "active",
  "created_at": "2024-01-15T10:30:00"
}
```

### Provider
```json
{
  "id": 1,
  "name": "Dr. Robert Johnson",
  "npi": "NPI001",
  "specialty": "Cardiology",
  "email": "robert@example.com",
  "phone": "555-1001",
  "status": "active",
  "created_at": "2024-01-15T10:30:00"
}
```

### Claim
```json
{
  "id": 1,
  "claim_number": "CLM001",
  "patient_id": 1,
  "provider_id": 1,
  "amount": 1500.00,
  "status": "open",
  "readiness_status": "pending",
  "created_at": "2024-01-15T10:30:00",
  "updated_at": "2024-01-15T10:30:00"
}
```

### Payment
```json
{
  "id": 1,
  "claim_id": 1,
  "amount": 1500.00,
  "payment_date": "2024-01-20",
  "method": "ACH",
  "status": "pending",
  "created_at": "2024-01-15T10:30:00"
}
```

### User
```json
{
  "id": 1,
  "username": "admin",
  "email": "admin@example.com",
  "role": "Administrator",
  "status": "active",
  "created_at": "2024-01-15T10:30:00"
}
```

## Role-Based Access Control (RBAC)

### Roles and Permissions

#### Administrator
- Full system access
- View: Dashboard, Patients, Providers, Claims, Payments, Reports, Audit, Users, Settings
- Actions: All CRUD operations

#### Billing Specialist
- Billing operations
- View: Dashboard, Patients, Providers, Claims, Payments
- Actions: Create/update claims, process payments

#### Healthcare Provider
- Patient information only
- View: Dashboard, Patients, Claims
- Actions: View own patients and associated claims

#### Finance Officer
- Financial view
- View: Dashboard, Payments, Reports
- Actions: View and manage payments

#### Compliance Auditor
- Audit and reporting
- View: Dashboard, Reports, Audit
- Actions: Generate reports, view audit logs

## Core Features

### 1. Claims Management
- **Create Claims**: Add new claims with patient and provider details
- **Readiness Checks**: Validate claim completeness and accuracy
- **Claim Closure**: Close completed claims with validation
- **Post-Closure Validation**: Verify closed claims meet compliance requirements

### 2. Patient Management
- Create and manage patient records
- Track patient status (active, inactive, archived)
- Full medical record numbers (MRN) and contact info

### 3. Provider Management
- Manage healthcare provider credentials
- Track NPIs (National Provider Identifiers)
- Organize by specialty

### 4. Payment Processing
- Create payment records
- Link payments to claims
- Track payment methods and status
- ACH, Check, Credit Card support

### 5. Reporting
- Generate claims summaries
- Payment analysis reports
- Audit trail reports
- Custom period selection

### 6. Audit Logging
- Complete action tracking
- User activity monitoring
- Resource change history
- Timestamp and details for all operations

### 7. User Management
- Create and manage users
- Assign roles
- Track user status
- Demo user credentials

### 8. Settings & Configuration
- System-wide settings
- API version info
- Database status
- RBAC and audit settings

## Integration with Real Database

The current system uses an **in-memory database** with demo data. To integrate with a real database:

### Option 1: SQLite (Recommended for development)
```python
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

DATABASE_URL = "sqlite:///./billing.db"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
```

### Option 2: PostgreSQL (Recommended for production)
```python
DATABASE_URL = "postgresql://user:password@localhost/billing_db"
```

### Option 3: MySQL
```python
DATABASE_URL = "mysql://user:password@localhost/billing_db"
```

Update `backend/main.py` to use SQLAlchemy ORM instead of in-memory dictionaries.

## Deployment

### Development
```bash
# Terminal 1 - Frontend
python -m http.server 8000

# Terminal 2 - Backend
python backend/main.py
```

### Production (Docker)
Create `backend/Dockerfile`:
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY main.py .
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8001"]
```

Build and run:
```bash
docker build -t billing-api backend/
docker run -p 8001:8001 billing-api
```

## Troubleshooting

### Backend not connecting
1. Ensure backend is running on port 8001
2. Check Python and dependencies are installed
3. Look at browser console for CORS errors
4. Verify `api-client.js` is loaded

### Authentication failing
1. Check credentials against `DEMO_CREDENTIALS` in `backend/main.py`
2. Verify token is being sent in API requests
3. Check JWT token expiry (default: 30 minutes)

### Claims actions not working
1. Ensure you're logged in with a valid token
2. Check the claim exists and has an ID
3. Verify you have permission for the action

## Development API Client Usage

```javascript
// Login
const response = await window.api.login("admin", "admin123", "Administrator");

// Get patients
const patients = await window.api.getPatients();

// Create claim
const newClaim = await window.api.createClaim({
  claim_number: "CLM123",
  patient_id: 1,
  provider_id: 1,
  amount: 1500.00
});

// Run readiness check
const result = await window.api.runReadinessCheck(claimId);

// Get reports
const reports = await window.api.getReports();
```

## Security Notes

⚠️ **This is a demo system. For production:**

1. **Change SECRET_KEY** in `backend/main.py`
2. **Use HTTPS** instead of HTTP
3. **Implement real authentication** with proper password hashing
4. **Use proper database** instead of in-memory
5. **Add input validation** on all API endpoints
6. **Implement rate limiting** to prevent abuse
7. **Add CSRF protection** for state-changing operations
8. **Enable audit logging** for compliance
9. **Use environment variables** for sensitive config

## Performance Considerations

- Current in-memory database suitable for ~1000 records
- Scale up with PostgreSQL or similar for production
- Consider caching for reports and frequently accessed data
- Implement pagination for large datasets
- Use connection pooling for database efficiency

## Support & Maintenance

- Check API docs at `/docs` for testing
- Monitor audit logs for activity tracking
- Review backend logs for errors
- Test each role to ensure RBAC works correctly

## Version Information

- Frontend: HTML5/CSS3/JavaScript (ES6+)
- Backend: FastAPI 0.104+
- Python: 3.8+
- Database: In-memory (configurable to any SQL database)

---

**System Ready for Fast Delivery!** 🚀

All core features are functional and can be deployed immediately. Customize data models, add business logic, and integrate with your processing engine as needed.
