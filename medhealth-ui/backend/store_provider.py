from __future__ import annotations

from typing import TYPE_CHECKING, Any

from platform_core import PlatformStore
from runtime_config import get_runtime_settings

if TYPE_CHECKING:
    from postgres_store import PersistentPlatformStore


class StoreProvider:
    def __init__(self) -> None:
        self._settings = get_runtime_settings()
        self._inmemory_store: PlatformStore | None = None
        self._runtime_reason = "persistent runtime active"

    def _get_inmemory_store(self) -> PlatformStore:
        if self._inmemory_store is None:
            self._inmemory_store = PlatformStore()
        return self._inmemory_store

    def runtime_mode(self) -> str:
        return "in-memory" if self._settings.use_inmemory_store else "postgresql"

    def runtime_message(self) -> str:
        if self._settings.use_inmemory_store:
            return "local in-memory runtime enabled by MEDHEALTH_STORE_MODE=inmemory"
        return self._runtime_reason

    def get_store(self) -> tuple[Any, bool]:
        if self._settings.use_inmemory_store:
            self._runtime_reason = "local in-memory runtime enabled by MEDHEALTH_STORE_MODE=inmemory"
            return self._get_inmemory_store(), False

        try:
            from postgres_store import PersistentPlatformStore

            self._runtime_reason = "persistent runtime active"
            return PersistentPlatformStore(), True
        except Exception as exc:
            raise RuntimeError(
                "Persistent runtime initialization failed. Configure DATABASE_URL for PostgreSQL "
                "or set MEDHEALTH_STORE_MODE=inmemory in backend/.env.local for localhost-only development."
            ) from exc
