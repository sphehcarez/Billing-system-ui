from __future__ import annotations

import pathlib
import sys


ROOT = pathlib.Path(__file__).resolve().parents[2]
BACKEND = ROOT / "backend"
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

from demo_seed import dumps_pretty, seed_reference_data
from postgres_store import PersistentPlatformStore


def main() -> None:
    store = PersistentPlatformStore()
    try:
        payload = seed_reference_data(store)
        print(dumps_pretty({"seed": "reference_data", "result": payload}))
    finally:
        store.close()


if __name__ == "__main__":
    main()
