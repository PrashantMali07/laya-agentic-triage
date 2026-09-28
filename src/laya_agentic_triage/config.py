from functools import lru_cache
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "Laya Agentic Incident Triage"
    app_version: str = "0.1.0"

    # System-2
    llm_provider: Literal["groq", "ollama"] = "groq"

    groq_api_key: str | None = None
    groq_model: str = "openai/gpt-oss-20b"

    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "lfm2.5:latest"

    # System-1
    laya_model: str = "convaiinnovations/laya-typed-decisions"
    laya_device: str = "cuda"

    laya_confidence_threshold: float = 0.80
    laya_human_threshold: float = 0.65
    laya_max_concurrency: int = 2


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()