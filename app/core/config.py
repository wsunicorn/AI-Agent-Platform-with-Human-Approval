from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "HumanGate AI"
    app_env: str = "development"

    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/humangate"
    redis_url: str = "redis://localhost:6379/0"

    llm_primary_provider: str = "gemini"
    llm_primary_model: str = "gemini-3.1-flash-lite"
    gemini_api_key: str = ""

    local_provider: str = "ollama"
    ollama_base_url: str = "http://localhost:11434"
    local_fast_model: str = "gemma3:4b"
    local_quality_model: str = "qwen3:8b"
    local_router_model: str = "qwen2.5:3b"

    embedding_provider: str = "local"
    local_embedding_model: str = "nomic-embed-text-v2-moe"
    local_embedding_dimensions: int = 768

    redis_events_channel: str = "humangate.events"
    redis_events_stream: str = "humangate:events"
    redis_events_stream_maxlen: int = 10000

    tool_default_timeout_seconds: float = 15.0
    tool_default_max_attempts: int = 3
    tool_retry_initial_backoff_seconds: float = 0.25
    tool_retry_backoff_multiplier: float = 2.0

    approval_execution_lock_ttl_seconds: int = 60

    cors_origins: list[str] = Field(
        default_factory=lambda: [
            "http://localhost:5173",
            "http://127.0.0.1:5173",
        ]
    )

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
