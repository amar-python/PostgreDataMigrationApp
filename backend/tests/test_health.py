"""Smoke tests for the MEP backend skeleton."""
from fastapi.testclient import TestClient

from main import app

client = TestClient(app)


def test_root_returns_200():
    """Root route responds with 200 and the running message."""
    response = client.get("/")
    assert response.status_code == 200
    body = response.json()
    assert body["message"] == "MEP API is running"
    assert body["version"] == "0.1.0"


def test_health_returns_200_with_status():
    """Health route responds with 200 and a status field.

    The database may be unavailable in CI; the endpoint must still return 200
    and report the database as either connected or disconnected.
    """
    response = client.get("/api/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "healthy"
    assert body["version"] == "0.1.0"
    assert "environment" in body
    assert body["database"] in ("connected", "disconnected")
