"""Switch state update logic."""

import random

from common.logging import get_logger

from .config import settings

logger = get_logger(__name__)


def update_bandwidth(current_bandwidth: float, bw_trend: float) -> tuple[float, float]:
    """Update bandwidth with trend and random variation."""
    new_trend = bw_trend + random.uniform(-0.05, 0.05)
    new_trend = max(min(new_trend, 1.0), -1.0)

    bandwidth = current_bandwidth + new_trend + random.uniform(-2.0, 2.0)
    bandwidth = max(min(bandwidth, 100.0), 0.0)

    return round(bandwidth, 2), new_trend


def update_latency(current_latency: float) -> float:
    """Update latency with spikes."""
    latency = max(current_latency + random.uniform(-0.5, 0.5), 0.2)

    if random.random() < settings.spike_probability:
        latency += random.uniform(10.0, 80.0)
        logger.debug("Latency spike occurred", new_latency=latency)

    return round(latency, 2)


def update_packet_errors(current_errors: int) -> int:
    """Update packet errors with bursts."""
    packet_errors = current_errors

    if random.random() < settings.error_burst_probability:
        packet_errors += random.randint(1, 20)
        logger.debug("Error burst occurred", new_errors=packet_errors)
    else:
        packet_errors = max(packet_errors - random.randint(0, 2), 0)

    return packet_errors


def update_cpu_utilization(current_cpu: float) -> float:
    """Update CPU utilization with fluctuations and spikes."""
    cpu_util = current_cpu + random.uniform(-2.0, 2.0)

    if random.random() < 0.05:  # 5% chance of CPU spike
        cpu_util += random.uniform(10.0, 30.0)

    cpu_util = max(min(cpu_util, 100.0), 0.0)
    return round(cpu_util, 1)


def update_memory_utilization(current_mem: float) -> float:
    """Update memory utilization with slow trends."""
    mem_util = current_mem + random.uniform(-1.0, 1.0)
    mem_util = max(min(mem_util, 100.0), 0.0)
    return round(mem_util, 1)


def update_drops(current_drops: int, bandwidth: float, latency: float) -> int:
    """Update packet drops with correlation to load."""
    drops = current_drops
    drop_probability = 0.02

    # Higher drop chance under load
    if bandwidth > 80.0 or latency > 20.0:
        drop_probability = 0.08

    if random.random() < drop_probability:
        drops += random.randint(1, 10)
        logger.debug("Packet drops occurred", new_drops=drops)
    else:
        drops = max(drops - random.randint(0, 1), 0)

    return drops
