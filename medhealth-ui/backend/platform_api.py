import os
import asyncio
from datetime import UTC, datetime, timedelta
from typing import Any, Dict, List, Set

from fastapi import Depends, FastAPI, Header, HTTPException, Query, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, PlainTextResponse
from jose import ExpiredSignatureError, JWTError, jwt

from runtime_config import get_runtime_settings
from store_provider import StoreProvider
from platform_core import (
    ClaimClosureRequest,
    ClaimReadinessService,
    ClaimReadyProfile,
    ClaimSubmissionRequest,
    CopayItem,
    Invoice,
    LoginRequest,
    OutboxEvent,
    PatientBalance,
    PolicyProfilePatch,
    RulePatch,
    cents_to_str,
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

_claim_subscribers: dict[int, Set[WebSocket]] = {}

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

class StoreProxy:
    def __init__(self) -> None:
        self._provider = StoreProvider()

    def runtime_mode(self) -> str:
        return self._provider.runtime_mode()

    def runtime_message(self) -> str:
        return self._provider.runtime_message()

    def __getattr__(self, name: str):
        def call(*args, **kwargs):
            store, should_close = self._provider.get_store()
            try:
                return getattr(store, name)(*args, **kwargs)
            finally:
                if should_close:
                    store.close()

        store, should_close = self._provider.get_store()
        try:
            attribute = getattr(store, name)
            if callable(attribute):
                return call
            return attribute
        finally:
            if should_close:
                store.close()


db = StoreProxy()
runtime_settings = get_runtime_settings()
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
    tenant_id = payload.get("tenant_id")
    practice_id = payload.get("practice_id")
    if not username or not role or not user_id or not tenant_id:
        raise HTTPException(status_code=401, detail="Malformed token")
    return {
        "username": username,
        "role": role,
        "user_id": user_id,
        "tenant_id": tenant_id,
        "practice_id": practice_id,
    }


def require_permission(user: Dict[str, Any], resource: str, action: str) -> None:
    allowed = ROLE_PERMISSIONS.get(user["role"], {}).get(resource, set())
    if action not in allowed:
        raise HTTPException(status_code=403, detail=f"{user['role']} may not {action} {resource}")


def current_identity(user: Dict[str, Any]) -> tuple[str, str]:
    return user["username"], user["role"]


def ensure_scope_access(current_user: Dict[str, Any], tenant_id: str) -> None:
    if tenant_id != current_user["tenant_id"]:
        raise HTTPException(status_code=403, detail="Cross-tenant access is not allowed")


def ensure_claim_access(current_user: Dict[str, Any], claim_id: int) -> Dict[str, Any]:
    claim = db.get_claim(claim_id)
    provider = db.get_provider(claim["provider_id"])
    ensure_scope_access(current_user, provider.tenant_id)
    return claim


async def broadcast_claim_update(claim_id: int, update_data: Dict[str, Any]) -> None:
    subscribers = _claim_subscribers.get(claim_id)
    if not subscribers:
        return

    disconnected: list[WebSocket] = []
    for websocket in list(subscribers):
        try:
            await websocket.send_json(
                {
                    "type": "claim_update",
                    "claim_id": claim_id,
                    "timestamp": datetime.now(UTC).isoformat(),
                    "data": update_data,
                }
            )
        except RuntimeError:
            disconnected.append(websocket)

    for websocket in disconnected:
        subscribers.discard(websocket)

    if not subscribers:
        _claim_subscribers.pop(claim_id, None)


@app.get("/")
def root() -> Dict[str, str]:
    return {"message": "Medhealth claims rules platform", "docs": "/docs", "api": "/api/docs"}


@app.get("/health")
def health() -> Dict[str, str]:
    if db.runtime_mode() == "postgresql":
        from db_runtime import database_healthcheck

        health_status = database_healthcheck()
        health_status["runtime"] = "postgresql"
        return health_status
    return {
        "status": "ok",
        "db": "in-memory",
        "runtime": "in-memory",
        "detail": db.runtime_message(),
    }


@app.post("/api/auth/login")
def login(request: LoginRequest) -> Dict[str, Any]:
    auth_record = db.auth_users.get(request.username)
    if not auth_record or auth_record["password"] != request.password:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    token = create_access_token(
        {
            "sub": request.username,
            "role": auth_record["role"],
            "user_id": auth_record["user_id"],
            "tenant_id": auth_record["tenant_id"],
            "practice_id": auth_record.get("practice_id"),
        }
    )
    return {
        "access_token": token,
        "token_type": "bearer",
        "role": auth_record["role"],
        "tenant_id": auth_record["tenant_id"],
        "practice_id": auth_record.get("practice_id"),
    }


@app.get("/api/dashboard/summary")
def dashboard_summary(current_user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
    require_permission(current_user, "claims", "read")
    return db.dashboard_summary(
        tenant_id=current_user["tenant_id"],
        role=current_user["role"],
        practice_id=current_user.get("practice_id"),
        user_id=current_user.get("user_id"),
    )


@app.get("/api/tenants")
def list_tenants(current_user: Dict[str, Any] = Depends(get_current_user)) -> List[Dict[str, Any]]:
    return [db.get_tenant(current_user["tenant_id"]).model_dump()]


@app.get("/api/tenants/{tenant_id}")
def get_tenant(tenant_id: str, current_user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
    ensure_scope_access(current_user, tenant_id)
    return db.get_tenant(tenant_id).model_dump()


@app.get("/api/practices")
def list_practices(
    tenant_id: str | None = None,
    current_user: Dict[str, Any] = Depends(get_current_user),
) -> List[Dict[str, Any]]:
    scoped_tenant_id = tenant_id or current_user["tenant_id"]
    ensure_scope_access(current_user, scoped_tenant_id)
    return db.list_practices(tenant_id=scoped_tenant_id)


@app.get("/api/practices/{practice_id}")
def get_practice(practice_id: str, current_user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
    practice = db.get_practice(practice_id)
    ensure_scope_access(current_user, practice.tenant_id)
    return practice.model_dump()


@app.post("/api/practices")
def create_practice(payload: Dict[str, Any], current_user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
    require_permission(current_user, "providers", "write")
    actor, role = current_identity(current_user)
    target_tenant_id = payload.get("tenant_id") or current_user["tenant_id"]
    ensure_scope_access(current_user, target_tenant_id)
    return db.create_practice(payload, actor, role, tenant_id=target_tenant_id)


@app.get("/api/patients")
def list_patients(current_user: Dict[str, Any] = Depends(get_current_user)) -> List[Dict[str, Any]]:
    require_permission(current_user, "patients", "read")
    return db.list_patients(tenant_id=current_user["tenant_id"])


@app.get("/api/patients/{patient_id}")
def get_patient(patient_id: int, current_user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
    require_permission(current_user, "patients", "read")
    patient = db.get_patient(patient_id)
    ensure_scope_access(current_user, patient.tenant_id)
    return patient.model_dump()


@app.get("/api/patients/{patient_id}/claim-context")
def get_patient_claim_context(patient_id: int, current_user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
    require_permission(current_user, "patients", "read")
    ensure_scope_access(current_user, db.get_patient(patient_id).tenant_id)
    return db.get_patient_claim_context(patient_id)


@app.get("/api/patients/{patient_id}/timeline")
def get_patient_timeline(patient_id: int, current_user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
    require_permission(current_user, "patients", "read")
    ensure_scope_access(current_user, db.get_patient(patient_id).tenant_id)
    return db.get_patient_timeline(patient_id)


@app.post("/api/patients")
def create_patient(payload: Dict[str, Any], current_user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
    require_permission(current_user, "patients", "write")
    actor, role = current_identity(current_user)
    return db.create_patient(
        payload,
        actor,
        role,
        tenant_id=current_user["tenant_id"],
        practice_id=current_user.get("practice_id"),
    )


@app.put("/api/patients/{patient_id}")
def update_patient(patient_id: int, payload: Dict[str, Any], current_user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
    require_permission(current_user, "patients", "write")
    ensure_scope_access(current_user, db.get_patient(patient_id).tenant_id)
    actor, role = current_identity(current_user)
    return db.update_patient(patient_id, payload, actor, role)


@app.delete("/api/patients/{patient_id}", status_code=204)
def delete_patient(patient_id: int, current_user: Dict[str, Any] = Depends(get_current_user)) -> None:
    require_permission(current_user, "patients", "delete")
    ensure_scope_access(current_user, db.get_patient(patient_id).tenant_id)
    actor, role = current_identity(current_user)
    db.delete_patient(patient_id, actor, role)


@app.get("/api/providers")
def list_providers(current_user: Dict[str, Any] = Depends(get_current_user)) -> List[Dict[str, Any]]:
    require_permission(current_user, "providers", "read")
    return db.list_providers(tenant_id=current_user["tenant_id"])


@app.get("/api/providers/{provider_id}")
def get_provider(provider_id: int, current_user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
    require_permission(current_user, "providers", "read")
    provider = db.get_provider(provider_id)
    ensure_scope_access(current_user, provider.tenant_id)
    return provider.model_dump()


@app.post("/api/providers")
def create_provider(payload: Dict[str, Any], current_user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
    require_permission(current_user, "providers", "write")
    actor, role = current_identity(current_user)
    return db.create_provider(
        payload,
        actor,
        role,
        tenant_id=current_user["tenant_id"],
        practice_id=current_user.get("practice_id"),
    )


@app.put("/api/providers/{provider_id}")
def update_provider(provider_id: int, payload: Dict[str, Any], current_user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
    require_permission(current_user, "providers", "write")
    ensure_scope_access(current_user, db.get_provider(provider_id).tenant_id)
    actor, role = current_identity(current_user)
    return db.update_provider(provider_id, payload, actor, role)


@app.delete("/api/providers/{provider_id}", status_code=204)
def delete_provider(provider_id: int, current_user: Dict[str, Any] = Depends(get_current_user)) -> None:
    require_permission(current_user, "providers", "delete")
    ensure_scope_access(current_user, db.get_provider(provider_id).tenant_id)
    actor, role = current_identity(current_user)
    db.delete_provider(provider_id, actor, role)


@app.get("/api/claims")
def list_claims(current_user: Dict[str, Any] = Depends(get_current_user)) -> List[Dict[str, Any]]:
    require_permission(current_user, "claims", "read")
    return db.list_claims(tenant_id=current_user["tenant_id"])


@app.get("/api/claims/worklist")
def claim_worklist(current_user: Dict[str, Any] = Depends(get_current_user)) -> List[Dict[str, Any]]:
    require_permission(current_user, "claims", "read")
    return db.list_worklist(
        tenant_id=current_user["tenant_id"],
        role=current_user["role"],
        practice_id=current_user.get("practice_id"),
    )


@app.get("/api/claims/{claim_id}")
def get_claim(claim_id: int, current_user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
    require_permission(current_user, "claims", "read")
    return ensure_claim_access(current_user, claim_id)


@app.websocket("/ws/claims/{claim_id}")
async def websocket_claim_updates(
    websocket: WebSocket,
    claim_id: int,
    token: str | None = Query(default=None),
) -> None:
    if not token:
        await websocket.close(code=1008, reason="Missing authentication token")
        return

    try:
        current_user = get_current_user(token)
    except HTTPException:
        await websocket.close(code=1008, reason="Invalid authentication token")
        return

    try:
        ensure_claim_access(current_user, claim_id)
    except HTTPException:
        await websocket.close(code=1008, reason="Unauthorized")
        return

    await websocket.accept()
    subscribers = _claim_subscribers.setdefault(claim_id, set())
    subscribers.add(websocket)

    try:
        while True:
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_json({"type": "pong"})
    except WebSocketDisconnect:
        pass
    finally:
        subscribers.discard(websocket)
        if not subscribers:
            _claim_subscribers.pop(claim_id, None)


@app.post("/api/claims")
def create_claim(payload: Dict[str, Any], current_user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
    require_permission(current_user, "claims", "write")
    actor, role = current_identity(current_user)
    return db.create_claim(payload, actor, role, tenant_id=current_user["tenant_id"]).model_dump()


@app.put("/api/claims/{claim_id}")
def update_claim(claim_id: int, payload: Dict[str, Any], current_user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
    require_permission(current_user, "claims", "write")
    actor, role = current_identity(current_user)
    return db.update_claim(claim_id, payload, actor, role)


@app.get("/api/claims/{claim_id}/diagnoses")
def get_claim_diagnoses(claim_id: int, current_user: Dict[str, Any] = Depends(get_current_user)) -> List[Dict[str, Any]]:
    require_permission(current_user, "claims", "read")
    return [item.model_dump() for item in db.get_claim_diagnoses(claim_id)]


@app.post("/api/claims/{claim_id}/diagnoses")
def add_claim_diagnosis(claim_id: int, payload: Dict[str, Any], current_user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
    require_permission(current_user, "claims", "write")
    actor, role = current_identity(current_user)
    return db.add_claim_diagnosis(claim_id, payload, actor, role)


@app.put("/api/claims/{claim_id}/diagnoses/{diagnosis_id}/make-primary")
def make_primary_diagnosis(claim_id: int, diagnosis_id: str, current_user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
    require_permission(current_user, "claims", "write")
    actor, role = current_identity(current_user)
    return db.make_primary_diagnosis(claim_id, diagnosis_id, actor, role)


@app.post("/api/claims/{claim_id}/diagnoses/auto-fix-primary")
def auto_fix_primary_diagnosis(claim_id: int, current_user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
    require_permission(current_user, "claims", "write")
    actor, role = current_identity(current_user)
    return db.auto_fix_primary_diagnosis(claim_id, actor, role)


@app.get("/api/claims/{claim_id}/line-items")
def get_claim_line_items(claim_id: int, current_user: Dict[str, Any] = Depends(get_current_user)) -> List[Dict[str, Any]]:
    require_permission(current_user, "claims", "read")
    return db.get_claim_line_items(claim_id)


@app.get("/api/claims/{claim_id}/attachments")
def get_claim_attachments(claim_id: int, current_user: Dict[str, Any] = Depends(get_current_user)) -> List[Dict[str, Any]]:
    require_permission(current_user, "claims", "read")
    return db.get_claim_attachments(claim_id)


@app.post("/api/claims/{claim_id}/attachments")
def add_claim_attachment(
    claim_id: int,
    payload: Dict[str, Any],
    current_user: Dict[str, Any] = Depends(get_current_user),
) -> Dict[str, Any]:
    require_permission(current_user, "claims", "write")
    actor, role = current_identity(current_user)
    return db.add_claim_attachment(claim_id, payload, actor, role)


@app.delete("/api/claims/{claim_id}/attachments/{document_id}")
def delete_claim_attachment(
    claim_id: int,
    document_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user),
) -> Dict[str, Any]:
    require_permission(current_user, "claims", "write")
    actor, role = current_identity(current_user)
    return db.delete_claim_attachment(claim_id, document_id, actor, role)


@app.put("/api/claims/{claim_id}/line-items/{line_id}/diagnosis-links")
def update_claim_line_item_diagnosis_links(
    claim_id: int,
    line_id: str,
    payload: Dict[str, Any],
    current_user: Dict[str, Any] = Depends(get_current_user),
) -> Dict[str, Any]:
    require_permission(current_user, "claims", "write")
    actor, role = current_identity(current_user)
    return db.update_claim_line_diagnosis_links(
        claim_id,
        line_id,
        list(payload.get("diagnosis_ids") or []),
        actor,
        role,
    )


@app.post("/api/claims/{claim_id}/readiness")
def run_readiness(claim_id: int, current_user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
    require_permission(current_user, "claims", "process")
    ensure_claim_access(current_user, claim_id)
    actor, role = current_identity(current_user)
    result = db.run_readiness(claim_id, actor, role)
    claim = db.get_claim(claim_id)
    asyncio.run(
        broadcast_claim_update(
            claim_id,
            {
                "status": claim["status"],
                "affected_roles": result.get("affected_roles", []),
                "state_progression": result.get("state_progression", []),
                "onboarding_blockers": result.get("onboarding_blockers", []),
            },
        )
    )
    return result


@app.post("/api/claims/{claim_id}/readiness/run")
def run_readiness_alias(claim_id: int, current_user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
    return run_readiness(claim_id, current_user)


@app.post("/api/claims/{claim_id}/close")
def close_claim(claim_id: int, request: ClaimClosureRequest | None = None, current_user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
    require_permission(current_user, "claims", "process")
    ensure_claim_access(current_user, claim_id)
    actor, role = current_identity(current_user)
    result = db.close_claim(claim_id, request or ClaimClosureRequest(), actor, role)
    claim = db.get_claim(claim_id)
    asyncio.run(
        broadcast_claim_update(
            claim_id,
            {
                "status": claim["status"],
                "affected_roles": result.get("affected_roles", []),
                "state_progression": result.get("state_progression", []),
                "onboarding_blockers": result.get("onboarding_blockers", []),
            },
        )
    )
    return result


@app.post("/api/claims/{claim_id}/closure/confirm")
def close_claim_alias(claim_id: int, request: ClaimClosureRequest | None = None, current_user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
    return close_claim(claim_id, request, current_user)


@app.post("/api/claims/{claim_id}/validate")
def post_closure_validate(claim_id: int, current_user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
    require_permission(current_user, "claims", "process")
    ensure_claim_access(current_user, claim_id)
    actor, role = current_identity(current_user)
    result = db.run_post_closure_validation(claim_id, actor, role)
    claim = db.get_claim(claim_id)
    asyncio.run(
        broadcast_claim_update(
            claim_id,
            {
                "status": claim["status"],
                "affected_roles": result.get("affected_roles", []),
                "state_progression": result.get("state_progression", []),
                "onboarding_blockers": result.get("onboarding_blockers", []),
            },
        )
    )
    return result


@app.post("/api/claims/{claim_id}/validation/post-closure")
def post_closure_validate_alias(claim_id: int, current_user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
    return post_closure_validate(claim_id, current_user)


@app.post("/api/claims/{claim_id}/payload")
def build_payload(claim_id: int, current_user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
    require_permission(current_user, "claims", "process")
    ensure_claim_access(current_user, claim_id)
    actor, role = current_identity(current_user)
    return db.build_payload(claim_id, actor, role)


@app.get("/api/claims/{claim_id}/payloads/{version}")
def get_claim_payload(claim_id: int, version: int, current_user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
    require_permission(current_user, "claims", "read")
    ensure_claim_access(current_user, claim_id)
    return db.get_payload_for_claim_version(claim_id, version)


@app.get("/api/claims/{claim_id}/payloads/{version}/structured")
def get_structured_claim_payload(claim_id: int, version: int, current_user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
    require_permission(current_user, "claims", "read")
    ensure_claim_access(current_user, claim_id)
    return db.get_structured_payload(claim_id, version)


@app.post("/api/claims/{claim_id}/payloads/{version}/edi/generate")
def generate_claim_edi(claim_id: int, version: int, current_user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
    require_permission(current_user, "claims", "process")
    ensure_claim_access(current_user, claim_id)
    actor, role = current_identity(current_user)
    return db.generate_edi_artifact(claim_id, version, actor, role)


@app.post("/api/claims/{claim_id}/payloads/{version}/edi/validate")
def validate_claim_edi(claim_id: int, version: int, current_user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
    require_permission(current_user, "claims", "process")
    ensure_claim_access(current_user, claim_id)
    actor, role = current_identity(current_user)
    return db.validate_edi_artifact(claim_id, version, actor, role)


@app.get("/api/claims/{claim_id}/payloads/{version}/edi/download", response_class=PlainTextResponse)
def download_claim_edi(claim_id: int, version: int, current_user: Dict[str, Any] = Depends(get_current_user)) -> PlainTextResponse:
    require_permission(current_user, "claims", "read")
    ensure_claim_access(current_user, claim_id)
    content = db.download_edi_artifact(claim_id, version)
    return PlainTextResponse(
        content,
        headers={"Content-Disposition": f'attachment; filename=\"claim-{claim_id}-v{version}.edi.txt\"'},
    )


@app.post("/api/claims/{claim_id}/payloads/{version}/edi/submit")
def submit_claim_edi(
    claim_id: int,
    version: int,
    channel: str = Query("SWITCH"),
    idempotency_key: str | None = Query(None),
    current_user: Dict[str, Any] = Depends(get_current_user),
) -> Dict[str, Any]:
    require_permission(current_user, "claims", "submit")
    ensure_claim_access(current_user, claim_id)
    actor, role = current_identity(current_user)
    return db.submit_edi_artifact(claim_id, version, channel, idempotency_key, actor, role)


@app.post("/api/claims/{claim_id}/submit")
def submit_claim(claim_id: int, request: ClaimSubmissionRequest, current_user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
    require_permission(current_user, "claims", "submit")
    ensure_claim_access(current_user, claim_id)
    actor, role = current_identity(current_user)
    result = db.submit_claim(claim_id, request, actor, role)
    claim = db.get_claim(claim_id)
    asyncio.run(
        broadcast_claim_update(
            claim_id,
            {
                "status": claim["status"],
                "affected_roles": result.get("affected_roles", []),
                "state_progression": result.get("state_progression", []),
                "onboarding_blockers": result.get("onboarding_blockers", []),
            },
        )
    )
    return result


@app.post("/api/submissions/claims/{claim_id}")
def submit_claim_alias(
    claim_id: int,
    channel: str = Query("DIRECT"),
    idempotency_key: str | None = Query(None),
    current_user: Dict[str, Any] = Depends(get_current_user),
) -> Dict[str, Any]:
    return submit_claim(claim_id, ClaimSubmissionRequest(channel=channel, idempotency_key=idempotency_key), current_user)


@app.get("/api/submissions/{submission_id}/logs")
def submission_logs(submission_id: str, current_user: Dict[str, Any] = Depends(get_current_user)) -> List[Dict[str, Any]]:
    require_permission(current_user, "claims", "read")
    return [item.model_dump() for item in db.get_transport_logs_for_submission(submission_id)]


@app.get("/api/claims/{claim_id}/transport-logs")
def claim_transport_logs(claim_id: int, current_user: Dict[str, Any] = Depends(get_current_user)) -> List[Dict[str, Any]]:
    require_permission(current_user, "claims", "read")
    ensure_claim_access(current_user, claim_id)
    return [item.model_dump() for item in db.get_transport_logs_for_claim(claim_id)]


@app.get("/api/claims/{claim_id}/remittance")
def claim_remittance(claim_id: int, current_user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
    require_permission(current_user, "claims", "read")
    ensure_claim_access(current_user, claim_id)
    return db.get_claim_remittance(claim_id)


@app.get("/api/payments/claims/{claim_id}/remittance")
def claim_remittance_alias(claim_id: int, current_user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
    return claim_remittance(claim_id, current_user)


@app.get("/api/payments/claims/{claim_id}/reconciliation")
def claim_reconciliation(claim_id: int, current_user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
    require_permission(current_user, "payments", "read")
    ensure_claim_access(current_user, claim_id)
    return db.get_claim_reconciliation(claim_id)


@app.get("/api/payments/reconciliation-exceptions")
def list_reconciliation_exceptions(current_user: Dict[str, Any] = Depends(get_current_user)) -> List[Dict[str, Any]]:
    require_permission(current_user, "payments", "read")
    return db.list_reconciliation_exceptions(
        tenant_id=current_user["tenant_id"],
        role=current_user["role"],
    )


@app.post("/api/payments/claims/{claim_id}/reconciliation/resolve")
def resolve_claim_reconciliation(
    claim_id: int,
    payload: Dict[str, Any],
    current_user: Dict[str, Any] = Depends(get_current_user),
) -> Dict[str, Any]:
    require_permission(current_user, "payments", "write")
    ensure_claim_access(current_user, claim_id)
    actor, role = current_identity(current_user)
    resolution = str(payload.get("resolution") or "").upper()
    note = payload.get("note")
    write_off_cents = int(payload.get("write_off_cents") or 0)
    return db.resolve_reconciliation_exception(
        claim_id,
        resolution,
        actor,
        role,
        note=note,
        write_off_cents=write_off_cents,
    )


@app.get("/api/claims/{claim_id}/evidence")
def claim_evidence(claim_id: int, current_user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
    require_permission(current_user, "claims", "read")
    ensure_claim_access(current_user, claim_id)
    return db.get_evidence_packet(claim_id)


@app.get("/api/audit/claims/{claim_id}/evidence-packet")
def claim_evidence_alias(claim_id: int, current_user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
    require_permission(current_user, "audit", "read")
    return db.get_evidence_packet(claim_id)


@app.get("/api/claims/{claim_id}/pmb")
def claim_pmb_decisions(claim_id: int, current_user: Dict[str, Any] = Depends(get_current_user)) -> List[Dict[str, Any]]:
    require_permission(current_user, "claims", "read")
    return db.get_pmb_decisions_for_claim(claim_id)


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
    return db.list_users(tenant_id=current_user["tenant_id"])


@app.get("/api/users/{user_id}")
def get_user(user_id: int, current_user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
    require_permission(current_user, "users", "read")
    user = db.get_user(user_id)
    ensure_scope_access(current_user, user.tenant_id)
    return user.model_dump()


@app.post("/api/users")
def create_user(payload: Dict[str, Any], current_user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
    require_permission(current_user, "users", "write")
    actor, role = current_identity(current_user)
    return db.create_user(
        payload,
        actor,
        role,
        tenant_id=current_user["tenant_id"],
        practice_id=current_user.get("practice_id"),
    )


@app.put("/api/users/{user_id}")
def update_user(user_id: int, payload: Dict[str, Any], current_user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
    require_permission(current_user, "users", "write")
    ensure_scope_access(current_user, db.get_user(user_id).tenant_id)
    actor, role = current_identity(current_user)
    return db.update_user(user_id, payload, actor, role)


@app.delete("/api/users/{user_id}", status_code=204)
def delete_user(user_id: int, current_user: Dict[str, Any] = Depends(get_current_user)) -> None:
    require_permission(current_user, "users", "delete")
    ensure_scope_access(current_user, db.get_user(user_id).tenant_id)
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


@app.get("/api/audit")
def audit_logs_alias(
    entity_type: str | None = Query(None),
    entity_id: str | None = Query(None),
    current_user: Dict[str, Any] = Depends(get_current_user),
) -> List[Dict[str, Any]]:
    require_permission(current_user, "audit", "read")
    rows = db.list_audit_events()
    if entity_type:
        rows = [item for item in rows if str(item["resource"]).startswith(f"{entity_type}:")]
    if entity_id:
        rows = [item for item in rows if str(item["resource"]).endswith(f":{entity_id}")]
    return rows


@app.get("/api/audit/{audit_event_id}")
def audit_event_detail(audit_event_id: str, current_user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
    require_permission(current_user, "audit", "read")
    return db.get_audit_event(audit_event_id)


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


@app.get("/api/reference/icd10")
def icd10_reference(current_user: Dict[str, Any] = Depends(get_current_user)) -> List[Dict[str, Any]]:
    require_permission(current_user, "rules", "read")
    return db.list_icd10_reference()


@app.get("/api/reference/pmb-mappings")
def pmb_mapping_reference(current_user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
    require_permission(current_user, "rules", "read")
    return db.list_pmb_mapping_reference()


@app.get("/api/reference/pmb-mappings/simulate")
def simulate_pmb_mapping(icd10_code: str, current_user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
    require_permission(current_user, "rules", "write")
    return db.simulate_pmb_mapping(icd10_code)


@app.post("/api/reference/pmb-mappings")
def create_pmb_mapping(payload: Dict[str, Any], current_user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
    require_permission(current_user, "rules", "write")
    actor, role = current_identity(current_user)
    return db.create_pmb_mapping(payload, actor, role)


@app.patch("/api/reference/pmb-mappings/{mapping_id}")
def update_pmb_mapping(mapping_id: str, payload: Dict[str, Any], current_user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
    require_permission(current_user, "rules", "write")
    actor, role = current_identity(current_user)
    return db.update_pmb_mapping(mapping_id, payload, actor, role)


@app.delete("/api/reference/pmb-mappings/{mapping_id}")
def delete_pmb_mapping(mapping_id: str, current_user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
    require_permission(current_user, "rules", "write")
    actor, role = current_identity(current_user)
    return db.delete_pmb_mapping(mapping_id, actor, role)


@app.patch("/api/rules/{rule_id}")
def update_rule(rule_id: str, patch: RulePatch, current_user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
    require_permission(current_user, "rules", "write")
    actor, role = current_identity(current_user)
    return db.update_rule(rule_id, patch, actor, role)


@app.get("/api/patients/{patient_id}/claim-ready-profile")
def get_claim_ready_profile(
    patient_id: int,
    current_user: Dict[str, Any] = Depends(get_current_user),
) -> Dict[str, Any]:
    require_permission(current_user, "patients", "read")
    profile = db.claim_readiness_service.evaluate(patient_id)
    return profile.model_dump()


@app.get("/api/patients/{patient_id}/balances")
def get_patient_balance(
    patient_id: int,
    current_user: Dict[str, Any] = Depends(get_current_user),
) -> Dict[str, Any]:
    require_permission(current_user, "patients", "read")
    ensure_scope_access(current_user, db.get_patient(patient_id).tenant_id)
    balance = db.patient_balances.get(patient_id, {"balance_cents": 0, "credit_cents": 0})
    balance_cents = (
        balance.get("balance_cents", 0)
        if isinstance(balance, dict)
        else getattr(balance, "balance_cents", 0)
    )
    credit_cents = (
        balance.get("credit_cents", 0)
        if isinstance(balance, dict)
        else getattr(balance, "credit_cents", 0)
    )
    return {
        "patient_id": patient_id,
        "balance_cents": balance_cents,
        "credit_cents": credit_cents,
        "balance_display": cents_to_str(balance_cents),
    }


@app.get("/api/patients/{patient_id}/invoices")
def get_patient_invoices(
    patient_id: int,
    current_user: Dict[str, Any] = Depends(get_current_user),
) -> List[Dict[str, Any]]:
    require_permission(current_user, "patients", "read")
    ensure_scope_access(current_user, db.get_patient(patient_id).tenant_id)
    all_invoices = db.invoices
    invoices_list = [
        inv for inv in all_invoices.values()
        if (inv.patient_id if hasattr(inv, "patient_id") else inv.get("patient_id")) == patient_id
    ]
    return [
        inv.model_dump() if hasattr(inv, "model_dump") else inv
        for inv in invoices_list
    ]


@app.get("/api/patients/{patient_id}/payments")
def get_patient_payments(
    patient_id: int,
    current_user: Dict[str, Any] = Depends(get_current_user),
) -> List[Dict[str, Any]]:
    require_permission(current_user, "payments", "read")
    ensure_scope_access(current_user, db.get_patient(patient_id).tenant_id)
    return db.list_patient_payments(patient_id)


@app.post("/api/patients/{patient_id}/payments")
def record_patient_payment(
    patient_id: int,
    body: Dict[str, Any],
    idempotency_key: str = Header(default=None, alias="Idempotency-Key"),
    current_user: Dict[str, Any] = Depends(get_current_user),
) -> Dict[str, Any]:
    require_permission(current_user, "payments", "write")
    ensure_scope_access(current_user, db.get_patient(patient_id).tenant_id)
    if not idempotency_key:
        raise HTTPException(status_code=422, detail="Idempotency-Key header is required")
    amount_cents = body.get("amount_cents")
    method = body.get("method", "EFT")
    if not isinstance(amount_cents, int) or amount_cents <= 0:
        raise HTTPException(status_code=422, detail="amount_cents must be a positive integer")
    result = db.record_patient_payment(patient_id, amount_cents, method, idempotency_key, body)
    return result


@app.get("/api/patients/{patient_id}/statement")
def get_patient_statement(
    patient_id: int,
    current_user: Dict[str, Any] = Depends(get_current_user),
) -> Dict[str, Any]:
    require_permission(current_user, "patients", "read")
    ensure_scope_access(current_user, db.get_patient(patient_id).tenant_id)
    actor, role = current_identity(current_user)
    return db.generate_patient_statement(patient_id, actor, role)


@app.get("/api/integrations/switch")
def get_switch_integration_profile(current_user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
    require_permission(current_user, "claims", "read")
    return db.get_switch_integration_profile()


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
            "icd10_validation",
            "claim_diagnosis_capture",
            "pmb_auto_flagging",
            "benefit_routing",
            "costing_preview",
            "validation_summary_popups",
        ],
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        app,
        host=runtime_settings.host,
        port=runtime_settings.port,
    )
