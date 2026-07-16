"""Tests for production configuration safety gates in ``config.Settings``.

The key invariant: the application must REFUSE to start when
``APP_ENV=production`` and ``ALLOW_SCHEMA_AUTO_CREATE=true``, because schema
auto-creation in production can silently mutate the database schema.
"""
import pytest
from pydantic import ValidationError

from config import Settings


def make_settings(**overrides):
    """Build Settings isolated from any local .env file."""
    return Settings(_env_file=None, **overrides)


class TestProductionSafetyGate:
    def test_production_with_auto_create_fails(self):
        """production + auto-create enabled must raise at construction time."""
        with pytest.raises(ValidationError) as exc_info:
            make_settings(APP_ENV="production", ALLOW_SCHEMA_AUTO_CREATE=True)
        assert "ALLOW_SCHEMA_AUTO_CREATE" in str(exc_info.value)

    def test_production_case_insensitive(self):
        """The gate must not be bypassable via casing or whitespace."""
        for env in ("PRODUCTION", "Production", " production "):
            with pytest.raises(ValidationError):
                make_settings(APP_ENV=env, ALLOW_SCHEMA_AUTO_CREATE=True)

    def test_production_with_auto_create_disabled_ok(self):
        """production + auto-create disabled is a valid configuration."""
        s = make_settings(APP_ENV="production", ALLOW_SCHEMA_AUTO_CREATE=False)
        assert s.APP_ENV == "production"
        assert s.ALLOW_SCHEMA_AUTO_CREATE is False

    def test_development_with_auto_create_ok(self):
        """development keeps the convenient auto-create default."""
        s = make_settings(APP_ENV="development", ALLOW_SCHEMA_AUTO_CREATE=True)
        assert s.ALLOW_SCHEMA_AUTO_CREATE is True

    def test_staging_with_auto_create_ok(self):
        """staging is not gated (only production is fatal)."""
        s = make_settings(APP_ENV="staging", ALLOW_SCHEMA_AUTO_CREATE=True)
        assert s.ALLOW_SCHEMA_AUTO_CREATE is True

    def test_default_is_development_with_auto_create(self):
        """Defaults stay developer-friendly."""
        s = make_settings()
        assert s.APP_ENV == "development"
        assert s.ALLOW_SCHEMA_AUTO_CREATE is True

    def test_env_variable_string_coercion(self, monkeypatch):
        """Values coming from environment variables are honoured too."""
        monkeypatch.setenv("APP_ENV", "production")
        monkeypatch.setenv("ALLOW_SCHEMA_AUTO_CREATE", "true")
        with pytest.raises(ValidationError):
            Settings(_env_file=None)

        monkeypatch.setenv("ALLOW_SCHEMA_AUTO_CREATE", "false")
        s = Settings(_env_file=None)
        assert s.ALLOW_SCHEMA_AUTO_CREATE is False
