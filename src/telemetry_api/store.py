import asyncio
import time
from typing import Any

from .schemas import Snapshot

_lock = asyncio.Lock()
_snapshot: Snapshot | None = None
_last_ingest_ts: float | None = None


async def set_snapshot(snapshot: Snapshot) -> None:
    global _snapshot, _last_ingest_ts
    async with _lock:
        _snapshot = snapshot
        _last_ingest_ts = time.time()


async def get_snapshot() -> Snapshot | None:
    async with _lock:
        return _snapshot


async def get_etag() -> str | None:
    async with _lock:
        return _snapshot.etag if _snapshot else None


async def meta() -> dict[str, Any]:
    async with _lock:
        snap = _snapshot
        return {
            "has_snapshot": snap is not None,
            "last_update_ts": snap.last_update_ts if snap else None,
            "age_ms": int((time.time() - snap.last_update_ts) * 1000) if snap else None,
            "etag": snap.etag if snap else None,
            "last_ingest_ts": _last_ingest_ts,
        }
