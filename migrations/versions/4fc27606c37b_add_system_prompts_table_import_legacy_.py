"""add system_prompts table + import legacy community/query.db

Revision ID: 4fc27606c37b
Revises: 5fa1bf417796
Create Date: 2026-06-07 03:19:59.621566

"""
from pathlib import Path
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '4fc27606c37b'
down_revision: Union[str, Sequence[str], None] = '5fa1bf417796'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _coerce_dt(value) -> "datetime | None":
    """Parse the legacy `time` column (REAL seconds-since-epoch) into a
    datetime. The seed data has '0000-00-00 00:00:00' as a sentinel that
    SQLite does not interpret as a real date - return None in that case
    so the new DateTime column stays null instead of erroring on insert.
    """
    from datetime import datetime
    if value is None or value == "":
        return None
    if isinstance(value, datetime):
        return value if value.year > 1 else None
    if isinstance(value, (int, float)):
        try:
            return datetime.utcfromtimestamp(float(value))
        except (OSError, OverflowError, ValueError):
            return None
    if isinstance(value, str):
        s = value.strip()
        if not s or s.startswith("0000-"):
            return None
        for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%dT%H:%M:%S.%f"):
            try:
                return datetime.strptime(s, fmt)
            except ValueError:
                continue
        return None
    return None


def _import_legacy_system_prompts(conn) -> int:
    """Copy rows from the legacy community/query.db::community table OR the
    bundled seed_data/system_prompts.json into the new system_prompts
    table. Returns the number of rows imported.

    Idempotent: rows that would collide on random_val (the only UNIQUE
    constraint) are skipped, so re-running this migration is safe.

    Order:
      1. Try the legacy SQLite DB (preserves any user-edited data).
      2. Fall back to the bundled JSON seed (ships with the image and
         works in fresh containers where query.db is empty).
    """
    project_root = Path(__file__).resolve().parent.parent.parent
    legacy_db = project_root / "web" / "database" / "community" / "query.db"
    seed_json = project_root / "migrations" / "seed_data" / "system_prompts.json"

    # Fetch already-imported random_vals to skip duplicates (idempotency)
    existing = {
        rv for (rv,) in conn.execute(
            sa.text("SELECT random_val FROM system_prompts")
        ).fetchall()
    }

    def _insert(row: dict) -> bool:
        random_val = (row.get("random_val") or "").strip()
        if not random_val or random_val in existing:
            return False
        title = (row.get("title") or "").strip() or "Untitled"
        prompt = row.get("prompt") or ""
        if not prompt.strip():
            return False
        tag = (row.get("tag") or "").strip() or None
        time = _coerce_dt(row.get("time"))
        conn.execute(
            sa.text(
                "INSERT INTO system_prompts (random_val, title, prompt, tag, time) "
                "VALUES (:random_val, :title, :prompt, :tag, :time)"
            ),
            {
                "random_val": random_val,
                "title": title,
                "prompt": prompt,
                "tag": tag,
                "time": time,
            },
        )
        existing.add(random_val)
        return True

    # 1) Try the legacy DB
    legacy_rows = []
    if legacy_db.exists():
        import sqlite3
        try:
            legacy_conn = sqlite3.connect(str(legacy_db))
            legacy_conn.row_factory = sqlite3.Row
            cur = legacy_conn.execute(
                'SELECT random_val, username AS owner, tittle AS title, prompt, tag, time FROM community'
            )
            legacy_rows = [dict(r) for r in cur.fetchall()]
            legacy_conn.close()
        except sqlite3.OperationalError:
            legacy_rows = []

    if legacy_rows:
        return sum(1 for r in legacy_rows if _insert(r))

    # 2) Fall back to bundled seed JSON
    if seed_json.exists():
        import json
        with seed_json.open(encoding="utf-8") as f:
            seed_rows = json.load(f)
        return sum(1 for r in seed_rows if _insert(r))

    return 0


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        'system_prompts',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('random_val', sa.String(length=64), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('prompt', sa.Text(), nullable=False),
        sa.Column('tag', sa.String(length=255), nullable=True),
        sa.Column('time', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('random_val'),
    )

    # Import from legacy community/query.db::community, or fall back to
    # the bundled seed_data/system_prompts.json. Idempotent.
    conn = op.get_bind()
    inserted = _import_legacy_system_prompts(conn)
    if inserted:
        print(f"  imported {inserted} system prompts")


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table('system_prompts')
