"""Alembic environment: uses the app's engine/settings and model metadata.

No logging.fileConfig() here on purpose: it would disable the app's loggers when migrations run at startup.
"""
from alembic import context

import app.models  # noqa: F401  (registers every table on Base.metadata)
from app.core.config import settings
from app.db.session import Base, engine

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    context.configure(url=settings.database_url, target_metadata=target_metadata,
                      literal_binds=True, render_as_batch=True)
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    # init_db() passes its own connection; the CLI falls back to the app engine.
    connection = context.config.attributes.get("connection")
    if connection is not None:
        _run(connection)
    else:
        with engine.connect() as conn:
            _run(conn)


def _run(connection) -> None:
    # render_as_batch: SQLite can't ALTER most columns, so Alembic copies the table instead.
    context.configure(connection=connection, target_metadata=target_metadata, render_as_batch=True)
    with context.begin_transaction():
        context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
