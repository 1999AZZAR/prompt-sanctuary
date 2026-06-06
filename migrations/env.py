"""Alembic environment configuration.

- Loads DATABASE_URL from env (falls back to the unified SQLite at
  web/database/app.db so the same path the app uses is what Alembic migrates)
- Sets target_metadata to web.db.models.Base.metadata so `alembic revision
  --autogenerate` can diff the schema against the DB
- Disables SQLAlchemy's "transactional DDL" wrapping on SQLite (so PRAGMAs
  and other engine-level statements work in migrations)
"""

from __future__ import annotations

import os
import sys
from logging.config import fileConfig
from pathlib import Path

from alembic import context
from sqlalchemy import engine_from_config, pool

# Make `web` importable so we can pull the declarative metadata
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from web.db.models import Base  # noqa: E402

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Resolve the database URL the same way web.db does
def _resolve_url() -> str:
    url = os.getenv("DATABASE_URL")
    if url:
        return url
    db_path = os.getenv("APP_DATABASE", str(ROOT / "web" / "database" / "app.db"))
    return f"sqlite:///{db_path}"


config.set_main_option("sqlalchemy.url", _resolve_url())

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        render_as_batch=True,
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        is_sqlite = connection.dialect.name == "sqlite"
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            render_as_batch=is_sqlite,
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
