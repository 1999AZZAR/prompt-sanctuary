"""SQLAlchemy 2.0 declarative models for Prompt Sanctuary.

Single unified database (`app.db`) replacing the legacy four-DB layout:

  Legacy                                  New (unified)
  ----------------------------------      --------------------------------
  user.db::users                          users
  user.db::sessions                       sessions
  user.db::user_logins                    user_logins
  user.db::point_transactions             point_transactions
  user.db::point_history                  point_history
  user.db::achievements                   achievements
  user.db::user_achievements              user_achievements
  prompt_data.db::prompt_versions         prompt_versions
  prompt_data.db::prompts_<username>      prompts   (with username column)
  community/shared.db::shared             shared_prompts   (with owner column)
  feedback.db::feedback                   feedback
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    text,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"

    username: Mapped[str] = mapped_column(String(64), primary_key=True)
    password: Mapped[str] = mapped_column(String(255), nullable=False)
    points: Mapped[float] = mapped_column(Float, default=80.0, nullable=False)
    gemini_api_key: Mapped[Optional[str]] = mapped_column(String(255))
    api_key_validated: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    email: Mapped[Optional[str]] = mapped_column(String(255))
    identicon_value: Mapped[Optional[str]] = mapped_column(String(64))

    sessions: Mapped[list["Session"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    logins: Mapped[list["UserLogin"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    point_transactions: Mapped[list["PointTransaction"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    point_history: Mapped[list["PointHistory"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    achievements: Mapped[list["UserAchievement"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    prompts: Mapped[list["Prompt"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    prompt_versions: Mapped[list["PromptVersion"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    shared_prompts: Mapped[list["SharedPrompt"]] = relationship(back_populates="owner_user", cascade="all, delete-orphan")
    feedback_entries: Mapped[list["Feedback"]] = relationship(back_populates="user", cascade="all, delete-orphan")

    __table_args__ = (
        Index("idx_users_email_unique", "email", unique=True, sqlite_where=text("email IS NOT NULL")),
    )


class Session(Base):
    __tablename__ = "sessions"

    token: Mapped[str] = mapped_column(String(64), primary_key=True)
    username: Mapped[str] = mapped_column(String(64), ForeignKey("users.username", ondelete="CASCADE"), nullable=False, index=True)
    user_agent: Mapped[Optional[str]] = mapped_column(String(512))
    ip: Mapped[Optional[str]] = mapped_column(String(45))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    last_active: Mapped[Optional[datetime]] = mapped_column(DateTime)
    revoked: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    user: Mapped["User"] = relationship(back_populates="sessions")


class UserLogin(Base):
    __tablename__ = "user_logins"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(String(64), ForeignKey("users.username", ondelete="CASCADE"), nullable=False, index=True)
    login_date: Mapped[Date] = mapped_column(Date, nullable=False)
    points_awarded: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)

    user: Mapped["User"] = relationship(back_populates="logins")

    __table_args__ = (UniqueConstraint("username", "login_date", name="uq_user_logins_username_date"),)


class PointTransaction(Base):
    __tablename__ = "point_transactions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(String(64), ForeignKey("users.username", ondelete="CASCADE"), nullable=False, index=True)
    points: Mapped[float] = mapped_column(Float, nullable=False)
    source: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    description: Mapped[Optional[str]] = mapped_column(String(512))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime, index=True)
    is_expired: Mapped[int] = mapped_column(Integer, default=0, nullable=False, index=True)

    user: Mapped["User"] = relationship(back_populates="point_transactions")
    history: Mapped[list["PointHistory"]] = relationship(back_populates="transaction", cascade="all, delete-orphan")


class PointHistory(Base):
    __tablename__ = "point_history"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(String(64), ForeignKey("users.username", ondelete="CASCADE"), nullable=False, index=True)
    transaction_id: Mapped[int] = mapped_column(Integer, ForeignKey("point_transactions.id", ondelete="CASCADE"), nullable=False, index=True)
    action: Mapped[str] = mapped_column(String(16), nullable=False)
    points_before: Mapped[float] = mapped_column(Float, nullable=False)
    points_after: Mapped[float] = mapped_column(Float, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    user: Mapped["User"] = relationship(back_populates="point_history")
    transaction: Mapped["PointTransaction"] = relationship(back_populates="history")


class Achievement(Base):
    __tablename__ = "achievements"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(128), unique=True, nullable=False)
    description: Mapped[str] = mapped_column(String(512), nullable=False)
    icon: Mapped[str] = mapped_column(String(64), nullable=False)
    points_reward: Mapped[float] = mapped_column(Float, nullable=False)
    category: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    condition_type: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    condition_value: Mapped[Optional[int]] = mapped_column(Integer)
    hidden: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    unlocks: Mapped[list["UserAchievement"]] = relationship(back_populates="achievement", cascade="all, delete-orphan")


class UserAchievement(Base):
    __tablename__ = "user_achievements"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(String(64), ForeignKey("users.username", ondelete="CASCADE"), nullable=False, index=True)
    achievement_id: Mapped[int] = mapped_column(Integer, ForeignKey("achievements.id", ondelete="CASCADE"), nullable=False, index=True)
    unlocked_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    user: Mapped["User"] = relationship(back_populates="achievements")
    achievement: Mapped["Achievement"] = relationship(back_populates="unlocks")

    __table_args__ = (UniqueConstraint("username", "achievement_id", name="uq_user_achievements_user_ach"),)


class Prompt(Base):
    """Replaces the legacy per-user prompts_<username> tables.

    The legacy layout created one SQLite table per user (random_val PK, title,
    prompt, time). The unified layout stores all prompts in a single table with
    a username column and a surrogate autoincrement id. random_val is the
    legacy stable identifier used by URL paths and JS — preserved.
    """
    __tablename__ = "prompts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(String(64), ForeignKey("users.username", ondelete="CASCADE"), nullable=False, index=True)
    random_val: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    prompt: Mapped[str] = mapped_column(Text, nullable=False)
    time: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    user: Mapped["User"] = relationship(back_populates="prompts")

    __table_args__ = (UniqueConstraint("username", "random_val", name="uq_prompts_username_random"),)


class PromptVersion(Base):
    __tablename__ = "prompt_versions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(String(64), ForeignKey("users.username", ondelete="CASCADE"), nullable=False, index=True)
    prompt_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    version_number: Mapped[int] = mapped_column(Integer, nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    prompt: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    user: Mapped["User"] = relationship(back_populates="prompt_versions")

    __table_args__ = (UniqueConstraint("username", "prompt_id", "version_number", name="uq_prompt_versions_user_pid_v"),)


class SharedPrompt(Base):
    """Replaces the legacy community/shared.db::shared table.

    Legacy columns: id, owner, random_val (UNIQUE), title, prompt, time.
    The random_val UNIQUE constraint is preserved at the table level (not on
    (owner, random_val)) for backward compatibility with the existing
    /library and /share lookups that key on random_val alone.
    """
    __tablename__ = "shared_prompts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    owner: Mapped[str] = mapped_column(String(64), ForeignKey("users.username", ondelete="CASCADE"), nullable=False, index=True)
    random_val: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    prompt: Mapped[str] = mapped_column(Text, nullable=False)
    time: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    owner_user: Mapped["User"] = relationship(back_populates="shared_prompts")


class Feedback(Base):
    __tablename__ = "feedback"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(String(64), ForeignKey("users.username", ondelete="CASCADE"), nullable=False, index=True)
    feedback: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    user: Mapped["User"] = relationship(back_populates="feedback_entries")


__all__ = [
    "Base",
    "User",
    "Session",
    "UserLogin",
    "PointTransaction",
    "PointHistory",
    "Achievement",
    "UserAchievement",
    "Prompt",
    "PromptVersion",
    "SharedPrompt",
    "Feedback",
]
