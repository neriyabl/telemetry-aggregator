from collections.abc import Mapping

from pydantic import BaseModel, ConfigDict

MetricValue = int | float
SwitchData = dict[str, MetricValue]
MappingSwitchData = Mapping[str, MetricValue]


class Snapshot(BaseModel):
    model_config = ConfigDict(frozen=True)

    data: Mapping[str, MappingSwitchData]
    metric_names: tuple[str, ...]
    last_update_ts: float
    etag: str | None


class MetricResponse(BaseModel):
    switch_id: str
    metric: str
    value: MetricValue
    last_update_ts: float
    age_ms: int


class ListMetricsResponse(BaseModel):
    data: dict[str, SwitchData]
    metric_names: list[str]
    switch_count: int
    last_update_ts: float
    age_ms: int
    stale: bool


class HealthResponse(BaseModel):
    has_snapshot: bool
    last_update_ts: float | None
    age_ms: int | None
    etag: str | None
    last_ingest_ts: float | None
