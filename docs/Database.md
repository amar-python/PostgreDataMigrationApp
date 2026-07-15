# MEP Database Design

## Overview

MEP uses **PostgreSQL 15** as its primary datastore. During development/testing,
SQLite may be used for backend unit tests.

## Connection

| Setting | Default |
|---------|---------|
| Engine | PostgreSQL 15 (Alpine) |
| URL | `postgresql://mep_user:mep_password@db:5432/mep_db` |
| Pool | `pool_pre_ping=True` (auto-recycle stale connections) |
| ORM | SQLAlchemy 2.x with Declarative Base |

Connection is managed via `backend/database/connection.py`.
Configuration lives in `backend/config.py` (reads `DATABASE_URL` from `.env`).

## Schema

### `migration_runs`

Tracks each migration session.

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| `id` | INTEGER PK | No | Auto-increment |
| `name` | VARCHAR(255) | No | Human-readable run name |
| `environment` | VARCHAR(100) | No | `development` / `staging` / `production` |
| `description` | TEXT | Yes | Free-form description |
| `status` | ENUM(`run_status`) | No | Lifecycle state — see below |
| `created_at` | TIMESTAMP WITH TZ | No | Creation timestamp (UTC) |
| `updated_at` | TIMESTAMP WITH TZ | No | Last-modified timestamp (UTC) |

**`run_status` enum values:**

| Value | Meaning |
|-------|---------|
| `created` | Run created, no processing started |
| `uploading` | Files being uploaded |
| `validating` | Schema discovery / validation in progress |
| `migrating` | Data loading into staging tables |
| `completed` | Migration finished successfully |
| `failed` | Migration encountered errors |

### `uploaded_files`

Metadata for each CSV file attached to a run.

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| `id` | INTEGER PK | No | Auto-increment |
| `migration_run_id` | INTEGER FK → `migration_runs.id` | No | Parent run (CASCADE delete) |
| `original_filename` | VARCHAR(500) | No | User-facing filename |
| `stored_filename` | VARCHAR(500) | No | UUID-based name on disk |
| `file_size` | BIGINT | No | Size in bytes |
| `content_type` | VARCHAR(100) | Yes | MIME type (default `text/csv`) |
| `row_count` | INTEGER | Yes | Data rows (excluding header) |
| `column_count` | INTEGER | Yes | Number of CSV columns |
| `columns` | TEXT | Yes | JSON array of column header names |
| `uploaded_at` | TIMESTAMP WITH TZ | No | Upload timestamp (UTC) |

### Staging Tables (dynamic)

Created at migration execution time. Naming convention:

```
staging_{run_id}_{sanitized_filename}
```

Column types are inferred from CSV analysis:

| CSV Inferred Type | PostgreSQL Type |
|-------------------|-----------------|
| `integer` | `BIGINT` |
| `decimal` | `DOUBLE PRECISION` |
| `boolean` | `BOOLEAN` |
| `date` | `TIMESTAMP` |
| `text` | `TEXT` |

## Entity Relationship

```
migration_runs (1) ──→ (N) uploaded_files
migration_runs (1) ──→ (N) staging_* tables (dynamic)
```

## Migrations

Currently tables are auto-created via `Base.metadata.create_all()` at startup.
For production, switch to **Alembic** migrations:

```bash
cd backend
alembic init alembic
alembic revision --autogenerate -m "initial schema"
alembic upgrade head
```

## File Storage

Uploaded CSVs are stored on disk at:

```
backend/uploads/{run_id}/{uuid}.csv
```

This path is configurable via the `MEP_UPLOAD_DIR` environment variable.
Reports are stored at `backend/reports/{run_id}/report.{json|html}`.
