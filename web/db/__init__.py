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

import logging
import os
import subprocess
import sys
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

from flask import Flask, g
from sqlalchemy import create_engine, event, text
from sqlalchemy.engine import Engine

logger = logging.getLogger(__name__)
from sqlalchemy.orm import Session, sessionmaker  # noqa: E402

from .models import Base  # noqa: E402


def _database_url() -> str:
    """Resolve the database URL. Honors DATABASE_URL; falls back to SQLite.

    Supports SQLite and PostgreSQL via SQLAlchemy URL schemes
    (sqlite:///... and postgresql+psycopg://...).
    """
    url = os.getenv("DATABASE_URL")
    if url:
        return url
    base = Path(__file__).resolve().parent.parent
    db_path = os.getenv("APP_DATABASE", str(base / "database" / "app.db"))
    return f"sqlite:///{db_path}"


def _is_postgres(url: str) -> bool:
    return url.startswith(("postgres://", "postgresql://", "postgresql+"))


def _ensure_sqlite_dir(url: str) -> None:
    if url.startswith("sqlite:///"):
        path = url.replace("sqlite:///", "", 1)
        parent = Path(path).parent
        if parent and not parent.exists():
            parent.mkdir(parents=True, exist_ok=True)


def _engine_kwargs(url: str) -> dict:
    """Per-dialect engine config.

    - Postgres: real connection pool sized for gunicorn workers x threads,
      pool_pre_ping reconnects stale connections, recycle every hour.
    - SQLite: single shared connection per process (each gunicorn worker has
      one) — multi-thread is handled via check_same_thread=False because
      gunicorn's threaded worker model needs to share.
    """
    if _is_postgres(url):
        return dict(
            pool_size=int(os.getenv("DB_POOL_SIZE", "10")),
            max_overflow=int(os.getenv("DB_MAX_OVERFLOW", "20")),
            pool_pre_ping=True,
            pool_recycle=3600,
            pool_timeout=30,
            future=True,
            echo=False,
        )
    return dict(
        connect_args={"check_same_thread": False},
        future=True,
        echo=False,
    )


engine: Engine = create_engine(_database_url(), **_engine_kwargs(_database_url()))

_ensure_sqlite_dir(_database_url())

_IS_POSTGRES = _is_postgres(_database_url())


@event.listens_for(Engine, "connect")
def _on_connect(dbapi_connection, connection_record):
    """Apply per-dialect connect-time settings.

    - SQLite: enable FK enforcement and WAL mode (see PRAGMAs below).
    - Postgres: set the application_name for pg_stat_activity so the
      app's connections are recognisable in the DB.
    """
    if _IS_POSTGRES:
        try:
            cursor = dbapi_connection.cursor()
            cursor.execute("SET application_name = 'prompt-sanctuary'")
            cursor.close()
        except Exception:
            pass
        return

    try:
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.execute("PRAGMA synchronous=NORMAL")
        cursor.close()
    except Exception:
        pass


SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False, future=True)


@contextmanager
def get_session() -> Iterator[Session]:
    """Context-managed session. Commits on success, rolls back on exception.

    Use this for one-off operations outside a Flask request (CLI, jobs).
    Inside a request, prefer the g.db_session attached by init_app().
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


def _acquire_alembic_lock() -> object | None:
    """Lock so gunicorn workers don't race the first `alembic upgrade head`.

    - Postgres: a session-scoped advisory lock (pg_advisory_lock). All workers
      queue on the same integer key; only one runs the migration at a time.
    - SQLite: an OS file lock on a sentinel file next to the DB file.
    """
    db_url = _database_url()
    if _is_postgres(db_url):
        # Return a context manager that holds an advisory lock for the
        # duration of the migration. Use a fixed key derived from the
        # DATABASE_URL so multiple apps on the same DB don't collide.
        key = abs(hash(db_url)) % (2**31)
        holder = _PostgresAdvisoryLock(engine, key)
        holder.acquire()
        return holder
    db_path = db_url.replace("sqlite:///", "")
    lock_path = f"{db_path}.alembic.lock"
    try:
        import fcntl
    except ImportError:
        fcntl = None  # type: ignore[assignment]
    file = open(lock_path, "w")
    if fcntl is not None:
        try:
            fcntl.flock(file.fileno(), fcntl.LOCK_EX)
        except OSError:
            pass
    return file


class _PostgresAdvisoryLock:
    """Holds a Postgres transaction-scoped advisory lock.

    pg_advisory_lock(int) is session-scoped: the lock is released when
    the session ends (or pg_advisory_unlock is called). We hold a single
    long-lived session for the migration.
    """

    def __init__(self, eng: Engine, key: int) -> None:
        self._engine = eng
        self._key = key
        self._conn = None

    def acquire(self) -> None:
        # Use a separate engine with no pool so we can keep the connection
        # open for the migration lifetime without it being reused.
        from sqlalchemy.pool import NullPool

        eng = create_engine(_database_url(), poolclass=NullPool, future=True)
        self._conn = eng.connect()
        self._conn.execution_options(isolation_level="AUTOCOMMIT")
        self._conn.execute(text("SELECT pg_advisory_lock(:k)"), {"k": self._key})

    def release(self) -> None:
        try:
            if self._conn is not None:
                self._conn.execute(text("SELECT pg_advisory_unlock(:k)"), {"k": self._key})
                self._conn.close()
        except Exception:
            pass


def _run_migrations() -> None:
    """Run `alembic upgrade head` against the configured DATABASE_URL.

    Called once on Flask startup. Safe to call repeatedly: Alembic tracks
    applied revisions in the alembic_version table.

    On Postgres the advisory lock serialises workers; on SQLite the file
    lock does the same.
    """
    project_root = Path(__file__).resolve().parent.parent.parent
    migrations_dir = project_root / "migrations"
    alembic_ini = project_root / "alembic.ini"
    if not (migrations_dir.exists() and alembic_ini.exists()):
        logger.warning(
            "Skipping alembic migrations: %s or %s not found",
            migrations_dir,
            alembic_ini,
        )
        return

    lock = _acquire_alembic_lock()
    try:
        env = os.environ.copy()
        env.setdefault("DATABASE_URL", _database_url())
        result = subprocess.run(
            [sys.executable, "-m", "alembic", "-c", str(alembic_ini), "upgrade", "head"],
            cwd=str(project_root),
            env=env,
            check=False,
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            logger.error("alembic upgrade head failed (rc=%s)", result.returncode)
            if result.stdout:
                logger.error("stdout: %s", result.stdout)
            if result.stderr:
                logger.error("stderr: %s", result.stderr)
        else:
            if result.stdout and result.stdout.strip():
                for line in result.stdout.splitlines():
                    if line.strip():
                        logger.info("alembic: %s", line)
    finally:
        if lock is not None and hasattr(lock, "release"):
            lock.release()


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
