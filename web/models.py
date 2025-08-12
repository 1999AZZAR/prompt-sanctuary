import os
import secrets
import time
import re
from datetime import datetime
from sqlite3 import connect, OperationalError, Row

DATABASE_NAME = 'database/prompts.db'
SHARED_PROMPTS_TABLE = 'shared_prompts'

def get_db_connection(db_path):
    """Get a connection to the SQLite database with integrity enforced.
    Ensures the directory for the database exists before connecting.
    """
    os.makedirs(os.path.dirname(db_path) or '.', exist_ok=True)
    conn = connect(db_path)
    conn.execute("PRAGMA foreign_keys = ON")
    conn.row_factory = Row
    return conn


def execute_sql(conn, sql, params=None):
    """Execute SQL query and commit changes."""
    cursor = conn.cursor()
    if params:
        cursor.execute(sql, params)
    else:
        cursor.execute(sql)
    conn.commit()


def create_tables(user_db, prompt_db, community_db, feedback_db):
    """Create necessary tables in the databases."""
    tables = {
        user_db: """
            CREATE TABLE IF NOT EXISTS users (
                username TEXT PRIMARY KEY,
                password TEXT NOT NULL
            );
        """,
        prompt_db: """
            CREATE TABLE IF NOT EXISTS prompt_versions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL,
                prompt_id TEXT NOT NULL,
                version_number INTEGER NOT NULL,
                title TEXT NOT NULL,
                prompt TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(username, prompt_id, version_number)
            );
        """,
        community_db: """
            CREATE TABLE IF NOT EXISTS shared (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                owner TEXT NOT NULL,
                random_val TEXT UNIQUE NOT NULL,
                title TEXT NOT NULL,
                prompt TEXT NOT NULL,
                time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """,
        feedback_db: """
            CREATE TABLE IF NOT EXISTS feedback (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL,
                feedback TEXT NOT NULL
            );
        """,
    }

    for db_path, sql in tables.items():
        with get_db_connection(db_path) as conn:
            execute_sql(conn, sql)

    # Ensure prompt_versions schema is compatible with single-DB FKs (SQLite cannot FK across DB files)
    ensure_prompt_versions_schema(prompt_db)
    ensure_shared_schema(community_db)
    ensure_users_schema(user_db)
    ensure_feedback_schema(feedback_db)


def ensure_prompt_versions_schema(prompt_db):
    """Ensure prompt_versions table does not reference users table across DBs.
    If a foreign key exists, migrate to a schema without FK.
    """
    with get_db_connection(prompt_db) as conn:
        cursor = conn.cursor()
        # Check existence
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='prompt_versions'")
        if not cursor.fetchone():
            return  # Table not present yet; create_tables will create it

        # Inspect foreign keys
        cursor.execute("PRAGMA foreign_key_list(prompt_versions)")
        fk_rows = cursor.fetchall()
        if not fk_rows:
            return  # No FKs to migrate

        # If any FK exists (especially to users), migrate table without FK
        # Disable FK enforcement for migration
        cursor.execute("PRAGMA foreign_keys=OFF")
        conn.commit()
        try:
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS prompt_versions_new (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT NOT NULL,
                    prompt_id TEXT NOT NULL,
                    version_number INTEGER NOT NULL,
                    title TEXT NOT NULL,
                    prompt TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(username, prompt_id, version_number)
                );
                """
            )
            cursor.execute(
                """
                INSERT INTO prompt_versions_new (id, username, prompt_id, version_number, title, prompt, created_at)
                SELECT id, username, prompt_id, version_number, title, prompt, created_at
                FROM prompt_versions
                """
            )
            cursor.execute("DROP TABLE prompt_versions")
            cursor.execute("ALTER TABLE prompt_versions_new RENAME TO prompt_versions")
            conn.commit()
        finally:
            cursor.execute("PRAGMA foreign_keys=ON")
            conn.commit()


def ensure_shared_schema(community_db):
    """Ensure shared table does not reference users across DB files."""
    with get_db_connection(community_db) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='shared'")
        if not cursor.fetchone():
            return
        cursor.execute("PRAGMA foreign_key_list(shared)")
        fk_rows = cursor.fetchall()
        if not fk_rows:
            return
        cursor.execute("PRAGMA foreign_keys=OFF")
        conn.commit()
        try:
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS shared_new (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    owner TEXT NOT NULL,
                    random_val TEXT UNIQUE NOT NULL,
                    title TEXT NOT NULL,
                    prompt TEXT NOT NULL,
                    time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
                """
            )
            cursor.execute(
                """
                INSERT INTO shared_new (id, owner, random_val, title, prompt, time)
                SELECT id, owner, random_val, title, prompt, time FROM shared
                """
            )
            cursor.execute("DROP TABLE shared")
            cursor.execute("ALTER TABLE shared_new RENAME TO shared")
            conn.commit()
        finally:
            cursor.execute("PRAGMA foreign_keys=ON")
            conn.commit()

def ensure_feedback_schema(feedback_db):
    """Ensure feedback table does not have FK referencing users across DBs."""
    with get_db_connection(feedback_db) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='feedback'")
        if not cursor.fetchone():
            return
        cursor.execute("PRAGMA foreign_key_list(feedback)")
        fk_rows = cursor.fetchall()
        if not fk_rows:
            return
        cursor.execute("PRAGMA foreign_keys=OFF")
        conn.commit()
        try:
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS feedback_new (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT NOT NULL,
                    feedback TEXT NOT NULL
                );
                """
            )
            cursor.execute(
                """
                INSERT INTO feedback_new (id, username, feedback)
                SELECT id, username, feedback FROM feedback
                """
            )
            cursor.execute("DROP TABLE feedback")
            cursor.execute("ALTER TABLE feedback_new RENAME TO feedback")
            conn.commit()
        finally:
            cursor.execute("PRAGMA foreign_keys=ON")
            conn.commit()


def ensure_users_schema(user_db):
    """Ensure users table includes optional unique email and sessions table exists."""
    with get_db_connection(user_db) as conn:
        cursor = conn.cursor()
        # Add email column if missing
        cursor.execute("PRAGMA table_info(users)")
        cols = {row[1] for row in cursor.fetchall()}
        if "email" not in cols:
            cursor.execute("ALTER TABLE users ADD COLUMN email TEXT")
            conn.commit()
        # Create unique index on email if not exists (allows multiple NULLs in SQLite)
        cursor.execute(
            """
            CREATE UNIQUE INDEX IF NOT EXISTS idx_users_email_unique
            ON users(email)
            WHERE email IS NOT NULL
            """
        )
        conn.commit()

        # Sessions table
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS sessions (
                token TEXT PRIMARY KEY,
                username TEXT NOT NULL,
                user_agent TEXT,
                ip TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_active TIMESTAMP,
                revoked INTEGER DEFAULT 0
            );
            """
        )
        conn.commit()


def create_session_record(user_db, username: str, token: str, user_agent: str | None, ip: str | None):
    """Persist a new login session for the user."""
    with get_db_connection(user_db) as conn:
        execute_sql(
            conn,
            """
            INSERT INTO sessions (token, username, user_agent, ip, last_active)
            VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
            """,
            (token, username, user_agent, ip),
        )


def touch_session(user_db, token: str):
    """Update last_active timestamp for a session token."""
    with get_db_connection(user_db) as conn:
        execute_sql(
            conn,
            "UPDATE sessions SET last_active = CURRENT_TIMESTAMP WHERE token = ?",
            (token,),
        )


def is_session_valid(user_db, token: str, username: str) -> bool:
    """Return True if token exists, not revoked, and belongs to username."""
    with get_db_connection(user_db) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT 1 FROM sessions WHERE token = ? AND username = ? AND revoked = 0",
            (token, username),
        )
        return cursor.fetchone() is not None


def revoke_session(user_db, token: str, username: str) -> bool:
    """Revoke a session if it belongs to username. Returns True if updated."""
    with get_db_connection(user_db) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE sessions SET revoked = 1 WHERE token = ? AND username = ? AND revoked = 0",
            (token, username),
        )
        conn.commit()
        return cursor.rowcount > 0


def list_sessions_for_user(user_db, username: str):
    """List all non-deleted sessions for a user ordered by last_active desc."""
    with get_db_connection(user_db) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT token, user_agent, ip, created_at, last_active, revoked
            FROM sessions
            WHERE username = ?
            ORDER BY COALESCE(last_active, created_at) DESC
            """,
            (username,),
        )
        rows = cursor.fetchall()
        return [
            {
                "token": row[0],
                "user_agent": row[1],
                "ip": row[2],
                "created_at": row[3],
                "last_active": row[4],
                "revoked": bool(row[5]),
            }
            for row in rows
        ]


def revoke_other_sessions(user_db, username: str, except_token: str | None = None) -> int:
    """Revoke all sessions for user except optionally a specific token. Returns count."""
    with get_db_connection(user_db) as conn:
        if except_token:
            params = (username, except_token)
            sql = "UPDATE sessions SET revoked = 1 WHERE username = ? AND token != ? AND revoked = 0"
        else:
            params = (username,)
            sql = "UPDATE sessions SET revoked = 1 WHERE username = ? AND revoked = 0"
        cursor = conn.cursor()
        cursor.execute(sql, params)
        conn.commit()
        return cursor.rowcount


def update_user_email(user_db, username: str, email: str | None):
    """Update user's email. None clears the email. Raises on unique conflict."""
    with get_db_connection(user_db) as conn:
        execute_sql(
            conn,
            "UPDATE users SET email = ? WHERE username = ?",
            (email, username),
        )


def get_user_email(user_db, username: str) -> str | None:
    with get_db_connection(user_db) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT email FROM users WHERE username = ?", (username,))
        row = cursor.fetchone()
        return row[0] if row else None


def change_username_everywhere(old_username: str, new_username: str, user_db: str, prompt_db: str, community_db: str, feedback_db: str):
    """Rename a user's username across all DBs and rename their personal prompt table.
    Raises ValueError on invalid or conflicting names.
    """
    # Validate names for safe table naming
    if not re.match(r'^[A-Za-z0-9_]+$', new_username):
        raise ValueError("Invalid username format. Only letters, numbers, and underscores are allowed.")

    # Ensure target username not taken
    with get_db_connection(user_db) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT 1 FROM users WHERE username = ?", (new_username,))
        if cursor.fetchone():
            raise ValueError("Username already exists. Please choose another.")

    # Perform updates
    # 1) users table
    with get_db_connection(user_db) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE users SET username = ? WHERE username = ?",
            (new_username, old_username),
        )
        conn.commit()

    # 2) prompt versions table and rename personal table
    with get_db_connection(prompt_db) as conn:
        cursor = conn.cursor()
        # prompt_versions
        cursor.execute(
            "UPDATE prompt_versions SET username = ? WHERE username = ?",
            (new_username, old_username),
        )
        # rename personal table if exists
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
            (old_username,),
        )
        if cursor.fetchone():
            # Use double quotes to allow mixed case/underscore names safely
            cursor.execute(f"ALTER TABLE \"{old_username}\" RENAME TO \"{new_username}\"")
        conn.commit()

    # 3) community shared owner
    with get_db_connection(community_db) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE shared SET owner = ? WHERE owner = ?",
            (new_username, old_username),
        )
        conn.commit()

    # 4) feedback entries
    with get_db_connection(feedback_db) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE feedback SET username = ? WHERE username = ?",
            (new_username, old_username),
        )
        conn.commit()

    # 5) sessions records
    with get_db_connection(user_db) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE sessions SET username = ? WHERE username = ?",
            (new_username, old_username),
        )
        conn.commit()


def get_next_version_number(username, prompt_id, prompt_db):
    """Return the next version number for a user's prompt."""
    with get_db_connection(prompt_db) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT COALESCE(MAX(version_number), 0) FROM prompt_versions WHERE username = ? AND prompt_id = ?",
            (username, prompt_id),
        )
        current = cursor.fetchone()[0] or 0
        return current + 1


def insert_prompt_version(username, prompt_id, version_number, title, prompt_text, prompt_db):
    """Insert a new version row for the user's prompt."""
    with get_db_connection(prompt_db) as conn:
        execute_sql(
            conn,
            """
            INSERT INTO prompt_versions (username, prompt_id, version_number, title, prompt)
            VALUES (?, ?, ?, ?, ?)
            """,
            (username, prompt_id, version_number, title, prompt_text),
        )


def create_user_table_if_not_exists(username, prompt_db):
    """Create a user-specific table for saved prompts if it doesn't exist."""
    # Sanitize username for safe table naming
    if not re.match(r'^[A-Za-z0-9_]+$', username):
        raise ValueError(f'Invalid username for table: {username}')
    with get_db_connection(prompt_db) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name=?", (username,)
        )
        table_exists = cursor.fetchone()

        if not table_exists:
            sql = f'''
                CREATE TABLE IF NOT EXISTS "{username}" (
                    random_val TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    prompt TEXT NOT NULL,
                    time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )'''
            execute_sql(conn, sql)


def save_prompt_to_db(username, random_val, title, prompt_text, prompt_db):
    """Save a prompt to the user's table in the database."""
    # Sanitize username
    if not re.match(r'^[A-Za-z0-9_]+$', username):
        raise ValueError(f'Invalid username for table: {username}')
    with get_db_connection(prompt_db) as conn:
        sql = f'INSERT INTO "{username}" (random_val, title, prompt) VALUES (?, ?, ?)'
        execute_sql(conn, sql, (random_val, title, prompt_text))
    return random_val
