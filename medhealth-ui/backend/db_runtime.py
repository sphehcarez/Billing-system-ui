from __future__ import annotations

import os
from contextlib import contextmanager
from typing import Iterator

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker


DATABASE_URL_ENV = "DATABASE_URL"

_engine: Engine | None = None
_SessionLocal: sessionmaker[Session] | None = None


def get_database_url() -> str:
    database_url = os.getenv(DATABASE_URL_ENV)
    if not database_url:
        raise RuntimeError(
            "DATABASE_URL is required. Set it to a PostgreSQL connection string such as "
            "'postgresql+psycopg://postgres:postgres@localhost:5432/billing'."
        )
    return database_url


def get_engine() -> Engine:
    global _engine, _SessionLocal
    if _engine is None:
        _engine = create_engine(
            get_database_url(),
            future=True,
            pool_pre_ping=True,
        )
        _SessionLocal = sessionmaker(bind=_engine, autoflush=False, autocommit=False, expire_on_commit=False, future=True)
    return _engine


def get_sessionmaker() -> sessionmaker[Session]:
    global _SessionLocal
    if _SessionLocal is None:
        get_engine()
    assert _SessionLocal is not None
    return _SessionLocal


def create_session() -> Session:
    return get_sessionmaker()()


@contextmanager
def session_scope() -> Iterator[Session]:
    session = create_session()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def database_healthcheck() -> dict[str, str]:
    try:
        with get_engine().connect() as connection:
            connection.execute(text("SELECT 1"))
        return {"status": "ok", "db": "ok"}
    except Exception:
        return {"status": "degraded", "db": "down"}
