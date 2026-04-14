from platform_api import app

"""
from datetime import datetime, timedelta
import os
from typing import Any, Dict, List, Optional

from fastapi import Depends, FastAPI, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from jose import ExpiredSignatureError, JWTError, jwt
from pydantic import BaseModel


SECRET_KEY = os.getenv("MEDHEALTH_SECRET_KEY", "dev-only-change-me")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
ALLOWED_ORIGINS = [
    "http://localhost:8000",
    "http://127.0.0.1:8000",
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:5500",
    "http://127.0.0.1:5500",
    "null",
]

ROLE_PERMISSIONS = {
    "Administrator": {
        "patients": {"read", "write", "delete"},
        "providers": {"read", "write", "delete"},
        "claims": {"read", "write", "process", "submit"},
        "payments": {"read", "write"},
        "reports": {"read", "generate"},
        "audit": {"read"},
        "users": {"read", "write", "delete"},
        "settings": {"read", "write"},
    },
    "Billing Specialist": {
        "patients": {"read", "write"},
        "providers": {"read", "write"},
        "claims": {"read", "write", "process", "submit"},
        "payments": {"read", "write"},
    },
    "Healthcare Provider": {
        "patients": {"read"},
        "providers": {"read"},
        "claims": {"read", "process"},
    },
    "Finance Officer": {
        "claims": {"read"},
        "payments": {"read", "write"},
        "reports": {"read", "generate"},
    },
    "Compliance Auditor": {
        "patients": {"read"},
        "providers": {"read"},
        "claims": {"read"},
        "payments": {"read"},
        "reports": {"read"},
        "audit": {"read"},
    },
}

DEMO_USERS = {
    "demo.user": {
        "password": "password123",
        "role": "Billing Specialist",
        "email": "demo.user@example.com",
    },
    "admin": {
        "password": "admin123",
        "role": "Administrator",
        "email": "admin@example.com",
    },
    "billing": {
        "password": "billing123",
        "role": "Billing Specialist",
        "email": "billing@example.com",
    },
    "provider": {
        "password": "provider123",
        "role": "Healthcare Provider",
        "email": "provider@example.com",
    },
    "finance": {
        "password": "finance123",
        "role": "Finance Officer",
        "email": "finance@example.com",
    },
    "auditor": {
        "password": "auditor123",
        "role": "Compliance Auditor",
        "email": "auditor@example.com",
    },
}


def utc_now() -> str:
    return datetime.utcnow().isoformat()


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: str


class LoginRequest(BaseModel):
    username: str
    password: str
    role: Optional[str] = None


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
    member_number: Optional[str] = None
    scheme: str = "SCHEMEA"
    amount: float
    status: str = "open"
    readiness_status: str = "pending"
    validation_status: Optional[str] = None
    submission_status: str = "not_submitted"
    submission_channel: Optional[str] = None
    remittance_status: str = "pending"
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


class UserCreate(User):
    password: str


class Report(BaseModel):
    id: Optional[int] = None
    name: str
    report_type: str
    generated_at: str
    period: str


class ReportList(BaseModel):
    reports: List[Report]


class ReportRequest(BaseModel):
    report_type: str
    period: str


class ClaimSubmissionRequest(BaseModel):
    channel: str


class AuditLog(BaseModel):
    id: Optional[int] = None
    user_id: int
    username: str
    action: str
    resource: str
    timestamp: str
    details: str


class Database:
    def __init__(self) -> None:
        self.patients: Dict[int, Patient] = {}
        self.providers: Dict[int, Provider] = {}
        self.claims: Dict[int, Claim] = {}
        self.payments: Dict[int, Payment] = {}
        self.users: Dict[int, User] = {}
        self.reports: Dict[int, Report] = {}
        self.audit_logs: Dict[int, AuditLog] = {}
        self.auth_users: Dict[str, Dict[str, Any]] = {}
        self.settings: Dict[str, Any] = {
            "api_version": "1.0.0",
            "demo_mode": True,
            "database": "in-memory",
            "rbac_enabled": True,
            "audit_logging": True,
            "scheme": "SCHEMEA",
            "option": "OPT1",
            "policy_version": "v1",
        }
        self.counter = {
            "patient": 1,
            "provider": 1,
            "claim": 1,
            "payment": 1,
            "user": 1,
            "report": 1,
            "audit": 1,
        }
        self.init_demo_data()

    def next_id(self, resource: str) -> int:
        value = self.counter[resource]
        self.counter[resource] += 1
        return value

    def add_audit_log(self, user_id: int, username: str, action: str, resource: str, details: str = "") -> AuditLog:
        audit_id = self.next_id("audit")
        audit = AuditLog(
            id=audit_id,
            user_id=user_id,
            username=username,
            action=action,
            resource=resource,
            timestamp=utc_now(),
            details=details,
        )
        self.audit_logs[audit_id] = audit
        return audit

    def register_user(self, username: str, email: str, role: str, password: str, status: str = "active") -> User:
        user_id = self.next_id("user")
        user = User(
            id=user_id,
            username=username,
            email=email,
            role=role,
            status=status,
            created_at=utc_now(),
        )
        self.users[user_id] = user
        self.auth_users[username] = {
            "password": password,
            "role": role,
            "email": email,
            "user_id": user_id,
        }
        return user

    def init_demo_data(self) -> None:
        patient_one = Patient(
            id=self.next_id("patient"),
            name="John Doe",
            mrn="MRN001",
            dob="1985-06-15",
            email="john@example.com",
            phone="555-0001",
            created_at=utc_now(),
        )
        patient_two = Patient(
            id=self.next_id("patient"),
            name="Jane Smith",
            mrn="MRN002",
            dob="1992-03-22",
            email="jane@example.com",
            phone="555-0002",
            created_at=utc_now(),
        )
        self.patients[patient_one.id] = patient_one
        self.patients[patient_two.id] = patient_two

        provider_one = Provider(
            id=self.next_id("provider"),
            name="Dr. Robert Johnson",
            npi="NPI001",
            specialty="Cardiology",
            email="robert@example.com",
            phone="555-1001",
            created_at=utc_now(),
        )
        provider_two = Provider(
            id=self.next_id("provider"),
            name="Dr. Sarah Williams",
            npi="NPI002",
            specialty="Orthopedics",
            email="sarah@example.com",
            phone="555-1002",
            created_at=utc_now(),
        )
        self.providers[provider_one.id] = provider_one
        self.providers[provider_two.id] = provider_two

        claim_one = Claim(
            id=self.next_id("claim"),
            claim_number="CLM001",
            patient_id=patient_one.id,
            provider_id=provider_one.id,
            member_number=patient_one.mrn,
            scheme=self.settings["scheme"],
            amount=1500.00,
            created_at=utc_now(),
            updated_at=utc_now(),
        )
        claim_two = Claim(
            id=self.next_id("claim"),
            claim_number="CLM002",
            patient_id=patient_two.id,
            provider_id=provider_two.id,
            member_number=patient_two.mrn,
            scheme=self.settings["scheme"],
            amount=2200.00,
            status="closed",
            readiness_status="validated",
            validation_status="valid",
            submission_status="submitted",
            submission_channel="direct",
            remittance_status="matched",
            created_at=utc_now(),
            updated_at=utc_now(),
        )
        self.claims[claim_one.id] = claim_one
        self.claims[claim_two.id] = claim_two

        payment = Payment(
            id=self.next_id("payment"),
            claim_id=claim_two.id,
            amount=2200.00,
            payment_date="2026-04-10",
            method="ACH",
            status="completed",
            created_at=utc_now(),
        )
        self.payments[payment.id] = payment

        for username, payload in DEMO_USERS.items():
            self.register_user(username, payload["email"], payload["role"], payload["password"])

        report_specs = [
            ("Claims Summary", "summary", "Q1 2026"),
            ("Payment Analysis", "payment", "Q1 2026"),
            ("Audit Trail", "audit", "Q1 2026"),
        ]
        for name, report_type, period in report_specs:
            report_id = self.next_id("report")
            self.reports[report_id] = Report(
                id=report_id,
                name=name,
                report_type=report_type,
                generated_at=utc_now(),
                period=period,
            )

        billing_id = self.auth_users["billing"]["user_id"]
        finance_id = self.auth_users["finance"]["user_id"]
        self.add_audit_log(billing_id, "billing", "CREATE", "Claim", f"Created claim {claim_one.claim_number}")
        self.add_audit_log(finance_id, "finance", "POST", "Payment", f"Posted payment for claim {claim_two.claim_number}")


db = Database()

app = FastAPI(title="Med Directory Billing API", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    payload = data.copy()
    payload["exp"] = expire
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def extract_token(authorization: Optional[str], legacy_token: Optional[str]) -> str:
    if authorization:
        scheme, _, credentials = authorization.partition(" ")
        if scheme.lower() != "bearer" or not credentials:
            raise HTTPException(status_code=401, detail="Invalid authorization header")
        return credentials.strip()

    if legacy_token:
        return legacy_token.strip()

    raise HTTPException(status_code=401, detail="Authorization token missing")


def verify_token(token: str) -> Dict[str, Any]:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except ExpiredSignatureError as error:
        raise HTTPException(status_code=401, detail="Token expired") from error
    except JWTError as error:
        raise HTTPException(status_code=401, detail="Invalid token") from error

    username = payload.get("sub")
    role = payload.get("role")
    user_id = payload.get("user_id")
    account = db.auth_users.get(username)
    user = db.users.get(user_id)

    if not username or not role or not user_id or account is None or user is None:
        raise HTTPException(status_code=401, detail="Invalid token")

    if account["role"] != role or user.role != role or user.status != "active":
        raise HTTPException(status_code=401, detail="Token no longer valid")

    return {"username": username, "role": role, "user_id": user_id}


def get_current_user(
    authorization: Optional[str] = Header(default=None),
    legacy_token: Optional[str] = Header(default=None, alias="Token"),
) -> Dict[str, Any]:
    token = extract_token(authorization, legacy_token)
    return verify_token(token)


def require_permission(current_user: Dict[str, Any], resource: str, action: str) -> None:
    allowed = ROLE_PERMISSIONS.get(current_user["role"], {}).get(resource, set())
    if action not in allowed:
        raise HTTPException(
            status_code=403,
            detail=f"{current_user['role']} cannot {action} {resource}",
        )


def get_required_item(store: Dict[int, Any], item_id: int, label: str) -> Any:
    item = store.get(item_id)
    if item is None:
        raise HTTPException(status_code=404, detail=f"{label} not found")
    return item


def audit(current_user: Dict[str, Any], action: str, resource: str, details: str) -> None:
    db.add_audit_log(current_user["user_id"], current_user["username"], action, resource, details)


@app.post("/api/auth/login", response_model=Token)
def login(request: LoginRequest) -> Token:
    account = db.auth_users.get(request.username)
    if account is None or account["password"] != request.password:
        raise HTTPException(status_code=401, detail="Invalid username or password")

    access_token = create_access_token(
        {
            "sub": request.username,
            "role": account["role"],
            "user_id": account["user_id"],
        },
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
    )
    return Token(access_token=access_token, role=account["role"])


@app.get("/api/patients", response_model=List[Patient])
def list_patients(current_user: Dict[str, Any] = Depends(get_current_user)) -> List[Patient]:
    require_permission(current_user, "patients", "read")
    return list(db.patients.values())


@app.get("/api/patients/{patient_id}", response_model=Patient)
def get_patient(patient_id: int, current_user: Dict[str, Any] = Depends(get_current_user)) -> Patient:
    require_permission(current_user, "patients", "read")
    return get_required_item(db.patients, patient_id, "Patient")


@app.post("/api/patients", response_model=Patient)
def create_patient(patient: Patient, current_user: Dict[str, Any] = Depends(get_current_user)) -> Patient:
    require_permission(current_user, "patients", "write")
    if any(existing.mrn == patient.mrn for existing in db.patients.values()):
        raise HTTPException(status_code=409, detail="Patient MRN already exists")

    patient.id = db.next_id("patient")
    patient.created_at = utc_now()
    db.patients[patient.id] = patient
    audit(current_user, "CREATE", "Patient", f"Created patient {patient.name}")
    return patient


@app.put("/api/patients/{patient_id}", response_model=Patient)
def update_patient(
    patient_id: int,
    patient: Patient,
    current_user: Dict[str, Any] = Depends(get_current_user),
) -> Patient:
    require_permission(current_user, "patients", "write")
    existing = get_required_item(db.patients, patient_id, "Patient")
    patient.id = patient_id
    patient.created_at = existing.created_at
    db.patients[patient_id] = patient
    audit(current_user, "UPDATE", "Patient", f"Updated patient {patient.name}")
    return patient


@app.delete("/api/patients/{patient_id}")
def delete_patient(patient_id: int, current_user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, str]:
    require_permission(current_user, "patients", "delete")
    get_required_item(db.patients, patient_id, "Patient")

    if any(claim.patient_id == patient_id for claim in db.claims.values()):
        raise HTTPException(status_code=409, detail="Patient has linked claims and cannot be deleted")

    del db.patients[patient_id]
    audit(current_user, "DELETE", "Patient", f"Deleted patient {patient_id}")
    return {"detail": "Patient deleted"}


@app.get("/api/providers", response_model=List[Provider])
def list_providers(current_user: Dict[str, Any] = Depends(get_current_user)) -> List[Provider]:
    require_permission(current_user, "providers", "read")
    return list(db.providers.values())


@app.get("/api/providers/{provider_id}", response_model=Provider)
def get_provider(provider_id: int, current_user: Dict[str, Any] = Depends(get_current_user)) -> Provider:
    require_permission(current_user, "providers", "read")
    return get_required_item(db.providers, provider_id, "Provider")


@app.post("/api/providers", response_model=Provider)
def create_provider(provider: Provider, current_user: Dict[str, Any] = Depends(get_current_user)) -> Provider:
    require_permission(current_user, "providers", "write")
    if any(existing.npi == provider.npi for existing in db.providers.values()):
        raise HTTPException(status_code=409, detail="Provider NPI already exists")

    provider.id = db.next_id("provider")
    provider.created_at = utc_now()
    db.providers[provider.id] = provider
    audit(current_user, "CREATE", "Provider", f"Created provider {provider.name}")
    return provider


@app.put("/api/providers/{provider_id}", response_model=Provider)
def update_provider(
    provider_id: int,
    provider: Provider,
    current_user: Dict[str, Any] = Depends(get_current_user),
) -> Provider:
    require_permission(current_user, "providers", "write")
    existing = get_required_item(db.providers, provider_id, "Provider")
    provider.id = provider_id
    provider.created_at = existing.created_at
    db.providers[provider_id] = provider
    audit(current_user, "UPDATE", "Provider", f"Updated provider {provider.name}")
    return provider


@app.delete("/api/providers/{provider_id}")
def delete_provider(provider_id: int, current_user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, str]:
    require_permission(current_user, "providers", "delete")
    get_required_item(db.providers, provider_id, "Provider")

    if any(claim.provider_id == provider_id for claim in db.claims.values()):
        raise HTTPException(status_code=409, detail="Provider has linked claims and cannot be deleted")

    del db.providers[provider_id]
    audit(current_user, "DELETE", "Provider", f"Deleted provider {provider_id}")
    return {"detail": "Provider deleted"}


@app.get("/api/claims", response_model=List[Claim])
def list_claims(current_user: Dict[str, Any] = Depends(get_current_user)) -> List[Claim]:
    require_permission(current_user, "claims", "read")
    return list(db.claims.values())


@app.get("/api/claims/{claim_id}", response_model=Claim)
def get_claim(claim_id: int, current_user: Dict[str, Any] = Depends(get_current_user)) -> Claim:
    require_permission(current_user, "claims", "read")
    return get_required_item(db.claims, claim_id, "Claim")


@app.post("/api/claims", response_model=Claim)
def create_claim(claim: Claim, current_user: Dict[str, Any] = Depends(get_current_user)) -> Claim:
    require_permission(current_user, "claims", "write")
    patient = get_required_item(db.patients, claim.patient_id, "Patient")
    get_required_item(db.providers, claim.provider_id, "Provider")

    claim.id = db.next_id("claim")
    claim.member_number = claim.member_number or patient.mrn
    claim.scheme = claim.scheme or db.settings["scheme"]
    claim.created_at = utc_now()
    claim.updated_at = claim.created_at
    db.claims[claim.id] = claim
    audit(current_user, "CREATE", "Claim", f"Created claim {claim.claim_number}")
    return claim


@app.put("/api/claims/{claim_id}", response_model=Claim)
def update_claim(
    claim_id: int,
    claim: Claim,
    current_user: Dict[str, Any] = Depends(get_current_user),
) -> Claim:
    require_permission(current_user, "claims", "write")
    existing = get_required_item(db.claims, claim_id, "Claim")
    get_required_item(db.patients, claim.patient_id, "Patient")
    get_required_item(db.providers, claim.provider_id, "Provider")

    claim.id = claim_id
    claim.created_at = existing.created_at
    claim.updated_at = utc_now()
    claim.member_number = claim.member_number or existing.member_number
    claim.scheme = claim.scheme or existing.scheme
    db.claims[claim_id] = claim
    audit(current_user, "UPDATE", "Claim", f"Updated claim {claim.claim_number}")
    return claim


@app.post("/api/claims/{claim_id}/readiness")
def run_readiness_check(claim_id: int, current_user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
    require_permission(current_user, "claims", "process")
    claim = get_required_item(db.claims, claim_id, "Claim")
    claim.readiness_status = "validated"
    claim.updated_at = utc_now()
    audit(current_user, "PROCESS", "Claim", f"Ran readiness check on {claim.claim_number}")
    return {"claim_id": claim.id, "claim_number": claim.claim_number, "status": claim.readiness_status}


@app.post("/api/claims/{claim_id}/close")
def close_claim(claim_id: int, current_user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
    require_permission(current_user, "claims", "process")
    claim = get_required_item(db.claims, claim_id, "Claim")
    if claim.readiness_status != "validated":
        raise HTTPException(status_code=400, detail="Claim must pass readiness before closing")

    claim.status = "closed"
    claim.updated_at = utc_now()
    audit(current_user, "PROCESS", "Claim", f"Closed claim {claim.claim_number}")
    return {"claim_id": claim.id, "claim_number": claim.claim_number, "status": claim.status}


@app.post("/api/claims/{claim_id}/validate")
def post_closure_validate(claim_id: int, current_user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
    require_permission(current_user, "claims", "process")
    claim = get_required_item(db.claims, claim_id, "Claim")
    if claim.status != "closed":
        raise HTTPException(status_code=400, detail="Claim must be closed before validation")

    claim.validation_status = "valid"
    claim.updated_at = utc_now()
    audit(current_user, "PROCESS", "Claim", f"Validated claim {claim.claim_number}")
    return {"claim_id": claim.id, "claim_number": claim.claim_number, "validation_status": claim.validation_status}


@app.post("/api/claims/{claim_id}/submit")
def submit_claim(
    claim_id: int,
    submission: ClaimSubmissionRequest,
    current_user: Dict[str, Any] = Depends(get_current_user),
) -> Dict[str, Any]:
    require_permission(current_user, "claims", "submit")
    claim = get_required_item(db.claims, claim_id, "Claim")
    if claim.status != "closed" or claim.validation_status != "valid":
        raise HTTPException(status_code=400, detail="Claim must be closed and validated before submission")
    if submission.channel not in {"direct", "switch"}:
        raise HTTPException(status_code=400, detail="Submission channel must be direct or switch")

    claim.submission_status = "submitted"
    claim.submission_channel = submission.channel
    claim.remittance_status = "received" if submission.channel == "direct" else "pending"
    claim.updated_at = utc_now()
    audit(current_user, "SUBMIT", "Claim", f"Submitted claim {claim.claim_number} via {submission.channel}")
    return {
        "claim_id": claim.id,
        "claim_number": claim.claim_number,
        "channel": submission.channel,
        "submission_status": claim.submission_status,
    }


@app.get("/api/claims/{claim_id}/remittance")
def get_claim_remittance(claim_id: int, current_user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
    require_permission(current_user, "claims", "read")
    claim = get_required_item(db.claims, claim_id, "Claim")
    status = "matched" if claim.remittance_status in {"received", "matched"} else "pending"
    return {
        "claim_id": claim.id,
        "reference": f"REM-{claim.claim_number}",
        "status": status,
        "amount": claim.amount,
    }


@app.get("/api/claims/{claim_id}/evidence")
def get_claim_evidence(claim_id: int, current_user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
    require_permission(current_user, "claims", "read")
    claim = get_required_item(db.claims, claim_id, "Claim")
    return {
        "claim_id": claim.id,
        "documents": [
            f"{claim.claim_number}-readiness.json",
            f"{claim.claim_number}-validation.json",
            f"{claim.claim_number}-audit-trail.csv",
        ],
    }


@app.get("/api/payments", response_model=List[Payment])
def list_payments(current_user: Dict[str, Any] = Depends(get_current_user)) -> List[Payment]:
    require_permission(current_user, "payments", "read")
    return list(db.payments.values())


@app.get("/api/payments/{payment_id}", response_model=Payment)
def get_payment(payment_id: int, current_user: Dict[str, Any] = Depends(get_current_user)) -> Payment:
    require_permission(current_user, "payments", "read")
    return get_required_item(db.payments, payment_id, "Payment")


@app.post("/api/payments", response_model=Payment)
def create_payment(payment: Payment, current_user: Dict[str, Any] = Depends(get_current_user)) -> Payment:
    require_permission(current_user, "payments", "write")
    get_required_item(db.claims, payment.claim_id, "Claim")
    payment.id = db.next_id("payment")
    payment.created_at = utc_now()
    db.payments[payment.id] = payment
    audit(current_user, "CREATE", "Payment", f"Created payment for claim {payment.claim_id}")
    return payment


@app.put("/api/payments/{payment_id}", response_model=Payment)
def update_payment(
    payment_id: int,
    payment: Payment,
    current_user: Dict[str, Any] = Depends(get_current_user),
) -> Payment:
    require_permission(current_user, "payments", "write")
    existing = get_required_item(db.payments, payment_id, "Payment")
    get_required_item(db.claims, payment.claim_id, "Claim")
    payment.id = payment_id
    payment.created_at = existing.created_at
    db.payments[payment_id] = payment
    audit(current_user, "UPDATE", "Payment", f"Updated payment {payment_id}")
    return payment


@app.get("/api/users", response_model=List[User])
def list_users(current_user: Dict[str, Any] = Depends(get_current_user)) -> List[User]:
    require_permission(current_user, "users", "read")
    return list(db.users.values())


@app.get("/api/users/{user_id}", response_model=User)
def get_user(user_id: int, current_user: Dict[str, Any] = Depends(get_current_user)) -> User:
    require_permission(current_user, "users", "read")
    return get_required_item(db.users, user_id, "User")


@app.post("/api/users", response_model=User)
def create_user(user: UserCreate, current_user: Dict[str, Any] = Depends(get_current_user)) -> User:
    require_permission(current_user, "users", "write")
    if user.role not in ROLE_PERMISSIONS:
        raise HTTPException(status_code=400, detail="Unknown role")
    if user.username in db.auth_users:
        raise HTTPException(status_code=409, detail="Username already exists")

    created_user = db.register_user(user.username, user.email, user.role, user.password, user.status)
    audit(current_user, "CREATE", "User", f"Created user {created_user.username}")
    return created_user


@app.put("/api/users/{user_id}", response_model=User)
def update_user(user_id: int, user: User, current_user: Dict[str, Any] = Depends(get_current_user)) -> User:
    require_permission(current_user, "users", "write")
    existing = get_required_item(db.users, user_id, "User")
    if user.role not in ROLE_PERMISSIONS:
        raise HTTPException(status_code=400, detail="Unknown role")

    auth_record = db.auth_users.pop(existing.username)
    if user.username != existing.username and user.username in db.auth_users:
        db.auth_users[existing.username] = auth_record
        raise HTTPException(status_code=409, detail="Username already exists")

    updated = User(
        id=user_id,
        username=user.username,
        email=user.email,
        role=user.role,
        status=user.status,
        created_at=existing.created_at,
    )
    db.users[user_id] = updated
    auth_record.update({"role": user.role, "email": user.email, "user_id": user_id})
    db.auth_users[user.username] = auth_record
    audit(current_user, "UPDATE", "User", f"Updated user {updated.username}")
    return updated


@app.delete("/api/users/{user_id}")
def delete_user(user_id: int, current_user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, str]:
    require_permission(current_user, "users", "delete")
    user = get_required_item(db.users, user_id, "User")
    if user_id == current_user["user_id"]:
        raise HTTPException(status_code=400, detail="You cannot delete your own account")

    del db.users[user_id]
    db.auth_users.pop(user.username, None)
    audit(current_user, "DELETE", "User", f"Deleted user {user.username}")
    return {"detail": "User deleted"}


@app.get("/api/reports", response_model=ReportList)
def list_reports(current_user: Dict[str, Any] = Depends(get_current_user)) -> ReportList:
    require_permission(current_user, "reports", "read")
    reports = sorted(db.reports.values(), key=lambda report: report.generated_at, reverse=True)
    return ReportList(reports=reports)


@app.get("/api/reports/{report_id}", response_model=Report)
def get_report(report_id: int, current_user: Dict[str, Any] = Depends(get_current_user)) -> Report:
    require_permission(current_user, "reports", "read")
    return get_required_item(db.reports, report_id, "Report")


@app.post("/api/reports/generate", response_model=Report)
def generate_report(
    request: ReportRequest,
    current_user: Dict[str, Any] = Depends(get_current_user),
) -> Report:
    require_permission(current_user, "reports", "generate")
    report_id = db.next_id("report")
    report = Report(
        id=report_id,
        name=f"{request.report_type.title()} Report",
        report_type=request.report_type,
        generated_at=utc_now(),
        period=request.period,
    )
    db.reports[report_id] = report
    audit(current_user, "GENERATE", "Report", f"Generated {request.report_type} report for {request.period}")
    return report


@app.get("/api/audit-logs", response_model=List[AuditLog])
def list_audit_logs(current_user: Dict[str, Any] = Depends(get_current_user)) -> List[AuditLog]:
    require_permission(current_user, "audit", "read")
    logs = list(db.audit_logs.values())
    logs.sort(key=lambda log: log.timestamp, reverse=True)
    return logs


@app.get("/api/settings")
def get_settings(current_user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
    require_permission(current_user, "settings", "read")
    return db.settings


@app.put("/api/settings")
def update_settings(settings: Dict[str, Any], current_user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
    require_permission(current_user, "settings", "write")
    db.settings.update(settings)
    audit(current_user, "UPDATE", "Settings", "Updated system settings")
    return db.settings


@app.get("/api/docs")
def api_docs() -> Dict[str, Any]:
    return {
        "title": "Med Directory Billing API",
        "version": "1.0.0",
        "base_url": "http://localhost:8001/api",
        "authentication": "Bearer token in the Authorization header",
        "workflow_endpoints": {
            "POST /claims/{id}/readiness": "Run readiness validation",
            "POST /claims/{id}/close": "Close a claim after readiness validation",
            "POST /claims/{id}/validate": "Run post-closure validation",
            "POST /claims/{id}/submit": "Submit a closed claim via direct or switch",
            "GET /claims/{id}/remittance": "Read remittance status",
            "GET /claims/{id}/evidence": "List evidence packet artifacts",
        },
        "demo_credentials": {
            username: {"password": payload["password"], "role": payload["role"]}
            for username, payload in DEMO_USERS.items()
        },
    }


@app.get("/")
def health_check() -> Dict[str, str]:
    return {
        "status": "running",
        "service": "Med Directory Billing API",
        "version": "1.0.0",
        "docs": "http://localhost:8001/docs",
        "api_docs": "http://localhost:8001/api/docs",
    }
"""

__all__ = ["app"]
