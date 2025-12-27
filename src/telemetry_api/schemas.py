from pydantic import BaseModel, Field

MetricName = str
MetricValue = int | float
ComponentData = dict[MetricName, MetricValue]


class Snapshot(BaseModel):
    data: dict[str, ComponentData]
    metric_names: list[str]
    last_update_ts: float
    etag: str | None


class MetricResponse(BaseModel):
    component_id: str
    metric: str
    value: MetricValue
    last_update_ts: float
    age_ms: int
    etag: str | None = None


class ListMetricsResponse(BaseModel):
    data: dict[str, ComponentData]
    metric_names: list[str]
    component_count: int
    last_update_ts: float
    age_ms: int
    stale: bool
    etag: str | None = None


class WarmingUpResponse(BaseModel):
    detail: str = Field(default="warming_up")


class HealthResponse(BaseModel):
    has_snapshot: bool
    last_update_ts: float | None
    age_ms: int | None
    etag: str | None
    last_ingest_ts: float | None
