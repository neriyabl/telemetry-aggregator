import asyncio
import csv
import io
import time

import httpx
from fastapi import status

from common.etags import normalize_etag
from common.logging import get_logger

from .schemas import Snapshot, SwitchData
from .store import get_etag, set_snapshot

logger = get_logger(__name__)


def _parse_number(v: str) -> int | float:
    # more robust than isdigit() (supports negatives, floats)
    try:
        return int(v)
    except ValueError:
        return float(v)


def parse_counters_csv(
    csv_text: str,
) -> tuple[dict[str, SwitchData], float, list[str]]:
    reader = csv.DictReader(io.StringIO(csv_text))
    if not reader.fieldnames:
        raise ValueError("CSV has no header")

    fieldnames = reader.fieldnames
    if "switch_id" not in fieldnames:
        raise ValueError("CSV missing 'switch_id' column")
    if "last_update_epoch" not in fieldnames:
        raise ValueError("CSV missing 'last_update_epoch' column")

    metric_names = [
        c for c in fieldnames if c not in ("switch_id", "last_update_epoch")
    ]

    data: dict[str, SwitchData] = {}
    last_update_ts: float | None = None

    for row in reader:
        sid = row.get("switch_id")
        if not sid:
            continue

        if last_update_ts is None:
            last_update_ts = float(row["last_update_epoch"])

        metrics: dict[str, float | int] = {}
        for m in metric_names:
            raw = row.get(m)
            if raw is None or raw == "":
                continue
            metrics[m] = _parse_number(raw)

        data[sid] = metrics

    if last_update_ts is None:
        last_update_ts = time.time()

    return data, last_update_ts, metric_names


async def ingestion_loop(
    *,
    source_url: str,
    poll_interval_sec: float,
    timeout_sec: float,
    stop_event: asyncio.Event,
) -> None:
    source_url = source_url.rstrip("/")

    async with httpx.AsyncClient(timeout=timeout_sec) as client:
        while not stop_event.is_set():
            t0 = time.perf_counter()

            etag = await get_etag()
            headers = {"If-None-Match": etag} if etag else {}

            try:
                resp = await client.get(f"{source_url}/counters", headers=headers)
            except Exception as e:
                logger.warning("poll_failed", err=str(e))
                await asyncio.sleep(poll_interval_sec)
                continue

            fetch_ms = int((time.perf_counter() - t0) * 1000)

            if resp.status_code == status.HTTP_304_NOT_MODIFIED:
                logger.debug("poll_not_modified", fetch_ms=fetch_ms, etag=etag)
                await asyncio.sleep(poll_interval_sec)
                continue

            if resp.status_code != status.HTTP_200_OK:
                logger.warning(
                    "poll_bad_status", status=resp.status_code, fetch_ms=fetch_ms
                )
                await asyncio.sleep(poll_interval_sec)
                continue

            new_etag = resp.headers.get("ETag")
            csv_text = resp.text

            # save etag without extra "
            if new_etag:
                new_etag = normalize_etag(new_etag)

            t1 = time.perf_counter()
            try:
                data, last_update_ts, metric_names = parse_counters_csv(csv_text)
            except Exception as e:
                logger.warning("parse_failed", err=str(e))
                await asyncio.sleep(poll_interval_sec)
                continue
            parse_ms = int((time.perf_counter() - t1) * 1000)

            await set_snapshot(
                Snapshot(
                    data=data,
                    metric_names=metric_names,
                    last_update_ts=last_update_ts,
                    etag=new_etag,
                )
            )

            logger.info(
                "snapshot_updated",
                switches=len(data),
                metrics=len(metric_names),
                fetch_ms=fetch_ms,
                parse_ms=parse_ms,
                etag=new_etag,
            )

            await asyncio.sleep(poll_interval_sec)


def start_ingestion(
    *, source_url: str, poll_interval_sec: float, timeout_sec: float
) -> tuple[asyncio.Event, asyncio.Task]:
    stop_event = asyncio.Event()
    task = asyncio.create_task(
        ingestion_loop(
            source_url=source_url,
            poll_interval_sec=poll_interval_sec,
            timeout_sec=timeout_sec,
            stop_event=stop_event,
        )
    )
    return stop_event, task


async def stop_ingestion(stop_event: asyncio.Event, task: asyncio.Task) -> None:
    stop_event.set()
    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        pass
