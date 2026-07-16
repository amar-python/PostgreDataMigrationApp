"""Integration smoke test — verifies the API boots and answers on /api/health.

This is the minimum bar for any deploy: if this test fails, nothing else
matters. It uses the shared conftest fixtures (SQLite-backed TestClient), so
it runs in CI without a PostgreSQL service, yet exercises the full FastAPI
stack: routing, dependency injection, and the health service.
"""
import pytest


@pytest.mark.integration
def test_health_endpoint_returns_200(client):
    """GET /api/health must return HTTP 200 OK."""
    response = client.get("/api/health")
    assert response.status_code == 200


@pytest.mark.integration
def test_health_endpoint_reports_expected_shape(client):
    """The health payload must expose status / version / environment / database."""
    body = client.get("/api/health").json()
    assert body["status"] == "healthy"
    assert "version" in body
    assert "environment" in body
    assert body["database"] in ("connected", "disconnected")


@pytest.mark.integration
def test_root_endpoint_returns_200(client):
    """GET / must return HTTP 200 OK and identify the API."""
    response = client.get("/")
    assert response.status_code == 200
    assert response.json()["message"] == "MEP API is running"
