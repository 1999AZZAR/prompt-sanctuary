"""Domain functions for Prompt Sanctuary.

All persistence is now through SQLAlchemy (web.db). Function signatures are
preserved from the legacy raw-sql implementation so routes.py and any
external callers can keep working unchanged — the `user_db`, `prompt_db`,
`community_db`, `feedback_db` path arguments are accepted but ignored (all
data lives in a single unified `app.db`).
"""

from __future__ import annotations

import hashlib
import logging
import random
import re
import secrets
import time
from datetime import date, datetime, timedelta

from flask import g, session
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError, OperationalError

from db import SessionLocal, get_session
from db.models import (
    Achievement,
    Base,
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
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

POINT_EXPIRATION = {
    "daily_login": (17, 30),
    "achievement": 45,
    "api_key_add": 80,
    "api_key_usage": 95,
    "prompt_share": 30,
    "prompt_unshare": 30,
    "prompt_generation": 15,
    "advance_generation": 20,
    "api_key_remove": None,
    "original": None,
}


def _session():
    """Return the request-scoped session if we're inside a Flask request,
    otherwise a fresh standalone session.

    The Flask request session is on flask.g.db_session (set up by web.db.init_app).
    Standalone callers (CLI, jobs) get a one-shot session they must close.
    """
    try:
        return g.db_session
    except RuntimeError:
        with SessionLocal() as s:
            yield s


def _with_session(fn):
    """Decorator that runs `fn` inside a session context.

    - If the caller already passed a Session as the first positional argument
      (e.g. when one helper calls another from inside its own @_with_session
      body), use that session directly. No re-wrap.
    - Otherwise, in a Flask request, use the request-scoped session on
      flask.g (the teardown handler commits or rolls back).
    - Otherwise (CLI/standalone), open a fresh SessionLocal, commit on success,
      roll back on exception.
    """
    def wrapper(*args, **kwargs):
        if args and isinstance(args[0], Session):
            return fn(*args, **kwargs)
        try:
            sess = g.db_session
            return fn(sess, *args, **kwargs)
        except RuntimeError:
            with SessionLocal() as sess:
                try:
                    result = fn(sess, *args, **kwargs)
                    sess.commit()
                    return result
                except Exception:
                    sess.rollback()
                    raise
    return wrapper


# ============================================================================
# Schema initialization (now a no-op — Alembic manages the schema)
# ============================================================================

def invalidate_user_cache(username: str) -> None:
    """Drop the cached values that depend on the user's mutable state.

    Call this after any write that changes points, prompt list, or sharing
    status. The function is best-effort: if Redis is down, the cache will
    simply expire on its TTL.
    """
    from cache import cache_invalidate_pattern
    cache_invalidate_pattern(f"sanctuary:points:{username}:*")
    cache_invalidate_pattern(f"sanctuary:share_status:{username}:*")
    cache_invalidate_pattern(f"sanctuary:prompts:{username}:*")


def create_tables(user_db, prompt_db, community_db, feedback_db):
    """Deprecated. Schema is managed by Alembic; this is a no-op kept for
    backward compatibility with web.app.py. Run `alembic upgrade head` to
    apply migrations."""
    logger.debug("create_tables() is a no-op; schema managed by Alembic")


def create_user_table_if_not_exists(username, prompt_db):
    """Deprecated. Prompts are stored in a single unified table with a
    `username` column, so no per-user table is needed. This function is kept
    for routes.py backward compat."""
    if not re.match(r"^[A-Za-z0-9_]+$", username):
        raise ValueError(f"Invalid username for table: {username}")


def get_db_connection(db_path):
    """Deprecated. Use the SQLAlchemy session instead.

    Kept for backward compatibility with any code that imported this from
    web.models. Raises NotImplementedError.
    """
    raise NotImplementedError(
        "get_db_connection() is removed. Use the SQLAlchemy session from "
        "flask.g.db_session (in request handlers) or web.db.get_session() "
        "(in standalone code)."
    )


def execute_sql(conn, sql, params=None):
    raise NotImplementedError("execute_sql() is removed; use the SQLAlchemy session")


def enable_wal_mode(db_path):
    """No-op. SQLAlchemy's event listener in web.db.__init__ applies PRAGMAs
    on every new connection."""
    pass


# ============================================================================
# Schema migration helpers (legacy ensure_* functions)
# ============================================================================

def ensure_prompt_versions_schema(prompt_db):  # noqa: ARG001
    pass


def ensure_shared_schema(community_db):  # noqa: ARG001
    pass


def ensure_feedback_schema(feedback_db):  # noqa: ARG001
    pass


def ensure_users_schema(user_db):  # noqa: ARG001
    pass


# ============================================================================
# Users
# ============================================================================

@_with_session
def get_user_email(s, user_db, username: str):  # noqa: ARG001
    user = s.get(User, username)
    return user.email if user else None


@_with_session
def get_user_identicon_value(s, user_db, username: str):  # noqa: ARG001
    user = s.get(User, username)
    return user.identicon_value if user else None


@_with_session
def set_user_identicon_value(s, user_db, username: str, identicon_value: str):  # noqa: ARG001
    user = s.get(User, username)
    if user is not None:
        user.identicon_value = identicon_value


@_with_session
def update_user_email(s, user_db, username: str, email):  # noqa: ARG001
    user = s.get(User, username)
    if user is not None:
        user.email = email


def generate_identicon_value(username: str) -> str:
    return hashlib.sha256(username.encode("utf-8")).hexdigest()[:16]


@_with_session
def change_username_everywhere(s, old_username: str, new_username: str,
                              user_db, prompt_db, community_db, feedback_db):  # noqa: ARG001
    """Rename a user across all tables.

    Raises ValueError on invalid/conflicting names.
    """
    if not re.match(r"^[A-Za-z0-9_]+$", new_username):
        raise ValueError("Invalid username format. Only letters, numbers, and underscores are allowed.")
    if s.get(User, new_username) is not None:
        raise ValueError("Username already exists. Please choose another.")

    s.execute(
        User.__table__.update().where(User.username == old_username).values(username=new_username)
    )
    s.execute(
        Prompt.__table__.update().where(Prompt.username == old_username).values(username=new_username)
    )
    s.execute(
        PromptVersion.__table__.update().where(PromptVersion.username == old_username).values(username=new_username)
    )
    s.execute(
        SharedPrompt.__table__.update().where(SharedPrompt.owner == old_username).values(owner=new_username)
    )
    s.execute(
        Feedback.__table__.update().where(Feedback.username == old_username).values(username=new_username)
    )
    s.execute(
        UserLogin.__table__.update().where(UserLogin.username == old_username).values(username=new_username)
    )
    s.execute(
        PointTransaction.__table__.update().where(PointTransaction.username == old_username).values(username=new_username)
    )
    s.execute(
        PointHistory.__table__.update().where(PointHistory.username == old_username).values(username=new_username)
    )
    s.execute(
        UserAchievement.__table__.update().where(UserAchievement.username == old_username).values(username=new_username)
    )
    s.execute(
        SessionModel.__table__.update().where(SessionModel.username == old_username).values(username=new_username)
    )


# ============================================================================
# Sessions
# ============================================================================

@_with_session
def create_session_record(s, user_db, username: str, token: str,  # noqa: ARG001
                          user_agent, ip):  # noqa: ARG001
    s.add(SessionModel(
        token=token,
        username=username,
        user_agent=user_agent,
        ip=ip,
        last_active=datetime.utcnow(),
    ))


@_with_session
def touch_session(s, user_db, token: str):  # noqa: ARG001
    sess = s.get(SessionModel, token)
    if sess is not None:
        sess.last_active = datetime.utcnow()


@_with_session
def is_session_valid(s, user_db, token: str, username: str) -> bool:  # noqa: ARG001
    sess = s.get(SessionModel, token)
    return bool(sess and sess.username == username and not sess.revoked)


@_with_session
def revoke_session(s, user_db, token: str, username: str) -> bool:  # noqa: ARG001
    sess = s.get(SessionModel, token)
    if sess and sess.username == username and not sess.revoked:
        sess.revoked = 1
        return True
    return False


@_with_session
def list_sessions_for_user(s, user_db, username: str):  # noqa: ARG001
    rows = s.execute(
        select(SessionModel).where(SessionModel.username == username)
        .order_by(func.coalesce(SessionModel.last_active, SessionModel.created_at).desc())
    ).scalars().all()
    return [
        {
            "token": r.token,
            "user_agent": r.user_agent,
            "ip": r.ip,
            "created_at": r.created_at,
            "last_active": r.last_active,
            "revoked": bool(r.revoked),
        }
        for r in rows
    ]


@_with_session
def revoke_other_sessions(s, user_db, username: str, except_token=None) -> int:  # noqa: ARG001
    q = s.query(SessionModel).filter(
        SessionModel.username == username,
        SessionModel.revoked == 0,
    )
    if except_token:
        q = q.filter(SessionModel.token != except_token)
    n = 0
    for sess in q.all():
        sess.revoked = 1
        n += 1
    return n


# ============================================================================
# API key
# ============================================================================

@_with_session
def get_user_api_key(s, user_db, username: str):  # noqa: ARG001
    user = s.get(User, username)
    return user.gemini_api_key if user else None


@_with_session
def set_user_api_key(s, user_db, username: str, api_key: str):  # noqa: ARG001
    user = s.get(User, username)
    if user is not None:
        user.gemini_api_key = api_key


@_with_session
def is_api_key_validated(s, user_db, username: str) -> bool:  # noqa: ARG001
    user = s.get(User, username)
    return bool(user and user.api_key_validated)


@_with_session
def set_api_key_validated(s, user_db, username: str, validated: bool = True):  # noqa: ARG001
    user = s.get(User, username)
    if user is not None:
        user.api_key_validated = 1 if validated else 0


# ============================================================================
# Prompts (personal library)
# ============================================================================

@_with_session
def get_next_version_number(s, username, prompt_id, prompt_db):  # noqa: ARG001
    result = s.execute(
        select(func.coalesce(func.max(PromptVersion.version_number), 0))
        .where(PromptVersion.username == username, PromptVersion.prompt_id == prompt_id)
    ).scalar()
    return (result or 0) + 1


@_with_session
def insert_prompt_version(s, username, prompt_id, version_number, title, prompt_text, prompt_db):  # noqa: ARG001
    s.add(PromptVersion(
        username=username,
        prompt_id=prompt_id,
        version_number=version_number,
        title=title,
        prompt=prompt_text,
    ))


@_with_session
def save_prompt_to_db(s, username, random_val, title, prompt_text, prompt_db):  # noqa: ARG001
    if not re.match(r"^[A-Za-z0-9_]+$", username):
        raise ValueError(f"Invalid username for table: {username}")
    s.add(Prompt(
        username=username,
        random_val=random_val,
        title=title,
        prompt=prompt_text,
    ))
    return random_val


# ============================================================================
# Community (shared prompts)
# ============================================================================

@_with_session
def get_prompt_sharing_status(s, username: str, prompt_id: str, title: str,
                              prompt_content: str, prompt_db: str, community_db: str):  # noqa: ARG001
    from cache import cache_through, k
    key = k("share_status", username, prompt_id)
    def _compute():
        row = s.execute(
            select(SharedPrompt.title, SharedPrompt.prompt)
            .where(SharedPrompt.owner == username, SharedPrompt.random_val == prompt_id)
        ).first()
        if not row:
            return {
                "is_shared": False,
                "needs_update": False,
                "shared_title": None,
                "shared_content": None,
            }
        shared_title, shared_content = row
        return {
            "is_shared": True,
            "needs_update": shared_title != title or shared_content != prompt_content,
            "shared_title": shared_title,
            "shared_content": shared_content,
        }
    return cache_through(key, 60, _compute)


# ============================================================================
# Points / transactions / history
# ============================================================================

def calculate_expiration_date(source: str):
    if source == "original":
        return None
    cfg = POINT_EXPIRATION.get(source)
    if cfg is None:
        return None
    if isinstance(cfg, tuple):
        days = random.randint(*cfg)
    else:
        days = cfg
    return datetime.now() + timedelta(days=days)


@_with_session
def get_user_points(s, user_db, username: str) -> float:  # noqa: ARG001
    """Sum of non-expired point transactions for the user.

    Cached for 30s in Redis to absorb the per-request read on every page
    load. Invalidated on point changes (see invalidate_user_cache()).
    """
    from cache import cache_through, k

    def _compute() -> float:
        try:
            result = s.execute(
                select(func.coalesce(func.sum(PointTransaction.points), 0.0))
                .where(
                    PointTransaction.username == username,
                    PointTransaction.is_expired == 0,
                )
                .where(
                    (PointTransaction.expires_at.is_(None))
                    | (PointTransaction.expires_at > datetime.utcnow())
                )
            ).scalar()
            return float(result or 0.0) or 80.0
        except Exception as e:
            logger.exception("Failed to get user points for %s: %s", username, e)
            return 80.0

    return float(cache_through(k("points", username), 30, _compute) or 80.0)


@_with_session
def add_user_points_with_source(s, user_db, username: str, points: float,  # noqa: ARG001
                                source: str, description=None) -> bool:
    """Add points with source tracking. Caps at 500."""
    try:
        # Ensure initial 80-point transaction exists
        has_initial = s.execute(
            select(func.count()).select_from(PointTransaction)
            .where(PointTransaction.username == username, PointTransaction.source == "original")
        ).scalar()
        if not has_initial:
            s.add(PointTransaction(
                username=username,
                points=80.0,
                source="original",
                description="Initial points",
                expires_at=None,
                is_expired=0,
            ))

        expires_at = calculate_expiration_date(source)
        s.add(PointTransaction(
            username=username,
            points=points,
            source=source,
            description=description,
            expires_at=expires_at,
            is_expired=0,
        ))
        s.flush()
        transaction_id = s.execute(
            select(PointTransaction.id).where(PointTransaction.username == username)
            .order_by(PointTransaction.id.desc()).limit(1)
        ).scalar()

        # Compute before/after
        before = get_user_points(s, user_db, username) - points
        after = min(before + points, 500.0)

        s.add(PointHistory(
            username=username,
            transaction_id=transaction_id,
            action="add",
            points_before=before,
            points_after=after,
        ))
        invalidate_user_cache(username)
        return True
    except (IntegrityError, OperationalError) as e:
        s.rollback()
        logger.exception("Failed to add user points for %s: %s", username, e)
        raise


@_with_session
def deduct_user_points_with_source(s, user_db, username: str, cost: float,  # noqa: ARG001
                                   source: str, description=None) -> bool:
    """Deduct points. Returns False if insufficient balance."""
    try:
        current = get_user_points(s, user_db, username)
        if current < cost:
            return False
        s.add(PointTransaction(
            username=username,
            points=-cost,
            source=source,
            description=description,
            expires_at=None,
            is_expired=0,
        ))
        s.flush()
        transaction_id = s.execute(
            select(PointTransaction.id).where(PointTransaction.username == username)
            .order_by(PointTransaction.id.desc()).limit(1)
        ).scalar()
        s.add(PointHistory(
            username=username,
            transaction_id=transaction_id,
            action="deduct",
            points_before=current,
            points_after=current - cost,
        ))
        invalidate_user_cache(username)
        return True
    except (IntegrityError, OperationalError) as e:
        s.rollback()
        logger.exception("Failed to deduct points for %s: %s", username, e)
        raise


def add_user_points(user_db, username: str, points: float):
    return add_user_points_with_source(user_db, username, points, "legacy", "Legacy point addition")


def deduct_user_points(user_db, username: str, cost: float) -> bool:
    return deduct_user_points_with_source(user_db, username, cost, "legacy", "Legacy point deduction")


@_with_session
def expire_user_points(s, user_db, username: str):  # noqa: ARG001
    try:
        s.execute(
            PointTransaction.__table__.update()
            .where(PointTransaction.username == username)
            .where(PointTransaction.is_expired == 0)
            .where(PointTransaction.expires_at.isnot(None))
            .where(PointTransaction.expires_at <= datetime.utcnow())
            .values(is_expired=1)
        )
    except Exception as e:
        logger.exception("Failed to expire points for %s: %s", username, e)


@_with_session
def get_point_history(s, user_db, username: str, limit: int = 50):  # noqa: ARG001
    try:
        rows = s.execute(
            select(
                PointTransaction.points,
                PointTransaction.source,
                PointTransaction.description,
                PointTransaction.created_at,
                PointTransaction.expires_at,
                PointTransaction.is_expired,
                PointHistory.action,
                PointHistory.points_before,
                PointHistory.points_after,
            )
            .outerjoin(PointHistory, PointHistory.transaction_id == PointTransaction.id)
            .where(PointTransaction.username == username)
            .order_by(PointTransaction.created_at.desc())
            .limit(limit)
        ).all()
        return [tuple(r) for r in rows]
    except Exception as e:
        logger.exception("Failed to get point history for %s: %s", username, e)
        return []


@_with_session
def process_daily_login_bonus(s, user_db, username: str):  # noqa: ARG001
    """Add daily-login bonus. Returns points awarded (0 if already done)."""
    today = date.today()
    yesterday = today - timedelta(days=1)

    try:
        # Already got today?
        if s.execute(
            select(UserLogin).where(UserLogin.username == username, UserLogin.login_date == today)
        ).scalar_one_or_none() is not None:
            return 0

        # Streak: did they login yesterday?
        streak = 1
        if s.execute(
            select(UserLogin).where(UserLogin.username == username, UserLogin.login_date == yesterday)
        ).scalar_one_or_none() is not None:
            recent = s.execute(
                select(UserLogin.login_date).where(UserLogin.username == username)
                .order_by(UserLogin.login_date.desc()).limit(2)
            ).all()
            if len(recent) == 2:
                d1, d2 = recent[0][0], recent[1][0]
                if isinstance(d1, str):
                    d1 = datetime.strptime(d1, "%Y-%m-%d").date()
                if isinstance(d2, str):
                    d2 = datetime.strptime(d2, "%Y-%m-%d").date()
                if (d1 - d2).days == 1:
                    streak = 2

        bonus = random.randint(5, 12)
        s.add(UserLogin(username=username, login_date=today, points_awarded=bonus))

        expires_at = calculate_expiration_date("daily_login")
        s.add(PointTransaction(
            username=username,
            points=bonus,
            source="daily_login",
            description=f"Daily login bonus (streak: {streak})",
            expires_at=expires_at,
            is_expired=0,
        ))
        s.flush()
        transaction_id = s.execute(
            select(PointTransaction.id).where(PointTransaction.username == username)
            .order_by(PointTransaction.id.desc()).limit(1)
        ).scalar()

        current = get_user_points(s, user_db, username)
        s.add(PointHistory(
            username=username,
            transaction_id=transaction_id,
            action="add",
            points_before=current - bonus,
            points_after=min(current, 500.0),
        ))
        return bonus
    except (IntegrityError, OperationalError) as e:
        s.rollback()
        logger.exception("Failed to process daily login bonus for %s: %s", username, e)
        return 0


# ============================================================================
# Achievements
# ============================================================================

ACHIEVEMENT_SEED = [
    ("Welcome!", "Create your first account", "fas fa-star", 10, "welcome", "first_login", 1, 0),
    ("First Steps", "Generate your first prompt", "fas fa-baby", 5, "generation", "prompts_generated", 1, 0),
    ("Collector", "Save your first prompt", "fas fa-bookmark", 5, "collection", "prompts_saved", 1, 0),
    ("Community Member", "Share your first prompt", "fas fa-users", 10, "social", "prompts_shared", 1, 0),
    ("Getting Started", "Generate 10 prompts", "fas fa-seedling", 15, "generation", "prompts_generated", 10, 0),
    ("Dedicated", "Generate 50 prompts", "fas fa-fire", 25, "generation", "prompts_generated", 50, 0),
    ("Prompt Master", "Generate 100 prompts", "fas fa-crown", 50, "generation", "prompts_generated", 100, 0),
    ("Legendary Creator", "Generate 500 prompts", "fas fa-gem", 100, "generation", "prompts_generated", 500, 0),
    ("Archivist", "Save 10 prompts", "fas fa-archive", 15, "collection", "prompts_saved", 10, 0),
    ("Librarian", "Save 50 prompts", "fas fa-library", 25, "collection", "prompts_saved", 50, 0),
    ("Master Archivist", "Save 100 prompts", "fas fa-university", 50, "collection", "prompts_saved", 100, 0),
    ("Contributor", "Share 5 prompts", "fas fa-handshake", 20, "social", "prompts_shared", 5, 0),
    ("Community Leader", "Share 25 prompts", "fas fa-crown", 40, "social", "prompts_shared", 25, 0),
    ("Legendary Contributor", "Share 50 prompts", "fas fa-trophy", 75, "social", "prompts_shared", 50, 0),
    ("Explorer", "Try all prompt types", "fas fa-compass", 25, "special", "prompt_types_used", 6, 0),
    ("Profile Complete", "Complete your profile", "fas fa-user-check", 15, "profile", "profile_completed", 1, 0),
    ("Daily Visitor", "Login for 7 consecutive days", "fas fa-calendar-check", 30, "streak", "login_streak", 7, 0),
    ("Weekly Warrior", "Login for 30 consecutive days", "fas fa-shield-alt", 75, "streak", "login_streak", 30, 0),
    ("Monthly Master", "Login for 100 consecutive days", "fas fa-star-shield", 150, "streak", "login_streak", 100, 0),
    ("Feedback Guru", "Give feedback on 5 prompts", "fas fa-comments", 15, "quality", "feedback_given", 5, 0),
    ("Quality Contributor", "Receive 10 positive ratings", "fas fa-thumbs-up", 20, "quality", "positive_ratings", 10, 0),
    ("Critic", "Give detailed feedback on 25 prompts", "fas fa-search", 30, "quality", "detailed_feedback", 25, 0),
    ("Quality Master", "Receive 50 positive ratings", "fas fa-star", 50, "quality", "positive_ratings", 50, 0),
    ("Style Explorer", "Try 5 different prompt styles", "fas fa-palette", 20, "diversity", "styles_tried", 5, 0),
    ("Technique Master", "Use 10 different prompt techniques", "fas fa-tools", 25, "diversity", "techniques_used", 10, 0),
    ("Category Collector", "Create prompts in 8 different categories", "fas fa-folder-open", 30, "diversity", "categories_used", 8, 0),
    ("Format Specialist", "Use 6 different prompt formats", "fas fa-file-alt", 25, "diversity", "formats_used", 6, 0),
    ("Version Controller", "Create 10 different versions of a prompt", "fas fa-code-branch", 20, "advanced", "versions_created", 10, 0),
    ("Template Creator", "Create 5 custom prompt templates", "fas fa-file-code", 25, "advanced", "templates_created", 5, 0),
    ("Batch Processor", "Generate prompts in batch mode", "fas fa-layer-group", 15, "advanced", "batch_processing_used", 1, 0),
    ("Parameter Expert", "Use advanced parameters 25 times", "fas fa-sliders-h", 30, "advanced", "advanced_params_used", 25, 0),
    ("Helpful Member", "Help 5 other users", "fas fa-hands-helping", 25, "community", "users_helped", 5, 0),
    ("Mentor", "Provide guidance to 15 users", "fas fa-chalkboard-teacher", 40, "community", "users_helped", 15, 0),
    ("Community Helper", "Participate in community discussions", "fas fa-users-cog", 20, "community", "community_participation", 1, 0),
    ("Collaborator", "Work on shared projects with others", "fas fa-handshake", 35, "community", "collaborations", 3, 0),
    ("Steady Progress", "Login for 50 days total", "fas fa-route", 30, "consistency", "total_logins", 50, 0),
    ("Reliable User", "Login for 100 days total", "fas fa-shield-check", 50, "consistency", "total_logins", 100, 0),
    ("Dedicated Member", "Maintain a 30-day login streak", "fas fa-calendar-star", 75, "consistency", "login_streak", 30, 0),
    ("Loyal User", "Login for 200 days total", "fas fa-heart", 100, "consistency", "total_logins", 200, 0),
    ("Feature Explorer", "Try all main features", "fas fa-binoculars", 25, "exploration", "features_used", 10, 0),
    ("Settings Expert", "Customize all profile settings", "fas fa-cog", 15, "exploration", "settings_customized", 1, 0),
    ("Tool Master", "Use all available tools", "fas fa-toolbox", 30, "exploration", "tools_used", 8, 0),
    ("Discovery Seeker", "Find and use hidden features", "fas fa-lightbulb", 20, "exploration", "hidden_features_used", 5, 0),
    ("Power User", "Generate 1000 prompts", "fas fa-bolt", 200, "generation", "prompts_generated", 1000, 0),
    ("Library Master", "Save 250 prompts", "fas fa-book-reader", 75, "collection", "prompts_saved", 250, 0),
    ("Community Legend", "Share 100 prompts", "fas fa-crown", 150, "social", "prompts_shared", 100, 0),
    ("Year Round User", "Login for 365 consecutive days", "fas fa-calendar-alt", 200, "streak", "login_streak", 365, 0),
    ("Perfectionist", "Create 50 prompt versions", "fas fa-check-double", 40, "advanced", "versions_created", 50, 0),
    ("Innovation Leader", "Create 20 custom templates", "fas fa-lightbulb", 60, "advanced", "templates_created", 20, 0),
    ("Community Champion", "Help 50 other users", "fas fa-trophy", 100, "community", "users_helped", 50, 0),
    ("Feature Pioneer", "Try 20 different features", "fas fa-flag", 50, "exploration", "features_used", 20, 0),
    ("Early Adopter", "Be among the first 100 users", "fas fa-rocket", 100, "special", "user_rank", 100, 1),
    ("Reverse Engineer", "Use reverse image prompts", "fas fa-magic", 15, "special", "reverse_image_used", 1, 0),
    ("Advanced User", "Use advanced prompts", "fas fa-graduation-cap", 20, "special", "advanced_prompts_used", 1, 0),
    ("API Key Provider", "Add and validate your own Gemini API key", "fas fa-key", 100, "special", "api_key_validated", 1, 0),
]


@_with_session
def initialize_achievements(s, user_db):  # noqa: ARG001
    for row in ACHIEVEMENT_SEED:
        existing = s.execute(
            select(Achievement).where(Achievement.name == row[0])
        ).scalar_one_or_none()
        if existing is None:
            s.add(Achievement(
                name=row[0],
                description=row[1],
                icon=row[2],
                points_reward=row[3],
                category=row[4],
                condition_type=row[5],
                condition_value=row[6],
                hidden=row[7],
            ))


@_with_session
def get_user_achievements(s, user_db, username: str):  # noqa: ARG001
    rows = s.execute(
        select(Achievement, UserAchievement.unlocked_at)
        .join(UserAchievement, UserAchievement.achievement_id == Achievement.id)
        .where(UserAchievement.username == username)
        .order_by(UserAchievement.unlocked_at.desc())
    ).all()
    return [
        (
            ach.id,
            ach.name,
            ach.description,
            ach.icon,
            ach.points_reward,
            ach.category,
            unlocked_at,
        )
        for ach, unlocked_at in rows
    ]


@_with_session
def check_and_award_achievements(s, user_db, username: str, prompt_db: str, community_db: str):  # noqa: ARG001
    """Check for newly earned achievements and award points.

    Returns (newly_unlocked_names: list[str], total_points_earned: float).
    """
    try:
        stats = _get_user_stats_impl(s, username)

        unlocked_ids = set(s.execute(
            select(UserAchievement.achievement_id).where(UserAchievement.username == username)
        ).scalars().all())

        # Visible achievements + hidden ones the user already has
        candidates = s.execute(
            select(Achievement).where(
                (Achievement.hidden == 0)
                | (Achievement.id.in_(unlocked_ids))
            )
        ).scalars().all()

        newly_unlocked = []
        total_points = 0.0
        for ach in candidates:
            if ach.id in unlocked_ids:
                continue
            if check_achievement_condition(stats, ach.condition_type, ach.condition_value or 0):
                s.add(UserAchievement(username=username, achievement_id=ach.id))
                newly_unlocked.append(ach.name)
                total_points += ach.points_reward

        if newly_unlocked:
            expires_at = calculate_expiration_date("achievement")
            s.add(PointTransaction(
                username=username,
                points=total_points,
                source="achievement",
                description=f'Achievement rewards: {", ".join(newly_unlocked)}',
                expires_at=expires_at,
                is_expired=0,
            ))
            s.flush()
            transaction_id = s.execute(
                select(PointTransaction.id).where(PointTransaction.username == username)
                .order_by(PointTransaction.id.desc()).limit(1)
            ).scalar()
            current = get_user_points(s, user_db, username)
            s.add(PointHistory(
                username=username,
                transaction_id=transaction_id,
                action="add",
                points_before=current - total_points,
                points_after=min(current, 500.0),
            ))

        return newly_unlocked, total_points
    except Exception as e:
        s.rollback()
        logger.exception("Failed to check achievements for %s: %s", username, e)
        return [], 0.0


def get_user_stats(username, user_db, prompt_db, community_db):  # noqa: ARG001
    """Compute user's achievement stats. Uses a fresh session (called from
    both Flask request context and standalone code)."""
    with SessionLocal() as s:
        return _get_user_stats_impl(s, username)


def _get_user_stats_impl(s, username: str) -> dict:
    stats = {
        "prompts_generated": 0,
        "prompts_saved": 0,
        "prompts_shared": 0,
        "login_streak": 0,
        "profile_completed": 0,
        "user_rank": 0,
        "reverse_image_used": 0,
        "advanced_prompts_used": 0,
        "api_key_validated": 0,
        "feedback_given": 0,
        "positive_ratings": 0,
        "detailed_feedback": 0,
        "versions_created": 0,
        "templates_created": 0,
        "batch_processing_used": 0,
        "advanced_params_used": 0,
        "users_helped": 0,
        "community_participation": 0,
        "collaborations": 0,
        "total_logins": 0,
        "settings_customized": 0,
        "prompt_types_used": set(),
        "styles_tried": set(),
        "techniques_used": set(),
        "categories_used": set(),
        "formats_used": set(),
        "features_used": set(),
        "tools_used": set(),
        "hidden_features_used": set(),
    }

    stats["prompts_generated"] = s.execute(
        select(func.count()).select_from(PromptVersion).where(PromptVersion.username == username)
    ).scalar() or 0
    stats["prompts_saved"] = s.execute(
        select(func.count()).select_from(Prompt).where(Prompt.username == username)
    ).scalar() or 0
    stats["prompts_shared"] = s.execute(
        select(func.count()).select_from(SharedPrompt).where(SharedPrompt.owner == username)
    ).scalar() or 0
    stats["total_logins"] = s.execute(
        select(func.count()).select_from(UserLogin).where(UserLogin.username == username)
    ).scalar() or 0
    user = s.get(User, username)
    stats["api_key_validated"] = 1 if (user and user.api_key_validated) else 0
    stats["user_rank"] = s.execute(
        select(func.count()).select_from(User).where(User.username < username)
    ).scalar() or 0

    for key in (
        "prompt_types_used", "styles_tried", "techniques_used", "categories_used",
        "formats_used", "features_used", "tools_used", "hidden_features_used",
    ):
        stats[key] = len(stats[key])

    return stats


def check_achievement_condition(stats, condition_type: str, condition_value: int) -> bool:
    if condition_type == "first_login":
        return True
    if condition_type == "user_rank":
        return stats.get("user_rank", 0) < condition_value
    if condition_type in stats:
        try:
            return stats[condition_type] >= condition_value
        except TypeError:
            return False
    return False


# ============================================================================
# Backward-compat helpers used by routes.py that don't directly touch a DB
# ============================================================================

DATABASE_NAME = "database/app.db"
SHARED_PROMPTS_TABLE = "shared_prompts"


__all__ = [
    # Schema
    "create_tables", "create_user_table_if_not_exists",
    "get_db_connection", "execute_sql", "enable_wal_mode",
    "ensure_prompt_versions_schema", "ensure_shared_schema",
    "ensure_feedback_schema", "ensure_users_schema",
    "DATABASE_NAME", "SHARED_PROMPTS_TABLE",
    # Users
    "get_user_email", "get_user_identicon_value", "set_user_identicon_value",
    "update_user_email", "generate_identicon_value", "change_username_everywhere",
    # Sessions
    "create_session_record", "touch_session", "is_session_valid",
    "revoke_session", "list_sessions_for_user", "revoke_other_sessions",
    # API key
    "get_user_api_key", "set_user_api_key", "is_api_key_validated", "set_api_key_validated",
    # Prompts
    "get_next_version_number", "insert_prompt_version", "save_prompt_to_db",
    "get_prompt_sharing_status",
    # Points
    "calculate_expiration_date",
    "get_user_points", "add_user_points", "add_user_points_with_source",
    "deduct_user_points", "deduct_user_points_with_source",
    "expire_user_points", "get_point_history", "process_daily_login_bonus",
    "POINT_EXPIRATION",
    # Achievements
    "initialize_achievements", "check_and_award_achievements",
    "get_user_achievements", "get_user_stats", "check_achievement_condition",
    "ACHIEVEMENT_SEED",
]
