"""Tests for migration run and file upload API endpoints.

Uses an in-memory SQLite database so tests run without PostgreSQL.
"""
import io
import os
import shutil
import tempfile

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from database.models import Base
from database.connection import get_db
from main import app

# ---------------------------------------------------------------------------
# Test database setup — in-memory SQLite
# ---------------------------------------------------------------------------

SQLALCHEMY_TEST_URL = "sqlite:///./test_mep.db"
test_engine = create_engine(SQLALCHEMY_TEST_URL, connect_args={"check_same_thread": False})
TestSession = sessionmaker(bind=test_engine, autoflush=False, autocommit=False)

# Temporary upload directory for tests
TEST_UPLOAD_DIR = tempfile.mkdtemp(prefix="mep_test_uploads_")


def override_get_db():
    db = TestSession()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(autouse=True)
def setup_database():
    """Create tables before each test, drop after."""
    Base.metadata.create_all(bind=test_engine)
    # Point upload service to temp directory
    os.environ["MEP_UPLOAD_DIR"] = TEST_UPLOAD_DIR
    yield
    Base.metadata.drop_all(bind=test_engine)
    # Clean up upload files
    if os.path.isdir(TEST_UPLOAD_DIR):
        shutil.rmtree(TEST_UPLOAD_DIR, ignore_errors=True)
        os.makedirs(TEST_UPLOAD_DIR, exist_ok=True)


client = TestClient(app)


# ---------------------------------------------------------------------------
# Migration Run Tests
# ---------------------------------------------------------------------------

class TestMigrationRuns:
    """Tests for migration run CRUD endpoints."""

    def test_create_run(self):
        resp = client.post("/api/migrations", json={
            "name": "Test Migration",
            "environment": "development",
            "description": "A test run"
        })
        assert resp.status_code == 201
        data = resp.json()
        assert data["name"] == "Test Migration"
        assert data["environment"] == "development"
        assert data["status"] == "created"
        assert data["file_count"] == 0

    def test_create_run_minimal(self):
        """Only name is required."""
        resp = client.post("/api/migrations", json={"name": "Minimal Run"})
        assert resp.status_code == 201
        assert resp.json()["name"] == "Minimal Run"

    def test_create_run_empty_name_rejected(self):
        resp = client.post("/api/migrations", json={"name": ""})
        assert resp.status_code == 422

    def test_list_runs_empty(self):
        resp = client.get("/api/migrations")
        assert resp.status_code == 200
        assert resp.json()["runs"] == []
        assert resp.json()["total"] == 0

    def test_list_runs(self):
        client.post("/api/migrations", json={"name": "Run 1"})
        client.post("/api/migrations", json={"name": "Run 2"})
        resp = client.get("/api/migrations")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 2
        assert len(data["runs"]) == 2

    def test_get_run(self):
        create_resp = client.post("/api/migrations", json={"name": "Get Me"})
        run_id = create_resp.json()["id"]
        resp = client.get(f"/api/migrations/{run_id}")
        assert resp.status_code == 200
        assert resp.json()["name"] == "Get Me"

    def test_get_run_not_found(self):
        resp = client.get("/api/migrations/9999")
        assert resp.status_code == 404

    def test_delete_run(self):
        create_resp = client.post("/api/migrations", json={"name": "Delete Me"})
        run_id = create_resp.json()["id"]
        resp = client.delete(f"/api/migrations/{run_id}")
        assert resp.status_code == 200
        assert resp.json()["id"] == run_id
        # Confirm it's gone
        assert client.get(f"/api/migrations/{run_id}").status_code == 404

    def test_delete_run_not_found(self):
        resp = client.delete("/api/migrations/9999")
        assert resp.status_code == 404


# ---------------------------------------------------------------------------
# File Upload Tests
# ---------------------------------------------------------------------------

class TestFileUploads:
    """Tests for CSV file upload endpoints."""

    def _create_run(self, name: str = "Upload Test") -> int:
        resp = client.post("/api/migrations", json={"name": name})
        return resp.json()["id"]

    def _csv_content(self, headers: str = "id,name,email", rows: int = 3) -> bytes:
        lines = [headers]
        for i in range(1, rows + 1):
            lines.append(f"{i},User {i},user{i}@example.com")
        return "\n".join(lines).encode("utf-8")

    def test_upload_single_file(self):
        run_id = self._create_run()
        csv_data = self._csv_content()
        resp = client.post(
            f"/api/migrations/{run_id}/files",
            files=[("files", ("customers.csv", io.BytesIO(csv_data), "text/csv"))],
        )
        assert resp.status_code == 201
        data = resp.json()
        assert len(data) == 1
        assert data[0]["original_filename"] == "customers.csv"
        assert data[0]["row_count"] == 3
        assert data[0]["column_count"] == 3
        assert data[0]["file_size"] > 0

    def test_upload_multiple_files(self):
        run_id = self._create_run()
        files = [
            ("files", ("customers.csv", io.BytesIO(self._csv_content()), "text/csv")),
            ("files", ("orders.csv", io.BytesIO(self._csv_content("order_id,amount,date", 5)), "text/csv")),
        ]
        resp = client.post(f"/api/migrations/{run_id}/files", files=files)
        assert resp.status_code == 201
        assert len(resp.json()) == 2

    def test_upload_to_nonexistent_run(self):
        resp = client.post(
            "/api/migrations/9999/files",
            files=[("files", ("test.csv", io.BytesIO(b"a,b\n1,2"), "text/csv"))],
        )
        assert resp.status_code == 404

    def test_list_files(self):
        run_id = self._create_run()
        client.post(
            f"/api/migrations/{run_id}/files",
            files=[("files", ("data.csv", io.BytesIO(self._csv_content()), "text/csv"))],
        )
        resp = client.get(f"/api/migrations/{run_id}/files")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 1
        assert data["files"][0]["original_filename"] == "data.csv"

    def test_list_files_nonexistent_run(self):
        resp = client.get("/api/migrations/9999/files")
        assert resp.status_code == 404

    def test_delete_file(self):
        run_id = self._create_run()
        upload_resp = client.post(
            f"/api/migrations/{run_id}/files",
            files=[("files", ("delete_me.csv", io.BytesIO(self._csv_content()), "text/csv"))],
        )
        file_id = upload_resp.json()[0]["id"]
        resp = client.delete(f"/api/migrations/files/{file_id}")
        assert resp.status_code == 200
        assert resp.json()["id"] == file_id
        # Confirm file list is now empty
        list_resp = client.get(f"/api/migrations/{run_id}/files")
        assert list_resp.json()["total"] == 0

    def test_delete_file_not_found(self):
        resp = client.delete("/api/migrations/files/9999")
        assert resp.status_code == 404

    def test_run_file_count_updates(self):
        """After uploading files, the run's file_count should reflect them."""
        run_id = self._create_run()
        client.post(
            f"/api/migrations/{run_id}/files",
            files=[
                ("files", ("a.csv", io.BytesIO(self._csv_content()), "text/csv")),
                ("files", ("b.csv", io.BytesIO(self._csv_content()), "text/csv")),
            ],
        )
        run_resp = client.get(f"/api/migrations/{run_id}")
        assert run_resp.json()["file_count"] == 2
        assert run_resp.json()["total_size"] > 0
