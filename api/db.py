"""Connection pool + one-time schema bootstrap for the uploads registry."""

import logging
import time

import psycopg2
import psycopg2.pool
from psycopg2 import sql

from api.config import settings

logger = logging.getLogger(__name__)

_pool: psycopg2.pool.SimpleConnectionPool | None = None


def init_pool(max_attempts: int = 30, base_delay: float = 1.0) -> None:
    """Create the pool, retrying on connection errors.

    BUG-026: on containerised infra Postgres may not accept connections when
    the API starts. Retry with exponential backoff (capped at 10s) instead of
    dying at boot. Total wait is bounded by ``max_attempts`` * cap.
    """
    global _pool
    last_err: Exception | None = None
    for attempt in range(1, max_attempts + 1):
        try:
            _pool = psycopg2.pool.SimpleConnectionPool(
                minconn=1,
                maxconn=8,
                host=settings.PG_HOST,
                port=settings.PG_PORT,
                user=settings.PG_USER,
                password=settings.PG_PASSWORD,
                dbname=settings.PG_DATABASE,
            )
            if attempt > 1:
                logger.info("Connected to Postgres on attempt %d", attempt)
            return
        except psycopg2.OperationalError as exc:
            last_err = exc
            delay = min(base_delay * (2 ** (attempt - 1)), 10.0)
            logger.warning(
                "Postgres not reachable (attempt %d/%d): %s. Retrying in %.1fs.",
                attempt, max_attempts, str(exc).split("\n")[0][:120], delay,
            )
            time.sleep(delay)
    assert last_err is not None
    raise last_err


def close_pool() -> None:
    global _pool
    if _pool is not None:
        _pool.closeall()
        _pool = None


class Conn:
    """Context manager that borrows a pooled connection and always returns it."""

    def __enter__(self):
        if _pool is None:
            raise RuntimeError("DB pool not initialised — call init_pool() first")
        self._conn = _pool.getconn()
        return self._conn

    def __exit__(self, exc_type, exc, tb):
        if exc_type is not None:
            self._conn.rollback()
        _pool.putconn(self._conn)
        return False


def bootstrap() -> None:
    """Create the uploads schema + registry table if missing. Idempotent."""
    with Conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                sql.SQL("CREATE SCHEMA IF NOT EXISTS {}").format(
                    sql.Identifier(settings.UPLOADS_SCHEMA)
                )
            )
            cur.execute(
                sql.SQL(
                    """
                    CREATE TABLE IF NOT EXISTS {}.csv_files (
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
                ).format(sql.Identifier(settings.UPLOADS_SCHEMA))
            )
            cur.execute(
                sql.SQL(
                    "CREATE UNIQUE INDEX IF NOT EXISTS csv_files_name_uq ON {}.csv_files (file_name)"
                ).format(sql.Identifier(settings.UPLOADS_SCHEMA))
            )
            cur.execute(
                sql.SQL(
                    "CREATE UNIQUE INDEX IF NOT EXISTS csv_files_hash_uq ON {}.csv_files (file_hash)"
                ).format(sql.Identifier(settings.UPLOADS_SCHEMA))
            )
            # Audit log: persistent record of every destructive operation.
            cur.execute(
                sql.SQL(
                    """
                    CREATE TABLE IF NOT EXISTS {}.audit_log (
                        id BIGSERIAL PRIMARY KEY,
                        action TEXT NOT NULL,
                        file_id BIGINT,
                        file_name TEXT,
                        table_name TEXT,
                        mode TEXT,
                        performed_at TIMESTAMPTZ NOT NULL DEFAULT now()
                    )
                    """
                ).format(sql.Identifier(settings.UPLOADS_SCHEMA))
            )
        conn.commit()

