"""Alembic runtime — reads DB creds from api.config.settings.

BUG-032: no SQLAlchemy models exist in this project (the API uses raw psycopg2
throughout), so we do NOT use autogenerate. Every migration is hand-written
as raw SQL via op.execute(). This keeps parity with api/db.py and avoids
introducing an ORM.

The `alembic.ini` sqlalchemy.url is a placeholder — the real URL is built here
from the same environment variables (PGHOST/PGPORT/PGUSER/PGPASSWORD/PGDATABASE)
that scripts/start-api.ps1 sets. This means:
  - The API and Alembic always target the same database.
  - Running `python -m alembic upgrade head` from a shell uses the same env
    vars a developer already sets to run the API.
"""

from logging.config import fileConfig

from alembic import context
from sqlalchemy import create_engine, pool
from sqlalchemy.engine.url import URL

from api.config import settings

config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)


def _db_url() -> str:
    return URL.create(
        drivername="postgresql+psycopg2",
        username=settings.PG_USER,
        password=settings.PG_PASSWORD,
        host=settings.PG_HOST,
        port=settings.PG_PORT,
        database=settings.PG_DATABASE,
    ).render_as_string(hide_password=False)


def run_migrations_offline() -> None:
    """Emit SQL to stdout instead of applying — for --sql review workflows."""
    context.configure(
        url=_db_url(),
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Actually apply migrations against the configured database."""
    engine = create_engine(_db_url(), poolclass=pool.NullPool)
    with engine.connect() as connection:
        context.configure(connection=connection)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
