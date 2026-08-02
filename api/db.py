"""Connection pool + Alembic-driven schema bootstrap for the uploads registry."""

import logging
from pathlib import Path

import psycopg2
import psycopg2.pool

from api.config import settings

logger = logging.getLogger(__name__)

_pool: psycopg2.pool.SimpleConnectionPool | None = None


def init_pool() -> None:
    global _pool
    _pool = psycopg2.pool.SimpleConnectionPool(
        minconn=1,
        maxconn=8,
        host=settings.PG_HOST,
        port=settings.PG_PORT,
        user=settings.PG_USER,
        password=settings.PG_PASSWORD,
        dbname=settings.PG_DATABASE,
    )


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
    """Bring the uploads schema to head via Alembic.

    BUG-032: previously this function ran hand-written CREATE TABLE IF NOT EXISTS
    statements. That was idempotent for the initial deploy but did nothing on
    schema evolution — an ALTER TABLE added in a later release wouldn't ever
    run on an existing deployment.

    Now this function invokes `alembic upgrade head` in-process against the
    same database the API pool is configured for (see alembic/env.py, which
    reads the same api.config.settings values). Every startup checks the
    current schema version and applies any pending migrations transactionally.

    Idempotent: if the DB is already at head, this is a no-op that costs one
    `SELECT version_num FROM alembic_version` query.

    Safe to call after init_pool() — Alembic opens its own SQLAlchemy engine
    with a NullPool and doesn't share connections with the API pool.
    """
    # Deferred imports so pytest collection of api/ doesn't pull in Alembic
    # unless bootstrap() is actually called (e.g. in the lifespan handler,
    # which is only invoked by tests using TestClient as a context manager).
    from alembic import command
    from alembic.config import Config

    repo_root = Path(__file__).resolve().parent.parent
    cfg = Config(str(repo_root / "alembic.ini"))
    logger.info("Running alembic upgrade head against %s@%s:%s/%s",
                settings.PG_USER, settings.PG_HOST, settings.PG_PORT,
                settings.PG_DATABASE)
    command.upgrade(cfg, "head")
    logger.info("Alembic migrations complete")
