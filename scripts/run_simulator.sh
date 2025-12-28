#!/bin/bash
cd "$(dirname "$0")/.."

# Check for debug flag
if [[ "$1" == "--debug" ]]; then
    export LOG_LEVEL=DEBUG
    echo "Running in DEBUG mode"
fi

uvicorn telemetry_simulator.app:app --host 0.0.0.0 --port 9001 --reload --app-dir src
