import os
import secrets
import time
import re
import logging
import random
from datetime import datetime, timedelta
from sqlite3 import connect, OperationalError, Row

DATABASE_NAME = 'database/prompts.db'
SHARED_PROMPTS_TABLE = 'shared_prompts'

# Initialize logging
logger = logging.getLogger(__name__)

# Point expiration periods (in days)
POINT_EXPIRATION = {
    'daily_login': (17, 30),  # Random between 17-30 days
    'achievement': 45,         # 45 days
    'api_key_add': 80,         # 80 days
    'api_key_usage': 95,       # 95 days
    'prompt_share': 30,        # 30 days
    'original': None          # Original 80 points never expire
}

def get_db_connection(db_path):
    """Get a connection to the SQLite database with integrity enforced.
    Ensures the directory for the database exists before connecting.
    Enables WAL mode for better concurrent access.
    """
    os.makedirs(os.path.dirname(db_path) or '.', exist_ok=True)
    conn = connect(db_path)
    # Enable WAL mode for better concurrent access
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA synchronous=NORMAL")
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


def enable_wal_mode(db_path):
    """Enable WAL mode on an existing SQLite database."""
    try:
        conn = connect(db_path)
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA synchronous=NORMAL")
        conn.execute("PRAGMA foreign_keys = ON")
        conn.commit()
        conn.close()
        logger.info(f"Enabled WAL mode for database: {db_path}")
    except Exception as e:
        logger.exception(f"Failed to enable WAL mode for database: {db_path}")


def create_tables(user_db, prompt_db, community_db, feedback_db):
    """Create necessary tables in the databases."""
    # Enable WAL mode on all databases
    for db_path in [user_db, prompt_db, community_db, feedback_db]:
        enable_wal_mode(db_path)

    tables = {
        user_db: [
            """CREATE TABLE IF NOT EXISTS users (
                username TEXT PRIMARY KEY,
                password TEXT NOT NULL,
                points REAL DEFAULT 80.0,
                gemini_api_key TEXT,
                api_key_validated INTEGER DEFAULT 0
            );""",
            """CREATE TABLE IF NOT EXISTS achievements (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                description TEXT NOT NULL,
                icon TEXT NOT NULL,
                points_reward REAL NOT NULL,
                category TEXT NOT NULL,
                condition_type TEXT NOT NULL,
                condition_value INTEGER,
                hidden INTEGER DEFAULT 0
            );""",
            """CREATE TABLE IF NOT EXISTS user_achievements (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL,
                achievement_id INTEGER NOT NULL,
                unlocked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (achievement_id) REFERENCES achievements(id),
                UNIQUE(username, achievement_id)
            );""",
            """CREATE TABLE IF NOT EXISTS user_logins (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL,
                login_date DATE NOT NULL,
                points_awarded REAL DEFAULT 0,
                UNIQUE(username, login_date)
            );""",
            """CREATE TABLE IF NOT EXISTS point_transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL,
                points REAL NOT NULL,
                source TEXT NOT NULL,
                description TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                expires_at TIMESTAMP,
                is_expired INTEGER DEFAULT 0,
                FOREIGN KEY (username) REFERENCES users(username)
            );""",
            """CREATE TABLE IF NOT EXISTS point_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL,
                transaction_id INTEGER NOT NULL,
                action TEXT NOT NULL,
                points_before REAL NOT NULL,
                points_after REAL NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (username) REFERENCES users(username),
                FOREIGN KEY (transaction_id) REFERENCES point_transactions(id)
            );""",
        ],
        prompt_db: [
            """CREATE TABLE IF NOT EXISTS prompt_versions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL,
                prompt_id TEXT NOT NULL,
                version_number INTEGER NOT NULL,
                title TEXT NOT NULL,
                prompt TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(username, prompt_id, version_number)
            );""",
        ],
        community_db: [
            """CREATE TABLE IF NOT EXISTS shared (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                owner TEXT NOT NULL,
                random_val TEXT UNIQUE NOT NULL,
                title TEXT NOT NULL,
                prompt TEXT NOT NULL,
                time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );""",
        ],
        feedback_db: [
            """CREATE TABLE IF NOT EXISTS feedback (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL,
                feedback TEXT NOT NULL
            );""",
        ],
    }

    for db_path, sql_statements in tables.items():
        with get_db_connection(db_path) as conn:
            for sql in sql_statements:
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
    """Ensure users table includes optional unique email, identicon_value and sessions table exists."""
    with get_db_connection(user_db) as conn:
        cursor = conn.cursor()
        # Add email column if missing
        cursor.execute("PRAGMA table_info(users)")
        cols = {row[1] for row in cursor.fetchall()}
        if "email" not in cols:
            cursor.execute("ALTER TABLE users ADD COLUMN email TEXT")
            conn.commit()
        if "identicon_value" not in cols:
            cursor.execute("ALTER TABLE users ADD COLUMN identicon_value TEXT")
            conn.commit()
        if "points" not in cols:
            cursor.execute("ALTER TABLE users ADD COLUMN points REAL DEFAULT 80.0")
            conn.commit()
        if "gemini_api_key" not in cols:
            cursor.execute("ALTER TABLE users ADD COLUMN gemini_api_key TEXT")
            conn.commit()
        if "api_key_validated" not in cols:
            cursor.execute("ALTER TABLE users ADD COLUMN api_key_validated INTEGER DEFAULT 0")
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


def get_user_identicon_value(user_db, username: str) -> str | None:
    """Get the identicon value for a user."""
    with get_db_connection(user_db) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT identicon_value FROM users WHERE username = ?", (username,))
        row = cursor.fetchone()
        return row[0] if row else None


def set_user_identicon_value(user_db, username: str, identicon_value: str):
    """Set the identicon value for a user."""
    with get_db_connection(user_db) as conn:
        execute_sql(
            conn,
            "UPDATE users SET identicon_value = ? WHERE username = ?",
            (identicon_value, username),
        )


def generate_identicon_value(username: str) -> str:
    """Generate a consistent identicon value based on username."""
    import hashlib
    # Use SHA256 hash of username to generate a consistent identicon value
    hash_value = hashlib.sha256(username.encode('utf-8')).hexdigest()
    # Return first 16 characters of hash for identicon generation
    return hash_value[:16]


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


def get_user_points(user_db, username: str) -> float:
    """Get the current effective points for a user (excluding expired points)."""
    max_retries = 3
    for attempt in range(max_retries):
        try:
            with get_db_connection(user_db) as conn:
                cursor = conn.cursor()
                
                # Get current effective points from transactions
                cursor.execute("""
                    SELECT COALESCE(SUM(points), 0) 
                    FROM point_transactions 
                    WHERE username = ? AND is_expired = 0 AND (expires_at IS NULL OR expires_at > datetime('now'))
                """, (username,))
                result = cursor.fetchone()
                
                if result:
                    return result[0]
                else:
                    # If no transactions exist, return default 80 points
                    return 80.0
                    
        except Exception as e:
            logger.warning(f"Attempt {attempt + 1}/{max_retries} failed to get user points: {e}")
            if attempt < max_retries - 1:
                time.sleep(0.1 * (attempt + 1))
                continue
            else:
                logger.exception("Failed to get user points after all retries")
                return 80.0


def calculate_expiration_date(source: str) -> datetime:
    """Calculate expiration date for a given point source."""
    if source == 'original':
        return None  # Original points never expire
    
    expiration_config = POINT_EXPIRATION.get(source)
    if not expiration_config:
        return None
    
    if isinstance(expiration_config, tuple):
        # Random range (e.g., daily_login: (17, 30))
        min_days, max_days = expiration_config
        days = random.randint(min_days, max_days)
    else:
        # Fixed days
        days = expiration_config
    
    return datetime.now() + timedelta(days=days)


def add_user_points_with_source(user_db, username: str, points: float, source: str, description: str = None):
    """Add points to a user with source tracking and expiration."""
    max_retries = 5
    for attempt in range(max_retries):
        try:
            with get_db_connection(user_db) as conn:
                conn.execute("BEGIN IMMEDIATE")
                cursor = conn.cursor()
                
                # Check if user has initial points transaction
                cursor.execute("SELECT COUNT(*) FROM point_transactions WHERE username = ? AND source = 'original'", (username,))
                has_initial = cursor.fetchone()[0] > 0
                
                # Add initial 80 points if user doesn't have them
                if not has_initial:
                    cursor.execute("""
                        INSERT INTO point_transactions (username, points, source, description, expires_at, is_expired)
                        VALUES (?, ?, ?, ?, ?, ?)
                    """, (username, 80.0, 'original', 'Initial points', None, 0))
                
                # Calculate expiration date
                expires_at = calculate_expiration_date(source)
                
                # Add new points transaction
                cursor.execute("""
                    INSERT INTO point_transactions (username, points, source, description, expires_at, is_expired)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (username, points, source, description, expires_at, 0))
                
                # Get transaction ID for history
                transaction_id = cursor.lastrowid
                
                # Get points before and after
                points_before = get_user_points(user_db, username) - points
                points_after = min(points_before + points, 500.0)  # Cap at 500
                
                # Record in history
                cursor.execute("""
                    INSERT INTO point_history (username, transaction_id, action, points_before, points_after)
                    VALUES (?, ?, ?, ?, ?)
                """, (username, transaction_id, 'add', points_before, points_after))
                
                conn.commit()
                return True
                
        except Exception as e:
            logger.warning(f"Attempt {attempt + 1}/{max_retries} failed to add user points: {e}")
            if attempt < max_retries - 1:
                delay = 0.1 * (2 ** attempt) + (0.05 * attempt)
                time.sleep(delay)
                continue
            else:
                logger.exception("Failed to add user points after all retries")
                raise e


def deduct_user_points_with_source(user_db, username: str, cost: float, source: str, description: str = None) -> bool:
    """Deduct points from a user with source tracking."""
    max_retries = 5
    for attempt in range(max_retries):
        try:
            with get_db_connection(user_db) as conn:
                conn.execute("BEGIN IMMEDIATE")
                cursor = conn.cursor()
                
                current_points = get_user_points(user_db, username)
                if current_points < cost:
                    return False
                
                # Add deduction transaction
                cursor.execute("""
                    INSERT INTO point_transactions (username, points, source, description, expires_at, is_expired)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (username, -cost, source, description, None, 0))
                
                # Get transaction ID for history
                transaction_id = cursor.lastrowid
                
                # Record in history
                points_after = current_points - cost
                cursor.execute("""
                    INSERT INTO point_history (username, transaction_id, action, points_before, points_after)
                    VALUES (?, ?, ?, ?, ?)
                """, (username, transaction_id, 'deduct', current_points, points_after))
                
                conn.commit()
                return True
                
        except Exception as e:
            logger.warning(f"Attempt {attempt + 1}/{max_retries} failed to deduct user points: {e}")
            if attempt < max_retries - 1:
                delay = 0.1 * (2 ** attempt) + (0.05 * attempt)
                time.sleep(delay)
                continue
            else:
                logger.exception("Failed to deduct user points after all retries")
                raise e


def expire_user_points(user_db, username: str):
    """Mark expired points as expired for a user."""
    try:
        with get_db_connection(user_db) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE point_transactions 
                SET is_expired = 1 
                WHERE username = ? AND is_expired = 0 AND expires_at IS NOT NULL AND expires_at <= datetime('now')
            """, (username,))
            conn.commit()
    except Exception as e:
        logger.exception(f"Failed to expire points for user {username}: {e}")


def get_point_history(user_db, username: str, limit: int = 50) -> list:
    """Get point transaction history for a user."""
    try:
        with get_db_connection(user_db) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT pt.points, pt.source, pt.description, pt.created_at, pt.expires_at, pt.is_expired,
                       ph.action, ph.points_before, ph.points_after
                FROM point_transactions pt
                LEFT JOIN point_history ph ON pt.id = ph.transaction_id
                WHERE pt.username = ?
                ORDER BY pt.created_at DESC
                LIMIT ?
            """, (username, limit))
            return cursor.fetchall()
    except Exception as e:
        logger.exception(f"Failed to get point history for user {username}: {e}")
        return []


# Legacy functions for backward compatibility
def add_user_points(user_db, username: str, points: float):
    """Legacy function - adds points with 'legacy' source."""
    return add_user_points_with_source(user_db, username, points, 'legacy', 'Legacy point addition')


def deduct_user_points(user_db, username: str, cost: float) -> bool:
    """Legacy function - deducts points with 'legacy' source."""
    return deduct_user_points_with_source(user_db, username, cost, 'legacy', 'Legacy point deduction')


def get_prompt_sharing_status(username: str, prompt_id: str, title: str, prompt_content: str, prompt_db: str, community_db: str):
    """Check if a prompt is shared and if it needs updating.

    Returns:
        dict with keys:
        - is_shared: bool
        - needs_update: bool (True if shared but content differs)
        - shared_title: str (title in shared version, if different)
        - shared_content: str (content in shared version, if different)
    """
    with get_db_connection(community_db) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT title, prompt FROM shared WHERE owner = ? AND random_val = ?",
            (username, prompt_id)
        )
        shared_row = cursor.fetchone()

    if not shared_row:
        # Prompt is not shared
        return {
            'is_shared': False,
            'needs_update': False,
            'shared_title': None,
            'shared_content': None
        }

    shared_title, shared_content = shared_row

    # Check if content differs
    title_changed = shared_title != title
    content_changed = shared_content != prompt_content
    needs_update = title_changed or content_changed

    return {
        'is_shared': True,
        'needs_update': needs_update,
        'shared_title': shared_title,
        'shared_content': shared_content
    }


def initialize_achievements(user_db):
    """Initialize the achievements table with default achievements."""
    achievements = [
        # Welcome achievements
        ("Welcome!", "Create your first account", "fas fa-star", 10, "welcome", "first_login", 1, 0),
        ("First Steps", "Generate your first prompt", "fas fa-baby", 5, "generation", "prompts_generated", 1, 0),
        ("Collector", "Save your first prompt", "fas fa-bookmark", 5, "collection", "prompts_saved", 1, 0),
        ("Community Member", "Share your first prompt", "fas fa-users", 10, "social", "prompts_shared", 1, 0),

        # Progress achievements
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

        # Special achievements
        ("Explorer", "Try all prompt types", "fas fa-compass", 25, "special", "prompt_types_used", 6, 0),
        ("Profile Complete", "Complete your profile", "fas fa-user-check", 15, "profile", "profile_completed", 1, 0),
        ("Daily Visitor", "Login for 7 consecutive days", "fas fa-calendar-check", 30, "streak", "login_streak", 7, 0),
        ("Weekly Warrior", "Login for 30 consecutive days", "fas fa-shield-alt", 75, "streak", "login_streak", 30, 0),
        ("Monthly Master", "Login for 100 consecutive days", "fas fa-star-shield", 150, "streak", "login_streak", 100, 0),

        # Quality achievements
        ("Feedback Guru", "Give feedback on 5 prompts", "fas fa-comments", 15, "quality", "feedback_given", 5, 0),
        ("Quality Contributor", "Receive 10 positive ratings", "fas fa-thumbs-up", 20, "quality", "positive_ratings", 10, 0),
        ("Critic", "Give detailed feedback on 25 prompts", "fas fa-search", 30, "quality", "detailed_feedback", 25, 0),
        ("Quality Master", "Receive 50 positive ratings", "fas fa-star", 50, "quality", "positive_ratings", 50, 0),

        # Diversity achievements
        ("Style Explorer", "Try 5 different prompt styles", "fas fa-palette", 20, "diversity", "styles_tried", 5, 0),
        ("Technique Master", "Use 10 different prompt techniques", "fas fa-tools", 25, "diversity", "techniques_used", 10, 0),
        ("Category Collector", "Create prompts in 8 different categories", "fas fa-folder-open", 30, "diversity", "categories_used", 8, 0),
        ("Format Specialist", "Use 6 different prompt formats", "fas fa-file-alt", 25, "diversity", "formats_used", 6, 0),

        # Advanced features achievements
        ("Version Controller", "Create 10 different versions of a prompt", "fas fa-code-branch", 20, "advanced", "versions_created", 10, 0),
        ("Template Creator", "Create 5 custom prompt templates", "fas fa-file-code", 25, "advanced", "templates_created", 5, 0),
        ("Batch Processor", "Generate prompts in batch mode", "fas fa-layer-group", 15, "advanced", "batch_processing_used", 1, 0),
        ("Parameter Expert", "Use advanced parameters 25 times", "fas fa-sliders-h", 30, "advanced", "advanced_params_used", 25, 0),

        # Community engagement achievements
        ("Helpful Member", "Help 5 other users", "fas fa-hands-helping", 25, "community", "users_helped", 5, 0),
        ("Mentor", "Provide guidance to 15 users", "fas fa-chalkboard-teacher", 40, "community", "users_helped", 15, 0),
        ("Community Helper", "Participate in community discussions", "fas fa-users-cog", 20, "community", "community_participation", 1, 0),
        ("Collaborator", "Work on shared projects with others", "fas fa-handshake", 35, "community", "collaborations", 3, 0),

        # Consistency achievements
        ("Steady Progress", "Login for 50 days total", "fas fa-route", 30, "consistency", "total_logins", 50, 0),
        ("Reliable User", "Login for 100 days total", "fas fa-shield-check", 50, "consistency", "total_logins", 100, 0),
        ("Dedicated Member", "Maintain a 30-day login streak", "fas fa-calendar-star", 75, "consistency", "login_streak", 30, 0),
        ("Loyal User", "Login for 200 days total", "fas fa-heart", 100, "consistency", "total_logins", 200, 0),

        # Exploration achievements
        ("Feature Explorer", "Try all main features", "fas fa-binoculars", 25, "exploration", "features_used", 10, 0),
        ("Settings Expert", "Customize all profile settings", "fas fa-cog", 15, "exploration", "settings_customized", 1, 0),
        ("Tool Master", "Use all available tools", "fas fa-toolbox", 30, "exploration", "tools_used", 8, 0),
        ("Discovery Seeker", "Find and use hidden features", "fas fa-lightbulb", 20, "exploration", "hidden_features_used", 5, 0),

        # Additional achievements
        ("Power User", "Generate 1000 prompts", "fas fa-bolt", 200, "generation", "prompts_generated", 1000, 0),
        ("Library Master", "Save 250 prompts", "fas fa-book-reader", 75, "collection", "prompts_saved", 250, 0),
        ("Community Legend", "Share 100 prompts", "fas fa-crown", 150, "social", "prompts_shared", 100, 0),
        ("Year Round User", "Login for 365 consecutive days", "fas fa-calendar-alt", 200, "streak", "login_streak", 365, 0),
        ("Perfectionist", "Create 50 prompt versions", "fas fa-check-double", 40, "advanced", "versions_created", 50, 0),
        ("Innovation Leader", "Create 20 custom templates", "fas fa-lightbulb", 60, "advanced", "templates_created", 20, 0),
        ("Community Champion", "Help 50 other users", "fas fa-trophy", 100, "community", "users_helped", 50, 0),
        ("Feature Pioneer", "Try 20 different features", "fas fa-flag", 50, "exploration", "features_used", 20, 0),

        # Hidden achievements
        ("Early Adopter", "Be among the first 100 users", "fas fa-rocket", 100, "special", "user_rank", 100, 1),
        ("Reverse Engineer", "Use reverse image prompts", "fas fa-magic", 15, "special", "reverse_image_used", 1, 0),
        ("Advanced User", "Use advanced prompts", "fas fa-graduation-cap", 20, "special", "advanced_prompts_used", 1, 0),
        ("API Key Provider", "Add and validate your own Gemini API key", "fas fa-key", 100, "special", "api_key_validated", 1, 0),
    ]

    with get_db_connection(user_db) as conn:
        cursor = conn.cursor()

        for achievement in achievements:
            try:
                cursor.execute("""
                    INSERT OR IGNORE INTO achievements (name, description, icon, points_reward, category, condition_type, condition_value, hidden)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, achievement)
            except Exception as e:
                print(f"Error inserting achievement {achievement[0]}: {e}")

        conn.commit()


def check_and_award_achievements(user_db, username: str, prompt_db: str, community_db: str):
    """Check if user has earned any new achievements and award them."""
    max_retries = 3
    for attempt in range(max_retries):
        try:
            with get_db_connection(user_db) as conn:
                cursor = conn.cursor()

                # Get user's current stats
                stats = get_user_stats(username, prompt_db, community_db)

                # Get user's unlocked achievements
                cursor.execute("SELECT achievement_id FROM user_achievements WHERE username = ?", (username,))
                unlocked = {row[0] for row in cursor.fetchall()}

                # Check each achievement
                cursor.execute("SELECT * FROM achievements WHERE hidden = 0 OR id IN (SELECT achievement_id FROM user_achievements WHERE username = ?)", (username,))
                all_achievements = cursor.fetchall()

                newly_unlocked = []
                total_points_earned = 0

                for achievement in all_achievements:
                    achievement_id = achievement[0]
                    if achievement_id in unlocked:
                        continue

                    condition_type = achievement[6]  # condition_type column
                    condition_value = achievement[7]  # condition_value column

                    if check_achievement_condition(stats, condition_type, condition_value):
                        # Award achievement
                        cursor.execute(
                            "INSERT INTO user_achievements (username, achievement_id) VALUES (?, ?)",
                            (username, achievement_id)
                        )
                        newly_unlocked.append(achievement[1])  # name
                        total_points_earned += achievement[4]  # points_reward

                if newly_unlocked:
                    # Add achievement points using the new system
                    try:
                        # Calculate expiration date for achievement points
                        expires_at = calculate_expiration_date('achievement')
                        
                        # Add points transaction
                        cursor.execute("""
                            INSERT INTO point_transactions (username, points, source, description, expires_at, is_expired)
                            VALUES (?, ?, ?, ?, ?, ?)
                        """, (username, total_points_earned, 'achievement', f'Achievement rewards: {", ".join(newly_unlocked)}', expires_at, 0))
                        
                        # Get transaction ID for history
                        transaction_id = cursor.lastrowid
                        
                        # Get points before and after
                        current_points = get_user_points(user_db, username)
                        points_before = current_points - total_points_earned
                        points_after = min(current_points, 500.0)  # Cap at 500
                        
                        # Record in history
                        cursor.execute("""
                            INSERT INTO point_history (username, transaction_id, action, points_before, points_after)
                            VALUES (?, ?, ?, ?, ?)
                        """, (username, transaction_id, 'add', points_before, points_after))
                        
                    except Exception as e:
                        logger.exception("Failed to add achievement points")
                        # Don't fail the entire operation if points update fails

                conn.commit()
                return newly_unlocked, total_points_earned

        except Exception as e:
            if attempt < max_retries - 1:
                time.sleep(0.1 * (attempt + 1))
                continue
            else:
                logger.exception("Failed to check achievements after retries")
                return [], 0  # Return empty results on failure


def get_user_stats(username: str, prompt_db: str, community_db: str):
    """Get user's statistics for achievement checking."""
    stats = {
        'prompts_generated': 0,
        'prompts_saved': 0,
        'prompts_shared': 0,
        'prompt_types_used': set(),
        'login_streak': 0,
        'profile_completed': 0,
        'user_rank': 0,
        'reverse_image_used': 0,
        'advanced_prompts_used': 0,
        'api_key_validated': 0,
        # Quality stats
        'feedback_given': 0,
        'positive_ratings': 0,
        'detailed_feedback': 0,
        # Diversity stats
        'styles_tried': set(),
        'techniques_used': set(),
        'categories_used': set(),
        'formats_used': set(),
        # Advanced features stats
        'versions_created': 0,
        'templates_created': 0,
        'batch_processing_used': 0,
        'advanced_params_used': 0,
        # Community stats
        'users_helped': 0,
        'community_participation': 0,
        'collaborations': 0,
        # Consistency stats
        'total_logins': 0,
        # Exploration stats
        'features_used': set(),
        'settings_customized': 0,
        'tools_used': set(),
        'hidden_features_used': set()
    }

    # Get prompts generated (from prompt_versions)
    with get_db_connection(prompt_db) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM prompt_versions WHERE username = ?", (username,))
        stats['prompts_generated'] = cursor.fetchone()[0]

        # Get prompts saved (from user's personal table)
        cursor.execute(f"SELECT COUNT(*) FROM \"{username}\"")
        stats['prompts_saved'] = cursor.fetchone()[0]

    # Get prompts shared
    with get_db_connection(community_db) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM shared WHERE owner = ?", (username,))
        stats['prompts_shared'] = cursor.fetchone()[0]

    # Get user rank (count of users created before this user)
    with get_db_connection(prompt_db) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT COUNT(*) FROM users
            WHERE username IN (
                SELECT DISTINCT username FROM prompt_versions
                UNION
                SELECT DISTINCT owner FROM shared
                UNION
                SELECT DISTINCT username FROM user_logins
            ) AND username != ?
        """, (username,))
        stats['user_rank'] = cursor.fetchone()[0]

    # Get total logins
    with get_db_connection(prompt_db) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM user_logins WHERE username = ?", (username,))
        stats['total_logins'] = cursor.fetchone()[0]

    # Get API key validation status
    with get_db_connection(user_db) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT api_key_validated FROM users WHERE username = ?", (username,))
        row = cursor.fetchone()
        stats['api_key_validated'] = 1 if row and row[0] else 0

    # Convert sets to lengths for achievement checking
    stats['styles_tried'] = len(stats['styles_tried'])
    stats['techniques_used'] = len(stats['techniques_used'])
    stats['categories_used'] = len(stats['categories_used'])
    stats['formats_used'] = len(stats['formats_used'])
    stats['features_used'] = len(stats['features_used'])
    stats['tools_used'] = len(stats['tools_used'])
    stats['hidden_features_used'] = len(stats['hidden_features_used'])

    return stats


def check_achievement_condition(stats, condition_type: str, condition_value: int):
    """Check if a specific achievement condition is met."""
    if condition_type == "prompts_generated":
        return stats['prompts_generated'] >= condition_value
    elif condition_type == "prompts_saved":
        return stats['prompts_saved'] >= condition_value
    elif condition_type == "prompts_shared":
        return stats['prompts_shared'] >= condition_value
    elif condition_type == "prompt_types_used":
        return len(stats['prompt_types_used']) >= condition_value
    elif condition_type == "login_streak":
        return stats['login_streak'] >= condition_value
    elif condition_type == "profile_completed":
        return stats['profile_completed'] >= condition_value
    elif condition_type == "user_rank":
        return stats['user_rank'] < condition_value  # Lower rank number means earlier user
    elif condition_type == "first_login":
        return True  # Always true for welcome achievements
    elif condition_type == "reverse_image_used":
        return stats['reverse_image_used'] >= condition_value
    elif condition_type == "advanced_prompts_used":
        return stats['advanced_prompts_used'] >= condition_value
    # Quality conditions
    elif condition_type == "feedback_given":
        return stats['feedback_given'] >= condition_value
    elif condition_type == "positive_ratings":
        return stats['positive_ratings'] >= condition_value
    elif condition_type == "detailed_feedback":
        return stats['detailed_feedback'] >= condition_value
    # Diversity conditions
    elif condition_type == "styles_tried":
        return stats['styles_tried'] >= condition_value
    elif condition_type == "techniques_used":
        return stats['techniques_used'] >= condition_value
    elif condition_type == "categories_used":
        return stats['categories_used'] >= condition_value
    elif condition_type == "formats_used":
        return stats['formats_used'] >= condition_value
    # Advanced features conditions
    elif condition_type == "versions_created":
        return stats['versions_created'] >= condition_value
    elif condition_type == "templates_created":
        return stats['templates_created'] >= condition_value
    elif condition_type == "batch_processing_used":
        return stats['batch_processing_used'] >= condition_value
    elif condition_type == "advanced_params_used":
        return stats['advanced_params_used'] >= condition_value
    # Community conditions
    elif condition_type == "users_helped":
        return stats['users_helped'] >= condition_value
    elif condition_type == "community_participation":
        return stats['community_participation'] >= condition_value
    elif condition_type == "collaborations":
        return stats['collaborations'] >= condition_value
    # Consistency conditions
    elif condition_type == "total_logins":
        return stats['total_logins'] >= condition_value
    # Exploration conditions
    elif condition_type == "features_used":
        return stats['features_used'] >= condition_value
    elif condition_type == "settings_customized":
        return stats['settings_customized'] >= condition_value
    elif condition_type == "tools_used":
        return stats['tools_used'] >= condition_value
    elif condition_type == "hidden_features_used":
        return stats['hidden_features_used'] >= condition_value
    elif condition_type == "api_key_validated":
        return stats['api_key_validated'] >= condition_value

    return False


def get_user_achievements(user_db, username: str):
    """Get all achievements for a user."""
    with get_db_connection(user_db) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT a.id, a.name, a.description, a.icon, a.points_reward, a.category,
                   ua.unlocked_at
            FROM achievements a
            JOIN user_achievements ua ON a.id = ua.achievement_id
            WHERE ua.username = ?
            ORDER BY ua.unlocked_at DESC
        """, (username,))
        return cursor.fetchall()


def process_daily_login_bonus(user_db, username: str):
    """Process daily login bonus for a user. Returns points awarded."""
    import random
    import time
    from datetime import datetime, date

    today = date.today()
    yesterday = today.replace(day=today.day - 1) if today.day > 1 else today.replace(month=today.month - 1, day=31)

    # Retry logic for database operations
    max_retries = 3
    for attempt in range(max_retries):
        try:
            with get_db_connection(user_db) as conn:
                # Use immediate transaction for better concurrency
                conn.execute("BEGIN IMMEDIATE")
                cursor = conn.cursor()

                # Check if user already got bonus today
                cursor.execute("SELECT points_awarded FROM user_logins WHERE username = ? AND login_date = ?", (username, today))
                today_login = cursor.fetchone()

                if today_login:
                    conn.commit()
                    return 0  # Already got bonus today

                # Check yesterday's login to calculate streak
                cursor.execute("SELECT points_awarded FROM user_logins WHERE username = ? AND login_date = ?", (username, yesterday))
                yesterday_login = cursor.fetchone()

                # Calculate streak
                streak = 1
                if yesterday_login:
                    # Get current streak from yesterday's record
                    cursor.execute("""
                        SELECT login_date FROM user_logins
                        WHERE username = ?
                        ORDER BY login_date DESC
                        LIMIT 2
                    """, (username,))
                    recent_logins = cursor.fetchall()

                    if len(recent_logins) == 2:
                        from datetime import timedelta
                        date1 = recent_logins[0][0]
                        date2 = recent_logins[1][0]
                        if isinstance(date1, str):
                            date1 = datetime.strptime(date1, '%Y-%m-%d').date()
                        if isinstance(date2, str):
                            date2 = datetime.strptime(date2, '%Y-%m-%d').date()

                        if (date1 - date2).days == 1:
                            streak = 2  # At least 2 days in a row

                # Generate random bonus points (5-12)
                bonus_points = random.randint(5, 12)

                # Insert today's login record
                cursor.execute(
                    "INSERT OR REPLACE INTO user_logins (username, login_date, points_awarded) VALUES (?, ?, ?)",
                    (username, today, bonus_points)
                )

                # Add points using the new system with source tracking
                try:
                    # Calculate expiration date for daily login points
                    expires_at = calculate_expiration_date('daily_login')
                    
                    # Add points transaction
                    cursor.execute("""
                        INSERT INTO point_transactions (username, points, source, description, expires_at, is_expired)
                        VALUES (?, ?, ?, ?, ?, ?)
                    """, (username, bonus_points, 'daily_login', f'Daily login bonus (streak: {streak})', expires_at, 0))
                    
                    # Get transaction ID for history
                    transaction_id = cursor.lastrowid
                    
                    # Get points before and after
                    current_points = get_user_points(user_db, username)
                    points_before = current_points - bonus_points
                    points_after = min(current_points, 500.0)  # Cap at 500
                    
                    # Record in history
                    cursor.execute("""
                        INSERT INTO point_history (username, transaction_id, action, points_before, points_after)
                        VALUES (?, ?, ?, ?, ?)
                    """, (username, transaction_id, 'add', points_before, points_after))
                    
                except Exception as e:
                    # If updating points fails, try to rollback the login record
                    cursor.execute("DELETE FROM user_logins WHERE username = ? AND login_date = ?", (username, today))
                    conn.rollback()
                    raise e

                conn.commit()
                return bonus_points

        except Exception as e:
            if attempt < max_retries - 1:
                # Wait before retrying
                time.sleep(0.1 * (attempt + 1))
                continue
            else:
                logger.exception("Failed to process daily login bonus after retries")
                return 0  # Return 0 if all retries fail


def get_user_api_key(user_db, username: str) -> str | None:
    """Get the user's Gemini API key."""
    with get_db_connection(user_db) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT gemini_api_key FROM users WHERE username = ?", (username,))
        row = cursor.fetchone()
        return row[0] if row else None


def set_user_api_key(user_db, username: str, api_key: str):
    """Set the user's Gemini API key."""
    with get_db_connection(user_db) as conn:
        execute_sql(
            conn,
            "UPDATE users SET gemini_api_key = ? WHERE username = ?",
            (api_key, username),
        )


def is_api_key_validated(user_db, username: str) -> bool:
    """Check if the user's API key has been validated."""
    with get_db_connection(user_db) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT api_key_validated FROM users WHERE username = ?", (username,))
        row = cursor.fetchone()
        return bool(row and row[0])


def set_api_key_validated(user_db, username: str, validated: bool = True):
    """Mark the user's API key as validated."""
    with get_db_connection(user_db) as conn:
        execute_sql(
            conn,
            "UPDATE users SET api_key_validated = ? WHERE username = ?",
            (1 if validated else 0, username),
        )
