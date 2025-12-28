# Telemetry Aggregator

A telemetry system with simulator and metrics server.

## Structure

- `src/telemetry_simulator/` - Generates telemetry data (port 9001)
- `src/metrics_server/` - Polls and serves metrics (port 8080)  
- `src/common/` - Shared utilities
- `scripts/` - Run scripts

## Usage

```bash
# Install dependencies
uv sync --dev

# Run simulator
./scripts/run_simulator.sh

# Run metrics server  
./scripts/run_server.sh
```

## Endpoints

**Simulator (9001):**
- `GET /counters` - CSV telemetry data
- `GET /health` - Health check

**Metrics Server (8080):**
- `GET /telemetry/metrics` - JSON metrics for all switches
- `GET /telemetry/metrics/{switch_id}?metric=<name>` - Specific switch metric
- `GET /health` - Health check
