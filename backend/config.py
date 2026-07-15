"""Application configuration for the Migration Evaluation Platform (MEP).

Settings are loaded from environment variables and/or a local ``.env`` file
using pydantic-settings.
"""
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """MEP backend settings."""

    # Database connection string, e.g.
    # postgresql://mep_user:mep_password@db:5432/mep_db
    DATABASE_URL: str = "postgresql://mep_user:mep_password@db:5432/mep_db"

    # Runtime environment: development | staging | production
    APP_ENV: str = "development"

    # Enable debug behaviour (verbose logging, etc.)
    DEBUG: bool = True

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


# Single, importable settings instance used across the app.
settings = Settings()
