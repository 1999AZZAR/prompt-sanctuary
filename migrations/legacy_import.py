"""Initial data migration: copy data from the legacy 4-DB layout to the
unified `app.db` (created by the schema migration that just ran).

Source files (legacy):
  - web/database/user.db             (users, sessions, user_logins,
                                      point_transactions, point_history,
                                      achievements, user_achievements)
  - web/database/prompt_data.db      (prompt_versions, prompts_<username>)
  - web/database/community/shared.db (shared)
  - web/database/feedback.db         (feedback)

This script is idempotent: if the target table already has data for a given
source row, the row is skipped (by primary key / natural key). Running it
twice is safe.

Called from the alembic upgrade at the end of the schema migration
(see migrations/versions/0002_legacy_data_import.py).
"""

from __future__ import annotations

import os
import re
import sqlite3
from datetime import datetime
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import Session

from web.db.models import (
    Achievement,
    Feedback,
    PointHistory,
    PointTransaction,
    Prompt,
    PromptVersion,
    Session as SessionModel,
    SharedPrompt,
    User,
    UserAchievement,
    UserLogin,
)


def _root() -> Path:
    return Path(__file__).resolve().parent.parent


def _resolve(name: str, default: str) -> str:
    """Resolve a legacy DB path. Allow override via env var (same names
    the legacy app used) for the rare case of non-default locations."""
    return os.getenv(name, str(_root() / "web" / "database" / default))


def _sqlite_path(path: str) -> str:
    if path.startswith("sqlite:///"):
        return path.replace("sqlite:///", "", 1)
    return path


def _read_table(conn: sqlite3.Connection, table: str, columns: list[str]) -> list[tuple]:
    """Read all rows from a legacy table. Skips silently if the table
    doesn't exist (legacy DB might be in an early-migration state)."""
    cur = conn.cursor()
    cur.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
        (table,),
    )
    if not cur.fetchone():
        return []
    cols = ", ".join(f"[{c}]" for c in columns)
    cur.execute(f"SELECT {cols} FROM [{table}]")
    return cur.fetchall()


def _coerce_dt(value):
    if value is None or isinstance(value, datetime):
        return value
    if isinstance(value, str):
        # Try ISO format with optional microseconds and timezone first
        try:
            cleaned = value.replace("T", " ")
            # Strip fractional seconds if present (sometimes malformed)
            if "." in cleaned:
                base, _, frac = cleaned.partition(".")
                # Keep at most 6 digits of microseconds
                frac_clean = "".join(c for c in frac if c.isdigit())[:6]
                cleaned = f"{base}.{frac_clean}" if frac_clean else base
            # Strip trailing Z or +00:00 timezone for simplicity
            for tz_suffix in ("Z", "+00:00", "-00:00"):
                if cleaned.endswith(tz_suffix):
                    cleaned = cleaned[: -len(tz_suffix)]
            return datetime.fromisoformat(cleaned)
        except (ValueError, AttributeError):
            pass
        # Fall back to known fixed formats
        for fmt in (
            "%Y-%m-%d %H:%M:%S.%f",
            "%Y-%m-%d %H:%M:%S",
            "%Y-%m-%d",
            "%Y-%m-%dT%H:%M:%S",
            "%Y-%m-%dT%H:%M:%S.%f",
        ):
            try:
                return datetime.strptime(value, fmt)
            except ValueError:
                continue
    return value


def _coerce_date(value):
    if value is None:
        return None
    if isinstance(value, str):
        try:
            return datetime.strptime(value[:10], "%Y-%m-%d").date()
        except ValueError:
            return None
    return value


def import_legacy_data(target: Session) -> dict:
    """Copy all rows from the legacy 4-DB layout into the unified schema.

    Returns a dict of {table_name: rows_imported} for logging.
    """
    counts: dict[str, int] = {}

    user_db = _sqlite_path(_resolve("USER_DATABASE", "user.db"))
    prompt_db = _sqlite_path(_resolve("PROMPT_DATABASE", "prompt_data.db"))
    community_db = _sqlite_path(_resolve("COMMUNITY_DATABASE", "community/shared.db"))
    feedback_db = _sqlite_path(_resolve("FEEDBACK_DATABASE", "feedback.db"))

    # --- USERS ---
    with sqlite3.connect(user_db) as conn:
        rows = _read_table(
            conn,
            "users",
            [
                "username",
                "password",
                "points",
                "gemini_api_key",
                "api_key_validated",
                "email",
                "identicon_value",
            ],
        )
    n = 0
    for (
        username,
        password,
        points,
        gemini_api_key,
        api_key_validated,
        email,
        identicon_value,
    ) in rows:
        if target.get(User, username) is None:
            target.add(
                User(
                    username=username,
                    password=password,
                    points=points or 80.0,
                    gemini_api_key=gemini_api_key,
                    api_key_validated=int(api_key_validated or 0),
                    email=email,
                    identicon_value=identicon_value,
                )
            )
            n += 1
    target.flush()
    counts["users"] = n

    # --- SESSIONS ---
    with sqlite3.connect(user_db) as conn:
        rows = _read_table(
            conn,
            "sessions",
            ["token", "username", "user_agent", "ip", "created_at", "last_active", "revoked"],
        )
    n = 0
    for token, username, user_agent, ip, created_at, last_active, revoked in rows:
        if not target.get(User, username):
            continue
        if target.get(SessionModel, token) is None:
            target.add(
                SessionModel(
                    token=token,
                    username=username,
                    user_agent=user_agent,
                    ip=ip,
                    created_at=_coerce_dt(created_at) or datetime.utcnow(),
                    last_active=_coerce_dt(last_active),
                    revoked=int(revoked or 0),
                )
            )
            n += 1
    target.flush()
    counts["sessions"] = n

    # --- USER LOGINS ---
    with sqlite3.connect(user_db) as conn:
        rows = _read_table(conn, "user_logins", ["id", "username", "login_date", "points_awarded"])
    n = 0
    for _id, username, login_date, points_awarded in rows:
        if not target.get(User, username):
            continue
        existing = target.execute(
            select(UserLogin).where(
                UserLogin.username == username, UserLogin.login_date == _coerce_date(login_date)
            )
        ).scalar_one_or_none()
        if existing is None:
            target.add(
                UserLogin(
                    username=username,
                    login_date=_coerce_date(login_date),
                    points_awarded=points_awarded or 0.0,
                )
            )
            n += 1
    target.flush()
    counts["user_logins"] = n

    # --- ACHIEVEMENTS ---
    with sqlite3.connect(user_db) as conn:
        rows = _read_table(
            conn,
            "achievements",
            [
                "id",
                "name",
                "description",
                "icon",
                "points_reward",
                "category",
                "condition_type",
                "condition_value",
                "hidden",
            ],
        )
    n = 0
    name_to_id: dict[str, int] = {}
    for (
        legacy_id,
        name,
        description,
        icon,
        points_reward,
        category,
        condition_type,
        condition_value,
        hidden,
    ) in rows:
        existing = target.execute(
            select(Achievement).where(Achievement.name == name)
        ).scalar_one_or_none()
        if existing is None:
            ach = Achievement(
                name=name,
                description=description,
                icon=icon,
                points_reward=points_reward or 0.0,
                category=category,
                condition_type=condition_type,
                condition_value=condition_value,
                hidden=int(hidden or 0),
            )
            target.add(ach)
            target.flush()
            name_to_id[name] = ach.id
            n += 1
        else:
            name_to_id[name] = existing.id
    target.flush()
    counts["achievements"] = n

    # --- USER ACHIEVEMENTS ---
    with sqlite3.connect(user_db) as conn:
        rows = _read_table(
            conn, "user_achievements", ["id", "username", "achievement_id", "unlocked_at"]
        )
    n = 0
    for _id, username, legacy_achievement_id, unlocked_at in rows:
        if not target.get(User, username):
            continue
        ach = target.get(Achievement, legacy_achievement_id)
        if ach is None:
            continue
        existing = target.execute(
            select(UserAchievement).where(
                UserAchievement.username == username, UserAchievement.achievement_id == ach.id
            )
        ).scalar_one_or_none()
        if existing is None:
            target.add(
                UserAchievement(
                    username=username,
                    achievement_id=ach.id,
                    unlocked_at=_coerce_dt(unlocked_at) or datetime.utcnow(),
                )
            )
            n += 1
    target.flush()
    counts["user_achievements"] = n

    # --- POINT TRANSACTIONS ---
    pt_legacy_to_new: dict[int, int] = {}
    with sqlite3.connect(user_db) as conn:
        rows = _read_table(
            conn,
            "point_transactions",
            [
                "id",
                "username",
                "points",
                "source",
                "description",
                "created_at",
                "expires_at",
                "is_expired",
            ],
        )
    n = 0
    for (
        legacy_id,
        username,
        points,
        source,
        description,
        created_at,
        expires_at,
        is_expired,
    ) in rows:
        if not target.get(User, username):
            continue
        if target.get(PointTransaction, legacy_id) is None:
            pt = PointTransaction(
                id=legacy_id,
                username=username,
                points=points or 0.0,
                source=source or "unknown",
                description=description,
                created_at=_coerce_dt(created_at) or datetime.utcnow(),
                expires_at=_coerce_dt(expires_at),
                is_expired=int(is_expired or 0),
            )
            target.add(pt)
            pt_legacy_to_new[legacy_id] = legacy_id
            n += 1
    target.flush()
    counts["point_transactions"] = n

    # --- POINT HISTORY ---
    with sqlite3.connect(user_db) as conn:
        rows = _read_table(
            conn,
            "point_history",
            [
                "id",
                "username",
                "transaction_id",
                "action",
                "points_before",
                "points_after",
                "created_at",
            ],
        )
    n = 0
    for (
        legacy_id,
        username,
        transaction_id,
        action,
        points_before,
        points_after,
        created_at,
    ) in rows:
        if not target.get(User, username):
            continue
        new_txn_id = pt_legacy_to_new.get(transaction_id)
        if new_txn_id is None:
            continue
        if target.get(PointHistory, legacy_id) is None:
            target.add(
                PointHistory(
                    id=legacy_id,
                    username=username,
                    transaction_id=new_txn_id,
                    action=action or "add",
                    points_before=points_before or 0.0,
                    points_after=points_after or 0.0,
                    created_at=_coerce_dt(created_at) or datetime.utcnow(),
                )
            )
            n += 1
    target.flush()
    counts["point_history"] = n

    # --- PROMPT VERSIONS ---
    with sqlite3.connect(prompt_db) as conn:
        rows = _read_table(
            conn,
            "prompt_versions",
            ["id", "username", "prompt_id", "version_number", "title", "prompt", "created_at"],
        )
    n = 0
    for legacy_id, username, prompt_id, version_number, title, prompt_text, created_at in rows:
        if not target.get(User, username):
            continue
        if target.get(PromptVersion, legacy_id) is None:
            target.add(
                PromptVersion(
                    id=legacy_id,
                    username=username,
                    prompt_id=prompt_id,
                    version_number=version_number or 1,
                    title=title or "",
                    prompt=prompt_text or "",
                    created_at=_coerce_dt(created_at) or datetime.utcnow(),
                )
            )
            n += 1
    target.flush()
    counts["prompt_versions"] = n

    # --- PER-USER PROMPTS (the dynamic prompts_<username> tables) ---
    n = 0
    if os.path.exists(prompt_db):
        with sqlite3.connect(prompt_db) as conn:
            cur = conn.cursor()
            cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in cur.fetchall()]
        for table_name in tables:
            # Skip system tables, prompt_versions, and any name that doesn't look like a username
            if table_name in ("sqlite_sequence", "prompt_versions"):
                continue
            if not re.match(r"^[A-Za-z0-9_]{1,64}$", table_name):
                continue
            with sqlite3.connect(prompt_db) as conn:
                rows = _read_table(conn, table_name, ["random_val", "title", "prompt", "time"])
            for random_val, title, prompt_text, time in rows:
                if (
                    target.execute(
                        select(Prompt).where(
                            Prompt.username == table_name, Prompt.random_val == random_val
                        )
                    ).scalar_one_or_none()
                    is None
                ):
                    target.add(
                        Prompt(
                            username=table_name,
                            random_val=random_val,
                            title=title or "",
                            prompt=prompt_text or "",
                            time=_coerce_dt(time) or datetime.utcnow(),
                        )
                    )
                    n += 1
        target.flush()
    counts["prompts"] = n

    # --- SHARED PROMPTS ---
    n = 0
    if os.path.exists(community_db):
        with sqlite3.connect(community_db) as conn:
            rows = _read_table(
                conn, "shared", ["id", "owner", "random_val", "title", "prompt", "time"]
            )
        for legacy_id, owner, random_val, title, prompt_text, time in rows:
            if not target.get(User, owner):
                continue
            existing = target.execute(
                select(SharedPrompt).where(SharedPrompt.random_val == random_val)
            ).scalar_one_or_none()
            if existing is None:
                target.add(
                    SharedPrompt(
                        id=legacy_id,
                        owner=owner,
                        random_val=random_val,
                        title=title or "",
                        prompt=prompt_text or "",
                        time=_coerce_dt(time) or datetime.utcnow(),
                    )
                )
                n += 1
        target.flush()
    counts["shared_prompts"] = n

    # --- FEEDBACK ---
    n = 0
    if os.path.exists(feedback_db):
        with sqlite3.connect(feedback_db) as conn:
            rows = _read_table(conn, "feedback", ["id", "username", "feedback"])
        for legacy_id, username, feedback_text in rows:
            if not target.get(User, username):
                continue
            if target.get(Feedback, legacy_id) is None:
                target.add(
                    Feedback(
                        id=legacy_id,
                        username=username,
                        feedback=feedback_text or "",
                    )
                )
                n += 1
        target.flush()
    counts["feedback"] = n

    return counts
