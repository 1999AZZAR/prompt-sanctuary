"""
API Key Pool Management System

This module manages a pool of user-provided API keys that can be used by the system
to generate content for other users. It implements fair rotation and compensation.
"""

import time
import random
import logging
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


@dataclass
class ApiKeyInfo:
    """Information about an API key in the pool."""
    username: str
    api_key: str
    last_used: float
    usage_count: int
    total_compensation: float
    is_active: bool


class ApiKeyPool:
    """Manages a pool of user API keys with fair rotation and compensation."""
    
    def __init__(self, user_db_path: str):
        self.user_db_path = user_db_path
        self.api_keys: List[ApiKeyInfo] = []
        self.last_refresh = 0
        self.refresh_interval = 300  # Refresh every 5 minutes
        self.compensation_rate = 0.5  # 0.5 points per usage
        
        # Import here to avoid circular imports
        from models import get_db_connection
        
        self.get_db_connection = get_db_connection
        
    def _refresh_pool(self):
        """Refresh the API key pool from the database."""
        try:
            current_time = time.time()
            if current_time - self.last_refresh < self.refresh_interval:
                return  # Too soon to refresh
                
            logger.info("Refreshing API key pool")
            
            with self.get_db_connection(self.user_db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT username, gemini_api_key 
                    FROM users 
                    WHERE gemini_api_key IS NOT NULL 
                    AND gemini_api_key != '' 
                    AND api_key_validated = 1
                """)
                
                db_keys = cursor.fetchall()
                
                # Update existing keys and add new ones
                existing_usernames = {key.username for key in self.api_keys}
                db_usernames = {row[0] for row in db_keys}
                
                # Remove keys that are no longer in database
                self.api_keys = [key for key in self.api_keys if key.username in db_usernames]
                
                # Add or update keys from database
                for username, api_key in db_keys:
                    existing_key = next((k for k in self.api_keys if k.username == username), None)
                    if existing_key:
                        # Update existing key if it changed
                        if existing_key.api_key != api_key:
                            existing_key.api_key = api_key
                            existing_key.last_used = 0  # Reset usage tracking
                            logger.info(f"Updated API key for user {username}")
                    else:
                        # Add new key
                        new_key = ApiKeyInfo(
                            username=username,
                            api_key=api_key,
                            last_used=0,
                            usage_count=0,
                            total_compensation=0,
                            is_active=True
                        )
                        self.api_keys.append(new_key)
                        logger.info(f"Added new API key for user {username}")
                
                # Mark inactive keys
                for key in self.api_keys:
                    if key.username not in db_usernames:
                        key.is_active = False
                        logger.info(f"Marked API key inactive for user {key.username}")
                
                # Remove inactive keys older than 1 hour
                cutoff_time = current_time - 3600
                self.api_keys = [key for key in self.api_keys if key.is_active or key.last_used > cutoff_time]
                
                self.last_refresh = current_time
                logger.info(f"API key pool refreshed. Active keys: {len([k for k in self.api_keys if k.is_active])}")
                
        except Exception as e:
            logger.exception("Failed to refresh API key pool")
    
    def get_available_keys(self) -> List[ApiKeyInfo]:
        """Get all available API keys for system use."""
        self._refresh_pool()
        return [key for key in self.api_keys if key.is_active]
    
    def get_next_key(self, exclude_user: Optional[str] = None) -> Optional[ApiKeyInfo]:
        """Get the next API key to use, implementing fair rotation."""
        available_keys = self.get_available_keys()
        
        if not available_keys:
            logger.warning("No API keys available in pool")
            return None
        
        # Filter out the current user's key if specified
        if exclude_user:
            available_keys = [key for key in available_keys if key.username != exclude_user]
        
        if not available_keys:
            logger.info(f"No API keys available for user {exclude_user}")
            return None
        
        # Implement fair rotation based on least recently used
        # Sort by last_used time, then by usage_count for tie-breaking
        available_keys.sort(key=lambda k: (k.last_used, k.usage_count))
        
        selected_key = available_keys[0]
        
        # Update usage statistics
        current_time = time.time()
        selected_key.last_used = current_time
        selected_key.usage_count += 1
        
        logger.info(f"Selected API key for user {selected_key.username} (usage #{selected_key.usage_count})")
        return selected_key
    
    def award_compensation(self, username: str, amount: float = None):
        """Award compensation points to a user whose API key was used."""
        if amount is None:
            amount = self.compensation_rate
            
        try:
            from models import add_user_points_with_source
            add_user_points_with_source(self.user_db_path, username, amount, 'api_key_usage', f'Compensation for API key usage by system')
            
            # Update the key's compensation tracking
            key_info = next((k for k in self.api_keys if k.username == username), None)
            if key_info:
                key_info.total_compensation += amount
            
            logger.info(f"Awarded {amount} points compensation to {username}")
            
        except Exception as e:
            logger.exception(f"Failed to award compensation to {username}: {e}")
    
    def get_pool_stats(self) -> Dict:
        """Get statistics about the API key pool."""
        self._refresh_pool()
        
        active_keys = [key for key in self.api_keys if key.is_active]
        
        if not active_keys:
            return {
                "total_keys": 0,
                "active_keys": 0,
                "total_usage": 0,
                "total_compensation": 0,
                "average_usage": 0
            }
        
        total_usage = sum(key.usage_count for key in active_keys)
        total_compensation = sum(key.total_compensation for key in active_keys)
        
        return {
            "total_keys": len(self.api_keys),
            "active_keys": len(active_keys),
            "total_usage": total_usage,
            "total_compensation": total_compensation,
            "average_usage": total_usage / len(active_keys) if active_keys else 0,
            "keys": [
                {
                    "username": key.username,
                    "usage_count": key.usage_count,
                    "total_compensation": key.total_compensation,
                    "last_used": key.last_used,
                    "is_active": key.is_active
                }
                for key in active_keys
            ]
        }
    
    def get_user_stats(self, username: str) -> Dict:
        """Get statistics for a specific user's API key usage."""
        self._refresh_pool()
        
        key_info = next((k for k in self.api_keys if k.username == username), None)
        
        if not key_info:
            return {
                "has_key": False,
                "usage_count": 0,
                "total_compensation": 0,
                "last_used": None
            }
        
        return {
            "has_key": True,
            "usage_count": key_info.usage_count,
            "total_compensation": key_info.total_compensation,
            "last_used": key_info.last_used,
            "is_active": key_info.is_active
        }


# Global instance
_api_key_pool = None


def get_api_key_pool(user_db_path: str) -> ApiKeyPool:
    """Get the global API key pool instance."""
    global _api_key_pool
    if _api_key_pool is None or _api_key_pool.user_db_path != user_db_path:
        _api_key_pool = ApiKeyPool(user_db_path)
    return _api_key_pool


def use_system_api_key(user_db_path: str, exclude_user: Optional[str] = None) -> Tuple[Optional[str], Optional[str]]:
    """
    Get a system API key for use, excluding the specified user.
    
    Args:
        user_db_path: Path to the user database
        exclude_user: Username to exclude from API key selection
    
    Returns:
        Tuple of (api_key, username) or (None, None) if no key available
    """
    try:
        pool = get_api_key_pool(user_db_path)
        key_info = pool.get_next_key(exclude_user)
        
        if key_info:
            # Award compensation to the user
            pool.award_compensation(key_info.username)
            return key_info.api_key, key_info.username
        
        return None, None
        
    except Exception as e:
        logger.exception("Failed to get system API key")
        return None, None
