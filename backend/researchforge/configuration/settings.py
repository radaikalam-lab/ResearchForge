"""Application settings using Pydantic Settings."""

from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Central configuration for ResearchForge."""

    model_config = SettingsConfigDict(
        env_prefix="RESEARCHFORGE_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Core
    env: str = Field(default="development", description="Environment: development, test, production")
    debug: bool = Field(default=False, description="Debug mode")
    secret_key: str = Field(
        default="researchforge_default_secret_key_please_change_in_production",
        description="Secret key for security and signing",
    )
    api_host: str = Field(default="127.0.0.1", description="FastAPI bind host")
    api_port: int = Field(default=8000, description="FastAPI bind port")
    api_prefix: str = Field(default="/api/v1", description="API route prefix")

    # Storage paths
    data_dir: Path = Field(default=Path("./artifacts"), description="Artifacts and datasets root")
    provenance_ledger_path: Path = Field(
        default=Path("./artifacts/provenance.jsonl"),
        description="Path to append-only provenance ledger",
    )
    database_url: str = Field(
        default="sqlite:///./artifacts/researchforge.db",
        description="Database connection URL",
    )

    # Execution Sandbox & Policy
    sandbox_strict: bool = Field(default=True, description="Enforce strict sandbox constraints")
    max_execution_time_sec: int = Field(default=300, description="Max execution timeout for runs")
    max_memory_mb: int = Field(default=2048, description="Max memory allocation per run in MB")
    allow_network_execution: bool = Field(default=False, description="Allow network inside execution sandbox")

    # Cognitia Adapter
    cognitia_enabled: bool = Field(default=True, description="Enable Cognitia integration")
    cognitia_api_url: str = Field(default="http://127.0.0.1:8080", description="Cognitia API endpoint")
    cognitia_api_key: str | None = Field(default=None, description="Cognitia API Key")
    cognitia_mock_mode: bool = Field(default=True, description="Use local mock Cognitia engine")

    # Scholarly & AI
    openalex_api_key: str | None = None
    crossref_mailto: str = "researcher@example.org"
    semantic_scholar_api_key: str | None = None
    llm_provider: str = Field(default="mock", description="LLM provider: mock, ollama, openai")
    ollama_base_url: str = "http://127.0.0.1:11434"
    openai_api_key: str | None = None


@lru_cache
def get_settings() -> Settings:
    """Return cached application settings."""
    return Settings()
