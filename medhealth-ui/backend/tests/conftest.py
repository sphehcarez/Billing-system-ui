from __future__ import annotations

import os
import pathlib
import sys

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text


ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

os.environ.setdefault("DATABASE_URL", "postgresql+psycopg://postgres:postgres@localhost:5432/billing")

from db_runtime import create_session
from db_schema import TRUNCATE_TABLES
from demo_seed import seed_reference_data, seed_uat_scenarios
from postgres_store import PersistentPlatformStore
import platform_api


def _truncate_all() -> None:
    session = create_session()
    try:
        names = ", ".join(table.name for table in TRUNCATE_TABLES)
        session.execute(text(f"TRUNCATE TABLE {names} RESTART IDENTITY CASCADE"))
        session.commit()
    finally:
        session.close()


@pytest.fixture(autouse=True)
def seeded_db():
    _truncate_all()
    store = PersistentPlatformStore()
    try:
        seed_reference_data(store)
    finally:
        store.close()
    yield
    _truncate_all()


@pytest.fixture()
def reference_store():
    store = PersistentPlatformStore()
    try:
        yield store
    finally:
        store.close()


@pytest.fixture()
def uat_context(reference_store):
    claim_ids = seed_uat_scenarios(reference_store)
    return {"store": reference_store, "claim_ids": claim_ids}


@pytest.fixture()
def client():
    with TestClient(platform_api.app) as test_client:
        yield test_client


@pytest.fixture()
def admin_headers(client):
    response = client.post("/api/auth/login", json={"username": "admin", "password": "admin123", "role": "Administrator"})
    assert response.status_code == 200, response.text
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}
