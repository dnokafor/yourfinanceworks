"""
Unit tests for gamification caching layer (without app initialization).

Tests the Redis caching functionality for gamification data.
"""

import pytest
import json
from datetime import datetime, timezone
from unittest.mock import Mock, MagicMock
import sys
import os

# Add api directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def test_cache_key_prefixes():
    """Test that cache key prefixes are properly defined"""
    from core.services.gamification_cache import GamificationCache
    
    cache = GamificationCache(redis_client=MagicMock())
    
    # Verify all prefixes exist and are unique
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
    
    # All should be unique
    assert len(prefixes) == len(set(prefixes))
    
    # All should start with gamif:
    for prefix in prefixes:
        assert prefix.startswith("gamif:")


def test_cache_ttl_values():
    """Test that TTL values are reasonable"""
    from core.services.gamification_cache import GamificationCache
    
    cache = GamificationCache(redis_client=MagicMock())
    
    # All TTL values should be positive
    ttl_values = [
        cache.TTL_USER_PROFILE,
        cache.TTL_ACHIEVEMENTS,
        cache.TTL_STREAKS,
        cache.TTL_CHALLENGES,
        cache.TTL_HEALTH_SCORE,
        cache.TTL_LEADERBOARD,
        cache.TTL_DASHBOARD,
        cache.TTL_POINT_HISTORY,
        cache.TTL_ORG_CONFIG,
        cache.TTL_CHALLENGE_PROGRESS
    ]
    
    for ttl in ttl_values:
        assert ttl > 0
    
    # Org config should have longer TTL than dashboard
    assert cache.TTL_ORG_CONFIG > cache.TTL_DASHBOARD


def test_cache_initialization_with_mock_redis():
    """Test cache initialization with mock Redis"""
    from core.services.gamification_cache import GamificationCache
    
    mock_redis = MagicMock()
    cache = GamificationCache(redis_client=mock_redis)
    
    assert cache.redis == mock_redis


def test_cache_is_available_check():
    """Test is_available method"""
    from core.services.gamification_cache import GamificationCache
    
    mock_redis = MagicMock()
    mock_redis.ping.return_value = True
    
    cache = GamificationCache(redis_client=mock_redis)
    
    assert cache.is_available() is True
    mock_redis.ping.assert_called()


def test_cache_user_profile_success():
    """Test successful user profile caching"""
    from core.services.gamification_cache import GamificationCache
    
    mock_redis = MagicMock()
    cache = GamificationCache(redis_client=mock_redis)
    
    user_id = 123
    profile_data = {
        "user_id": user_id,
        "level": 5,
        "total_xp": 1000
    }
    
    result = cache.cache_user_profile(user_id, profile_data)
    
    assert result is True
    mock_redis.setex.assert_called_once()
    
    # Verify the call arguments
    call_args = mock_redis.setex.call_args
    assert call_args[0][0] == f"gamif:profile:{user_id}"
    assert call_args[0][1] == cache.TTL_USER_PROFILE


def test_cache_user_profile_error_handling():
    """Test error handling in cache_user_profile"""
    from core.services.gamification_cache import GamificationCache
    
    mock_redis = MagicMock()
    mock_redis.setex.side_effect = Exception("Redis error")
    
    cache = GamificationCache(redis_client=mock_redis)
    
    result = cache.cache_user_profile(123, {"level": 5})
    
    assert result is False


def test_get_cached_user_profile_success():
    """Test successful retrieval of cached profile"""
    from core.services.gamification_cache import GamificationCache
    
    mock_redis = MagicMock()
    profile_data = {"user_id": 123, "level": 5}
    mock_redis.get.return_value = json.dumps(profile_data)
    
    cache = GamificationCache(redis_client=mock_redis)
    
    result = cache.get_cached_user_profile(123)
    
    assert result == profile_data


def test_get_cached_user_profile_not_found():
    """Test retrieval when profile not in cache"""
    from core.services.gamification_cache import GamificationCache
    
    mock_redis = MagicMock()
    mock_redis.get.return_value = None
    
    cache = GamificationCache(redis_client=mock_redis)
    
    result = cache.get_cached_user_profile(123)
    
    assert result is None


def test_invalidate_user_profile():
    """Test invalidating user profile cache"""
    from core.services.gamification_cache import GamificationCache
    
    mock_redis = MagicMock()
    cache = GamificationCache(redis_client=mock_redis)
    
    result = cache.invalidate_user_profile(123)
    
    assert result is True
    mock_redis.delete.assert_called_once_with("gamif:profile:123")


def test_cache_achievements():
    """Test caching achievements"""
    from core.services.gamification_cache import GamificationCache
    
    mock_redis = MagicMock()
    cache = GamificationCache(redis_client=mock_redis)
    
    user_id = 123
    achievements = [
        {"id": "ach1", "name": "First Expense"},
        {"id": "ach2", "name": "Streak Master"}
    ]
    
    result = cache.cache_user_achievements(user_id, achievements)
    
    assert result is True
    mock_redis.setex.assert_called_once()


def test_cache_health_score():
    """Test caching financial health score"""
    from core.services.gamification_cache import GamificationCache
    
    mock_redis = MagicMock()
    cache = GamificationCache(redis_client=mock_redis)
    
    user_id = 123
    score_data = {"overall": 75, "components": {}}
    
    result = cache.cache_health_score(user_id, score_data)
    
    assert result is True
    call_args = mock_redis.setex.call_args
    assert call_args[0][0] == f"gamif:health:{user_id}"


def test_cache_leaderboard_with_org():
    """Test caching organization leaderboard"""
    from core.services.gamification_cache import GamificationCache
    
    mock_redis = MagicMock()
    cache = GamificationCache(redis_client=mock_redis)
    
    org_id = 456
    leaderboard = [{"rank": 1, "user_id": 1, "xp": 5000}]
    
    result = cache.cache_leaderboard(org_id, leaderboard)
    
    assert result is True
    call_args = mock_redis.setex.call_args
    assert call_args[0][0] == f"gamif:leaderboard:{org_id}"


def test_cache_leaderboard_global():
    """Test caching global leaderboard"""
    from core.services.gamification_cache import GamificationCache
    
    mock_redis = MagicMock()
    cache = GamificationCache(redis_client=mock_redis)
    
    leaderboard = [{"rank": 1, "user_id": 1, "xp": 5000}]
    
    result = cache.cache_leaderboard(None, leaderboard)
    
    assert result is True
    call_args = mock_redis.setex.call_args
    assert call_args[0][0] == "gamif:leaderboard:global"


def test_invalidate_user_all_caches():
    """Test invalidating all caches for a user"""
    from core.services.gamification_cache import GamificationCache
    
    mock_redis = MagicMock()
    cache = GamificationCache(redis_client=mock_redis)
    
    result = cache.invalidate_user_all_caches(123)
    
    assert result is True
    # Should delete multiple keys
    assert mock_redis.delete.call_count >= 1


def test_clear_all_caches():
    """Test clearing all gamification caches"""
    from core.services.gamification_cache import GamificationCache
    
    mock_redis = MagicMock()
    mock_redis.keys.return_value = ["gamif:profile:1", "gamif:achievements:1"]
    
    cache = GamificationCache(redis_client=mock_redis)
    
    result = cache.clear_all_caches()
    
    assert result is True
    mock_redis.keys.assert_called_once_with("gamif:*")


def test_get_cache_stats():
    """Test getting cache statistics"""
    from core.services.gamification_cache import GamificationCache
    
    mock_redis = MagicMock()
    mock_redis.info.return_value = {
        "used_memory_human": "10M",
        "connected_clients": 5,
        "uptime_in_seconds": 3600
    }
    mock_redis.keys.return_value = ["gamif:profile:1"]
    
    cache = GamificationCache(redis_client=mock_redis)
    
    stats = cache.get_cache_stats()
    
    assert stats["available"] is True
    assert stats["total_keys"] == 1
    assert stats["memory_used"] == "10M"


def test_background_processor_task_types():
    """Test background processor task types"""
    from core.services.gamification_background_processor import BackgroundTaskType
    
    task_types = [
        BackgroundTaskType.RECALCULATE_LEADERBOARD,
        BackgroundTaskType.UPDATE_HEALTH_SCORES,
        BackgroundTaskType.CHECK_ACHIEVEMENTS,
        BackgroundTaskType.AGGREGATE_CHALLENGE_PROGRESS,
        BackgroundTaskType.PROCESS_STREAK_UPDATES,
        BackgroundTaskType.GENERATE_RECOMMENDATIONS,
        BackgroundTaskType.CLEANUP_EXPIRED_DATA
    ]
    
    assert len(task_types) == 7


def test_background_task_creation():
    """Test creating a background task"""
    from core.services.gamification_background_processor import BackgroundTask, BackgroundTaskType
    
    task = BackgroundTask(
        task_type=BackgroundTaskType.CHECK_ACHIEVEMENTS,
        user_id=123,
        priority=7
    )
    
    assert task.task_type == BackgroundTaskType.CHECK_ACHIEVEMENTS
    assert task.user_id == 123
    assert task.priority == 7
    assert task.task_id is not None


def test_background_task_to_dict():
    """Test converting task to dictionary"""
    from core.services.gamification_background_processor import BackgroundTask, BackgroundTaskType
    
    task = BackgroundTask(
        task_type=BackgroundTaskType.UPDATE_HEALTH_SCORES,
        org_id=456,
        priority=5
    )
    
    task_dict = task.to_dict()
    
    assert task_dict["task_type"] == "update_health_scores"
    assert task_dict["org_id"] == 456
    assert task_dict["priority"] == 5


def test_background_processor_queue_names():
    """Test background processor queue names are unique"""
    from core.services.gamification_background_processor import GamificationBackgroundProcessor
    
    processor = GamificationBackgroundProcessor(redis_client=MagicMock())
    
    queues = [
        processor.QUEUE_HIGH_PRIORITY,
        processor.QUEUE_NORMAL_PRIORITY,
        processor.QUEUE_LOW_PRIORITY
    ]
    
    assert len(queues) == len(set(queues))


def test_query_optimizer_initialization():
    """Test query optimizer initialization"""
    from core.services.gamification_query_optimizer import GamificationQueryOptimizer
    
    mock_db = MagicMock()
    optimizer = GamificationQueryOptimizer(db=mock_db)
    
    assert optimizer.db == mock_db


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
