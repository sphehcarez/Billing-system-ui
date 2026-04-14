import os
from datetime import UTC, datetime, timedelta
from typing import Any, Dict, List

from fastapi import Depends, FastAPI, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from jose import ExpiredSignatureError, JWTError, jwt

from platform_core import (
    ClaimClosureRequest,
    ClaimSubmissionRequest,
    LoginRequest,
    PlatformStore,
    PolicyProfilePatch,
    RulePatch,
)


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
        "policies": {"read", "write", "publish"},
        "rules": {"read", "write"},
    },
    "Billing Specialist": {
        "patients": {"read", "write"},
        "providers": {"read", "write"},
        "claims": {"read", "write", "process", "submit"},
        "payments": {"read", "write"},
        "reports": {"read", "generate"},
        "audit": {"read"},
        "policies": {"read"},
        "rules": {"read"},
    },
    "Healthcare Provider": {
        "patients": {"read"},
        "providers": {"read"},
        "claims": {"read", "process"},
        "audit": {"read"},
    },
    "Finance Officer": {
        "claims": {"read"},
        "payments": {"read", "write"},
        "reports": {"read", "generate"},
        "audit": {"read"},
    },
    "Compliance Auditor": {
        "patients": {"read"},
        "providers": {"read"},
        "claims": {"read"},
        "payments": {"read"},
        "reports": {"read"},
        "audit": {"read"},
        "policies": {"read"},
        "rules": {"read"},
    },
}

db = PlatformStore()
app = FastAPI(title="Medhealth Claims Rules Platform", version="2.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(KeyError)
def handle_key_error(_, exc: KeyError) -> JSONResponse:
    return JSONResponse(status_code=404, content={"detail": str(exc).strip("'")})


@app.exception_handler(ValueError)
def handle_value_error(_, exc: ValueError) -> JSONResponse:
    return JSONResponse(status_code=400, content={"detail": str(exc)})


def create_access_token(data: Dict[str, Any], expires_delta: timedelta | None = None) -> str:
    payload = data.copy()
    expire = datetime.now(UTC) + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    payload.update({"exp": expire})
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def get_current_user(authorization: str | None = Header(default=None)) -> Dict[str, Any]:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid Authorization header")
    token = authorization.replace("Bearer ", "", 1).strip()
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except ExpiredSignatureError as exc:
        raise HTTPException(status_code=401, detail="Token has expired") from exc
    except JWTError as exc:
        raise HTTPException(status_code=401, detail="Invalid token") from exc
    username = payload.get("sub")
    role = payload.get("role")
    user_id = payload.get("user_id")
    if not username or not role or not user_id:
        raise HTTPException(status_code=401, detail="Malformed token")
    return {"username": username, "role": role, "user_id": user_id}


def require_permission(user: Dict[str, Any], resource: str, action: str) -> None:
    allowed = ROLE_PERMISSIONS.get(user["role"], {}).get(resource, set())
    if action not in allowed:
        raise HTTPException(status_code=403, detail=f"{user['role']} may not {action} {resource}")


def current_identity(user: Dict[str, Any]) -> tuple[str, str]:
    return user["username"], user["role"]


@app.get("/")
def root() -> Dict[str, str]:
    return {"message": "Medhealth claims rules platform", "docs": "/docs", "api": "/api/docs"}


@app.post("/api/auth/login")
def login(request: LoginRequest) -> Dict[str, Any]:
    auth_record = db.auth_users.get(request.username)
    if not auth_record or auth_record["password"] != request.password:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    token = create_access_token({"sub": request.username, "role": auth_record["role"], "user_id": auth_record["user_id"]})
    return {"access_token": token, "token_type": "bearer", "role": auth_record["role"]}


@app.get("/api/dashboard/summary")
def dashboard_summary(current_user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
    require_permission(current_user, "claims", "read")
    return db.dashboard_summary()


@app.get("/api/patients")
def list_patients(current_user: Dict[str, Any] = Depends(get_current_user)) -> List[Dict[str, Any]]:
    require_permission(current_user, "patients", "read")
    return db.list_patients()


@app.get("/api/patients/{patient_id}")
def get_patient(patient_id: int, current_user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
    require_permission(current_user, "patients", "read")
    return db.get_patient(patient_id).model_dump()


@app.post("/api/patients")
def create_patient(payload: Dict[str, Any], current_user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
    require_permission(current_user, "patients", "write")
    actor, role = current_identity(current_user)
    return db.create_patient(payload, actor, role)


@app.put("/api/patients/{patient_id}")
def update_patient(patient_id: int, payload: Dict[str, Any], current_user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
    require_permission(current_user, "patients", "write")
    actor, role = current_identity(current_user)
    return db.update_patient(patient_id, payload, actor, role)


@app.delete("/api/patients/{patient_id}", status_code=204)
def delete_patient(patient_id: int, current_user: Dict[str, Any] = Depends(get_current_user)) -> None:
    require_permission(current_user, "patients", "delete")
    actor, role = current_identity(current_user)
    db.delete_patient(patient_id, actor, role)


@app.get("/api/providers")
def list_providers(current_user: Dict[str, Any] = Depends(get_current_user)) -> List[Dict[str, Any]]:
    require_permission(current_user, "providers", "read")
    return db.list_providers()


@app.get("/api/providers/{provider_id}")
def get_provider(provider_id: int, current_user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
    require_permission(current_user, "providers", "read")
    return db.get_provider(provider_id).model_dump()


@app.post("/api/providers")
def create_provider(payload: Dict[str, Any], current_user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
    require_permission(current_user, "providers", "write")
    actor, role = current_identity(current_user)
    return db.create_provider(payload, actor, role)


@app.put("/api/providers/{provider_id}")
def update_provider(provider_id: int, payload: Dict[str, Any], current_user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
    require_permission(current_user, "providers", "write")
    actor, role = current_identity(current_user)
    return db.update_provider(provider_id, payload, actor, role)


@app.delete("/api/providers/{provider_id}", status_code=204)
def delete_provider(provider_id: int, current_user: Dict[str, Any] = Depends(get_current_user)) -> None:
    require_permission(current_user, "providers", "delete")
    actor, role = current_identity(current_user)
    db.delete_provider(provider_id, actor, role)


@app.get("/api/claims")
def list_claims(current_user: Dict[str, Any] = Depends(get_current_user)) -> List[Dict[str, Any]]:
    require_permission(current_user, "claims", "read")
    return db.list_claims()


@app.get("/api/claims/worklist")
def claim_worklist(current_user: Dict[str, Any] = Depends(get_current_user)) -> List[Dict[str, Any]]:
    require_permission(current_user, "claims", "read")
    return db.list_worklist()


@app.get("/api/claims/{claim_id}")
def get_claim(claim_id: int, current_user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
    require_permission(current_user, "claims", "read")
    return db.get_claim(claim_id)


@app.post("/api/claims")
def create_claim(payload: Dict[str, Any], current_user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
    require_permission(current_user, "claims", "write")
    actor, role = current_identity(current_user)
    return db.create_claim(payload, actor, role).model_dump()


@app.put("/api/claims/{claim_id}")
def update_claim(claim_id: int, payload: Dict[str, Any], current_user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
    require_permission(current_user, "claims", "write")
    actor, role = current_identity(current_user)
    return db.update_claim(claim_id, payload, actor, role)


@app.post("/api/claims/{claim_id}/readiness")
def run_readiness(claim_id: int, current_user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
    require_permission(current_user, "claims", "process")
    actor, role = current_identity(current_user)
    return db.run_readiness(claim_id, actor, role)


@app.post("/api/claims/{claim_id}/close")
def close_claim(claim_id: int, request: ClaimClosureRequest | None = None, current_user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
    require_permission(current_user, "claims", "process")
    actor, role = current_identity(current_user)
    return db.close_claim(claim_id, request or ClaimClosureRequest(), actor, role)


@app.post("/api/claims/{claim_id}/validate")
def post_closure_validate(claim_id: int, current_user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
    require_permission(current_user, "claims", "process")
    actor, role = current_identity(current_user)
    return db.run_post_closure_validation(claim_id, actor, role)


@app.post("/api/claims/{claim_id}/payload")
def build_payload(claim_id: int, current_user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
    require_permission(current_user, "claims", "process")
    actor, role = current_identity(current_user)
    return db.build_payload(claim_id, actor, role)


@app.post("/api/claims/{claim_id}/submit")
def submit_claim(claim_id: int, request: ClaimSubmissionRequest, current_user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
    require_permission(current_user, "claims", "submit")
    actor, role = current_identity(current_user)
    return db.submit_claim(claim_id, request, actor, role)


@app.get("/api/claims/{claim_id}/remittance")
def claim_remittance(claim_id: int, current_user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
    require_permission(current_user, "claims", "read")
    return db.get_claim_remittance(claim_id)


@app.get("/api/claims/{claim_id}/evidence")
def claim_evidence(claim_id: int, current_user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
    require_permission(current_user, "claims", "read")
    return db.get_evidence_packet(claim_id)


@app.get("/api/payments")
def list_payments(current_user: Dict[str, Any] = Depends(get_current_user)) -> List[Dict[str, Any]]:
    require_permission(current_user, "payments", "read")
    return db.list_payments()


@app.get("/api/payments/{payment_id}")
def get_payment(payment_id: int, current_user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
    require_permission(current_user, "payments", "read")
    return db.get_payment(payment_id).model_dump()


@app.post("/api/payments")
def create_payment(payload: Dict[str, Any], current_user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
    require_permission(current_user, "payments", "write")
    actor, role = current_identity(current_user)
    return db.create_payment(payload, actor, role)


@app.put("/api/payments/{payment_id}")
def update_payment(payment_id: int, payload: Dict[str, Any], current_user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
    require_permission(current_user, "payments", "write")
    actor, role = current_identity(current_user)
    return db.update_payment(payment_id, payload, actor, role)


@app.get("/api/users")
def list_users(current_user: Dict[str, Any] = Depends(get_current_user)) -> List[Dict[str, Any]]:
    require_permission(current_user, "users", "read")
    return db.list_users()


@app.get("/api/users/{user_id}")
def get_user(user_id: int, current_user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
    require_permission(current_user, "users", "read")
    return db.get_user(user_id).model_dump()


@app.post("/api/users")
def create_user(payload: Dict[str, Any], current_user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
    require_permission(current_user, "users", "write")
    actor, role = current_identity(current_user)
    return db.create_user(payload, actor, role)


@app.put("/api/users/{user_id}")
def update_user(user_id: int, payload: Dict[str, Any], current_user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
    require_permission(current_user, "users", "write")
    actor, role = current_identity(current_user)
    return db.update_user(user_id, payload, actor, role)


@app.delete("/api/users/{user_id}", status_code=204)
def delete_user(user_id: int, current_user: Dict[str, Any] = Depends(get_current_user)) -> None:
    require_permission(current_user, "users", "delete")
    actor, role = current_identity(current_user)
    db.delete_user(user_id, actor, role)


@app.get("/api/reports")
def list_reports(current_user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
    require_permission(current_user, "reports", "read")
    return db.list_reports()


@app.post("/api/reports/generate")
def generate_report(payload: Dict[str, Any], current_user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
    require_permission(current_user, "reports", "generate")
    return db.generate_report(payload["report_type"], payload["period"])


@app.get("/api/reports/{report_id}")
def get_report(report_id: int, current_user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
    require_permission(current_user, "reports", "read")
    return db.get_report(report_id)


@app.get("/api/audit-logs")
def audit_logs(current_user: Dict[str, Any] = Depends(get_current_user)) -> List[Dict[str, Any]]:
    require_permission(current_user, "audit", "read")
    return db.list_audit_events()


@app.get("/api/settings")
def get_settings(current_user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
    require_permission(current_user, "settings", "read")
    return db.get_settings()


@app.put("/api/settings")
def update_settings(payload: Dict[str, Any], current_user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
    require_permission(current_user, "settings", "write")
    actor, role = current_identity(current_user)
    return db.update_settings(payload, actor, role)


@app.get("/api/policy-profiles")
def policy_profiles(current_user: Dict[str, Any] = Depends(get_current_user)) -> List[Dict[str, Any]]:
    require_permission(current_user, "policies", "read")
    return db.list_policy_profiles()


@app.post("/api/policy-profiles/{policy_profile_id}/versions")
def create_policy_version(policy_profile_id: str, current_user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
    require_permission(current_user, "policies", "write")
    actor, role = current_identity(current_user)
    return db.create_policy_version(policy_profile_id, actor, role)


@app.patch("/api/policy-profiles/{policy_profile_id}/versions/{version}")
def update_policy_profile(policy_profile_id: str, version: int, patch: PolicyProfilePatch, current_user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
    require_permission(current_user, "policies", "write")
    actor, role = current_identity(current_user)
    return db.update_policy_profile(policy_profile_id, version, patch, actor, role)


@app.post("/api/policy-profiles/{policy_profile_id}/versions/{version}/activate")
def activate_policy_profile(policy_profile_id: str, version: int, current_user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
    require_permission(current_user, "policies", "publish")
    actor, role = current_identity(current_user)
    return db.activate_policy_profile(policy_profile_id, version, actor, role)


@app.get("/api/rules")
def list_rules(current_user: Dict[str, Any] = Depends(get_current_user)) -> List[Dict[str, Any]]:
    require_permission(current_user, "rules", "read")
    return db.list_rules()


@app.patch("/api/rules/{rule_id}")
def update_rule(rule_id: str, patch: RulePatch, current_user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
    require_permission(current_user, "rules", "write")
    actor, role = current_identity(current_user)
    return db.update_rule(rule_id, patch, actor, role)


@app.get("/api/docs")
def api_docs() -> Dict[str, Any]:
    return {
        "name": app.title,
        "version": app.version,
        "capabilities": [
            "draft_claim_crud",
            "readiness",
            "closure_and_snapshot",
            "post_closure_validation",
            "payload_generation",
            "submission_transport",
            "response_handling",
            "adjudication",
            "remittance",
            "reconciliation",
            "audit_evidence",
            "policy_rule_management",
        ],
    }
