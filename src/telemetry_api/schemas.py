from pydantic import BaseModel

MetricName = str
MetricValue = int | float
SwitchData = dict[MetricName, MetricValue]


class Snapshot(BaseModel):
    data: dict[str, SwitchData]
    metric_names: list[str]
    last_update_ts: float
    etag: str | None


class MetricResponse(BaseModel):
    switch_id: str
    metric: str
    value: MetricValue
    last_update_ts: float
    age_ms: int
    etag: str | None = None


class ListMetricsResponse(BaseModel):
    data: dict[str, SwitchData]
    metric_names: list[str]
    switch_count: int
    last_update_ts: float
    age_ms: int
    stale: bool
    etag: str | None = None


class HealthResponse(BaseModel):
    has_snapshot: bool
    last_update_ts: float | None
    age_ms: int | None
    etag: str | None
    last_ingest_ts: float | None
