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

from fastapi import FastAPI, Request, Response, status
from fastapi.responses import PlainTextResponse

from common.logging import get_logger, setup_logging

from .config import settings
from .service import get_counters_csv, get_health_status, start_service, stop_service

# Setup logging for this service
setup_logging("telemetry-simulator", settings.log_file_path)
logger = get_logger(__name__)


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
async def counters(request: Request) -> Response:
    """
    Return the current telemetry snapshot in CSV format.

    The response contains a matrix-style CSV where each row represents a switch
    and each column represents a telemetry metric. The snapshot reflects the
    most recently generated telemetry state.
    """
    if_none_match = request.headers.get("if-none-match")
    csv_text, etag = await get_counters_csv(if_none_match)

    if csv_text is None:
        return Response(
            status_code=status.HTTP_304_NOT_MODIFIED, headers={"ETag": etag}
        )

    return Response(
        content=csv_text,
        media_type="text/csv; charset=utf-8",
        headers={"ETag": etag},
    )


@app.get("/health")
async def health() -> dict:
    """
    Health check endpoint.

    Returns basic service status and configuration details to indicate that the
    telemetry simulator is running and updating metrics as expected.
    """
    logger.info("Health endpoint requested")
    return get_health_status()
