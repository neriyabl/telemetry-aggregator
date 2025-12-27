"""
Telemetry Simulator API.

This module exposes a lightweight HTTP server that simulates a telemetry source
(e.g., network switches or servers). It maintains an internal, continuously
updated snapshot of telemetry metrics and exposes them via a CSV-based endpoint.

The simulator is intentionally stateful and active: metrics are updated in the
background at a configurable interval, and API requests always return the latest
available snapshot.

Endpoints:
- GET /counters : Returns the current telemetry snapshot as a CSV matrix.
- GET /health   : Returns basic liveness and configuration information.
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI, Response
from fastapi.responses import PlainTextResponse

from common.logging import logger
from .service import start_service, stop_service, get_counters_csv, get_health_status


@asynccontextmanager
async def lifespan(_: FastAPI):
    """
    Application lifespan manager.

    Starts the telemetry simulation service on application startup and ensures
    that background update tasks are gracefully stopped on shutdown.
    """
    logger.info("Telemetry simulator starting on port 9001")
    await start_service()
    yield
    logger.info("Telemetry simulator shutting down")
    await stop_service()


app = FastAPI(title="Telemetry Simulator", version="1.0.0", lifespan=lifespan)


@app.get("/counters", response_class=PlainTextResponse)
async def counters() -> Response:
    """
    Return the current telemetry snapshot in CSV format.

    The response contains a matrix-style CSV where each row represents a switch
    and each column represents a telemetry metric. The snapshot reflects the
    most recently generated telemetry state.
    """
    logger.info("Counters endpoint requested")
    csv_text = await get_counters_csv()
    return Response(content=csv_text, media_type="text/csv; charset=utf-8")


@app.get("/health")
async def health() -> dict:
    """
    Health check endpoint.

    Returns basic service status and configuration details to indicate that the
    telemetry simulator is running and updating metrics as expected.
    """
    logger.info("Health endpoint requested")
    return get_health_status()
