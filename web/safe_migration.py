#!/usr/bin/env python3
"""
Safe Database Migration Utility for Prompt Sanctuary

This script automatically migrates, updates, and fixes all databases to have
all necessary tables and data. It performs comprehensive database maintenance
including schema updates, data validation, and automatic repairs.

Usage:
    python safe_migration.py [--dry-run] [--force] [--backup-dir BACKUP_DIR] [--auto-fix]
    
Options:
    --dry-run      Show what would be changed without making actual changes
    --force        Force migration even if backup fails
    --backup-dir   Directory to store backups (default: ./backups)
    --auto-fix     Automatically fix data inconsistencies and missing data
    --rebuild      Completely rebuild all databases from scratch (destructive!)
    --fix-foreign-keys  Fix foreign key issues and enable constraints
"""

import os
import sys
import shutil
import sqlite3
import argparse
import logging
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(__file__))

from models import get_db_connection, enable_wal_mode

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('migration.log')
    ]
)
logger = logging.getLogger(__name__)


class DatabaseMigrator:
    """Handles safe database migrations with backup and rollback capabilities."""
    
    def __init__(self, backup_dir: str = "./backups", force: bool = False, auto_fix: bool = False):
        self.backup_dir = Path(backup_dir)
        self.force = force
        self.auto_fix = auto_fix
        self.migrations_performed = []
        self.backup_files = []
        self.fixes_applied = []
        
        # Ensure backup directory exists
        self.backup_dir.mkdir(parents=True, exist_ok=True)
    
    def backup_database(self, db_path: str) -> str:
        """Create a backup of the database before migration."""
        try:
            db_path_obj = Path(db_path)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_filename = f"{db_path_obj.stem}_backup_{timestamp}.db"
            backup_path = self.backup_dir / backup_filename
            
            logger.info(f"Creating backup: {db_path} -> {backup_path}")
            
            # Copy the database file
            shutil.copy2(db_path, backup_path)
            
            # Verify backup
            if not backup_path.exists():
                raise Exception("Backup file was not created")
            
            # Test backup integrity
            with sqlite3.connect(str(backup_path)) as conn:
                conn.execute("PRAGMA integrity_check")
            
            logger.info(f"Backup created successfully: {backup_path}")
            self.backup_files.append(str(backup_path))
            return str(backup_path)
            
        except Exception as e:
            logger.error(f"Failed to create backup for {db_path}: {e}")
            if not self.force:
                raise Exception(f"Backup failed: {e}")
            else:
                logger.warning(f"Continuing without backup (force mode): {e}")
                return ""
    
    def get_table_info(self, db_path: str, table_name: str) -> List[Dict[str, Any]]:
        """Get information about table columns."""
        with get_db_connection(db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(f"PRAGMA table_info({table_name})")
            columns = cursor.fetchall()
            return [
                {
                    'cid': col[0],
                    'name': col[1],
                    'type': col[2],
                    'notnull': col[3],
                    'dflt_value': col[4],
                    'pk': col[5]
                }
                for col in columns
            ]
    
    def column_exists(self, db_path: str, table_name: str, column_name: str) -> bool:
        """Check if a column exists in a table."""
        try:
            columns = self.get_table_info(db_path, table_name)
            return any(col['name'] == column_name for col in columns)
        except Exception:
            return False
    
    def table_exists(self, db_path: str, table_name: str) -> bool:
        """Check if a table exists."""
        try:
            with get_db_connection(db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
                    (table_name,)
                )
                return cursor.fetchone() is not None
        except Exception:
            return False
    
    def add_column_if_not_exists(self, db_path: str, table_name: str, 
                                column_name: str, column_definition: str, dry_run: bool = False) -> bool:
        """Add a column to a table if it doesn't exist."""
        if self.column_exists(db_path, table_name, column_name):
            logger.info(f"Column {table_name}.{column_name} already exists, skipping")
            return False
        
        sql = f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_definition}"
        
        if dry_run:
            logger.info(f"[DRY RUN] Would execute: {sql}")
            return True
        
        try:
            with get_db_connection(db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(sql)
                conn.commit()
                logger.info(f"Added column {table_name}.{column_name}")
                self.migrations_performed.append(f"Added column {table_name}.{column_name}")
                return True
        except Exception as e:
            logger.error(f"Failed to add column {table_name}.{column_name}: {e}")
            return False
    
    def create_table_if_not_exists(self, db_path: str, table_name: str, 
                                  table_definition: str, dry_run: bool = False) -> bool:
        """Create a table if it doesn't exist."""
        if self.table_exists(db_path, table_name):
            logger.info(f"Table {table_name} already exists, skipping")
            return False
        
        sql = f"CREATE TABLE IF NOT EXISTS {table_name} {table_definition}"
        
        if dry_run:
            logger.info(f"[DRY RUN] Would execute: {sql}")
            return True
        
        try:
            with get_db_connection(db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(sql)
                conn.commit()
                logger.info(f"Created table {table_name}")
                self.migrations_performed.append(f"Created table {table_name}")
                return True
        except Exception as e:
            logger.error(f"Failed to create table {table_name}: {e}")
            return False
    
    def create_index_if_not_exists(self, db_path: str, index_name: str, 
                                  index_definition: str, dry_run: bool = False) -> bool:
        """Create an index if it doesn't exist."""
        try:
            with get_db_connection(db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT name FROM sqlite_master WHERE type='index' AND name=?",
                    (index_name,)
                )
                if cursor.fetchone():
                    logger.info(f"Index {index_name} already exists, skipping")
                    return False
        except Exception:
            pass
        
        sql = f"CREATE INDEX IF NOT EXISTS {index_name} {index_definition}"
        
        if dry_run:
            logger.info(f"[DRY RUN] Would execute: {sql}")
            return True
        
        try:
            with get_db_connection(db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(sql)
                conn.commit()
                logger.info(f"Created index {index_name}")
                self.migrations_performed.append(f"Created index {index_name}")
                return True
        except Exception as e:
            logger.error(f"Failed to create index {index_name}: {e}")
            return False
    
    def migrate_users_table(self, db_path: str, dry_run: bool = False) -> bool:
        """Migrate the users table to remove point system and make API keys mandatory."""
        logger.info(f"Migrating users table in {db_path}")
        
        # Check if users table exists
        if not self.table_exists(db_path, 'users'):
            logger.info(f"Users table does not exist in {db_path} - skipping users table migration")
            return True  # This is not an error for databases that don't need users table
        
        try:
            with get_db_connection(db_path) as conn:
                cursor = conn.cursor()
                
                # Check if point system tables exist, if not, migration may have already been completed
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='point_transactions'")
                if not cursor.fetchone():
                    logger.info("Point system tables not found, migration may have already been completed")
                    return True
                
                # 1. Update users table schema
                logger.info("Updating users table schema...")
                
                # Disable foreign key constraints temporarily
                cursor.execute("PRAGMA foreign_keys=OFF")
                conn.commit()
                
                # Drop existing users_new table if it exists
                cursor.execute("DROP TABLE IF EXISTS users_new")
                
                # Make gemini_api_key and api_key_validated NOT NULL with defaults
                cursor.execute("""
                    CREATE TABLE users_new (
                        username TEXT PRIMARY KEY,
                        password TEXT NOT NULL,
                        email TEXT,
                        identicon_value TEXT,
                        gemini_api_key TEXT NOT NULL DEFAULT '',
                        api_key_validated INTEGER NOT NULL DEFAULT 0
                    )
                """)
                
                # Copy existing data, handling NULL values
                cursor.execute("""
                    INSERT INTO users_new (username, password, email, identicon_value, gemini_api_key, api_key_validated)
                    SELECT 
                        username, 
                        password, 
                        COALESCE(email, '') as email,
                        COALESCE(identicon_value, '') as identicon_value,
                        COALESCE(gemini_api_key, '') as gemini_api_key,
                        COALESCE(api_key_validated, 0) as api_key_validated
                    FROM users
                """)
                
                # Drop old table and rename new one
                cursor.execute("DROP TABLE users")
                cursor.execute("ALTER TABLE users_new RENAME TO users")
                
                # Re-enable foreign key constraints
                cursor.execute("PRAGMA foreign_keys=ON")
                conn.commit()
                
                # 2. Remove point-related tables
                logger.info("Removing point-related tables...")
                
                tables_to_remove = [
                    "point_transactions",
                    "point_history",
                    "user_logins",
                    "achievements",
                    "user_achievements",
                ]
                
                for table in tables_to_remove:
                    cursor.execute(f"DROP TABLE IF EXISTS {table}")
                    logger.info(f"Removed table: {table}")
                conn.commit()

                # Ensure sessions table exists and is correct (it's not point-related but good to check)
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='sessions'")
                if not cursor.fetchone():
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
                    logger.info("Created sessions table.")
                else:
                    logger.info("Sessions table already exists")

                logger.info("User database migration completed successfully")
                return True
            
        except Exception as e:
            logger.error(f"Failed to migrate users table: {e}")
            return False
    
    def migrate_api_key_system(self, db_path: str, dry_run: bool = False) -> bool:
        """Migrate to API key system - remove point system and make API keys mandatory."""
        logger.info(f"Migrating to API key system in {db_path}")
        
        # Only run this on user database
        if 'user.db' not in db_path:
            logger.info(f"Skipping API key migration for non-user database: {db_path}")
            return True
        
        try:
            with get_db_connection(db_path) as conn:
                cursor = conn.cursor()
                
                # Check if point system tables exist, if not, migration may have already been completed
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='point_transactions'")
                if not cursor.fetchone():
                    logger.info("Point system tables not found, API key migration may have already been completed")
                    return True
                
                # 1. Update users table schema
                logger.info("Updating users table schema...")
                
                # Disable foreign key constraints temporarily
                cursor.execute("PRAGMA foreign_keys=OFF")
                conn.commit()
                
                # Drop existing users_new table if it exists
                cursor.execute("DROP TABLE IF EXISTS users_new")
                
                # Make gemini_api_key and api_key_validated NOT NULL with defaults
                cursor.execute("""
                    CREATE TABLE users_new (
                        username TEXT PRIMARY KEY,
                        password TEXT NOT NULL,
                        email TEXT,
                        identicon_value TEXT,
                        gemini_api_key TEXT NOT NULL DEFAULT '',
                        api_key_validated INTEGER NOT NULL DEFAULT 0
                    )
                """)
                
                # Copy existing data, handling NULL values
                cursor.execute("""
                    INSERT INTO users_new (username, password, email, identicon_value, gemini_api_key, api_key_validated)
                    SELECT 
                        username, 
                        password, 
                        COALESCE(email, '') as email,
                        COALESCE(identicon_value, '') as identicon_value,
                        COALESCE(gemini_api_key, '') as gemini_api_key,
                        COALESCE(api_key_validated, 0) as api_key_validated
                    FROM users
                """)
                
                # Drop old table and rename new one
                cursor.execute("DROP TABLE users")
                cursor.execute("ALTER TABLE users_new RENAME TO users")
                
                # Re-enable foreign key constraints
                cursor.execute("PRAGMA foreign_keys=ON")
                conn.commit()
                
                # 2. Remove point-related tables
                logger.info("Removing point-related tables...")
                
                tables_to_remove = [
                    "point_transactions",
                    "point_history",
                    "user_logins",
                    "achievements",
                    "user_achievements",
                ]
                
                for table in tables_to_remove:
                    cursor.execute(f"DROP TABLE IF EXISTS {table}")
                    logger.info(f"Removed table: {table}")
                conn.commit()

                # Ensure sessions table exists and is correct
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='sessions'")
                if not cursor.fetchone():
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
                    logger.info("Created sessions table.")
                else:
                    logger.info("Sessions table already exists")

                logger.info("API key system migration completed successfully")
                return True
                
        except Exception as e:
            logger.error(f"Failed to migrate to API key system: {e}")
            return False
    
    
    def migrate_user_logins_table(self, db_path: str, dry_run: bool = False) -> bool:
        """Migrate the user_logins table."""
        logger.info(f"Migrating user_logins table in {db_path}")
        
        try:
            # Create user_logins table
            user_logins_table = """
            (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL,
                login_date DATE NOT NULL,
                points_awarded REAL DEFAULT 0,
                UNIQUE(username, login_date)
            )
            """
            
            self.create_table_if_not_exists(
                db_path, 'user_logins', user_logins_table, dry_run
            )
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to migrate user_logins table: {e}")
            return False
    
    def migrate_sessions_table(self, db_path: str, dry_run: bool = False) -> bool:
        """Migrate the sessions table."""
        logger.info(f"Migrating sessions table in {db_path}")
        
        try:
            # Create sessions table
            sessions_table = """
            (
                token TEXT PRIMARY KEY,
                username TEXT NOT NULL,
                user_agent TEXT,
                ip TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_active TIMESTAMP,
                revoked INTEGER DEFAULT 0
            )
            """
            
            self.create_table_if_not_exists(
                db_path, 'sessions', sessions_table, dry_run
            )
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to migrate sessions table: {e}")
            return False
    
    def migrate_community_tables(self, db_path: str, dry_run: bool = False) -> bool:
        """Migrate community-related tables."""
        logger.info(f"Migrating community tables in {db_path}")
        
        try:
            # Create shared table if it doesn't exist (for shared.db)
            if 'shared.db' in db_path:
                shared_table = """
                (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    owner TEXT NOT NULL,
                    random_val TEXT UNIQUE NOT NULL,
                    title TEXT NOT NULL,
                    prompt TEXT NOT NULL,
                    time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
                """
                
                self.create_table_if_not_exists(
                    db_path, 'shared', shared_table, dry_run
                )
            
            # Create community table if it doesn't exist (for query.db)
            elif 'query.db' in db_path:
                community_table = """
                (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    random_val TEXT UNIQUE NOT NULL,
                    username TEXT NOT NULL,
                    tittle TEXT NOT NULL,
                    prompt TEXT NOT NULL,
                    tag TEXT,
                    time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
                """
                
                self.create_table_if_not_exists(
                    db_path, 'community', community_table, dry_run
                )
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to migrate community tables: {e}")
            return False
    
    def migrate_feedback_table(self, db_path: str, dry_run: bool = False) -> bool:
        """Migrate the feedback table."""
        logger.info(f"Migrating feedback table in {db_path}")
        
        try:
            # Create feedback table
            feedback_table = """
            (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL,
                feedback TEXT NOT NULL
            )
            """
            
            self.create_table_if_not_exists(
                db_path, 'feedback', feedback_table, dry_run
            )
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to migrate feedback table: {e}")
            return False
    
    def migrate_prompt_versions_table(self, db_path: str, dry_run: bool = False) -> bool:
        """Migrate the prompt_versions table."""
        logger.info(f"Migrating prompt_versions table in {db_path}")
        
        try:
            # Create prompt_versions table
            prompt_versions_table = """
            (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL,
                prompt_id TEXT NOT NULL,
                version_number INTEGER NOT NULL,
                title TEXT NOT NULL,
                prompt TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(username, prompt_id, version_number)
            )
            """
            
            self.create_table_if_not_exists(
                db_path, 'prompt_versions', prompt_versions_table, dry_run
            )
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to migrate prompt_versions table: {e}")
            return False
    
    
    
    
    def enable_foreign_keys(self, db_path: str, dry_run: bool = False) -> bool:
        """Enable foreign key constraints on a database."""
        if dry_run:
            logger.info(f"[DRY RUN] Would enable foreign keys for {db_path}")
            return True
        
        try:
            with get_db_connection(db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("PRAGMA foreign_keys = ON")
                conn.commit()
                
                # Verify foreign keys are enabled
                cursor.execute("PRAGMA foreign_keys")
                result = cursor.fetchone()
                if result and result[0]:
                    logger.info(f"Enabled foreign keys for {db_path}")
                    self.migrations_performed.append(f"Enabled foreign keys for {os.path.basename(db_path)}")
                    return True
                else:
                    logger.warning(f"Failed to enable foreign keys for {db_path}")
                    return False
        except Exception as e:
            logger.error(f"Failed to enable foreign keys for {db_path}: {e}")
            return False
    
    def validate_foreign_keys(self, db_path: str, dry_run: bool = False) -> bool:
        """Validate foreign key constraints in a database."""
        if dry_run:
            logger.info(f"[DRY RUN] Would validate foreign keys for {db_path}")
            return True
        
        try:
            with get_db_connection(db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("PRAGMA foreign_key_check")
                violations = cursor.fetchall()
                
                if violations:
                    logger.warning(f"Foreign key violations found in {db_path}: {len(violations)} violations")
                    for violation in violations:
                        logger.warning(f"  Table: {violation[0]}, Row: {violation[1]}, Parent: {violation[2]}, FKey: {violation[3]}")
                    return False
                else:
                    logger.info(f"Foreign key validation passed for {db_path}")
                    return True
        except Exception as e:
            logger.error(f"Failed to validate foreign keys for {db_path}: {e}")
            return False
    
    
    def fix_missing_user_data(self, db_path: str, dry_run: bool = False) -> bool:
        """Fix missing user data like identicon values and initial points."""
        # Only run this on user database
        if 'user.db' not in db_path:
            return True
        
        if dry_run:
            logger.info(f"[DRY RUN] Would fix missing user data in {db_path}")
            return True
        
        try:
            with get_db_connection(db_path) as conn:
                cursor = conn.cursor()
                
                # Fix users without identicon values
                cursor.execute("""
                    SELECT username FROM users 
                    WHERE identicon_value IS NULL OR identicon_value = ''
                """)
                users_without_identicon = cursor.fetchall()
                
                if users_without_identicon:
                    logger.info(f"Fixing {len(users_without_identicon)} users without identicon values")
                    for (username,) in users_without_identicon:
                        from models import generate_identicon_value
                        identicon_value = generate_identicon_value(username)
                        cursor.execute(
                            "UPDATE users SET identicon_value = ? WHERE username = ?",
                            (identicon_value, username)
                        )
                    conn.commit()
                    self.fixes_applied.append(f"Added identicon values for {len(users_without_identicon)} users")
                
                # Fix users without initial points transactions
                cursor.execute("""
                    SELECT u.username FROM users u
                    LEFT JOIN point_transactions pt ON u.username = pt.username AND pt.source = 'original'
                    WHERE pt.username IS NULL
                """)
                users_without_initial_points = cursor.fetchall()
                
                if users_without_initial_points:
                    logger.info(f"Adding initial 80 points for {len(users_without_initial_points)} users")
                    for (username,) in users_without_initial_points:
                        cursor.execute("""
                            INSERT INTO point_transactions (username, points, source, description, expires_at, is_expired)
                            VALUES (?, ?, ?, ?, ?, ?)
                        """, (username, 80.0, 'original', 'Initial points', None, 0))
                    conn.commit()
                    self.fixes_applied.append(f"Added initial points for {len(users_without_initial_points)} users")
                
                return True
        except Exception as e:
            logger.error(f"Failed to fix missing user data for {db_path}: {e}")
            return False
    
    
    def fix_data_inconsistencies(self, db_path: str, dry_run: bool = False) -> bool:
        """Fix various data inconsistencies across all databases."""
        if dry_run:
            logger.info(f"[DRY RUN] Would fix data inconsistencies in {db_path}")
            return True
        
        try:
            with get_db_connection(db_path) as conn:
                cursor = conn.cursor()
                
                fixes_count = 0
                
                # Only fix point_transactions issues in user database
                if 'user.db' in db_path:
                    # Fix negative points in transactions
                    cursor.execute("""
                        SELECT id, username, points FROM point_transactions 
                        WHERE points < 0 AND source NOT IN ('api_key_remove')
                    """)
                    negative_transactions = cursor.fetchall()
                    
                    if negative_transactions:
                        logger.warning(f"Found {len(negative_transactions)} unexpected negative point transactions")
                        for transaction_id, username, points in negative_transactions:
                            # Convert to positive and mark as deduction
                            cursor.execute("""
                                UPDATE point_transactions 
                                SET points = ?, source = 'deduction_fix'
                                WHERE id = ?
                            """, (abs(points), transaction_id))
                        fixes_count += len(negative_transactions)
                        self.fixes_applied.append(f"Fixed {len(negative_transactions)} negative point transactions")
                    
                    # Fix invalid timestamps (future dates)
                    cursor.execute("""
                        SELECT COUNT(*) FROM point_transactions 
                        WHERE created_at > datetime('now', '+1 day')
                    """)
                    future_timestamps = cursor.fetchone()[0]
                    
                    if future_timestamps > 0:
                        cursor.execute("""
                            UPDATE point_transactions 
                            SET created_at = datetime('now')
                            WHERE created_at > datetime('now', '+1 day')
                        """)
                        fixes_count += future_timestamps
                        self.fixes_applied.append(f"Fixed {future_timestamps} future timestamps")
                    
                    # Fix expired points that aren't marked as expired
                    cursor.execute("""
                        UPDATE point_transactions 
                        SET is_expired = 1 
                        WHERE is_expired = 0 AND expires_at IS NOT NULL AND expires_at <= datetime('now')
                    """)
                    expired_fixes = cursor.rowcount
                    if expired_fixes > 0:
                        fixes_count += expired_fixes
                        self.fixes_applied.append(f"Marked {expired_fixes} points as expired")
                
                # Fix general data inconsistencies in all databases
                # Fix invalid timestamps in any table with created_at column
                cursor.execute("""
                    SELECT name FROM sqlite_master 
                    WHERE type='table' AND sql LIKE '%created_at%'
                """)
                tables_with_timestamps = [row[0] for row in cursor.fetchall()]
                
                for table in tables_with_timestamps:
                    try:
                        cursor.execute(f"""
                            UPDATE {table} 
                            SET created_at = datetime('now')
                            WHERE created_at > datetime('now', '+1 day')
                        """)
                        timestamp_fixes = cursor.rowcount
                        if timestamp_fixes > 0:
                            fixes_count += timestamp_fixes
                            self.fixes_applied.append(f"Fixed {timestamp_fixes} future timestamps in {table}")
                    except Exception as e:
                        # Table might not have created_at column, skip
                        pass
                
                conn.commit()
                
                if fixes_count > 0:
                    logger.info(f"Applied {fixes_count} data consistency fixes to {db_path}")
                
                return True
        except Exception as e:
            logger.error(f"Failed to fix data inconsistencies for {db_path}: {e}")
            return False
    
    def validate_and_fix_user_tables(self, db_path: str, dry_run: bool = False) -> bool:
        """Validate and fix user-specific tables in prompt database."""
        # Only run this on prompt database
        if 'prompt_data.db' not in db_path:
            return True
        
        if dry_run:
            logger.info(f"[DRY RUN] Would validate and fix user tables in {db_path}")
            return True
        
        try:
            with get_db_connection(db_path) as conn:
                cursor = conn.cursor()
                
                # Get all user tables
                cursor.execute("""
                    SELECT name FROM sqlite_master 
                    WHERE type='table' AND name NOT LIKE 'sqlite_%' AND name != 'prompt_versions'
                """)
                user_tables = [row[0] for row in cursor.fetchall()]
                
                fixes_count = 0
                
                for table_name in user_tables:
                    # Validate table structure
                    cursor.execute(f"PRAGMA table_info({table_name})")
                    columns = [col[1] for col in cursor.fetchall()]
                    
                    expected_columns = ['random_val', 'title', 'prompt', 'time']
                    missing_columns = [col for col in expected_columns if col not in columns]
                    
                    if missing_columns:
                        logger.warning(f"User table {table_name} missing columns: {missing_columns}")
                        # For now, just log - in future we could add missing columns
                        fixes_count += 1
                    
                    # Check for empty titles or prompts
                    cursor.execute(f"""
                        SELECT COUNT(*) FROM "{table_name}" 
                        WHERE title IS NULL OR title = '' OR prompt IS NULL OR prompt = ''
                    """)
                    invalid_entries = cursor.fetchone()[0]
                    
                    if invalid_entries > 0:
                        logger.warning(f"User table {table_name} has {invalid_entries} invalid entries")
                        # Remove invalid entries
                        cursor.execute(f"""
                            DELETE FROM "{table_name}" 
                            WHERE title IS NULL OR title = '' OR prompt IS NULL OR prompt = ''
                        """)
                        fixes_count += invalid_entries
                        self.fixes_applied.append(f"Removed {invalid_entries} invalid entries from {table_name}")
                
                conn.commit()
                
                if fixes_count > 0:
                    logger.info(f"Applied {fixes_count} user table fixes to {db_path}")
                
                return True
        except Exception as e:
            logger.error(f"Failed to validate user tables for {db_path}: {e}")
            return False
    
    def create_missing_indexes(self, db_path: str, dry_run: bool = False) -> bool:
        """Create missing indexes for better performance."""
        if dry_run:
            logger.info(f"[DRY RUN] Would create missing indexes in {db_path}")
            return True
        
        try:
            with get_db_connection(db_path) as conn:
                cursor = conn.cursor()
                
                indexes_created = 0
                
                # Define indexes based on database type
                if 'user.db' in db_path:
                    indexes = [
                        ("idx_sessions_username", "sessions", "username"),
                        ("idx_sessions_token", "sessions", "token"),
                    ]
                elif 'prompt_data.db' in db_path:
                    indexes = [
                        ("idx_prompt_versions_username", "prompt_versions", "username"),
                        ("idx_prompt_versions_prompt_id", "prompt_versions", "prompt_id"),
                    ]
                elif 'shared.db' in db_path:
                    indexes = [
                        ("idx_shared_owner", "shared", "owner"),
                        ("idx_shared_random_val", "shared", "random_val"),
                    ]
                elif 'query.db' in db_path:
                    indexes = [
                        ("idx_community_username", "community", "username"),
                        ("idx_community_random_val", "community", "random_val"),
                    ]
                elif 'feedback.db' in db_path:
                    indexes = [
                        ("idx_feedback_username", "feedback", "username"),
                    ]
                else:
                    indexes = []
                
                for index_name, table_name, columns in indexes:
                    # Check if index already exists
                    cursor.execute("""
                        SELECT name FROM sqlite_master 
                        WHERE type='index' AND name=?
                    """, (index_name,))
                    
                    if not cursor.fetchone():
                        try:
                            cursor.execute(f"CREATE INDEX {index_name} ON {table_name} ({columns})")
                            indexes_created += 1
                            self.migrations_performed.append(f"Created index {index_name}")
                        except Exception as e:
                            logger.warning(f"Failed to create index {index_name}: {e}")
                
                conn.commit()
                
                if indexes_created > 0:
                    logger.info(f"Created {indexes_created} indexes in {db_path}")
                
                return True
        except Exception as e:
            logger.error(f"Failed to create indexes for {db_path}: {e}")
            return False
    
    def auto_fix_all_databases(self, dry_run: bool = False) -> bool:
        """Perform automatic fixes on all databases."""
        if not self.auto_fix:
            return True
        
        logger.info("Starting automatic database fixes")
        
        # Define database paths
        base_dir = os.path.dirname(__file__)
        databases = {
            'user': os.path.join(base_dir, 'database', 'user.db'),
            'prompt': os.path.join(base_dir, 'database', 'prompt_data.db'),
            'community': os.path.join(base_dir, 'database', 'community', 'shared.db'),
            'query': os.path.join(base_dir, 'database', 'community', 'query.db'),
            'feedback': os.path.join(base_dir, 'database', 'feedback.db')
        }
        
        success = True
        
        for db_name, db_path in databases.items():
            if not os.path.exists(db_path):
                logger.info(f"Database {db_name} does not exist, skipping fixes: {db_path}")
                continue
            
            logger.info(f"Applying auto-fixes to {db_name} database: {db_path}")
            
            # Create backup unless in dry run mode
            if not dry_run:
                try:
                    self.backup_database(db_path)
                except Exception as e:
                    logger.error(f"Backup failed: {e}")
                    if not self.force:
                        continue
            
            # Apply various fixes
            success &= self.create_missing_indexes(db_path, dry_run)
        
        return success
    
    def comprehensive_database_validation(self, db_path: str, dry_run: bool = False) -> bool:
        """Perform comprehensive validation and auto-fix of all database issues."""
        logger.info(f"Performing comprehensive validation of {db_path}")
        
        if dry_run:
            logger.info(f"[DRY RUN] Would perform comprehensive validation of {db_path}")
            return True
        
        try:
            with get_db_connection(db_path) as conn:
                cursor = conn.cursor()
                
                # Check database integrity
                cursor.execute("PRAGMA integrity_check")
                integrity_result = cursor.fetchone()[0]
                if integrity_result != 'ok':
                    logger.error(f"Database integrity check failed: {integrity_result}")
                    return False
                
                # Check foreign key constraints
                cursor.execute("PRAGMA foreign_key_check")
                fk_violations = cursor.fetchall()
                if fk_violations:
                    logger.warning(f"Found {len(fk_violations)} foreign key violations")
                    # Log details but don't fail - we'll fix these separately
                
                # Check for missing tables based on database type
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
                existing_tables = {row[0] for row in cursor.fetchall()}
                
                missing_tables = []
                if 'user.db' in db_path:
                    required_tables = ['users', 'sessions']
                    missing_tables = [t for t in required_tables if t not in existing_tables]
                elif 'prompt_data.db' in db_path:
                    required_tables = ['prompt_versions']
                    missing_tables = [t for t in required_tables if t not in existing_tables]
                elif 'shared.db' in db_path:
                    required_tables = ['shared']
                    missing_tables = [t for t in required_tables if t not in existing_tables]
                elif 'query.db' in db_path:
                    required_tables = ['community']
                    missing_tables = [t for t in required_tables if t not in existing_tables]
                elif 'feedback.db' in db_path:
                    required_tables = ['feedback']
                    missing_tables = [t for t in required_tables if t not in existing_tables]
                
                if missing_tables:
                    logger.warning(f"Missing required tables: {missing_tables}")
                    # These will be created by the migration process
                
                # Check for missing indexes
                cursor.execute("SELECT name FROM sqlite_master WHERE type='index'")
                existing_indexes = {row[0] for row in cursor.fetchall()}
                
                # This is handled by the create_missing_indexes function
                
                logger.info(f"Comprehensive validation completed for {db_path}")
                return True
                
        except Exception as e:
            logger.error(f"Failed comprehensive validation for {db_path}: {e}")
            return False
    
    def migrate_database(self, db_path: str, dry_run: bool = False) -> bool:
        """Perform complete migration of a database."""
        logger.info(f"Starting migration of {db_path}")
        
        # Create database file if it doesn't exist
        if not os.path.exists(db_path):
            logger.info(f"Database file does not exist, creating: {db_path}")
            if not dry_run:
                # Ensure directory exists
                os.makedirs(os.path.dirname(db_path), exist_ok=True)
                # Create empty database
                with get_db_connection(db_path) as conn:
                    conn.commit()
        
        # Create backup unless in dry run mode (only if database already existed)
        elif not dry_run:
            try:
                self.backup_database(db_path)
            except Exception as e:
                logger.error(f"Backup failed: {e}")
                if not self.force:
                    return False
        
        # Enable WAL mode and foreign keys
        if not dry_run:
            enable_wal_mode(db_path)
        
        success = True
        
        # Skip point system fixes since we're migrating to API key system
        
        # Enable foreign key constraints
        success &= self.enable_foreign_keys(db_path, dry_run)
        
        # Migrate all tables based on database type
        if 'user.db' in db_path:
            # User database migrations - migrate to API key system
            success &= self.migrate_api_key_system(db_path, dry_run)
        elif 'prompt_data.db' in db_path:
            # Prompt database migrations
            success &= self.migrate_prompt_versions_table(db_path, dry_run)
        elif 'shared.db' in db_path or 'query.db' in db_path:
            # Community database migrations
            success &= self.migrate_community_tables(db_path, dry_run)
        elif 'feedback.db' in db_path:
            # Feedback database migrations
            success &= self.migrate_feedback_table(db_path, dry_run)
        else:
            logger.warning(f"Unknown database type for {db_path}, attempting all migrations")
            # Try all migrations for unknown database types
            success &= self.migrate_users_table(db_path, dry_run)
            success &= self.migrate_user_logins_table(db_path, dry_run)
            success &= self.migrate_sessions_table(db_path, dry_run)
            success &= self.migrate_community_tables(db_path, dry_run)
            success &= self.migrate_feedback_table(db_path, dry_run)
            success &= self.migrate_prompt_versions_table(db_path, dry_run)
        
        # Validate foreign key constraints after migration
        if success and not dry_run:
            fk_valid = self.validate_foreign_keys(db_path, dry_run)
            if not fk_valid:
                logger.warning(f"Foreign key validation failed for {db_path}, but migration completed")
        
        # Perform comprehensive validation and auto-fixes if enabled
        if self.auto_fix and success:
            logger.info(f"Applying comprehensive validation and auto-fixes to {db_path}")
            success &= self.comprehensive_database_validation(db_path, dry_run)
            success &= self.create_missing_indexes(db_path, dry_run)
        
        if success:
            logger.info(f"Migration completed successfully for {db_path}")
        else:
            logger.error(f"Migration failed for {db_path}")
        
        return success
    
    def rebuild_database(self, db_path: str, dry_run: bool = False) -> bool:
        """Completely rebuild a database from scratch to match current schema."""
        logger.info(f"Rebuilding database from scratch: {db_path}")
        
        # Create backup of existing database if it exists
        if os.path.exists(db_path) and not dry_run:
            try:
                self.backup_database(db_path)
            except Exception as e:
                logger.error(f"Backup failed: {e}")
                if not self.force:
                    return False
        
        # Remove existing database file
        if os.path.exists(db_path) and not dry_run:
            logger.info(f"Removing existing database: {db_path}")
            os.remove(db_path)
        elif dry_run:
            logger.info(f"[DRY RUN] Would remove existing database: {db_path}")
        
        # Create new database file
        if not dry_run:
            logger.info(f"Creating new database: {db_path}")
            os.makedirs(os.path.dirname(db_path), exist_ok=True)
            with get_db_connection(db_path) as conn:
                conn.commit()
        
        # Run migration on the new database
        return self.migrate_database(db_path, dry_run)
    
    def rebuild_all_databases(self, dry_run: bool = False) -> bool:
        """Completely rebuild all databases from scratch."""
        logger.info("Rebuilding all databases from scratch")
        
        # Define database paths
        base_dir = os.path.dirname(__file__)
        databases = {
            'user': os.path.join(base_dir, 'database', 'user.db'),
            'prompt': os.path.join(base_dir, 'database', 'prompt_data.db'),
            'community': os.path.join(base_dir, 'database', 'community', 'shared.db'),
            'query': os.path.join(base_dir, 'database', 'community', 'query.db'),
            'feedback': os.path.join(base_dir, 'database', 'feedback.db')
        }
        
        success = True
        
        for db_name, db_path in databases.items():
            logger.info(f"Rebuilding {db_name} database: {db_path}")
            success &= self.rebuild_database(db_path, dry_run)
        
        return success
    
    def migrate_all_databases(self, dry_run: bool = False) -> bool:
        """Migrate all databases in the system."""
        logger.info("Starting migration of all databases")
        
        # Define database paths
        base_dir = os.path.dirname(__file__)
        databases = {
            'user': os.path.join(base_dir, 'database', 'user.db'),
            'prompt': os.path.join(base_dir, 'database', 'prompt_data.db'),
            'community': os.path.join(base_dir, 'database', 'community', 'shared.db'),
            'query': os.path.join(base_dir, 'database', 'community', 'query.db'),
            'feedback': os.path.join(base_dir, 'database', 'feedback.db')
        }
        
        success = True
        
        for db_name, db_path in databases.items():
            logger.info(f"Migrating {db_name} database: {db_path}")
            
            # Ensure directory exists
            os.makedirs(os.path.dirname(db_path), exist_ok=True)
            
            # Create empty database if it doesn't exist
            if not os.path.exists(db_path):
                logger.info(f"Creating new {db_name} database: {db_path}")
                if not dry_run:
                    with get_db_connection(db_path) as conn:
                        conn.commit()
            
            success &= self.migrate_database(db_path, dry_run)
        
        return success
    
    def fix_foreign_key_issues(self, dry_run: bool = False) -> bool:
        """Fix foreign key issues in all databases."""
        logger.info("Starting foreign key fix for all databases")
        
        # Define database paths
        base_dir = os.path.dirname(__file__)
        databases = {
            'user': os.path.join(base_dir, 'database', 'user.db'),
            'prompt': os.path.join(base_dir, 'database', 'prompt_data.db'),
            'community': os.path.join(base_dir, 'database', 'community', 'shared.db'),
            'query': os.path.join(base_dir, 'database', 'community', 'query.db'),
            'feedback': os.path.join(base_dir, 'database', 'feedback.db')
        }
        
        success = True
        
        for db_name, db_path in databases.items():
            if not os.path.exists(db_path):
                logger.info(f"Database {db_name} does not exist, skipping: {db_path}")
                continue
            
            logger.info(f"Fixing foreign keys for {db_name} database: {db_path}")
            
            # Create backup unless in dry run mode
            if not dry_run:
                try:
                    self.backup_database(db_path)
                except Exception as e:
                    logger.error(f"Backup failed: {e}")
                    if not self.force:
                        continue
            
            # Fix orphaned point transactions (only for user database)
            if 'user.db' in db_path:
                success &= self.fix_orphaned_point_transactions(db_path, dry_run)
            
            # Enable foreign key constraints
            success &= self.enable_foreign_keys(db_path, dry_run)
            
            # Validate foreign key constraints
            if success and not dry_run:
                fk_valid = self.validate_foreign_keys(db_path, dry_run)
                if not fk_valid:
                    logger.warning(f"Foreign key validation failed for {db_name} database")
        
        return success
    
    def print_summary(self):
        """Print migration summary."""
        print("\n" + "="*60)
        print("MIGRATION SUMMARY")
        print("="*60)
        
        if self.migrations_performed:
            print(f"Migrations performed: {len(self.migrations_performed)}")
            for migration in self.migrations_performed:
                print(f"  ✓ {migration}")
        else:
            print("No migrations were needed (databases are up to date)")
        
        if self.fixes_applied:
            print(f"\nAuto-fixes applied: {len(self.fixes_applied)}")
            for fix in self.fixes_applied:
                print(f"  🔧 {fix}")
        
        if self.backup_files:
            print(f"\nBackups created: {len(self.backup_files)}")
            for backup in self.backup_files:
                print(f"  📁 {backup}")
        
        print("="*60)


def main():
    """Main function to handle command line arguments and run migration."""
    parser = argparse.ArgumentParser(
        description="Safe Database Migration Utility for Prompt Sanctuary",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python safe_migration.py                    # Normal migration with backup
  python safe_migration.py --dry-run          # Show what would be changed
  python safe_migration.py --force            # Force migration even if backup fails
  python safe_migration.py --auto-fix         # Automatically fix data issues
  python safe_migration.py --reward-points    # Reward all users with 50 points
  python safe_migration.py --rebuild          # Completely rebuild all databases
  python safe_migration.py --rebuild --dry-run # Show what rebuild would do
  python safe_migration.py --fix-foreign-keys # Fix foreign key issues only
  python safe_migration.py --backup-dir ./my_backups  # Custom backup directory
        """
    )
    
    parser.add_argument(
        '--dry-run', 
        action='store_true',
        help='Show what would be changed without making actual changes'
    )
    
    parser.add_argument(
        '--force', 
        action='store_true',
        help='Force migration even if backup fails'
    )
    
    parser.add_argument(
        '--rebuild', 
        action='store_true',
        help='Completely rebuild all databases from scratch (destructive!)'
    )
    
    parser.add_argument(
        '--backup-dir', 
        default='./backups',
        help='Directory to store backups (default: ./backups)'
    )
    
    parser.add_argument(
        '--fix-foreign-keys', 
        action='store_true',
        help='Fix foreign key issues and enable constraints'
    )
    
    parser.add_argument(
        '--auto-fix', 
        action='store_true',
        help='Automatically fix data inconsistencies and missing data'
    )
    
    parser.add_argument(
        '--reward-points', 
        action='store_true',
        help='Reward all users with 50 never-expired points'
    )
    
    args = parser.parse_args()
    
    print("Prompt Sanctuary Database Migration Utility")
    print("=" * 50)
    
    if args.dry_run:
        print("🔍 DRY RUN MODE - No changes will be made")
        print()
    
    if args.force:
        print("⚠️  FORCE MODE - Migration will continue even if backup fails")
        print()
    
    if args.auto_fix:
        print("🔧 AUTO-FIX MODE - Will automatically fix data inconsistencies and missing data")
        print()
    
    if args.reward_points:
        print("🎁 REWARD POINTS MODE - Will reward all users with 50 never-expired points")
        print()
    
    if args.rebuild:
        print("🔥 REBUILD MODE - All databases will be completely rebuilt!")
        if not args.dry_run:
            print("⚠️  WARNING: This will delete all existing data!")
            response = input("Are you sure you want to continue? (yes/no): ")
            if response.lower() != 'yes':
                print("Rebuild cancelled.")
                sys.exit(0)
        print()
    
    print(f"Backup directory: {args.backup_dir}")
    print()
    
    # Create migrator instance
    migrator = DatabaseMigrator(backup_dir=args.backup_dir, force=args.force, auto_fix=args.auto_fix)
    
    try:
        # Run migration, rebuild, foreign key fix, auto-fix, or reward points
        if args.rebuild:
            success = migrator.rebuild_all_databases(dry_run=args.dry_run)
            operation = "rebuild"
        elif args.fix_foreign_keys:
            success = migrator.fix_foreign_key_issues(dry_run=args.dry_run)
            operation = "foreign key fix"
        elif args.auto_fix:
            success = migrator.auto_fix_all_databases(dry_run=args.dry_run)
            operation = "auto-fix"
        elif args.reward_points:
            success = migrator.reward_all_users_points(
                os.path.join(os.path.dirname(__file__), 'database', 'user.db'), 
                dry_run=args.dry_run
            )
            operation = "reward points"
        else:
            success = migrator.migrate_all_databases(dry_run=args.dry_run)
            operation = "migration"
        
        # Print summary
        migrator.print_summary()
        
        if success:
            if args.dry_run:
                print(f"\n✅ Dry run completed successfully!")
                print(f"Run without --dry-run to apply changes.")
            else:
                print(f"\n✅ {operation.title()} completed successfully!")
                if args.rebuild:
                    print("All databases have been rebuilt from scratch.")
                else:
                    print("Your databases are now up to date.")
        else:
            print(f"\n❌ {operation.title()} failed!")
            print("Check the log file 'migration.log' for details.")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n\n⚠️  Operation interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.exception(f"{operation.title()} failed with exception")
        print(f"\n❌ {operation.title()} failed: {e}")
        sys.exit(1)


def auto_migrate_all():
    """Automatically migrate all databases with auto-fix enabled."""
    print("Prompt Sanctuary - Automatic Database Migration")
    print("=" * 50)
    print("🔧 Running automatic migration with auto-fix enabled")
    print("This will migrate, update, and fix all databases automatically.")
    print()
    
    # Create migrator with auto-fix enabled
    migrator = DatabaseMigrator(backup_dir="./backups", force=False, auto_fix=True)
    
    try:
        # Run migration with auto-fix
        success = migrator.migrate_all_databases(dry_run=False)
        
        # Print summary
        migrator.print_summary()
        
        if success:
            print("\n✅ Automatic migration completed successfully!")
            print("All databases are now up to date and fixed.")
        else:
            print("\n❌ Automatic migration failed!")
            print("Check the log file 'migration.log' for details.")
            return False
            
    except KeyboardInterrupt:
        print("\n\n⚠️  Operation interrupted by user")
        return False
    except Exception as e:
        logger.exception("Automatic migration failed with exception")
        print(f"\n❌ Automatic migration failed: {e}")
        return False
    
    return True


if __name__ == "__main__":
    # If called directly without arguments, run auto-migration
    if len(sys.argv) == 1:
        auto_migrate_all()
    else:
        main()
