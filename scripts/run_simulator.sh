#!/bin/bash
cd "$(dirname "$0")/.."
uvicorn src.telemetry_simulator.app:app --host 0.0.0.0 --port 9001 --reload --log-level info
