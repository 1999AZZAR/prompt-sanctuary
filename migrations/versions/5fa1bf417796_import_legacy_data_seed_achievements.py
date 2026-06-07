"""import legacy data + seed achievements

Revision ID: 5fa1bf417796
Revises: 4f958357504d
Create Date: 2026-06-06 21:01:30.488970
"""

from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import table, column, Integer, String, Float
from sqlalchemy.orm import Session

# revision identifiers, used by Alembic.
revision: str = "5fa1bf417796"
down_revision: Union[str, Sequence[str], None] = "4f958357504d"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


ACHIEVEMENT_SEED = [
    # (name, description, icon, points_reward, category, condition_type, condition_value, hidden)
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


def upgrade() -> None:
    """Import legacy data and seed default achievements."""
    bind = op.get_bind()

    # 1) Seed achievements (insert OR ignore on unique name)
    ach_table = table(
        "achievements",
        column("name", String),
        column("description", String),
        column("icon", String),
        column("points_reward", Float),
        column("category", String),
        column("condition_type", String),
        column("condition_value", Integer),
        column("hidden", Integer),
    )
    dialect = bind.dialect.name
    for row in ACHIEVEMENT_SEED:
        if dialect == "postgresql":
            # Postgres: ON CONFLICT DO NOTHING on the unique name column.
            from sqlalchemy.dialects.postgresql import insert as pg_insert
            op.execute(
                pg_insert(ach_table).values(
                    name=row[0],
                    description=row[1],
                    icon=row[2],
                    points_reward=row[3],
                    category=row[4],
                    condition_type=row[5],
                    condition_value=row[6],
                    hidden=row[7],
                ).on_conflict_do_nothing(index_elements=["name"])
            )
        else:
            op.execute(
                ach_table.insert().prefix_with("OR IGNORE").values(
                    name=row[0],
                    description=row[1],
                    icon=row[2],
                    points_reward=row[3],
                    category=row[4],
                    condition_type=row[5],
                    condition_value=row[6],
                    hidden=row[7],
                )
            )

    # 2) Import legacy data
    from migrations.legacy_import import import_legacy_data  # noqa: PLC0415

    with Session(bind) as session:
        counts = import_legacy_data(session)
        session.commit()

    print("Legacy data import counts:", counts)


def downgrade() -> None:
    """No-op downgrade: data is preserved (we don't drop it on downgrade)."""
    pass
