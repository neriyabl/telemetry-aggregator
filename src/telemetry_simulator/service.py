# Module-level state
import asyncio
import random
import time

from common.etags import etag_from_ts, normalize_etag
from common.logging import get_logger

from .config import settings
from .model import SwitchState

_snapshot: dict[str, SwitchState] = {}
_last_update_ts = 0.0
_lock = asyncio.Lock()
_update_task = None

logger = get_logger(__name__)


def create_initial_state() -> SwitchState:
    """
    Create initial random state for a network switch.

    Returns:
        SwitchState with randomized initial values for bandwidth, latency,
        zero packet errors, and random bandwidth trend.
    """
    return SwitchState(
        bandwidth_gbps=random.uniform(5.0, 80.0),
        latency_ms=random.uniform(1.0, 5.0),
        packet_errors=0,
        bw_trend=random.uniform(-0.2, 0.2),
    )


def create_initial_snapshot(switch_ids: list[str]) -> dict[str, SwitchState]:
    """
    Create initial snapshot with random states for all switches.

    Args:
        switch_ids: List of switch identifier strings.

    Returns:
        Dictionary mapping switch IDs to their initial SwitchState objects.
    """
    snapshot = {sid: create_initial_state() for sid in switch_ids}
    logger.info("Created initial snapshot", switch_count=len(snapshot))
    return snapshot


def update_switch_state(state: SwitchState) -> SwitchState:
    """
    Update switch state with realistic variations and occasional spikes/bursts.

    Args:
        state: Current SwitchState to update.

    Returns:
        New SwitchState with updated values including bandwidth variations,
        latency spikes, and packet error bursts based on configured probabilities.
    """
    # Update bandwidth trend
    bw_trend = state.bw_trend + random.uniform(-0.05, 0.05)
    bw_trend = max(min(bw_trend, 1.0), -1.0)

    # Update bandwidth
    bandwidth = state.bandwidth_gbps + bw_trend + random.uniform(-2.0, 2.0)
    bandwidth = max(min(bandwidth, 100.0), 0.0)

    # Update latency with spikes
    latency = max(state.latency_ms + random.uniform(-0.5, 0.5), 0.2)
    if random.random() < settings.spike_probability:
        latency += random.uniform(10.0, 80.0)
        logger.debug("Latency spike occurred", new_latency=latency)

    # Update packet errors with bursts
    packet_errors = state.packet_errors
    if random.random() < settings.error_burst_probability:
        packet_errors += random.randint(1, 20)
        logger.debug("Error burst occurred", new_errors=packet_errors)
    else:
        packet_errors = max(packet_errors - random.randint(0, 2), 0)

    return SwitchState(
        bandwidth_gbps=round(bandwidth, 2),
        latency_ms=round(latency, 2),
        packet_errors=int(packet_errors),
        bw_trend=bw_trend,
    )


def update_snapshot(
    snapshot: dict[str, SwitchState],
) -> tuple[dict[str, SwitchState], float]:
    """
    Update all switches in snapshot and return new snapshot with timestamp.

    Args:
        snapshot: Current snapshot dictionary mapping switch IDs to states.

    Returns:
        Tuple containing:
        - New snapshot with updated switch states
        - Current timestamp as float
    """
    new_snapshot = {sid: update_switch_state(state) for sid, state in snapshot.items()}
    timestamp = time.time()

    # Log aggregate metrics
    total_bandwidth = sum(s.bandwidth_gbps for s in new_snapshot.values())
    avg_latency = sum(s.latency_ms for s in new_snapshot.values()) / len(new_snapshot)
    total_errors = sum(s.packet_errors for s in new_snapshot.values())

    logger.debug(
        "Snapshot updated",
        total_bandwidth_gbps=round(total_bandwidth, 2),
        avg_latency_ms=round(avg_latency, 2),
        total_packet_errors=total_errors,
    )

    return new_snapshot, timestamp


def snapshot_to_csv(snapshot: dict[str, SwitchState], last_update: float) -> str:
    """
    Convert snapshot to CSV format with headers.

    Args:
        snapshot: Dictionary mapping switch IDs to their current states.
        last_update: Timestamp of the last update as float.

    Returns:
        CSV formatted string with headers and data for all switches.
    """
    lines = ["switch_id," + ",".join(settings.metrics) + ",last_update_epoch"]

    for sid in snapshot.keys():
        state = snapshot[sid]
        row = [
            sid,
            f"{state.bandwidth_gbps:.2f}",
            f"{state.latency_ms:.2f}",
            str(state.packet_errors),
            f"{last_update:.3f}",
        ]
        lines.append(",".join(row))

    csv_data = "\n".join(lines) + "\n"
    logger.debug("Generated CSV", lines=len(lines), size_bytes=len(csv_data))

    return csv_data


async def start_service():
    """
    Start the telemetry service with initial data and background update task.

    Initializes switch data, creates background update task, and starts
    periodic telemetry updates. Safe to call multiple times - won't restart
    if already running.
    """
    global _snapshot, _update_task, _last_update_ts

    if _update_task and not _update_task.done():
        return
    logger.info("Starting telemetry service", switch_count=settings.switch_count)

    switch_ids = [f"sw{i:04d}" for i in range(1, settings.switch_count + 1)]
    _snapshot = create_initial_snapshot(switch_ids)
    _last_update_ts = time.time()
    _update_task = asyncio.create_task(_update_loop())

    logger.info(
        "Telemetry service started", update_interval=settings.update_interval_sec
    )


async def stop_service():
    """
    Stop the telemetry service and cancel background tasks.

    Gracefully cancels the background update task and waits for it to complete.
    Safe to call multiple times.
    """
    global _update_task
    logger.info("Stopping telemetry service")

    if _update_task:
        _update_task.cancel()
        try:
            await _update_task
        except asyncio.CancelledError:
            pass

    logger.info("Telemetry service stopped")


async def _update_loop():
    """
    Background task that periodically updates telemetry data.

    Runs continuously, updating all switch states at configured intervals
    and maintaining thread-safe access to the global snapshot.
    """
    global _snapshot, _last_update_ts
    while True:
        await asyncio.sleep(settings.update_interval_sec)

        new_snapshot, timestamp = update_snapshot(_snapshot)

        async with _lock:
            _snapshot = new_snapshot
            _last_update_ts = timestamp

        logger.debug(
            "Updated telemetry data",
            switches_updated=len(_snapshot),
            timestamp=timestamp,
        )


async def get_counters_csv(if_none_match: str | None) -> tuple[str | None, str]:
    """
    Get telemetry counters in CSV format with ETag support.

    Args:
        if_none_match: ETag value from If-None-Match header for conditional requests.

    Returns:
        Tuple containing:
        - CSV data string or None if not modified (304 response)
        - ETag header value for response
    """
    async with _lock:
        snapshot = _snapshot
        last_update_ts = _last_update_ts

    etag_value = etag_from_ts(last_update_ts)
    etag_header = f'"{etag_value}"'

    inm = normalize_etag(if_none_match)
    if inm is not None and inm == etag_value:
        return None, etag_header

    csv_data = snapshot_to_csv(snapshot, last_update_ts)
    logger.debug(
        "Generated CSV counters",
        switches=len(snapshot),
        last_update=last_update_ts,
        etag=etag_value,
    )
    return csv_data, etag_header


def get_health_status() -> dict:
    """
    Get health status information for the telemetry service.

    Returns:
        Dictionary containing service status, switch count, and update interval.
    """
    status = {
        "status": "ok",
        "switch_count": settings.switch_count,
        "update_interval_sec": settings.update_interval_sec,
    }

    logger.debug("Health check requested", **status)
    return status
