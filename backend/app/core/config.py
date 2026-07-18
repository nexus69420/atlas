"""Application settings loaded from environment variables.

Why pydantic-settings:
- Type-safe configuration (bad env values fail at startup, not at runtime)
- Single source of truth for every tunable knob
- Easy to swap `.env` locally vs Docker Compose without code changes
"""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime configuration for the Atlas API."""

    model_config = SettingsConfigDict(
        # Prefer cwd `.env` (backend/), fall back to repo-root `.env`
        env_file=(".env", "../.env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "Atlas API"
    app_env: str = "development"
    debug: bool = False
    api_v1_prefix: str = "/api/v1"

    # postgresql+psycopg://user:pass@host:port/db — psycopg3 dialect for SQLAlchemy 2
    database_url: str = "postgresql+psycopg://atlas:atlas@localhost:5432/atlas"

    # Auth — override SECRET_KEY in any non-local environment
    secret_key: str = "dev-only-change-me-atlas-secret-key"
    access_token_expire_minutes: int = 60 * 24  # 24 hours for V1 simplicity
    jwt_algorithm: str = "HS256"

    # Local file storage for V1 (MinIO/S3 is a later swap behind the same interface)
    storage_path: str = "storage/datasets"
    artifact_storage_path: str = "storage/artifacts"
    max_upload_bytes: int = 50 * 1024 * 1024  # 50 MiB
    dataset_preview_default_rows: int = 20
    dataset_preview_max_rows: int = 100


@lru_cache
def get_settings() -> Settings:
    """Return a cached Settings instance.

    Caching avoids re-reading the environment on every request.
    Clear with `get_settings.cache_clear()` in tests if you mutate env.
    """
    return Settings()
