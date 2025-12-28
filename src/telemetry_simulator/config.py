from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class SimulatorSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="SIM_", env_file=".env", extra="ignore"
    )

    switch_count: int = Field(default=32, ge=1)
    update_interval_sec: float = Field(default=10.0, ge=0.1)
    spike_probability: float = Field(default=0.03, ge=0.0, le=1.0)
    error_burst_probability: float = Field(default=0.02, ge=0.0, le=1.0)
    log_file_path: str = Field(default="logs/telemetry-simulator.log")

    # Metrics configuration
    @property
    def metrics(self) -> list[str]:
        return ["bandwidth_gbps", "latency_ms", "packet_errors"]


settings = SimulatorSettings()
