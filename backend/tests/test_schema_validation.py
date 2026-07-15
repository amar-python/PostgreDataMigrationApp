"""Tests for schema discovery, validation, and dashboard endpoints."""
import io
import pytest


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _create_run_and_upload(client, csv_content: bytes, filename: str = "test.csv") -> int:
    resp = client.post("/api/migrations", json={"name": "Schema Test"})
    run_id = resp.json()["id"]
    client.post(
        f"/api/migrations/{run_id}/files",
        files=[("files", (filename, io.BytesIO(csv_content), "text/csv"))],
    )
    return run_id


# ---------------------------------------------------------------------------
# Schema Discovery Tests
# ---------------------------------------------------------------------------

class TestSchemaDiscovery:

    def test_integer_columns_detected(self, client):
        csv = b"id,count\n1,100\n2,200\n3,300"
        run_id = _create_run_and_upload(client, csv)
        resp = client.post(f"/api/migrations/{run_id}/validate")
        assert resp.status_code == 200
        schema = resp.json()["files"][0]["schema"]
        assert schema[0]["inferred_type"] == "integer"
        assert schema[1]["inferred_type"] == "integer"

    def test_decimal_columns_detected(self, client):
        csv = b"price,amount\n10.5,20.3\n30.1,40.7"
        run_id = _create_run_and_upload(client, csv)
        resp = client.post(f"/api/migrations/{run_id}/validate")
        schema = resp.json()["files"][0]["schema"]
        assert schema[0]["inferred_type"] == "decimal"

    def test_date_columns_detected(self, client):
        csv = b"created\n2024-01-15\n2024-02-20\n2024-03-25"
        run_id = _create_run_and_upload(client, csv)
        resp = client.post(f"/api/migrations/{run_id}/validate")
        schema = resp.json()["files"][0]["schema"]
        assert schema[0]["inferred_type"] == "date"

    def test_boolean_columns_detected(self, client):
        csv = b"active,verified\ntrue,yes\nfalse,no\ntrue,yes"
        run_id = _create_run_and_upload(client, csv)
        resp = client.post(f"/api/migrations/{run_id}/validate")
        schema = resp.json()["files"][0]["schema"]
        assert schema[0]["inferred_type"] == "boolean"
        assert schema[1]["inferred_type"] == "boolean"

    def test_text_columns_default(self, client):
        csv = b"name,city\nAlice,NYC\nBob,London"
        run_id = _create_run_and_upload(client, csv)
        resp = client.post(f"/api/migrations/{run_id}/validate")
        schema = resp.json()["files"][0]["schema"]
        assert schema[0]["inferred_type"] == "text"

    def test_nullable_detected(self, client):
        csv = b"id,name\n1,Alice\n2,\n3,Charlie"
        run_id = _create_run_and_upload(client, csv)
        resp = client.post(f"/api/migrations/{run_id}/validate")
        schema = resp.json()["files"][0]["schema"]
        name_col = schema[1]
        assert name_col["nullable"] is True
        assert name_col["null_count"] == 1

    def test_uniqueness_detected(self, client):
        csv = b"id,category\n1,A\n2,A\n3,B"
        run_id = _create_run_and_upload(client, csv)
        resp = client.post(f"/api/migrations/{run_id}/validate")
        schema = resp.json()["files"][0]["schema"]
        assert schema[0]["unique"] is True
        assert schema[1]["unique"] is False

    def test_sample_values_provided(self, client):
        csv = b"color\nred\nblue\ngreen\nyellow\npurple\norange\npink"
        run_id = _create_run_and_upload(client, csv)
        resp = client.post(f"/api/migrations/{run_id}/validate")
        schema = resp.json()["files"][0]["schema"]
        assert len(schema[0]["sample_values"]) == 5


# ---------------------------------------------------------------------------
# Validation Tests
# ---------------------------------------------------------------------------

class TestValidation:

    def test_clean_csv_passes(self, client):
        csv = b"id,name,email\n1,Alice,a@b.com\n2,Bob,b@c.com"
        run_id = _create_run_and_upload(client, csv)
        resp = client.post(f"/api/migrations/{run_id}/validate")
        data = resp.json()
        assert data["summary"]["passed"] is True
        assert data["summary"]["errors"] == 0

    def test_null_values_warning(self, client):
        csv = b"id,name\n1,Alice\n2,\n3,\n4,Dave"
        run_id = _create_run_and_upload(client, csv)
        resp = client.post(f"/api/migrations/{run_id}/validate")
        issues = resp.json()["files"][0]["issues"]
        null_issues = [i for i in issues if i["check"] == "null_values"]
        assert len(null_issues) > 0

    def test_duplicate_rows_warning(self, client):
        csv = b"id,name\n1,Alice\n1,Alice\n2,Bob"
        run_id = _create_run_and_upload(client, csv)
        resp = client.post(f"/api/migrations/{run_id}/validate")
        issues = resp.json()["files"][0]["issues"]
        dup_issues = [i for i in issues if i["check"] == "duplicate_rows"]
        assert len(dup_issues) == 1

    def test_duplicate_column_error(self, client):
        csv = b"id,name,name\n1,Alice,Smith\n2,Bob,Jones"
        run_id = _create_run_and_upload(client, csv)
        resp = client.post(f"/api/migrations/{run_id}/validate")
        data = resp.json()
        issues = data["files"][0]["issues"]
        dup_col = [i for i in issues if i["check"] == "duplicate_column"]
        assert len(dup_col) == 1
        assert data["summary"]["errors"] >= 1
        assert data["summary"]["passed"] is False

    def test_validate_nonexistent_run(self, client):
        resp = client.post("/api/migrations/9999/validate")
        assert resp.status_code == 404

    def test_validate_run_no_files(self, client):
        resp = client.post("/api/migrations", json={"name": "Empty"})
        run_id = resp.json()["id"]
        resp = client.post(f"/api/migrations/{run_id}/validate")
        assert resp.status_code == 200
        assert resp.json()["status"] == "no_files"

    def test_multiple_files_validated(self, client):
        resp = client.post("/api/migrations", json={"name": "Multi"})
        run_id = resp.json()["id"]
        client.post(
            f"/api/migrations/{run_id}/files",
            files=[
                ("files", ("a.csv", io.BytesIO(b"x,y\n1,2\n3,4"), "text/csv")),
                ("files", ("b.csv", io.BytesIO(b"p,q,r\na,b,c"), "text/csv")),
            ],
        )
        resp = client.post(f"/api/migrations/{run_id}/validate")
        data = resp.json()
        assert data["summary"]["total_files"] == 2
        assert len(data["files"]) == 2

    def test_validation_summary_counts(self, client):
        csv = b"id,name,name\n1,,\n2,,\n3,,"
        run_id = _create_run_and_upload(client, csv)
        resp = client.post(f"/api/migrations/{run_id}/validate")
        summary = resp.json()["summary"]
        assert summary["errors"] >= 1
        assert summary["total_files"] == 1


# ---------------------------------------------------------------------------
# Dashboard Tests
# ---------------------------------------------------------------------------

class TestDashboard:

    def test_empty_dashboard(self, client):
        resp = client.get("/api/dashboard")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total_runs"] == 0
        assert data["total_files"] == 0

    def test_dashboard_with_runs(self, client):
        client.post("/api/migrations", json={"name": "Run 1"})
        client.post("/api/migrations", json={"name": "Run 2"})
        resp = client.get("/api/dashboard")
        data = resp.json()
        assert data["total_runs"] == 2
        assert len(data["recent_runs"]) == 2

    def test_dashboard_file_stats(self, client):
        resp = client.post("/api/migrations", json={"name": "Upload Run"})
        run_id = resp.json()["id"]
        client.post(
            f"/api/migrations/{run_id}/files",
            files=[("files", ("data.csv", io.BytesIO(b"a,b\n1,2\n3,4"), "text/csv"))],
        )
        resp = client.get("/api/dashboard")
        data = resp.json()
        assert data["total_files"] == 1
        assert data["total_rows"] == 2
        assert data["total_size"] > 0
