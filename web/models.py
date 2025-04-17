import os
import secrets
import time
import re
from datetime import datetime
from sqlite3 import connect, OperationalError, Row


def get_db_connection(db_path):
    """Get a connection to the SQLite database with integrity enforced."""
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


def create_tables(user_db, prompt_db, image_log, community_db, feedback_db):
    """Create necessary tables in the databases."""
    tables = {
        user_db: """
            CREATE TABLE IF NOT EXISTS users (
                username TEXT PRIMARY KEY,
                password TEXT NOT NULL
            );
        """,
        image_log: """
            CREATE TABLE IF NOT EXISTS images (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                filename TEXT NOT NULL,
                creation_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """,
        community_db: """
            CREATE TABLE IF NOT EXISTS shared (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                owner TEXT NOT NULL,
                random_val TEXT UNIQUE NOT NULL,
                title TEXT NOT NULL,
                prompt TEXT NOT NULL,
                time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(owner) REFERENCES users(username) ON DELETE CASCADE
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
                CREATE TABLE "{username}" (
                    random_val TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    prompt TEXT NOT NULL,
                    time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )'''
            execute_sql(conn, sql)


def save_prompt_to_db(username, title, prompt, prompt_db):
    """Save a prompt to the user's table in the database."""
    # Sanitize username
    if not re.match(r'^[A-Za-z0-9_]+$', username):
        raise ValueError(f'Invalid username for table: {username}')
    random_value = secrets.token_urlsafe(8)
    with get_db_connection(prompt_db) as conn:
        sql = f'INSERT INTO "{username}" (random_val, title, prompt) VALUES (?, ?, ?)'
        execute_sql(conn, sql, (random_value, title, prompt))
    return random_value


def delete_old_images(image_log):
    """Delete old images from the database and filesystem."""
    with get_db_connection(image_log) as conn:
        cursor = conn.cursor()
        image_dir = "./static/image"
        if os.path.exists(image_dir):
            now = time.time()
            for row in cursor.execute("SELECT filename, creation_time FROM images"):
                filename, creation_time = row
                creation_time = time.mktime(
                    time.strptime(creation_time, "%Y-%m-%d %H:%M:%S")
                )
                file_path = os.path.join(image_dir, filename)
                if os.path.isfile(file_path) and now - creation_time > 1800:
                    os.remove(file_path)
                    execute_sql(
                        conn, "DELETE FROM images WHERE filename=?", (filename,)
                    )
