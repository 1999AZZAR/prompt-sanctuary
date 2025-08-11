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
                feedback TEXT NOT NULL,
                FOREIGN KEY(username) REFERENCES users(username) ON DELETE CASCADE
            );
        """,
    }

    for db_path, sql in tables.items():
        with get_db_connection(db_path) as conn:
            execute_sql(conn, sql)

    # Ensure prompt_versions schema is compatible with single-DB FKs (SQLite cannot FK across DB files)
    ensure_prompt_versions_schema(prompt_db)
    ensure_shared_schema(community_db)


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
