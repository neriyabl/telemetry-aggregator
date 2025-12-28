"""
In-memory snapshot store for telemetry data.

This module maintains the latest telemetry snapshot ingested from the simulator.
Snapshots are replaced atomically and treated as immutable, allowing lock-free
reads on the request path for low-latency API responses.

Concurrency model:
- Writes (snapshot updates) are protected by a lock.
- Reads are lock-free and return the latest available snapshot reference.
"""

import asyncio
import time
from typing import Any

from common.logging import get_logger

from .schemas import Snapshot

logger = get_logger(__name__)

_lock = asyncio.Lock()
_snapshot: Snapshot | None = None
_last_ingest_ts: float | None = None


async def set_snapshot(snapshot: Snapshot) -> None:
    """
    Atomically replace the current telemetry snapshot.

    This function is called by the ingestion loop after successfully parsing
    new telemetry data. The entire snapshot is swapped at once to ensure
    readers always observe a consistent view.

    Args:
        snapshot: Immutable Snapshot object containing the latest telemetry data.
    """
    global _snapshot, _last_ingest_ts
    async with _lock:
        _snapshot = snapshot
        _last_ingest_ts = time.time()


async def get_snapshot() -> Snapshot | None:
    """
    Retrieve the latest telemetry snapshot.

    This function is intentionally lock-free to avoid contention on the
    request path. Callers may receive either the previous or the latest
    snapshot, both of which are valid and internally consistent.

    Returns:
        The latest Snapshot, or None if ingestion has not completed yet.
    """
    return _snapshot


async def get_etag() -> str | None:
    """
    Retrieve the current snapshot ETag, if available.

    Used by the ingestion loop to perform conditional polling using
    If-None-Match headers.

    Returns:
        ETag string if a snapshot exists, otherwise None.
    """
    snap = _snapshot
    return snap.etag if snap else None


async def meta() -> dict[str, Any]:
    """
    Return metadata about the current snapshot and ingestion status.

    Provides basic observability into snapshot freshness and ingestion activity.
    This function is lock-free and may return slightly inconsistent timing
    values, which is acceptable for monitoring purposes.

    Returns:
        Dictionary containing snapshot presence, timestamps, age, and ETag.
    """
    snap = _snapshot
    return {
        "has_snapshot": snap is not None,
        "last_update_ts": snap.last_update_ts if snap else None,
        "age_ms": int((time.time() - snap.last_update_ts) * 1000) if snap else None,
        "etag": snap.etag if snap else None,
        "last_ingest_ts": _last_ingest_ts,
    }
