"""
Redis caching layer for gamification system.

This module provides caching functionality for frequently accessed gamification data
to improve performance and reduce database load. It handles:
- User profile caching
- Achievement data caching
- Leaderboard caching
- Challenge progress caching
- Financial health score caching
"""

import json
import logging
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone, timedelta
import redis
from redis import Redis
from functools import wraps
import asyncio

logger = logging.getLogger(__name__)


class GamificationCache:
    """
    Redis-based caching layer for gamification data.
    
    Provides methods to cache and retrieve frequently accessed gamification data
    with configurable TTL (time-to-live) for different data types.
    """
    
    # Cache key prefixes
    PREFIX_USER_PROFILE = "gamif:profile:"
    PREFIX_USER_ACHIEVEMENTS = "gamif:achievements:"
    PREFIX_USER_STREAKS = "gamif:streaks:"
    PREFIX_USER_CHALLENGES = "gamif:challenges:"
    PREFIX_HEALTH_SCORE = "gamif:health:"
    PREFIX_LEADERBOARD = "gamif:leaderboard:"
    PREFIX_DASHBOARD = "gamif:dashboard:"
    PREFIX_POINT_HISTORY = "gamif:points:"
    PREFIX_ORG_CONFIG = "gamif:org_config:"
    PREFIX_CHALLENGE_PROGRESS = "gamif:challenge_progress:"
    
    # Default TTL values (in seconds)
    TTL_USER_PROFILE = 300  # 5 minutes
    TTL_ACHIEVEMENTS = 600  # 10 minutes
    TTL_STREAKS = 300  # 5 minutes
    TTL_CHALLENGES = 300  # 5 minutes
    TTL_HEALTH_SCORE = 600  # 10 minutes
    TTL_LEADERBOARD = 1800  # 30 minutes
    TTL_DASHBOARD = 300  # 5 minutes
    TTL_POINT_HISTORY = 600  # 10 minutes
    TTL_ORG_CONFIG = 3600  # 1 hour
    TTL_CHALLENGE_PROGRESS = 300  # 5 minutes
    
    def __init__(self, redis_client: Optional[Redis] = None):
        """
        Initialize the caching layer.
        
        Args:
            redis_client: Redis client instance. If None, will attempt to connect to default Redis.
        """
        self.redis = redis_client
        self._initialize_redis()
    
    def _initialize_redis(self):
        """Initialize Redis connection if not provided"""
        if self.redis is None:
            try:
                self.redis = redis.from_url(
                    "redis://localhost:6379/0",
                    decode_responses=True,
                    socket_connect_timeout=5,
                    socket_keepalive=True
                )
                # Test connection
                self.redis.ping()
                logger.info("Redis cache initialized successfully")
            except Exception as e:
                logger.warning(f"Failed to initialize Redis cache: {str(e)}. Caching will be disabled.")
                self.redis = None
    
    def is_available(self) -> bool:
        """Check if Redis cache is available"""
        if self.redis is None:
            return False
        try:
            self.redis.ping()
            return True
        except Exception as e:
            logger.warning(f"Redis cache unavailable: {str(e)}")
            return False
    
    # User Profile Caching
    def cache_user_profile(self, user_id: int, profile_data: Dict[str, Any]) -> bool:
        """
        Cache user gamification profile.
        
        Args:
            user_id: User ID
            profile_data: Profile data to cache
            
        Returns:
            True if cached successfully, False otherwise
        """
        if not self.is_available():
            return False
        
        try:
            key = f"{self.PREFIX_USER_PROFILE}{user_id}"
            self.redis.setex(
                key,
                self.TTL_USER_PROFILE,
                json.dumps(profile_data, default=str)
            )
            return True
        except Exception as e:
            logger.error(f"Error caching user profile for user {user_id}: {str(e)}")
            return False
    
    def get_cached_user_profile(self, user_id: int) -> Optional[Dict[str, Any]]:
        """
        Retrieve cached user profile.
        
        Args:
            user_id: User ID
            
        Returns:
            Cached profile data or None if not found/expired
        """
        if not self.is_available():
            return None
        
        try:
            key = f"{self.PREFIX_USER_PROFILE}{user_id}"
            data = self.redis.get(key)
            if data:
                return json.loads(data)
            return None
        except Exception as e:
            logger.error(f"Error retrieving cached user profile for user {user_id}: {str(e)}")
            return None
    
    def invalidate_user_profile(self, user_id: int) -> bool:
        """
        Invalidate cached user profile.
        
        Args:
            user_id: User ID
            
        Returns:
            True if invalidated successfully
        """
        if not self.is_available():
            return False
        
        try:
            key = f"{self.PREFIX_USER_PROFILE}{user_id}"
            self.redis.delete(key)
            return True
        except Exception as e:
            logger.error(f"Error invalidating user profile cache for user {user_id}: {str(e)}")
            return False
    
    # Achievements Caching
    def cache_user_achievements(self, user_id: int, achievements: List[Dict[str, Any]]) -> bool:
        """
        Cache user achievements.
        
        Args:
            user_id: User ID
            achievements: List of achievement data
            
        Returns:
            True if cached successfully
        """
        if not self.is_available():
            return False
        
        try:
            key = f"{self.PREFIX_USER_ACHIEVEMENTS}{user_id}"
            self.redis.setex(
                key,
                self.TTL_ACHIEVEMENTS,
                json.dumps(achievements, default=str)
            )
            return True
        except Exception as e:
            logger.error(f"Error caching achievements for user {user_id}: {str(e)}")
            return False
    
    def get_cached_user_achievements(self, user_id: int) -> Optional[List[Dict[str, Any]]]:
        """
        Retrieve cached user achievements.
        
        Args:
            user_id: User ID
            
        Returns:
            Cached achievements or None if not found/expired
        """
        if not self.is_available():
            return None
        
        try:
            key = f"{self.PREFIX_USER_ACHIEVEMENTS}{user_id}"
            data = self.redis.get(key)
            if data:
                return json.loads(data)
            return None
        except Exception as e:
            logger.error(f"Error retrieving cached achievements for user {user_id}: {str(e)}")
            return None
    
    def invalidate_user_achievements(self, user_id: int) -> bool:
        """Invalidate cached achievements for a user"""
        if not self.is_available():
            return False
        
        try:
            key = f"{self.PREFIX_USER_ACHIEVEMENTS}{user_id}"
            self.redis.delete(key)
            return True
        except Exception as e:
            logger.error(f"Error invalidating achievements cache for user {user_id}: {str(e)}")
            return False
    
    # Streaks Caching
    def cache_user_streaks(self, user_id: int, streaks: List[Dict[str, Any]]) -> bool:
        """Cache user streaks"""
        if not self.is_available():
            return False
        
        try:
            key = f"{self.PREFIX_USER_STREAKS}{user_id}"
            self.redis.setex(
                key,
                self.TTL_STREAKS,
                json.dumps(streaks, default=str)
            )
            return True
        except Exception as e:
            logger.error(f"Error caching streaks for user {user_id}: {str(e)}")
            return False
    
    def get_cached_user_streaks(self, user_id: int) -> Optional[List[Dict[str, Any]]]:
        """Retrieve cached user streaks"""
        if not self.is_available():
            return None
        
        try:
            key = f"{self.PREFIX_USER_STREAKS}{user_id}"
            data = self.redis.get(key)
            if data:
                return json.loads(data)
            return None
        except Exception as e:
            logger.error(f"Error retrieving cached streaks for user {user_id}: {str(e)}")
            return None
    
    def invalidate_user_streaks(self, user_id: int) -> bool:
        """Invalidate cached streaks for a user"""
        if not self.is_available():
            return False
        
        try:
            key = f"{self.PREFIX_USER_STREAKS}{user_id}"
            self.redis.delete(key)
            return True
        except Exception as e:
            logger.error(f"Error invalidating streaks cache for user {user_id}: {str(e)}")
            return False
    
    # Challenges Caching
    def cache_user_challenges(self, user_id: int, challenges: List[Dict[str, Any]]) -> bool:
        """Cache user challenges"""
        if not self.is_available():
            return False
        
        try:
            key = f"{self.PREFIX_USER_CHALLENGES}{user_id}"
            self.redis.setex(
                key,
                self.TTL_CHALLENGES,
                json.dumps(challenges, default=str)
            )
            return True
        except Exception as e:
            logger.error(f"Error caching challenges for user {user_id}: {str(e)}")
            return False
    
    def get_cached_user_challenges(self, user_id: int) -> Optional[List[Dict[str, Any]]]:
        """Retrieve cached user challenges"""
        if not self.is_available():
            return None
        
        try:
            key = f"{self.PREFIX_USER_CHALLENGES}{user_id}"
            data = self.redis.get(key)
            if data:
                return json.loads(data)
            return None
        except Exception as e:
            logger.error(f"Error retrieving cached challenges for user {user_id}: {str(e)}")
            return None
    
    def invalidate_user_challenges(self, user_id: int) -> bool:
        """Invalidate cached challenges for a user"""
        if not self.is_available():
            return False
        
        try:
            key = f"{self.PREFIX_USER_CHALLENGES}{user_id}"
            self.redis.delete(key)
            return True
        except Exception as e:
            logger.error(f"Error invalidating challenges cache for user {user_id}: {str(e)}")
            return False
    
    # Financial Health Score Caching
    def cache_health_score(self, user_id: int, score_data: Dict[str, Any]) -> bool:
        """Cache financial health score"""
        if not self.is_available():
            return False
        
        try:
            key = f"{self.PREFIX_HEALTH_SCORE}{user_id}"
            self.redis.setex(
                key,
                self.TTL_HEALTH_SCORE,
                json.dumps(score_data, default=str)
            )
            return True
        except Exception as e:
            logger.error(f"Error caching health score for user {user_id}: {str(e)}")
            return False
    
    def get_cached_health_score(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Retrieve cached financial health score"""
        if not self.is_available():
            return None
        
        try:
            key = f"{self.PREFIX_HEALTH_SCORE}{user_id}"
            data = self.redis.get(key)
            if data:
                return json.loads(data)
            return None
        except Exception as e:
            logger.error(f"Error retrieving cached health score for user {user_id}: {str(e)}")
            return None
    
    def invalidate_health_score(self, user_id: int) -> bool:
        """Invalidate cached health score for a user"""
        if not self.is_available():
            return False
        
        try:
            key = f"{self.PREFIX_HEALTH_SCORE}{user_id}"
            self.redis.delete(key)
            return True
        except Exception as e:
            logger.error(f"Error invalidating health score cache for user {user_id}: {str(e)}")
            return False
    
    # Dashboard Caching
    def cache_dashboard(self, user_id: int, dashboard_data: Dict[str, Any]) -> bool:
        """Cache complete dashboard data"""
        if not self.is_available():
            return False
        
        try:
            key = f"{self.PREFIX_DASHBOARD}{user_id}"
            self.redis.setex(
                key,
                self.TTL_DASHBOARD,
                json.dumps(dashboard_data, default=str)
            )
            return True
        except Exception as e:
            logger.error(f"Error caching dashboard for user {user_id}: {str(e)}")
            return False
    
    def get_cached_dashboard(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Retrieve cached dashboard data"""
        if not self.is_available():
            return None
        
        try:
            key = f"{self.PREFIX_DASHBOARD}{user_id}"
            data = self.redis.get(key)
            if data:
                return json.loads(data)
            return None
        except Exception as e:
            logger.error(f"Error retrieving cached dashboard for user {user_id}: {str(e)}")
            return None
    
    def invalidate_dashboard(self, user_id: int) -> bool:
        """Invalidate cached dashboard for a user"""
        if not self.is_available():
            return False
        
        try:
            key = f"{self.PREFIX_DASHBOARD}{user_id}"
            self.redis.delete(key)
            return True
        except Exception as e:
            logger.error(f"Error invalidating dashboard cache for user {user_id}: {str(e)}")
            return False
    
    # Leaderboard Caching
    def cache_leaderboard(self, org_id: Optional[int], leaderboard_data: List[Dict[str, Any]]) -> bool:
        """Cache leaderboard data"""
        if not self.is_available():
            return False
        
        try:
            key = f"{self.PREFIX_LEADERBOARD}{org_id or 'global'}"
            self.redis.setex(
                key,
                self.TTL_LEADERBOARD,
                json.dumps(leaderboard_data, default=str)
            )
            return True
        except Exception as e:
            logger.error(f"Error caching leaderboard for org {org_id}: {str(e)}")
            return False
    
    def get_cached_leaderboard(self, org_id: Optional[int]) -> Optional[List[Dict[str, Any]]]:
        """Retrieve cached leaderboard data"""
        if not self.is_available():
            return None
        
        try:
            key = f"{self.PREFIX_LEADERBOARD}{org_id or 'global'}"
            data = self.redis.get(key)
            if data:
                return json.loads(data)
            return None
        except Exception as e:
            logger.error(f"Error retrieving cached leaderboard for org {org_id}: {str(e)}")
            return None
    
    def invalidate_leaderboard(self, org_id: Optional[int]) -> bool:
        """Invalidate cached leaderboard"""
        if not self.is_available():
            return False
        
        try:
            key = f"{self.PREFIX_LEADERBOARD}{org_id or 'global'}"
            self.redis.delete(key)
            return True
        except Exception as e:
            logger.error(f"Error invalidating leaderboard cache for org {org_id}: {str(e)}")
            return False
    
    # Organization Configuration Caching
    def cache_org_config(self, org_id: int, config_data: Dict[str, Any]) -> bool:
        """Cache organization gamification configuration"""
        if not self.is_available():
            return False
        
        try:
            key = f"{self.PREFIX_ORG_CONFIG}{org_id}"
            self.redis.setex(
                key,
                self.TTL_ORG_CONFIG,
                json.dumps(config_data, default=str)
            )
            return True
        except Exception as e:
            logger.error(f"Error caching org config for org {org_id}: {str(e)}")
            return False
    
    def get_cached_org_config(self, org_id: int) -> Optional[Dict[str, Any]]:
        """Retrieve cached organization configuration"""
        if not self.is_available():
            return None
        
        try:
            key = f"{self.PREFIX_ORG_CONFIG}{org_id}"
            data = self.redis.get(key)
            if data:
                return json.loads(data)
            return None
        except Exception as e:
            logger.error(f"Error retrieving cached org config for org {org_id}: {str(e)}")
            return None
    
    def invalidate_org_config(self, org_id: int) -> bool:
        """Invalidate cached organization configuration"""
        if not self.is_available():
            return False
        
        try:
            key = f"{self.PREFIX_ORG_CONFIG}{org_id}"
            self.redis.delete(key)
            return True
        except Exception as e:
            logger.error(f"Error invalidating org config cache for org {org_id}: {str(e)}")
            return False
    
    # Bulk Invalidation
    def invalidate_user_all_caches(self, user_id: int) -> bool:
        """Invalidate all caches for a specific user"""
        if not self.is_available():
            return False
        
        try:
            keys_to_delete = [
                f"{self.PREFIX_USER_PROFILE}{user_id}",
                f"{self.PREFIX_USER_ACHIEVEMENTS}{user_id}",
                f"{self.PREFIX_USER_STREAKS}{user_id}",
                f"{self.PREFIX_USER_CHALLENGES}{user_id}",
                f"{self.PREFIX_HEALTH_SCORE}{user_id}",
                f"{self.PREFIX_DASHBOARD}{user_id}",
                f"{self.PREFIX_POINT_HISTORY}{user_id}",
            ]
            
            for key in keys_to_delete:
                try:
                    self.redis.delete(key)
                except Exception as e:
                    logger.warning(f"Error deleting cache key {key}: {str(e)}")
            
            return True
        except Exception as e:
            logger.error(f"Error invalidating all caches for user {user_id}: {str(e)}")
            return False
    
    def clear_all_caches(self) -> bool:
        """Clear all gamification caches (use with caution)"""
        if not self.is_available():
            return False
        
        try:
            # Get all gamification-related keys
            pattern = "gamif:*"
            keys = self.redis.keys(pattern)
            
            if keys:
                self.redis.delete(*keys)
            
            logger.info(f"Cleared {len(keys)} gamification cache entries")
            return True
        except Exception as e:
            logger.error(f"Error clearing all caches: {str(e)}")
            return False
    
    # Cache Statistics
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        if not self.is_available():
            return {"available": False}
        
        try:
            info = self.redis.info()
            keys = self.redis.keys("gamif:*")
            
            return {
                "available": True,
                "total_keys": len(keys),
                "memory_used": info.get("used_memory_human", "N/A"),
                "connected_clients": info.get("connected_clients", 0),
                "uptime_seconds": info.get("uptime_in_seconds", 0),
                "gamification_keys": len(keys)
            }
        except Exception as e:
            logger.error(f"Error getting cache stats: {str(e)}")
            return {"available": False, "error": str(e)}


# Global cache instance
_cache_instance: Optional[GamificationCache] = None


def get_gamification_cache() -> GamificationCache:
    """Get or create the global gamification cache instance"""
    global _cache_instance
    if _cache_instance is None:
        _cache_instance = GamificationCache()
    return _cache_instance


def cache_result(cache_key_prefix: str, ttl: int = 300):
    """
    Decorator for caching function results.
    
    Args:
        cache_key_prefix: Prefix for the cache key
        ttl: Time-to-live in seconds
    """
    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            cache = get_gamification_cache()
            
            # Build cache key from function name and arguments
            cache_key = f"{cache_key_prefix}:{':'.join(str(arg) for arg in args)}"
            
            # Try to get from cache
            cached_result = cache.redis.get(cache_key) if cache.is_available() else None
            if cached_result:
                try:
                    return json.loads(cached_result)
                except Exception as e:
                    logger.warning(f"Error deserializing cached result: {str(e)}")
            
            # Call the actual function
            result = await func(*args, **kwargs)
            
            # Cache the result
            if cache.is_available():
                try:
                    cache.redis.setex(
                        cache_key,
                        ttl,
                        json.dumps(result, default=str)
                    )
                except Exception as e:
                    logger.warning(f"Error caching result: {str(e)}")
            
            return result
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            cache = get_gamification_cache()
            
            # Build cache key from function name and arguments
            cache_key = f"{cache_key_prefix}:{':'.join(str(arg) for arg in args)}"
            
            # Try to get from cache
            cached_result = cache.redis.get(cache_key) if cache.is_available() else None
            if cached_result:
                try:
                    return json.loads(cached_result)
                except Exception as e:
                    logger.warning(f"Error deserializing cached result: {str(e)}")
            
            # Call the actual function
            result = func(*args, **kwargs)
            
            # Cache the result
            if cache.is_available():
                try:
                    cache.redis.setex(
                        cache_key,
                        ttl,
                        json.dumps(result, default=str)
                    )
                except Exception as e:
                    logger.warning(f"Error caching result: {str(e)}")
            
            return result
        
        # Return appropriate wrapper based on whether function is async
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator
