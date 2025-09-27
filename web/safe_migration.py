#!/usr/bin/env python3
"""
Safe Database Migration Utility for Prompt Sanctuary

This script safely migrates existing databases to the latest schema format.
It handles all new columns and ensures backward compatibility.

Usage:
    python safe_migration.py [--dry-run] [--force] [--backup-dir BACKUP_DIR]
    
Options:
    --dry-run      Show what would be changed without making actual changes
    --force        Force migration even if backup fails
    --backup-dir   Directory to store backups (default: ./backups)
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
    
    def __init__(self, backup_dir: str = "./backups", force: bool = False):
        self.backup_dir = Path(backup_dir)
        self.force = force
        self.migrations_performed = []
        self.backup_files = []
        
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
        """Migrate the users table to include new API key columns."""
        logger.info(f"Migrating users table in {db_path}")
        
        # Check if users table exists
        if not self.table_exists(db_path, 'users'):
            logger.info(f"Users table does not exist in {db_path} - skipping users table migration")
            return True  # This is not an error for databases that don't need users table
        
        try:
            # Add gemini_api_key column
            self.add_column_if_not_exists(
                db_path, 'users', 'gemini_api_key', 'TEXT', dry_run
            )
            
            # Add api_key_validated column
            self.add_column_if_not_exists(
                db_path, 'users', 'api_key_validated', 'INTEGER DEFAULT 0', dry_run
            )
            
            # Add email column if missing (for older databases)
            self.add_column_if_not_exists(
                db_path, 'users', 'email', 'TEXT', dry_run
            )
            
            # Add identicon_value column if missing
            self.add_column_if_not_exists(
                db_path, 'users', 'identicon_value', 'TEXT', dry_run
            )
            
            # Add points column if missing (shouldn't happen, but just in case)
            self.add_column_if_not_exists(
                db_path, 'users', 'points', 'REAL DEFAULT 80.0', dry_run
            )
            
            # Create unique index on email
            self.create_index_if_not_exists(
                db_path, 'idx_users_email_unique',
                'ON users(email) WHERE email IS NOT NULL', dry_run
            )
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to migrate users table: {e}")
            return False
    
    def migrate_achievements_table(self, db_path: str, dry_run: bool = False) -> bool:
        """Migrate the achievements table."""
        logger.info(f"Migrating achievements table in {db_path}")
        
        try:
            # Create achievements table
            achievements_table = """
            (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                description TEXT NOT NULL,
                icon TEXT NOT NULL,
                points_reward REAL NOT NULL,
                category TEXT NOT NULL,
                condition_type TEXT NOT NULL,
                condition_value INTEGER,
                hidden INTEGER DEFAULT 0
            )
            """
            
            self.create_table_if_not_exists(
                db_path, 'achievements', achievements_table, dry_run
            )
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to migrate achievements table: {e}")
            return False
    
    def migrate_user_achievements_table(self, db_path: str, dry_run: bool = False) -> bool:
        """Migrate the user_achievements table."""
        logger.info(f"Migrating user_achievements table in {db_path}")
        
        try:
            # Create user_achievements table
            user_achievements_table = """
            (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL,
                achievement_id INTEGER NOT NULL,
                unlocked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (achievement_id) REFERENCES achievements(id),
                UNIQUE(username, achievement_id)
            )
            """
            
            self.create_table_if_not_exists(
                db_path, 'user_achievements', user_achievements_table, dry_run
            )
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to migrate user_achievements table: {e}")
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
            # Create shared table if it doesn't exist
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
    
    def migrate_point_transactions_table(self, db_path: str, dry_run: bool = False) -> bool:
        """Migrate the point_transactions table."""
        logger.info(f"Migrating point_transactions table in {db_path}")
        
        # Only migrate this table in user database
        if 'user.db' not in db_path:
            logger.info(f"Skipping point_transactions table for non-user database: {db_path}")
            return True
        
        try:
            # Create point_transactions table
            point_transactions_table = """
            (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL,
                points REAL NOT NULL,
                source TEXT NOT NULL,
                description TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                expires_at TIMESTAMP,
                is_expired INTEGER DEFAULT 0,
                FOREIGN KEY (username) REFERENCES users(username)
            )
            """
            
            self.create_table_if_not_exists(
                db_path, 'point_transactions', point_transactions_table, dry_run
            )
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to migrate point_transactions table: {e}")
            return False
    
    def migrate_point_history_table(self, db_path: str, dry_run: bool = False) -> bool:
        """Migrate the point_history table."""
        logger.info(f"Migrating point_history table in {db_path}")
        
        # Only migrate this table in user database
        if 'user.db' not in db_path:
            logger.info(f"Skipping point_history table for non-user database: {db_path}")
            return True
        
        try:
            # Create point_history table
            point_history_table = """
            (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL,
                transaction_id INTEGER NOT NULL,
                action TEXT NOT NULL,
                points_before REAL NOT NULL,
                points_after REAL NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (username) REFERENCES users(username),
                FOREIGN KEY (transaction_id) REFERENCES point_transactions(id)
            )
            """
            
            self.create_table_if_not_exists(
                db_path, 'point_history', point_history_table, dry_run
            )
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to migrate point_history table: {e}")
            return False
    
    def migrate_database(self, db_path: str, dry_run: bool = False) -> bool:
        """Perform complete migration of a database."""
        logger.info(f"Starting migration of {db_path}")
        
        if not os.path.exists(db_path):
            logger.error(f"Database file does not exist: {db_path}")
            return False
        
        # Create backup unless in dry run mode
        if not dry_run:
            try:
                self.backup_database(db_path)
            except Exception as e:
                logger.error(f"Backup failed: {e}")
                if not self.force:
                    return False
        
        # Enable WAL mode
        if not dry_run:
            enable_wal_mode(db_path)
        
        success = True
        
        # Migrate all tables
        success &= self.migrate_users_table(db_path, dry_run)
        success &= self.migrate_achievements_table(db_path, dry_run)
        success &= self.migrate_user_achievements_table(db_path, dry_run)
        success &= self.migrate_user_logins_table(db_path, dry_run)
        success &= self.migrate_sessions_table(db_path, dry_run)
        success &= self.migrate_community_tables(db_path, dry_run)
        success &= self.migrate_feedback_table(db_path, dry_run)
        success &= self.migrate_prompt_versions_table(db_path, dry_run)
        success &= self.migrate_point_transactions_table(db_path, dry_run)
        success &= self.migrate_point_history_table(db_path, dry_run)
        
        if success:
            logger.info(f"Migration completed successfully for {db_path}")
        else:
            logger.error(f"Migration failed for {db_path}")
        
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
        '--backup-dir', 
        default='./backups',
        help='Directory to store backups (default: ./backups)'
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
    
    print(f"Backup directory: {args.backup_dir}")
    print()
    
    # Create migrator instance
    migrator = DatabaseMigrator(backup_dir=args.backup_dir, force=args.force)
    
    try:
        # Run migration
        success = migrator.migrate_all_databases(dry_run=args.dry_run)
        
        # Print summary
        migrator.print_summary()
        
        if success:
            if args.dry_run:
                print("\n✅ Dry run completed successfully!")
                print("Run without --dry-run to apply changes.")
            else:
                print("\n✅ Migration completed successfully!")
                print("Your databases are now up to date.")
        else:
            print("\n❌ Migration failed!")
            print("Check the log file 'migration.log' for details.")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n\n⚠️  Migration interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.exception("Migration failed with exception")
        print(f"\n❌ Migration failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
