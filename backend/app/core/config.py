"""Application configuration."""

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime settings loaded from environment variables."""

    # App/runtime settings
    app_name: str = "NG12 RAG Assessment API"
    app_env: str = Field(default="dev", alias="APP_ENV")
    app_host: str = Field(default="0.0.0.0", alias="APP_HOST")
    app_port: int = Field(default=8000, alias="APP_PORT")

    # Model provider settings (Vertex in prod, mock in local/offline mode)
    google_cloud_project: str | None = Field(default=None, alias="GOOGLE_CLOUD_PROJECT")
    google_cloud_location: str | None = Field(default=None, alias="GOOGLE_CLOUD_LOCATION")
    llm_provider: str = Field(default="mock", alias="LLM_PROVIDER")
    llm_model: str = Field(default="gemini-1.5-pro", alias="LLM_MODEL")
    embedding_provider: str = Field(default="mock", alias="EMBEDDING_PROVIDER")
    embedding_model: str = Field(default="text-embedding-004", alias="EMBEDDING_MODEL")

    # Shared data sources reused by both assessment and chat workflows
    vector_db_path: str = Field(default="backend/data/chroma", alias="VECTOR_DB_PATH")
    vector_collection: str = Field(default="ng12_guideline", alias="VECTOR_COLLECTION")
    patients_data_path: str = Field(default="backend/data/patients.json", alias="PATIENTS_DATA_PATH")
    guideline_rules_path: str = Field(
        default="backend/data/guideline_rules.yml",
        alias="GUIDELINE_RULES_PATH",
    )

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    # Settings are loaded once per process to avoid repeated env parsing.
    return Settings()
