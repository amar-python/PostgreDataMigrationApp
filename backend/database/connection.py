"""Database engine, session factory, and connection helpers for MEP.

Provides a synchronous SQLAlchemy engine built from ``settings.DATABASE_URL``,
a session factory, a ``get_db`` context manager / FastAPI dependency, and a
``check_db_connection`` helper used by the health endpoint.
"""
import logging
from typing import Generator

from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session, sessionmaker

from config import settings

logger = logging.getLogger(__name__)

# Create the SQLAlchemy engine. ``pool_pre_ping`` transparently recycles stale
# connections, which is helpful when the database container restarts.
engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,
    future=True,
)

# Session factory bound to the engine.
SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
    expire_on_commit=False,
    class_=Session,
)


def get_db() -> Generator[Session, None, None]:
    """Yield a database session, ensuring it is closed afterwards.

    Usable as a FastAPI dependency: ``db: Session = Depends(get_db)``.
    Also works with ``contextmanager`` wrapping when used outside FastAPI.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def check_db_connection() -> bool:
    """Return ``True`` if a simple ``SELECT 1`` succeeds, else ``False``."""
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        return True
    except Exception as exc:  # noqa: BLE001 - health check must never raise
        logger.warning("Database connection check failed: %s", exc)
        return False
