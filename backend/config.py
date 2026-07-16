"""Application configuration for the Migration Evaluation Platform (MEP).

Settings are loaded from environment variables and/or a local ``.env`` file
using pydantic-settings.
"""
from pydantic import model_validator
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

    # Allow the application to auto-create database tables on startup via
    # ``Base.metadata.create_all``. This is a development convenience only —
    # production schema changes MUST go through explicit, reviewed migrations
    # (e.g. Alembic). Startup fails fast if this is enabled in production.
    ALLOW_SCHEMA_AUTO_CREATE: bool = True

    @model_validator(mode="after")
    def _forbid_auto_create_in_production(self) -> "Settings":
        """Fail fast when schema auto-creation is enabled in production.

        Auto-creating tables in production can silently mutate the schema,
        mask missing migrations, and cause data loss on model drift. We treat
        this combination as a fatal misconfiguration so the service refuses to
        start rather than running unsafely.
        """
        if self.APP_ENV.strip().lower() == "production" and self.ALLOW_SCHEMA_AUTO_CREATE:
            raise ValueError(
                "Unsafe configuration: ALLOW_SCHEMA_AUTO_CREATE must be false when "
                "APP_ENV=production. Schema changes in production must be applied "
                "through explicit migrations, not automatic table creation. "
                "Set ALLOW_SCHEMA_AUTO_CREATE=false (and use a migration tool) "
                "to start the service in production."
            )
        return self

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


# Single, importable settings instance used across the app.
settings = Settings()
