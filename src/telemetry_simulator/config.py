import os

# Environment configuration
SWITCH_COUNT = int(os.getenv("SWITCH_COUNT", "32"))
UPDATE_INTERVAL_SEC = float(os.getenv("UPDATE_INTERVAL_SEC", "10"))
SPIKE_PROBABILITY = float(os.getenv("SPIKE_PROBABILITY", "0.03"))
ERROR_BURST_PROBABILITY = float(os.getenv("ERROR_BURST_PROBABILITY", "0.02"))

# Metrics configuration
METRICS: list[str] = ["bandwidth_gbps", "latency_ms", "packet_errors"]
