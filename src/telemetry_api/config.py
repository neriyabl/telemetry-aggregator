from typing import cast

from pydantic import AnyHttpUrl, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="TA_", env_file=".env", extra="ignore")

    telemetry_source_url: AnyHttpUrl = cast(AnyHttpUrl, "http://127.0.0.1:9001")
    poll_interval_sec: float = Field(default=1.0, ge=0.1)
    stale_after_sec: float = Field(default=5.0, ge=0.1)
    http_timeout_sec: float = Field(default=2.0, ge=0.1)
    log_file_path: str = "logs/telemetry-api.log"


settings = Settings()
