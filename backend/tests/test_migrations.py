"""Tests for migration run and file upload API endpoints."""
import io
import pytest


# ---------------------------------------------------------------------------
# Migration Run Tests
# ---------------------------------------------------------------------------

class TestMigrationRuns:

    def test_create_run(self, client):
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

    def test_create_run_minimal(self, client):
        resp = client.post("/api/migrations", json={"name": "Minimal Run"})
        assert resp.status_code == 201
        assert resp.json()["name"] == "Minimal Run"

    def test_create_run_empty_name_rejected(self, client):
        resp = client.post("/api/migrations", json={"name": ""})
        assert resp.status_code == 422

    def test_list_runs_empty(self, client):
        resp = client.get("/api/migrations")
        assert resp.status_code == 200
        assert resp.json()["runs"] == []
        assert resp.json()["total"] == 0

    def test_list_runs(self, client):
        client.post("/api/migrations", json={"name": "Run 1"})
        client.post("/api/migrations", json={"name": "Run 2"})
        resp = client.get("/api/migrations")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 2
        assert len(data["runs"]) == 2

    def test_get_run(self, client):
        create_resp = client.post("/api/migrations", json={"name": "Get Me"})
        run_id = create_resp.json()["id"]
        resp = client.get(f"/api/migrations/{run_id}")
        assert resp.status_code == 200
        assert resp.json()["name"] == "Get Me"

    def test_get_run_not_found(self, client):
        resp = client.get("/api/migrations/9999")
        assert resp.status_code == 404

    def test_delete_run(self, client):
        create_resp = client.post("/api/migrations", json={"name": "Delete Me"})
        run_id = create_resp.json()["id"]
        resp = client.delete(f"/api/migrations/{run_id}")
        assert resp.status_code == 200
        assert resp.json()["id"] == run_id
        assert client.get(f"/api/migrations/{run_id}").status_code == 404

    def test_delete_run_not_found(self, client):
        resp = client.delete("/api/migrations/9999")
        assert resp.status_code == 404


# ---------------------------------------------------------------------------
# File Upload Tests
# ---------------------------------------------------------------------------

class TestFileUploads:

    def _create_run(self, client, name: str = "Upload Test") -> int:
        resp = client.post("/api/migrations", json={"name": name})
        return resp.json()["id"]

    def _csv_content(self, headers: str = "id,name,email", rows: int = 3) -> bytes:
        lines = [headers]
        for i in range(1, rows + 1):
            lines.append(f"{i},User {i},user{i}@example.com")
        return "\n".join(lines).encode("utf-8")

    def test_upload_single_file(self, client):
        run_id = self._create_run(client)
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

    def test_upload_multiple_files(self, client):
        run_id = self._create_run(client)
        files = [
            ("files", ("customers.csv", io.BytesIO(self._csv_content()), "text/csv")),
            ("files", ("orders.csv", io.BytesIO(self._csv_content("order_id,amount,date", 5)), "text/csv")),
        ]
        resp = client.post(f"/api/migrations/{run_id}/files", files=files)
        assert resp.status_code == 201
        assert len(resp.json()) == 2

    def test_upload_to_nonexistent_run(self, client):
        resp = client.post(
            "/api/migrations/9999/files",
            files=[("files", ("test.csv", io.BytesIO(b"a,b\n1,2"), "text/csv"))],
        )
        assert resp.status_code == 404

    def test_list_files(self, client):
        run_id = self._create_run(client)
        client.post(
            f"/api/migrations/{run_id}/files",
            files=[("files", ("data.csv", io.BytesIO(self._csv_content()), "text/csv"))],
        )
        resp = client.get(f"/api/migrations/{run_id}/files")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 1
        assert data["files"][0]["original_filename"] == "data.csv"

    def test_list_files_nonexistent_run(self, client):
        resp = client.get("/api/migrations/9999/files")
        assert resp.status_code == 404

    def test_delete_file(self, client):
        run_id = self._create_run(client)
        upload_resp = client.post(
            f"/api/migrations/{run_id}/files",
            files=[("files", ("delete_me.csv", io.BytesIO(self._csv_content()), "text/csv"))],
        )
        file_id = upload_resp.json()[0]["id"]
        resp = client.delete(f"/api/migrations/files/{file_id}")
        assert resp.status_code == 200
        assert resp.json()["id"] == file_id
        list_resp = client.get(f"/api/migrations/{run_id}/files")
        assert list_resp.json()["total"] == 0

    def test_delete_file_not_found(self, client):
        resp = client.delete("/api/migrations/files/9999")
        assert resp.status_code == 404

    def test_run_file_count_updates(self, client):
        run_id = self._create_run(client)
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
