# Telemetry Aggregator

A lightweight, real-time telemetry aggregation system inspired by data-center monitoring platforms such as NVIDIA UFM.

The system simulates telemetry generation from network devices and exposes a low-latency API for querying the latest telemetry metrics. It is designed around asynchronous ingestion, in-memory snapshots, and fast non-blocking reads.

---

## High-Level Architecture

The system consists of two independent services:

1. **Telemetry Simulator**  
   Simulates a set of network switches producing telemetry metrics (bandwidth, latency, errors).
   Metrics are updated periodically and exposed as a CSV matrix over HTTP.

2. **Telemetry Aggregation API**  
   Polls telemetry data from the simulator asynchronously, maintains the latest snapshot in memory,
   and exposes a REST API for querying telemetry metrics with freshness metadata.

```
+--------------------+        +--------------------------+
| Telemetry Simulator| -----> | Telemetry Aggregator API |
|  (port 9001)       |  CSV   |  (port 8080)             |
+--------------------+        +--------------------------+
                                       |
                                       v
                                 REST Clients
```

---

## Key Design Decisions

- **Asynchronous ingestion**  
  Telemetry polling runs in a background task and never blocks API requests.

- **Immutable in-memory snapshots**  
  Each telemetry update replaces the entire snapshot atomically, ensuring consistent reads under
  concurrent access.

- **ETag-based conditional fetching**  
  The simulator supports `ETag` and `If-None-Match`, allowing the aggregator to avoid unnecessary
  parsing and data transfer when telemetry has not changed.

- **Freshness and staleness tracking**  
  API responses include timestamps, age, and staleness indicators to make data freshness explicit.

- **No persistence by design**  
  The system favors fast startup and simplicity over durability. After restart, telemetry is
  re-ingested from the source.

---

## Design Scope and Trade-offs

This implementation intentionally keeps all telemetry data in memory and avoids introducing
external dependencies such as databases, message queues, or persistent storage.

The goal of the assignment is to demonstrate a clear and efficient design for real-time telemetry
ingestion and querying, while avoiding unnecessary over-engineering. An in-memory snapshot model
provides:

- Very low-latency read paths
- Simple and predictable concurrency semantics
- Clear separation between ingestion and serving
- Fast startup and easy local development

Durability, replay, and fault-tolerance are deliberately left out of scope. In a production-grade
system, these concerns could be addressed by introducing durable storage or streaming backends
(e.g., Kafka, Redis Streams, or a time-series database), depending on throughput and reliability
requirements.

---

## Project Structure

```
src/
├── telemetry_simulator/   # Telemetry source simulator (port 9001)
├── telemetry_api/         # Aggregation & query API (port 8080)
├── common/                # Shared utilities (logging, ETags)
scripts/
├── run_simulator.sh
├── run_server.sh
tests/
```

---

## Installation

This project uses **uv** for dependency management.

### Runtime dependencies only (default)
```bash
uv sync
```

This is sufficient to **run the simulator and API services**.

### Development & test dependencies
```bash
uv sync --all-extras
```

This installs development dependencies such as test frameworks and linters.

---

## Running the System

```bash
# activate the virtual environment created by uv command
source .venv/bin/activate

# Run telemetry simulator
./scripts/run_simulator.sh

# Run telemetry API
./scripts/run_server.sh

# Run telemetry API in debug log level
./scripts/run_server.sh --debug
```

---

## Running Tests

Tests require development dependencies:

```bash
# sync virtual environment with all dependencies
uv sync --all-extras

# activate the virtual environment
source .venv/bin/activate

# run pytest from the venv
python -m pytest
```

---

## API Endpoints

### Telemetry Simulator (port 9001)

- `GET /counters`  
  Returns the current telemetry snapshot as a CSV matrix (one row per switch).

- `GET /health`  
  Basic liveness and configuration information.

---

### Telemetry Aggregator API (port 8080)

- `GET /telemetry/metrics`  
  Returns all telemetry metrics for all switches, including freshness metadata.

- `GET /telemetry/metrics/{switch_id}?metric=<metric_name>`  
  Returns the value of a specific metric for a specific switch.

- `GET /health`  
  Returns ingestion and snapshot status information.

---

## Limitations and Future Improvements

- Telemetry is stored in memory only (no persistence or replay).
- Single telemetry source; production systems would support multiple sources or streaming ingestion.
- No authentication or authorization.
- No horizontal scaling or leader election.
- Metrics and tracing are limited to structured logs.

In a production environment, this system could be extended with:
- Streaming ingestion (e.g., gRPC / Kafka / Redis Streams)
- Persistent or replicated state
- Horizontal scaling of the API layer
- Metrics export (Prometheus) and distributed tracing
