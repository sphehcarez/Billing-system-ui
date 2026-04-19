from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


LOCAL_ENV_FILE = ".env.local"


def load_local_env() -> Path | None:
    """Load local-only environment overrides without committing them to Git."""
    env_path = Path(__file__).resolve().parent / LOCAL_ENV_FILE
    if not env_path.exists():
        return None

    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        os.environ.setdefault(key, value)

    return env_path


@dataclass(frozen=True)
class RuntimeSettings:
    store_mode: str
    database_url: str | None
    host: str
    port: int

    @property
    def use_inmemory_store(self) -> bool:
        return self.store_mode == "inmemory"

    @property
    def use_persistent_store(self) -> bool:
        return self.store_mode == "persistent"


def get_runtime_settings() -> RuntimeSettings:
    load_local_env()

    store_mode = os.getenv("MEDHEALTH_STORE_MODE", "persistent").strip().lower()
    if store_mode not in {"persistent", "inmemory"}:
        store_mode = "persistent"

    return RuntimeSettings(
        store_mode=store_mode,
        database_url=os.getenv("DATABASE_URL"),
        host=os.getenv("MEDHEALTH_HOST", "0.0.0.0"),
        port=int(os.getenv("MEDHEALTH_PORT", "8001")),
    )
