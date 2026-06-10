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

    ollama_base_url: str = "http://localhost:11434"

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

