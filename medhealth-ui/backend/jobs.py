from __future__ import annotations

import os

from celery import Celery

from platform_core import ClaimClosureRequest
from postgres_store import PersistentPlatformStore


REDIS_URL = os.getenv("REDIS_URL")
celery_app = Celery("medhealth_jobs", broker=REDIS_URL, backend=REDIS_URL) if REDIS_URL else Celery("medhealth_jobs")
celery_app.conf.task_always_eager = not bool(REDIS_URL)
celery_app.conf.task_default_retry_delay = 5
celery_app.conf.task_routes = {"jobs.reprocess_claim": {"queue": "claims-reprocess"}}


def queue_enabled() -> bool:
    return bool(REDIS_URL)


@celery_app.task(bind=True, autoretry_for=(Exception,), retry_kwargs={"max_retries": 3})
def reprocess_claim(self, claim_id: int, version: int | None = None) -> dict[str, object]:
    store = PersistentPlatformStore()
    try:
        claim = store.get_claim(claim_id)
        if version is not None and claim["version"] != version:
            return {"claim_id": claim_id, "status": "skipped", "reason": "version_mismatch"}
        readiness = store.run_readiness(claim_id, "celery", "Background Worker")
        validation = None
        if readiness["outcome"] in {"PASS", "WARN"}:
            store.close_claim(claim_id, ClaimClosureRequest(), "celery", "Background Worker")
            validation = store.run_post_closure_validation(claim_id, "celery", "Background Worker")
        return {"claim_id": claim_id, "readiness": readiness, "validation": validation, "queue_enabled": queue_enabled()}
    finally:
        store.close()
