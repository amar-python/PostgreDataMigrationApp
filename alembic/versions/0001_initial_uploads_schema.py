"""Initial uploads schema (BUG-032 baseline).

Mirrors the previous api/db.py bootstrap() DDL 1:1 so a database that was
already bootstrapped by the pre-Alembic code path upgrades to head as a
no-op (every statement uses IF NOT EXISTS).

Creates:
  - csv_uploads schema
  - csv_uploads.csv_files table + unique indexes on file_name and file_hash
  - csv_uploads.audit_log table

Schema name is hardcoded here as `csv_uploads`. The runtime CSV_UPLOADS_SCHEMA
env var is respected by api/ code but Alembic migrations are static — if you
change the schema name in config, add a new migration that renames the schema
rather than relying on the env var here.

Revision ID: 0001
Revises:
Create Date: 2026-08-02
"""

from alembic import op

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None

# Fixed schema name — see module docstring.
_SCHEMA = "csv_uploads"


def upgrade() -> None:
    op.execute(f'CREATE SCHEMA IF NOT EXISTS "{_SCHEMA}"')
    op.execute(
        f"""
        CREATE TABLE IF NOT EXISTS "{_SCHEMA}".csv_files (
            id           BIGSERIAL PRIMARY KEY,
            file_name    TEXT NOT NULL,
            file_hash    TEXT NOT NULL,
            table_name   TEXT NOT NULL,
            mode         TEXT NOT NULL DEFAULT 'dynamic',
            row_count    BIGINT NOT NULL DEFAULT 0,
            column_names TEXT[] NOT NULL DEFAULT '{{}}',
            created_at   TIMESTAMPTZ NOT NULL DEFAULT now()
        )
        """
    )
    op.execute(
        f'CREATE UNIQUE INDEX IF NOT EXISTS csv_files_name_uq '
        f'ON "{_SCHEMA}".csv_files (file_name)'
    )
    op.execute(
        f'CREATE UNIQUE INDEX IF NOT EXISTS csv_files_hash_uq '
        f'ON "{_SCHEMA}".csv_files (file_hash)'
    )
    op.execute(
        f"""
        CREATE TABLE IF NOT EXISTS "{_SCHEMA}".audit_log (
            id BIGSERIAL PRIMARY KEY,
            action TEXT NOT NULL,
            file_id BIGINT,
            file_name TEXT,
            table_name TEXT,
            mode TEXT,
            performed_at TIMESTAMPTZ NOT NULL DEFAULT now()
        )
        """
    )


def downgrade() -> None:
    # Deliberately drops the whole schema — this migration is the baseline,
    # so downgrade returns the database to a completely uninitialised state.
    # Never run against a production DB with real uploads.
    op.execute(f'DROP TABLE IF EXISTS "{_SCHEMA}".audit_log')
    op.execute(f'DROP TABLE IF EXISTS "{_SCHEMA}".csv_files')
    op.execute(f'DROP SCHEMA IF EXISTS "{_SCHEMA}"')
