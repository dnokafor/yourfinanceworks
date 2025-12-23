"""
Tests for gamification caching layer.

Tests the Redis caching functionality for gamification data including:
- User profile caching
- Achievement caching
- Streak caching
- Challenge caching
- Health score caching
- Dashboard caching
- Leaderboard caching
"""

import pytest
import json
from datetime import datetime, timezone
from unittest.mock import Mock, patch, MagicMock
from core.services.gamification_cache import (
    GamificationCache,
    get_gamification_cache,
    cache_result
)


class TestGamificationCache:
    """Test suite for GamificationCache"""
    
    @pytest.fixture
    def mock_redis(self):
        """Create a mock Redis client"""
        return MagicMock()
    
    @pytest.fixture
    def cache(self, mock_redis):
        """Create a cache instance with mock Redis"""
        cache = GamificationCache(redis_client=mock_redis)
        return cache
    
    def test_cache_initialization(self, mock_redis):
        """Test cache initialization with provided Redis client"""
        cache = GamificationCache(redis_client=mock_redis)
        assert cache.redis == mock_redis
    
    def test_is_available_when_redis_connected(self, cache, mock_redis):
        """Test is_available returns True when Redis is connected"""
        mock_redis.ping.return_value = True
        assert cache.is_available() is True
    
    def test_is_available_when_redis_disconnected(self, cache, mock_redis):
        """Test is_available returns False when Redis is disconnected"""
        mock_redis.ping.side_effect = Exception("Connection failed")
        assert cache.is_available() is False
    
    def test_cache_user_profile(self, cache, mock_redis):
        """Test caching user profile"""
        user_id = 123
        profile_data = {
            "user_id": user_id,
            "level": 5,
            "total_xp": 1000,
            "achievements": []
        }
        
        result = cache.cache_user_profile(user_id, profile_data)
        
        assert result is True
        mock_redis.setex.assert_called_once()
        call_args = mock_redis.setex.call_args
        assert call_args[0][0] == f"gamif:profile:{user_id}"
        assert call_args[0][1] == cache.TTL_USER_PROFILE
    
    def test_get_cached_user_profile(self, cache, mock_redis):
        """Test retrieving cached user profile"""
        user_id = 123
        profile_data = {
            "user_id": user_id,
            "level": 5,
            "total_xp": 1000
        }
        
        mock_redis.get.return_value = json.dumps(profile_data)
        
        result = cache.get_cached_user_profile(user_id)
        
        assert result == profile_data
        mock_redis.get.assert_called_once_with(f"gamif:profile:{user_id}")
    
    def test_get_cached_user_profile_not_found(self, cache, mock_redis):
        """Test retrieving non-existent cached profile"""
        user_id = 123
        mock_redis.get.return_value = None
        
        result = cache.get_cached_user_profile(user_id)
        
        assert result is None
    
    def test_invalidate_user_profile(self, cache, mock_redis):
        """Test invalidating user profile cache"""
        user_id = 123
        
        result = cache.invalidate_user_profile(user_id)
        
        assert result is True
        mock_redis.delete.assert_called_once_with(f"gamif:profile:{user_id}")
    
    def test_cache_user_achievements(self, cache, mock_redis):
        """Test caching user achievements"""
        user_id = 123
        achievements = [
            {"id": "ach1", "name": "First Expense", "unlocked_at": "2024-01-01"},
            {"id": "ach2", "name": "Streak Master", "unlocked_at": "2024-01-02"}
        ]
        
        result = cache.cache_user_achievements(user_id, achievements)
        
        assert result is True
        mock_redis.setex.assert_called_once()
        call_args = mock_redis.setex.call_args
        assert call_args[0][0] == f"gamif:achievements:{user_id}"
    
    def test_cache_user_streaks(self, cache, mock_redis):
        """Test caching user streaks"""
        user_id = 123
        streaks = [
            {"habit_type": "daily_expense_tracking", "current_length": 7},
            {"habit_type": "weekly_budget_review", "current_length": 2}
        ]
        
        result = cache.cache_user_streaks(user_id, streaks)
        
        assert result is True
        mock_redis.setex.assert_called_once()
    
    def test_cache_health_score(self, cache, mock_redis):
        """Test caching financial health score"""
        user_id = 123
        score_data = {
            "overall": 75,
            "components": {
                "expense_tracking": 80,
                "budget_adherence": 70
            }
        }
        
        result = cache.cache_health_score(user_id, score_data)
        
        assert result is True
        mock_redis.setex.assert_called_once()
        call_args = mock_redis.setex.call_args
        assert call_args[0][0] == f"gamif:health:{user_id}"
    
    def test_cache_dashboard(self, cache, mock_redis):
        """Test caching complete dashboard"""
        user_id = 123
        dashboard_data = {
            "level": 5,
            "xp": 1000,
            "achievements": [],
            "streaks": [],
            "challenges": []
        }
        
        result = cache.cache_dashboard(user_id, dashboard_data)
        
        assert result is True
        mock_redis.setex.assert_called_once()
        call_args = mock_redis.setex.call_args
        assert call_args[0][0] == f"gamif:dashboard:{user_id}"
    
    def test_cache_leaderboard(self, cache, mock_redis):
        """Test caching leaderboard data"""
        org_id = 456
        leaderboard_data = [
            {"rank": 1, "user_id": 1, "xp": 5000},
            {"rank": 2, "user_id": 2, "xp": 4500}
        ]
        
        result = cache.cache_leaderboard(org_id, leaderboard_data)
        
        assert result is True
        mock_redis.setex.assert_called_once()
        call_args = mock_redis.setex.call_args
        assert call_args[0][0] == f"gamif:leaderboard:{org_id}"
    
    def test_cache_leaderboard_global(self, cache, mock_redis):
        """Test caching global leaderboard"""
        leaderboard_data = [
            {"rank": 1, "user_id": 1, "xp": 5000}
        ]
        
        result = cache.cache_leaderboard(None, leaderboard_data)
        
        assert result is True
        call_args = mock_redis.setex.call_args
        assert call_args[0][0] == "gamif:leaderboard:global"
    
    def test_invalidate_user_all_caches(self, cache, mock_redis):
        """Test invalidating all caches for a user"""
        user_id = 123
        
        result = cache.invalidate_user_all_caches(user_id)
        
        assert result is True
        # Should delete multiple keys
        assert mock_redis.delete.call_count >= 1
    
    def test_clear_all_caches(self, cache, mock_redis):
        """Test clearing all gamification caches"""
        mock_redis.keys.return_value = ["gamif:profile:1", "gamif:achievements:1"]
        
        result = cache.clear_all_caches()
        
        assert result is True
        mock_redis.keys.assert_called_once_with("gamif:*")
        mock_redis.delete.assert_called_once()
    
    def test_get_cache_stats(self, cache, mock_redis):
        """Test getting cache statistics"""
        mock_redis.info.return_value = {
            "used_memory_human": "10M",
            "connected_clients": 5,
            "uptime_in_seconds": 3600
        }
        mock_redis.keys.return_value = ["gamif:profile:1", "gamif:achievements:1"]
        
        stats = cache.get_cache_stats()
        
        assert stats["available"] is True
        assert stats["total_keys"] == 2
        assert stats["memory_used"] == "10M"
        assert stats["connected_clients"] == 5
    
    def test_cache_error_handling(self, cache, mock_redis):
        """Test cache handles errors gracefully"""
        user_id = 123
        profile_data = {"level": 5}
        
        mock_redis.setex.side_effect = Exception("Redis error")
        
        result = cache.cache_user_profile(user_id, profile_data)
        
        assert result is False
    
    def test_get_cached_error_handling(self, cache, mock_redis):
        """Test get_cached handles errors gracefully"""
        user_id = 123
        mock_redis.get.side_effect = Exception("Redis error")
        
        result = cache.get_cached_user_profile(user_id)
        
        assert result is None
    
    def test_cache_org_config(self, cache, mock_redis):
        """Test caching organization configuration"""
        org_id = 456
        config_data = {
            "custom_point_values": {"expense_tracking": 15},
            "enabled_features": ["points", "achievements"]
        }
        
        result = cache.cache_org_config(org_id, config_data)
        
        assert result is True
        call_args = mock_redis.setex.call_args
        assert call_args[0][0] == f"gamif:org_config:{org_id}"
        assert call_args[0][1] == cache.TTL_ORG_CONFIG
    
    def test_get_cached_org_config(self, cache, mock_redis):
        """Test retrieving cached organization configuration"""
        org_id = 456
        config_data = {
            "custom_point_values": {"expense_tracking": 15}
        }
        
        mock_redis.get.return_value = json.dumps(config_data)
        
        result = cache.get_cached_org_config(org_id)
        
        assert result == config_data
    
    def test_invalidate_org_config(self, cache, mock_redis):
        """Test invalidating organization configuration cache"""
        org_id = 456
        
        result = cache.invalidate_org_config(org_id)
        
        assert result is True
        mock_redis.delete.assert_called_once_with(f"gamif:org_config:{org_id}")


class TestCacheDecorator:
    """Test suite for cache_result decorator"""
    
    @pytest.mark.asyncio
    async def test_cache_result_decorator_async(self):
        """Test cache_result decorator with async function"""
        call_count = 0
        
        @cache_result("test_cache", ttl=300)
        async def test_function(user_id: int):
            nonlocal call_count
            call_count += 1
            return {"user_id": user_id, "data": "test"}
        
        # First call should execute function
        result1 = await test_function(123)
        assert result1["user_id"] == 123
        assert call_count == 1
    
    def test_cache_result_decorator_sync(self):
        """Test cache_result decorator with sync function"""
        call_count = 0
        
        @cache_result("test_cache", ttl=300)
        def test_function(user_id: int):
            nonlocal call_count
            call_count += 1
            return {"user_id": user_id, "data": "test"}
        
        # First call should execute function
        result1 = test_function(123)
        assert result1["user_id"] == 123
        assert call_count == 1


class TestCacheIntegration:
    """Integration tests for caching layer"""
    
    def test_cache_ttl_values(self):
        """Test that TTL values are reasonable"""
        cache = GamificationCache()
        
        # TTL values should be positive integers
        assert cache.TTL_USER_PROFILE > 0
        assert cache.TTL_ACHIEVEMENTS > 0
        assert cache.TTL_STREAKS > 0
        assert cache.TTL_CHALLENGES > 0
        assert cache.TTL_HEALTH_SCORE > 0
        assert cache.TTL_LEADERBOARD > 0
        assert cache.TTL_DASHBOARD > 0
        assert cache.TTL_ORG_CONFIG > 0
        
        # Longer TTL for less frequently changing data
        assert cache.TTL_ORG_CONFIG > cache.TTL_DASHBOARD
        assert cache.TTL_LEADERBOARD > cache.TTL_STREAKS
    
    def test_cache_key_prefixes_unique(self):
        """Test that cache key prefixes are unique"""
        cache = GamificationCache()
        
        prefixes = [
            cache.PREFIX_USER_PROFILE,
            cache.PREFIX_USER_ACHIEVEMENTS,
            cache.PREFIX_USER_STREAKS,
            cache.PREFIX_USER_CHALLENGES,
            cache.PREFIX_HEALTH_SCORE,
            cache.PREFIX_LEADERBOARD,
            cache.PREFIX_DASHBOARD,
            cache.PREFIX_POINT_HISTORY,
            cache.PREFIX_ORG_CONFIG,
            cache.PREFIX_CHALLENGE_PROGRESS
        ]
        
        # All prefixes should be unique
        assert len(prefixes) == len(set(prefixes))
        
        # All prefixes should start with "gamif:"
        for prefix in prefixes:
            assert prefix.startswith("gamif:")
