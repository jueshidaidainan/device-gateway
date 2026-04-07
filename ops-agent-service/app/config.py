from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Ops Agent Service"
    environment: str = "dev"
    llm_base_url: str | None = None
    llm_api_key: str | None = None
    llm_model: str = "gpt-4o-mini"
    prometheus_base_url: str | None = None
    loki_base_url: str | None = None
    gateway_ops_base_url: str | None = None
    loki_log_selector: str = '{job=~".*"}'
    metrics_name_flow: str = "topic_packets_sent_flow"
    metrics_name_total: str = "topic_packets_sent_total"
    sqlite_path: str = "ops-agent-service.sqlite3"
    request_timeout_seconds: float = 15.0
    default_lookback_minutes: int = 60
    default_query_step: str = "60s"
    log_line_limit: int = 50
    gateway_event_limit: int = 20
    diagnosis_examples_enabled: bool = True
    log_keywords: list[str] = Field(
        default_factory=lambda: ["error", "disconnect", "timeout", "parse failure", "exception"]
    )

    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="OPS_AGENT_",
        extra="ignore",
    )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
