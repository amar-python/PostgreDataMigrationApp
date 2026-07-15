# MEP API Reference

**Base URL:** `http://localhost:8000`

Interactive docs: [Swagger UI](/docs) | [ReDoc](/redoc)

---

## Foundation

### `GET /`

Root route — confirms the API is running.

### `GET /api/health`

Health check — returns database connection status.

---

## Migration Runs (Phase 1)

### `POST /api/migrations`

Create a new migration run.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| name | string | ✓ | Migration name (1–255 chars) |
| environment | string | | `development` / `staging` / `production` |
| description | string | | Optional description |

### `GET /api/migrations`

List all migration runs (newest first). Query params: `skip`, `limit`.

### `GET /api/migrations/{id}`

Get a single migration run by ID.

### `DELETE /api/migrations/{id}`

Delete a run and all its files.

### `POST /api/migrations/{id}/files`

Upload one or more CSV files (multipart/form-data, field: `files`).

### `GET /api/migrations/{id}/files`

List all files for a migration run.

### `DELETE /api/migrations/files/{id}`

Delete a single uploaded file.

---

## Schema Discovery & Validation (Phase 2)

### `POST /api/migrations/{id}/validate`

Discover column schemas and run validation checks on all files in a run.

**Response:**
```json
{
  "run_id": 1,
  "status": "passed",
  "files": [
    {
      "file_id": 1,
      "filename": "customers.csv",
      "schema": [
        {
          "name": "id",
          "inferred_type": "integer",
          "nullable": false,
          "unique": true,
          "sample_values": ["1", "2", "3"],
          "null_count": 0,
          "total_count": 100
        }
      ],
      "issues": [
        {
          "severity": "warning",
          "check": "null_values",
          "column": "email",
          "message": "5 null/empty values (5.0% of 100 rows)."
        }
      ]
    }
  ],
  "summary": {
    "total_files": 1,
    "errors": 0,
    "warnings": 1,
    "passed": true
  }
}
```

**Schema types inferred:** `integer`, `decimal`, `date`, `boolean`, `text`

**Validation checks:**
- Duplicate column names (error)
- Empty column names (error)
- Null/empty values per column (error/warning/info by threshold)
- Duplicate rows (warning)
- Mixed data types (warning)

---

## Migration Execution (Phase 5)

### `POST /api/migrations/{id}/execute`

Load validated CSVs into PostgreSQL staging tables.

- Creates `staging_{run_id}_{filename}` tables
- Bulk-inserts rows with inferred column types
- Updates run status to `completed` or `failed`

**Requires:** PostgreSQL (not available with SQLite test DB).

---

## Evaluation (Phase 6)

### `POST /api/migrations/{id}/evaluate`

Run quality checks comparing source CSVs against loaded staging tables.

**Checks:**
- Row count match (source vs target)
- Null percentage per column in target
- Duplicate rows in target

**Returns:** Per-file quality score (0–100) and overall `PASS`/`FAIL` verdict.

**Requires:** Migration must be executed first.

---

## Reports (Phase 7)

### `POST /api/reports/{id}/generate?format=json|html`

Generate a migration report. Automatically gathers validation and evaluation data.

### `GET /api/reports/{id}/download/{format}`

Download a previously generated report file.

---

## Dashboard (Phase 8)

### `GET /api/dashboard`

Aggregate statistics for the dashboard view.

**Response:**
```json
{
  "total_runs": 5,
  "runs_by_status": {"created": 2, "completed": 3},
  "total_files": 12,
  "total_rows": 50000,
  "total_size": 2048000,
  "recent_runs": [...]
}
```
