from dataclasses import dataclass


@dataclass
class SwitchState:
    bandwidth_gbps: float = 0.0
    latency_ms: float = 0.0
    packet_errors: int = 0
    bw_trend: float = 0.0
    cpu_util_pct: float = 0.0
    mem_util_pct: float = 0.0
    drops: int = 0
