"""SQLAlchemy engine, session factory, and Flask integration.

Exposes:
- Base (re-exported from models)
- engine: the SQLAlchemy Engine bound to DATABASE_URL
- SessionLocal: a sessionmaker (autoflush=False, expire_on_commit=False)
- get_session(): context manager that yields a session, commits on success,
  rolls back on exception
- init_app(app): Flask integration — binds a scoped session to the app, runs
  `alembic upgrade head` on first request, and registers a teardown handler
  that closes the session at the end of every request.
"""

from __future__ import annotations

import os
import subprocess
import sys
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

from flask import Flask, g
from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from .models import Base


def _database_url() -> str:
    """Resolve the database URL. Defaults to a single SQLite file in
    web/database/app.db. Honors DATABASE_URL env var (for postgres etc.)."""
    url = os.getenv("DATABASE_URL")
    if url:
        return url
    base = Path(__file__).resolve().parent.parent
    db_path = os.getenv("APP_DATABASE", str(base / "database" / "app.db"))
    return f"sqlite:///{db_path}"


def _ensure_sqlite_dir(url: str) -> None:
    """Create the parent directory for a sqlite:/// URL if needed."""
    if url.startswith("sqlite:///"):
        path = url.replace("sqlite:///", "", 1)
        parent = Path(path).parent
        if parent and not parent.exists():
            parent.mkdir(parents=True, exist_ok=True)


engine: Engine = create_engine(
    _database_url(),
    echo=False,
    future=True,
    pool_pre_ping=True,
)

_ensure_sqlite_dir(_database_url())


@event.listens_for(Engine, "connect")
def _enable_sqlite_pragmas(dbapi_connection, connection_record):
    """Apply PRAGMAs on every new SQLite connection.

    - foreign_keys=ON: enforce FK constraints (off by default in sqlite3)
    - journal_mode=WAL: better concurrent reads
    - synchronous=NORMAL: durability vs throughput tradeoff
    """
    try:
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.execute("PRAGMA synchronous=NORMAL")
        cursor.close()
    except Exception:
        # Non-sqlite dialects may not support these PRAGMAs
        pass


SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False, future=True)


@contextmanager
def get_session() -> Iterator[Session]:
    """Context-managed session. Commits on success, rolls back on exception.

    Use this for one-off operations outside a Flask request (CLI, jobs).
    Inside a request, prefer the g.session attached by init_app().
    """
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def _run_migrations() -> None:
    """Run `alembic upgrade head` against the configured DATABASE_URL.

    Called once on Flask startup. Safe to call repeatedly: Alembic tracks
    applied revisions in the alembic_version table.
    """
    migrations_dir = Path(__file__).resolve().parent.parent / "migrations"
    if not migrations_dir.exists():
        return
    env = os.environ.copy()
    env.setdefault("DATABASE_URL", _database_url())
    subprocess.run(
        [sys.executable, "-m", "alembic", "upgrade", "head"],
        cwd=str(migrations_dir.parent),
        env=env,
        check=False,
        capture_output=True,
    )


def init_app(app: Flask) -> None:
    """Bind SQLAlchemy to the Flask app.

    - Opens a per-request session stored on flask.g
    - Closes the session at the end of every request (even on exception)
    - Runs Alembic migrations once on first app startup
    """
    _run_migrations()

    @app.teardown_appcontext
    def _close_session(exc):
        session: Session | None = g.pop("db_session", None)
        if session is not None:
            try:
                if exc is None:
                    session.commit()
                else:
                    session.rollback()
            finally:
                session.close()

    @app.before_request
    def _open_session():
        if "db_session" not in g:
            g.db_session = SessionLocal()


__all__ = [
    "Base",
    "engine",
    "SessionLocal",
    "get_session",
    "init_app",
]
