"""Compatibility entrypoint for the current claims-platform API."""

from platform_api import app


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8001)

'''
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime, timedelta
from jose import jwt
import os
from pathlib import Path

# ============================================================================
# CONFIG & MODELS
# ============================================================================

SECRET_KEY = "your-secret-key-change-in-production"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

app = FastAPI(title="Med Directory Billing API", version="1.0.0")

# Enable CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================================================
# PYDANTIC MODELS
# ============================================================================

class Token(BaseModel):
    access_token: str
    token_type: str
    role: str

class LoginRequest(BaseModel):
    username: str
    password: str
    role: str

class Patient(BaseModel):
    id: Optional[int] = None
    name: str
    mrn: str
    dob: str
    email: str
    phone: str
    status: str = "active"
    created_at: Optional[str] = None

class Provider(BaseModel):
    id: Optional[int] = None
    name: str
    npi: str
    specialty: str
    email: str
    phone: str
    status: str = "active"
    created_at: Optional[str] = None

class Claim(BaseModel):
    id: Optional[int] = None
    claim_number: str
    patient_id: int
    provider_id: int
    amount: float
    status: str = "open"
    readiness_status: str = "pending"
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

class Payment(BaseModel):
    id: Optional[int] = None
    claim_id: int
    amount: float
    payment_date: str
    method: str
    status: str = "pending"
    created_at: Optional[str] = None

class User(BaseModel):
    id: Optional[int] = None
    username: str
    email: str
    role: str
    status: str = "active"
    created_at: Optional[str] = None

class Report(BaseModel):
    id: Optional[int] = None
    name: str
    report_type: str
    generated_at: str
    period: str

class AuditLog(BaseModel):
    id: Optional[int] = None
    user_id: int
    action: str
    resource: str
    timestamp: str
    details: str

# ============================================================================
# SIMULATED IN-MEMORY DATABASE
# ============================================================================

class Database:
    def __init__(self):
        self.patients = {}
        self.providers = {}
        self.claims = {}
        self.payments = {}
        self.users = {}
        self.audit_logs = {}
        self.counter = {"patient": 1, "provider": 1, "claim": 1, "payment": 1, "user": 1, "audit": 1}
        self.init_demo_data()

    def init_demo_data(self):
        # Demo patients
        self.patients[1] = Patient(
            id=1, name="John Doe", mrn="MRN001", dob="1985-06-15",
            email="john@example.com", phone="555-0001", created_at=datetime.now().isoformat()
        )
        self.patients[2] = Patient(
            id=2, name="Jane Smith", mrn="MRN002", dob="1992-03-22",
            email="jane@example.com", phone="555-0002", created_at=datetime.now().isoformat()
        )
        self.counter["patient"] = 3

        # Demo providers
        self.providers[1] = Provider(
            id=1, name="Dr. Robert Johnson", npi="NPI001", specialty="Cardiology",
            email="robert@example.com", phone="555-1001", created_at=datetime.now().isoformat()
        )
        self.providers[2] = Provider(
            id=2, name="Dr. Sarah Williams", npi="NPI002", specialty="Orthopedics",
            email="sarah@example.com", phone="555-1002", created_at=datetime.now().isoformat()
        )
        self.counter["provider"] = 3

        # Demo claims
        self.claims[1] = Claim(
            id=1, claim_number="CLM001", patient_id=1, provider_id=1, amount=1500.00,
            status="open", readiness_status="pending", created_at=datetime.now().isoformat()
        )
        self.claims[2] = Claim(
            id=2, claim_number="CLM002", patient_id=2, provider_id=2, amount=2200.00,
            status="closed", readiness_status="validated", created_at=datetime.now().isoformat()
        )
        self.counter["claim"] = 3

        # Demo users
        self.users[1] = User(
            id=1, username="admin", email="admin@example.com", role="Administrator",
            created_at=datetime.now().isoformat()
        )
        self.users[2] = User(
            id=2, username="billing", email="billing@example.com", role="Billing Specialist",
            created_at=datetime.now().isoformat()
        )
        self.counter["user"] = 3

    def add_audit_log(self, user_id: int, action: str, resource: str, details: str = ""):
        log_id = self.counter["audit"]
        audit = AuditLog(
            id=log_id, user_id=user_id, action=action, resource=resource,
            timestamp=datetime.now().isoformat(), details=details
        )
        self.audit_logs[log_id] = audit
        self.counter["audit"] += 1
        return audit

db = Database()

# ============================================================================
# AUTHENTICATION
# ============================================================================

DEMO_CREDENTIALS = {
    "demo.user": "password123",
    "admin": "admin123",
    "billing": "billing123",
    "provider": "provider123",
    "finance": "finance123",
    "auditor": "auditor123"
}

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def verify_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        role: str = payload.get("role")
        if username is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        return {"username": username, "role": role}
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

def get_current_user(token: str = None):
    if not token:
        raise HTTPException(status_code=401, detail="Authorization token missing")
    return verify_token(token)

# ============================================================================
# AUTH ENDPOINTS
# ============================================================================

@app.post("/api/auth/login", response_model=Token)
def login(request: LoginRequest):
    """Authenticate user and return JWT token"""
    if request.username not in DEMO_CREDENTIALS:
        raise HTTPException(status_code=401, detail="Invalid username")
    if DEMO_CREDENTIALS[request.username] != request.password:
        raise HTTPException(status_code=401, detail="Invalid password")
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": request.username, "role": request.role},
        expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer", "role": request.role}

# ============================================================================
# PATIENT ENDPOINTS
# ============================================================================

@app.get("/api/patients", response_model=List[Patient])
def list_patients(token: str = None):
    """Get all patients"""
    current_user = get_current_user(token)
    return list(db.patients.values())

@app.get("/api/patients/{patient_id}", response_model=Patient)
def get_patient(patient_id: int, token: str = None):
    """Get patient by ID"""
    current_user = get_current_user(token)
    if patient_id not in db.patients:
        raise HTTPException(status_code=404, detail="Patient not found")
    return db.patients[patient_id]

@app.post("/api/patients", response_model=Patient)
def create_patient(patient: Patient, token: str = None):
    """Create new patient"""
    current_user = get_current_user(token)
    patient_id = db.counter["patient"]
    patient.id = patient_id
    patient.created_at = datetime.now().isoformat()
    db.patients[patient_id] = patient
    db.counter["patient"] += 1
    db.add_audit_log(1, "CREATE", "Patient", f"Created patient {patient.name}")
    return patient

@app.put("/api/patients/{patient_id}", response_model=Patient)
def update_patient(patient_id: int, patient: Patient, token: str = None):
    """Update patient"""
    current_user = get_current_user(token)
    if patient_id not in db.patients:
        raise HTTPException(status_code=404, detail="Patient not found")
    patient.id = patient_id
    db.patients[patient_id] = patient
    db.add_audit_log(1, "UPDATE", "Patient", f"Updated patient {patient.name}")
    return patient

@app.delete("/api/patients/{patient_id}")
def delete_patient(patient_id: int, token: str = None):
    """Delete patient"""
    current_user = get_current_user(token)
    if patient_id not in db.patients:
        raise HTTPException(status_code=404, detail="Patient not found")
    del db.patients[patient_id]
    db.add_audit_log(1, "DELETE", "Patient", f"Deleted patient ID {patient_id}")
    return {"detail": "Patient deleted"}

# ============================================================================
# PROVIDER ENDPOINTS
# ============================================================================

@app.get("/api/providers", response_model=List[Provider])
def list_providers(token: str = None):
    """Get all providers"""
    current_user = get_current_user(token)
    return list(db.providers.values())

@app.get("/api/providers/{provider_id}", response_model=Provider)
def get_provider(provider_id: int, token: str = None):
    """Get provider by ID"""
    current_user = get_current_user(token)
    if provider_id not in db.providers:
        raise HTTPException(status_code=404, detail="Provider not found")
    return db.providers[provider_id]

@app.post("/api/providers", response_model=Provider)
def create_provider(provider: Provider, token: str = None):
    """Create new provider"""
    current_user = get_current_user(token)
    provider_id = db.counter["provider"]
    provider.id = provider_id
    provider.created_at = datetime.now().isoformat()
    db.providers[provider_id] = provider
    db.counter["provider"] += 1
    db.add_audit_log(1, "CREATE", "Provider", f"Created provider {provider.name}")
    return provider

@app.put("/api/providers/{provider_id}", response_model=Provider)
def update_provider(provider_id: int, provider: Provider, token: str = None):
    """Update provider"""
    current_user = get_current_user(token)
    if provider_id not in db.providers:
        raise HTTPException(status_code=404, detail="Provider not found")
    provider.id = provider_id
    db.providers[provider_id] = provider
    db.add_audit_log(1, "UPDATE", "Provider", f"Updated provider {provider.name}")
    return provider

# ============================================================================
# CLAIM ENDPOINTS
# ============================================================================

@app.get("/api/claims", response_model=List[Claim])
def list_claims(token: str = None):
    """Get all claims"""
    current_user = get_current_user(token)
    return list(db.claims.values())

@app.get("/api/claims/{claim_id}", response_model=Claim)
def get_claim(claim_id: int, token: str = None):
    """Get claim by ID"""
    current_user = get_current_user(token)
    if claim_id not in db.claims:
        raise HTTPException(status_code=404, detail="Claim not found")
    return db.claims[claim_id]

@app.post("/api/claims", response_model=Claim)
def create_claim(claim: Claim, token: str = None):
    """Create new claim"""
    current_user = get_current_user(token)
    claim_id = db.counter["claim"]
    claim.id = claim_id
    claim.created_at = datetime.now().isoformat()
    claim.updated_at = datetime.now().isoformat()
    db.claims[claim_id] = claim
    db.counter["claim"] += 1
    db.add_audit_log(1, "CREATE", "Claim", f"Created claim {claim.claim_number}")
    return claim

@app.put("/api/claims/{claim_id}", response_model=Claim)
def update_claim(claim_id: int, claim: Claim, token: str = None):
    """Update claim"""
    current_user = get_current_user(token)
    if claim_id not in db.claims:
        raise HTTPException(status_code=404, detail="Claim not found")
    claim.id = claim_id
    claim.updated_at = datetime.now().isoformat()
    db.claims[claim_id] = claim
    db.add_audit_log(1, "UPDATE", "Claim", f"Updated claim {claim.claim_number}")
    return claim

@app.post("/api/claims/{claim_id}/readiness")
def run_readiness_check(claim_id: int, token: str = None):
    """Run readiness validation on claim"""
    current_user = get_current_user(token)
    if claim_id not in db.claims:
        raise HTTPException(status_code=404, detail="Claim not found")
    
    claim = db.claims[claim_id]
    claim.readiness_status = "validated"
    db.add_audit_log(1, "ACTION", "Claim", f"Ran readiness check on {claim.claim_number}")
    return {"claim_id": claim_id, "status": "validated", "message": "Readiness check passed"}

@app.post("/api/claims/{claim_id}/close")
def close_claim(claim_id: int, token: str = None):
    """Close claim file"""
    current_user = get_current_user(token)
    if claim_id not in db.claims:
        raise HTTPException(status_code=404, detail="Claim not found")
    
    claim = db.claims[claim_id]
    claim.status = "closed"
    claim.updated_at = datetime.now().isoformat()
    db.add_audit_log(1, "ACTION", "Claim", f"Closed claim {claim.claim_number}")
    return {"claim_id": claim_id, "status": "closed", "message": "Claim closed successfully"}

@app.post("/api/claims/{claim_id}/validate")
def post_closure_validate(claim_id: int, token: str = None):
    """Post-closure validation"""
    current_user = get_current_user(token)
    if claim_id not in db.claims:
        raise HTTPException(status_code=404, detail="Claim not found")
    
    claim = db.claims[claim_id]
    db.add_audit_log(1, "ACTION", "Claim", f"Post-closure validation on {claim.claim_number}")
    return {"claim_id": claim_id, "validation_status": "valid", "message": "Post-closure validation passed"}

# ============================================================================
# PAYMENT ENDPOINTS
# ============================================================================

@app.get("/api/payments", response_model=List[Payment])
def list_payments(token: str = None):
    """Get all payments"""
    current_user = get_current_user(token)
    return list(db.payments.values())

@app.get("/api/payments/{payment_id}", response_model=Payment)
def get_payment(payment_id: int, token: str = None):
    """Get payment by ID"""
    current_user = get_current_user(token)
    if payment_id not in db.payments:
        raise HTTPException(status_code=404, detail="Payment not found")
    return db.payments[payment_id]

@app.post("/api/payments", response_model=Payment)
def create_payment(payment: Payment, token: str = None):
    """Create new payment"""
    current_user = get_current_user(token)
    payment_id = db.counter["payment"]
    payment.id = payment_id
    payment.created_at = datetime.now().isoformat()
    db.payments[payment_id] = payment
    db.counter["payment"] += 1
    db.add_audit_log(1, "CREATE", "Payment", f"Created payment for claim {payment.claim_id}")
    return payment

# ============================================================================
# USER ENDPOINTS
# ============================================================================

@app.get("/api/users", response_model=List[User])
def list_users(token: str = None):
    """Get all users"""
    current_user = get_current_user(token)
    return list(db.users.values())

@app.post("/api/users", response_model=User)
def create_user(user: User, token: str = None):
    """Create new user"""
    current_user = get_current_user(token)
    user_id = db.counter["user"]
    user.id = user_id
    user.created_at = datetime.now().isoformat()
    db.users[user_id] = user
    db.counter["user"] += 1
    db.add_audit_log(1, "CREATE", "User", f"Created user {user.username}")
    return user

# ============================================================================
# REPORT ENDPOINTS
# ============================================================================

@app.get("/api/reports")
def list_reports(token: str = None):
    """Get all reports"""
    current_user = get_current_user(token)
    return {
        "reports": [
            {"id": 1, "name": "Claims Summary", "report_type": "summary", "generated_at": datetime.now().isoformat(), "period": "Q1 2024"},
            {"id": 2, "name": "Payment Analysis", "report_type": "payment", "generated_at": datetime.now().isoformat(), "period": "Q1 2024"},
            {"id": 3, "name": "Audit Trail", "report_type": "audit", "generated_at": datetime.now().isoformat(), "period": "Q1 2024"},
        ]
    }

@app.post("/api/reports/generate")
def generate_report(report_type: str, period: str, token: str = None):
    """Generate a new report"""
    current_user = get_current_user(token)
    db.add_audit_log(1, "GENERATE", "Report", f"Generated {report_type} report for {period}")
    return {
        "id": 1, "name": f"{report_type} Report", "report_type": report_type,
        "generated_at": datetime.now().isoformat(), "period": period
    }

# ============================================================================
# AUDIT ENDPOINTS
# ============================================================================

@app.get("/api/audit-logs")
def list_audit_logs(token: str = None):
    """Get audit logs"""
    current_user = get_current_user(token)
    return list(db.audit_logs.values())

# ============================================================================
# SETTINGS ENDPOINTS
# ============================================================================

@app.get("/api/settings")
def get_settings(token: str = None):
    """Get system settings"""
    current_user = get_current_user(token)
    return {
        "api_version": "1.0.0",
        "demo_mode": True,
        "database": "in-memory",
        "rbac_enabled": True,
        "audit_logging": True
    }

@app.put("/api/settings")
def update_settings(settings: dict, token: str = None):
    """Update system settings"""
    current_user = get_current_user(token)
    db.add_audit_log(1, "UPDATE", "Settings", "Updated system settings")
    return {"detail": "Settings updated"}

# ============================================================================
# API DOCUMENTATION
# ============================================================================

@app.get("/api/docs")
def api_docs():
    """API Documentation"""
    return {
        "title": "Med Directory Billing API",
        "version": "1.0.0",
        "base_url": "http://localhost:8001/api",
        "documentation": "Full API documentation available at /docs (Swagger UI)",
        "endpoints": {
            "auth": {
                "POST /auth/login": "Authenticate user and get JWT token"
            },
            "patients": {
                "GET /patients": "List all patients",
                "POST /patients": "Create new patient",
                "GET /patients/{id}": "Get patient by ID",
                "PUT /patients/{id}": "Update patient",
                "DELETE /patients/{id}": "Delete patient"
            },
            "providers": {
                "GET /providers": "List all providers",
                "POST /providers": "Create new provider",
                "GET /providers/{id}": "Get provider by ID",
                "PUT /providers/{id}": "Update provider"
            },
            "claims": {
                "GET /claims": "List all claims",
                "POST /claims": "Create new claim",
                "GET /claims/{id}": "Get claim by ID",
                "PUT /claims/{id}": "Update claim",
                "POST /claims/{id}/readiness": "Run readiness check",
                "POST /claims/{id}/close": "Close claim",
                "POST /claims/{id}/validate": "Post-closure validation"
            },
            "payments": {
                "GET /payments": "List all payments",
                "POST /payments": "Create new payment",
                "GET /payments/{id}": "Get payment by ID"
            },
            "users": {
                "GET /users": "List all users",
                "POST /users": "Create new user"
            },
            "reports": {
                "GET /reports": "List all reports",
                "POST /reports/generate": "Generate new report"
            },
            "audit": {
                "GET /audit-logs": "Get audit logs"
            },
            "settings": {
                "GET /settings": "Get system settings",
                "PUT /settings": "Update system settings"
            }
        },
        "demo_credentials": {
            "username": "demo.user or admin or billing or provider or finance or auditor",
            "password": "password123 or admin123 (see code for all)"
        }
    }

# ============================================================================
# HEALTH CHECK
# ============================================================================

@app.get("/")
def health_check():
    """Health check endpoint"""
    return {
        "status": "running",
        "service": "Med Directory Billing API",
        "version": "1.0.0",
        "docs": "http://localhost:8001/docs",
        "api_docs": "http://localhost:8001/api/docs"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
'''
