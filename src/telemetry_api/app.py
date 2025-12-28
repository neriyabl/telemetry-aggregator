import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse

from common.logging import get_logger, setup_logging

from .config import settings
from .ingestion import start_ingestion, stop_ingestion
from .schemas import (
    HealthResponse,
    ListMetricsResponse,
    MetricResponse,
    WarmingUpResponse,
)
from .store import get_snapshot, meta

# Setup logging for this service
setup_logging("telemetry-api", settings.log_file_path)
logger = get_logger(__name__)

_stop_event = None
_task = None


@asynccontextmanager
async def lifespan(_: FastAPI):
    global _stop_event, _task
    logger.info("metrics_server_starting", **settings.model_dump())
    _stop_event, _task = start_ingestion(
        source_url=str(settings.telemetry_source_url),
        poll_interval_sec=settings.poll_interval_sec,
        timeout_sec=settings.http_timeout_sec,
    )
    yield
    logger.info("metrics_server_shutting_down")
    await stop_ingestion(_stop_event, _task)


app = FastAPI(title="Telemetry Aggregator", version="1.0.0", lifespan=lifespan)


@app.middleware("http")
async def timing_middleware(request: Request, call_next):
    t0 = time.perf_counter()
    resp = await call_next(request)
    dt_ms = int((time.perf_counter() - t0) * 1000)
    logger.debug(
        "api_request", path=request.url.path, status=resp.status_code, duration_ms=dt_ms
    )
    return resp


@app.get("/telemetry/metrics", response_model=ListMetricsResponse)
async def list_metrics():
    snap = await get_snapshot()
    if snap is None:
        return JSONResponse(content=WarmingUpResponse().model_dump(), status_code=503)

    age_ms = int((time.time() - snap.last_update_ts) * 1000)
    stale = (time.time() - snap.last_update_ts) > settings.stale_after_sec

    return ListMetricsResponse(
        data=snap.data,
        metric_names=snap.metric_names,
        component_count=len(snap.data),
        last_update_ts=snap.last_update_ts,
        age_ms=age_ms,
        stale=stale,
        etag=snap.etag,
    )


@app.get("/telemetry/metrics/{component_id}", response_model=MetricResponse)
async def get_metric(component_id: str, metric: str):
    snapshot = await get_snapshot()
    if snapshot is None:
        raise HTTPException(status_code=503, detail="warming_up")

    component = snapshot.data.get(component_id)
    if component is None:
        raise HTTPException(
            status_code=404, detail=f"component {component_id} Not Found"
        )

    if metric not in component:
        raise HTTPException(
            status_code=404,
            detail=f"unknown metric '{metric}' for component {component_id}",
        )

    age_ms = int((time.time() - snapshot.last_update_ts) * 1000)
    return MetricResponse(
        component_id=component_id,
        metric=metric,
        value=component[metric],
        last_update_ts=snapshot.last_update_ts,
        age_ms=age_ms,
        etag=snapshot.etag,
    )


@app.get("/health", response_model=HealthResponse)
async def health():
    return await meta()
