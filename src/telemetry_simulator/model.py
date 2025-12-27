from dataclasses import dataclass

@dataclass
class SwitchState:
    bandwidth_gbps: float = 0.0
    latency_ms: float = 0.0
    packet_errors: int = 0
    bw_trend: float = 0.0


