# Module-level state
import asyncio
import random
import time

from common.logging import logger
from .config import SWITCH_COUNT, UPDATE_INTERVAL_SEC, SPIKE_PROBABILITY, ERROR_BURST_PROBABILITY, METRICS
from .model import SwitchState

_snapshot: dict[str, SwitchState] = {}
_last_update_ts = 0.0
_lock = asyncio.Lock()
_update_task = None


def create_initial_state() -> SwitchState:
    return SwitchState(
        bandwidth_gbps=random.uniform(5.0, 80.0),
        latency_ms=random.uniform(1.0, 5.0),
        packet_errors=0,
        bw_trend=random.uniform(-0.2, 0.2)
    )


def create_initial_snapshot(switch_ids: list[str]) -> dict[str, SwitchState]:
    snapshot = {sid: create_initial_state() for sid in switch_ids}
    logger.info("Created initial snapshot", switch_count=len(snapshot))
    return snapshot


def update_switch_state(state: SwitchState) -> SwitchState:
    # Update bandwidth trend
    bw_trend = state.bw_trend + random.uniform(-0.05, 0.05)
    bw_trend = max(min(bw_trend, 1.0), -1.0)
    
    # Update bandwidth
    bandwidth = state.bandwidth_gbps + bw_trend + random.uniform(-2.0, 2.0)
    bandwidth = max(min(bandwidth, 100.0), 0.0)
    
    # Update latency with spikes
    latency = max(state.latency_ms + random.uniform(-0.5, 0.5), 0.2)
    if random.random() < SPIKE_PROBABILITY:
        latency += random.uniform(10.0, 80.0)
        logger.debug("Latency spike occurred", new_latency=latency)
    
    # Update packet errors with bursts
    packet_errors = state.packet_errors
    if random.random() < ERROR_BURST_PROBABILITY:
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


def update_snapshot(snapshot: dict[str, SwitchState]) -> tuple[dict[str, SwitchState], float]:
    new_snapshot = {sid: update_switch_state(state) for sid, state in snapshot.items()}
    timestamp = time.time()
    
    # Log aggregate metrics
    total_bandwidth = sum(s.bandwidth_gbps for s in new_snapshot.values())
    avg_latency = sum(s.latency_ms for s in new_snapshot.values()) / len(new_snapshot)
    total_errors = sum(s.packet_errors for s in new_snapshot.values())
    
    logger.debug("Snapshot updated",
                total_bandwidth_gbps=round(total_bandwidth, 2),
                avg_latency_ms=round(avg_latency, 2),
                total_packet_errors=total_errors)
    
    return new_snapshot, timestamp


def snapshot_to_csv(snapshot: dict[str, SwitchState], last_update: float) -> str:
    lines = ["switch_id," + ",".join(METRICS) + ",last_update_epoch"]
    
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
    global _snapshot, _update_task

    if _update_task and not _update_task.done():
        return
    logger.info("Starting telemetry service", switch_count=SWITCH_COUNT)
    
    switch_ids = [f"sw{i:04d}" for i in range(1, SWITCH_COUNT + 1)]
    _snapshot = create_initial_snapshot(switch_ids)
    _update_task = asyncio.create_task(_update_loop())
    
    logger.info("Telemetry service started", update_interval=UPDATE_INTERVAL_SEC)


async def stop_service():
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
    global _snapshot, _last_update_ts
    while True:
        await asyncio.sleep(UPDATE_INTERVAL_SEC)
        
        new_snapshot, timestamp = update_snapshot(_snapshot)
        
        async with _lock:
            _snapshot = new_snapshot
            _last_update_ts = timestamp
        
        logger.debug("Updated telemetry data", 
                    switches_updated=len(_snapshot),
                    timestamp=timestamp)


async def get_counters_csv() -> str:
    async with _lock:
        snapshot = _snapshot
        last_update_ts = _last_update_ts

    csv_data = snapshot_to_csv(snapshot, last_update_ts)
        
    logger.info("Generated CSV counters", 
               switches=len(_snapshot),
               last_update=_last_update_ts)
    
    return csv_data


def get_health_status() -> dict:
    status = {
        "status": "ok",
        "switch_count": SWITCH_COUNT,
        "update_interval_sec": UPDATE_INTERVAL_SEC
    }
    
    logger.debug("Health check requested", **status)
    return status
