#!/bin/bash
cd "$(dirname "$0")/.."
uvicorn src.telemetry_api.app:app --host 0.0.0.0 --port 8080 --reload
