from alembic import command
from alembic.autogenerate import compare_metadata
from alembic.config import Config
from alembic.migration import MigrationContext
from sqlalchemy import create_engine, inspect

import app.models  # noqa: F401
from app.core.config import BACKEND_DIR
from app.db.session import Base


def test_migrations_build_exactly_the_model_schema(tmp_path):
    """Fails when a model changes without a migration: run `alembic revision --autogenerate`."""
    engine = create_engine(f"sqlite:///{(tmp_path / 'migrated.db').as_posix()}")
    cfg = Config(str(BACKEND_DIR / "alembic.ini"))
    with engine.begin() as connection:
        cfg.attributes["connection"] = connection
        command.upgrade(cfg, "head")
        assert "alembic_version" in inspect(connection).get_table_names()
        differences = compare_metadata(MigrationContext.configure(connection), Base.metadata)
    assert differences == []
