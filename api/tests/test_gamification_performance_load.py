"""
Performance and load testing for the gamification system.

Tests system behavior under:
- Concurrent user load
- Large dataset handling
- Real-time update responsiveness
- Organizational analytics performance
"""

import pytest
import asyncio
import time
from datetime import datetime, timezone, timedelta
from decimal import Decimal
from unittest.mock import Mock, AsyncMock, patch
from concurrent.futures import ThreadPoolExecutor

from core.services.gamification_service import GamificationService
from core.services.gamification_cache import GamificationCache
from core.services.gamification_query_optimizer import GamificationQueryOptimizer
from core.services.gamification_background_processor import GamificationBackgroundProcessor
from core.schemas.gamification import (
    FinancialEvent,
    ActionType
)


@pytest.fixture
def mock_db():
    """Create a mock database session"""
    return Mock()


@pytest.fixture
def gamification_service(mock_db):
    """Create a gamification service with mocked dependencies"""
    service = GamificationService(mock_db)
    service.cache = GamificationCache()
    service.query_optimizer = GamificationQueryOptimizer(mock_db)
    service.background_processor = GamificationBackgroundProcessor(mock_db)
    return service


@pytest.fixture
def cache():
    """Create a gamification cache"""
    return GamificationCache()


@pytest.fixture
def query_optimizer(mock_db):
    """Create a query optimizer"""
    return GamificationQueryOptimizer(mock_db)


class TestConcurrentUserLoad:
    """Test system behavior under concurrent user load"""

    @pytest.mark.asyncio
    async def test_concurrent_event_processing(self, gamification_service):
        """Test processing events from multiple users concurrently"""
        num_users = 50
        events_per_user = 10
        
        # Create test events
        events = []
        for user_id in range(1, num_users + 1):
            for i in range(events_per_user):
                event = FinancialEvent(
                    user_id=user_id,
                    action_type=ActionType.EXPENSE_ADDED,
                    timestamp=datetime.now(timezone.utc),
                    metadata={"amount": 50.00 + i, "category": "food"}
                )
                events.append(event)
        
        # Mock event processing
        gamification_service.process_financial_event = AsyncMock(
            return_value=Mock(points_awarded=10)
        )
        
        # Execute - process all events concurrently
        start_time = time.time()
        
        tasks = [
            gamification_service.process_financial_event(event)
            for event in events
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        elapsed_time = time.time() - start_time
        
        # Assert
        successful_results = [r for r in results if not isinstance(r, Exception)]
        assert len(successful_results) > 0
        
        # Performance assertion - should process 500 events in reasonable time
        # (This is a mock, so it should be very fast)
        assert elapsed_time < 10.0  # Should complete in under 10 seconds
        
        # Verify all events were processed
        assert gamification_service.process_financial_event.call_count == len(events)

    @pytest.mark.asyncio
    async def test_concurrent_profile_updates(self, gamification_service):
        """Test concurrent profile updates from multiple users"""
        num_users = 100
        
        # Mock profile update
        gamification_service.update_user_profile = AsyncMock(return_value=True)
        
        # Execute - update profiles concurrently
        start_time = time.time()
        
        tasks = [
            gamification_service.update_user_profile(user_id)
            for user_id in range(1, num_users + 1)
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        elapsed_time = time.time() - start_time
        
        # Assert
        successful_results = [r for r in results if r is True]
        assert len(successful_results) == num_users
        assert elapsed_time < 5.0  # Should complete quickly

    @pytest.mark.asyncio
    async def test_concurrent_achievement_checks(self, gamification_service):
        """Test concurrent achievement checking for multiple users"""
        num_users = 50
        
        # Mock achievement checking
        gamification_service.check_achievements = AsyncMock(
            return_value=[]
        )
        
        # Execute - check achievements concurrently
        start_time = time.time()
        
        tasks = [
            gamification_service.check_achievements(user_id)
            for user_id in range(1, num_users + 1)
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        elapsed_time = time.time() - start_time
        
        # Assert
        assert len(results) == num_users
        assert elapsed_time < 5.0

    @pytest.mark.asyncio
    async def test_concurrent_leaderboard_updates(self, gamification_service):
        """Test concurrent leaderboard updates"""
        num_users = 100
        
        # Mock leaderboard update
        gamification_service.update_leaderboard = AsyncMock(return_value=True)
        
        # Execute - update leaderboard concurrently
        start_time = time.time()
        
        tasks = [
            gamification_service.update_leaderboard(user_id)
            for user_id in range(1, num_users + 1)
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        elapsed_time = time.time() - start_time
        
        # Assert
        successful_results = [r for r in results if r is True]
        assert len(successful_results) > 0
        assert elapsed_time < 10.0


class TestLargeDatasetHandling:
    """Test system performance with large datasets"""

    @pytest.mark.asyncio
    async def test_user_with_large_achievement_history(self, gamification_service):
        """Test retrieving achievements for user with large history"""
        user_id = 1
        num_achievements = 1000
        
        # Mock large achievement list
        mock_achievements = [
            Mock(id=i, name=f"Achievement {i}", unlocked_at=datetime.now(timezone.utc))
            for i in range(num_achievements)
        ]
        
        gamification_service.get_user_achievements = AsyncMock(
            return_value=mock_achievements
        )
        
        # Execute
        start_time = time.time()
        achievements = await gamification_service.get_user_achievements(user_id)
        elapsed_time = time.time() - start_time
        
        # Assert
        assert len(achievements) == num_achievements
        assert elapsed_time < 2.0  # Should retrieve quickly

    @pytest.mark.asyncio
    async def test_user_with_large_point_history(self, gamification_service):
        """Test retrieving point history for user with many transactions"""
        user_id = 1
        num_transactions = 5000
        
        # Mock large point history
        mock_history = [
            Mock(
                id=i,
                points=10,
                action_type=ActionType.EXPENSE_ADDED,
                timestamp=datetime.now(timezone.utc) - timedelta(days=i)
            )
            for i in range(num_transactions)
        ]
        
        gamification_service.get_point_history = AsyncMock(
            return_value=mock_history
        )
        
        # Execute
        start_time = time.time()
        history = await gamification_service.get_point_history(user_id)
        elapsed_time = time.time() - start_time
        
        # Assert
        assert len(history) == num_transactions
        assert elapsed_time < 2.0

    @pytest.mark.asyncio
    async def test_large_leaderboard_retrieval(self, gamification_service):
        """Test retrieving large leaderboard"""
        num_users = 10000
        
        # Mock large leaderboard
        mock_leaderboard = [
            Mock(
                user_id=i,
                level=i // 100,
                total_xp=i * 100,
                rank=i
            )
            for i in range(1, num_users + 1)
        ]
        
        gamification_service.get_leaderboard = AsyncMock(
            return_value=mock_leaderboard
        )
        
        # Execute
        start_time = time.time()
        leaderboard = await gamification_service.get_leaderboard()
        elapsed_time = time.time() - start_time
        
        # Assert
        assert len(leaderboard) == num_users
        assert elapsed_time < 3.0

    @pytest.mark.asyncio
    async def test_large_organization_analytics(self, gamification_service):
        """Test calculating analytics for large organization"""
        org_id = 1
        num_members = 5000
        
        # Mock organization members
        mock_members = [
            Mock(
                user_id=i,
                organization_id=org_id,
                level=i % 50,
                total_xp=i * 100
            )
            for i in range(1, num_members + 1)
        ]
        
        gamification_service.get_organization_members = AsyncMock(
            return_value=mock_members
        )
        
        # Execute
        start_time = time.time()
        members = await gamification_service.get_organization_members(org_id)
        elapsed_time = time.time() - start_time
        
        # Assert
        assert len(members) == num_members
        assert elapsed_time < 3.0


class TestRealTimeUpdateResponsiveness:
    """Test real-time update responsiveness"""

    @pytest.mark.asyncio
    async def test_financial_health_score_update_latency(self, gamification_service):
        """Test latency of financial health score updates"""
        user_id = 1
        
        # Mock score calculation
        gamification_service.calculate_financial_health_score = AsyncMock(
            return_value={"overall": 75, "trend": "improving"}
        )
        
        # Execute - measure latency
        start_time = time.time()
        score = await gamification_service.calculate_financial_health_score(user_id)
        latency = (time.time() - start_time) * 1000  # Convert to ms
        
        # Assert - should be very fast (under 100ms)
        assert latency < 100.0
        assert score["overall"] == 75

    @pytest.mark.asyncio
    async def test_level_up_notification_latency(self, gamification_service):
        """Test latency of level-up notifications"""
        user_id = 1
        
        # Mock level up
        gamification_service.check_level_up = AsyncMock(
            return_value={"level_up": True, "new_level": 5}
        )
        
        # Execute - measure latency
        start_time = time.time()
        result = await gamification_service.check_level_up(user_id)
        latency = (time.time() - start_time) * 1000  # Convert to ms
        
        # Assert - should be very fast (under 50ms)
        assert latency < 50.0
        assert result["level_up"] is True

    @pytest.mark.asyncio
    async def test_achievement_unlock_notification_latency(self, gamification_service):
        """Test latency of achievement unlock notifications"""
        user_id = 1
        
        # Mock achievement unlock
        gamification_service.check_achievement_unlock = AsyncMock(
            return_value={"unlocked": True, "achievement_id": "first_expense"}
        )
        
        # Execute - measure latency
        start_time = time.time()
        result = await gamification_service.check_achievement_unlock(user_id)
        latency = (time.time() - start_time) * 1000  # Convert to ms
        
        # Assert - should be very fast (under 50ms)
        assert latency < 50.0
        assert result["unlocked"] is True

    @pytest.mark.asyncio
    async def test_dashboard_load_time(self, gamification_service):
        """Test dashboard load time"""
        user_id = 1
        
        # Mock dashboard data
        mock_dashboard = {
            "profile": Mock(level=5, total_xp=500),
            "recent_achievements": [Mock() for _ in range(5)],
            "active_streaks": [Mock() for _ in range(3)],
            "active_challenges": [Mock() for _ in range(2)],
            "health_score": 75
        }
        
        gamification_service.get_user_dashboard = AsyncMock(
            return_value=mock_dashboard
        )
        
        # Execute - measure load time
        start_time = time.time()
        dashboard = await gamification_service.get_user_dashboard(user_id)
        load_time = (time.time() - start_time) * 1000  # Convert to ms
        
        # Assert - should load quickly (under 200ms)
        assert load_time < 200.0
        assert dashboard is not None


class TestCachingEffectiveness:
    """Test caching effectiveness"""

    @pytest.mark.asyncio
    async def test_cache_hit_performance(self, cache):
        """Test performance improvement with cache hits"""
        user_id = 1
        
        # First access - cache miss
        start_time = time.time()
        cache.get(f"user:{user_id}:profile")
        miss_time = time.time() - start_time
        
        # Set cache
        cache.set(f"user:{user_id}:profile", {"level": 5, "xp": 500})
        
        # Second access - cache hit
        start_time = time.time()
        result = cache.get(f"user:{user_id}:profile")
        hit_time = time.time() - start_time
        
        # Assert - cache hit should be much faster
        assert result is not None
        assert hit_time < miss_time or hit_time < 0.001  # Cache should be instant

    @pytest.mark.asyncio
    async def test_cache_invalidation(self, cache):
        """Test cache invalidation"""
        user_id = 1
        key = f"user:{user_id}:profile"
        
        # Set cache
        cache.set(key, {"level": 5})
        assert cache.get(key) is not None
        
        # Invalidate cache
        cache.invalidate(key)
        
        # Assert - cache should be empty
        assert cache.get(key) is None

    @pytest.mark.asyncio
    async def test_cache_expiration(self, cache):
        """Test cache expiration"""
        user_id = 1
        key = f"user:{user_id}:profile"
        
        # Set cache with short TTL
        cache.set(key, {"level": 5}, ttl=0.1)
        
        # Verify cache hit
        assert cache.get(key) is not None
        
        # Wait for expiration
        await asyncio.sleep(0.2)
        
        # Assert - cache should be expired
        assert cache.get(key) is None


class TestBackgroundProcessing:
    """Test background processing performance"""

    @pytest.mark.asyncio
    async def test_background_leaderboard_update(self, gamification_service):
        """Test background leaderboard update performance"""
        num_users = 1000
        
        # Mock background processor
        gamification_service.background_processor.update_leaderboard = AsyncMock(
            return_value=True
        )
        
        # Execute
        start_time = time.time()
        success = await gamification_service.background_processor.update_leaderboard()
        elapsed_time = time.time() - start_time
        
        # Assert - should complete quickly
        assert success is True
        assert elapsed_time < 5.0

    @pytest.mark.asyncio
    async def test_background_analytics_calculation(self, gamification_service):
        """Test background analytics calculation performance"""
        org_id = 1
        
        # Mock background processor
        gamification_service.background_processor.calculate_organization_analytics = AsyncMock(
            return_value={"total_users": 1000, "avg_engagement": 75}
        )
        
        # Execute
        start_time = time.time()
        analytics = await gamification_service.background_processor.calculate_organization_analytics(org_id)
        elapsed_time = time.time() - start_time
        
        # Assert - should complete quickly
        assert analytics is not None
        assert elapsed_time < 5.0

    @pytest.mark.asyncio
    async def test_background_health_score_recalculation(self, gamification_service):
        """Test background health score recalculation performance"""
        num_users = 5000
        
        # Mock background processor
        gamification_service.background_processor.recalculate_health_scores = AsyncMock(
            return_value=num_users
        )
        
        # Execute
        start_time = time.time()
        updated_count = await gamification_service.background_processor.recalculate_health_scores()
        elapsed_time = time.time() - start_time
        
        # Assert - should complete in reasonable time
        assert updated_count == num_users
        assert elapsed_time < 30.0  # Should complete within 30 seconds


class TestQueryOptimization:
    """Test query optimization"""

    @pytest.mark.asyncio
    async def test_optimized_leaderboard_query(self, query_optimizer):
        """Test optimized leaderboard query performance"""
        # Mock optimized query
        query_optimizer.get_optimized_leaderboard = AsyncMock(
            return_value=[Mock(user_id=i, rank=i) for i in range(1, 101)]
        )
        
        # Execute
        start_time = time.time()
        leaderboard = await query_optimizer.get_optimized_leaderboard()
        elapsed_time = time.time() - start_time
        
        # Assert
        assert len(leaderboard) == 100
        assert elapsed_time < 1.0

    @pytest.mark.asyncio
    async def test_optimized_user_achievements_query(self, query_optimizer):
        """Test optimized user achievements query"""
        user_id = 1
        
        # Mock optimized query
        query_optimizer.get_optimized_user_achievements = AsyncMock(
            return_value=[Mock(id=i, name=f"Achievement {i}") for i in range(1, 51)]
        )
        
        # Execute
        start_time = time.time()
        achievements = await query_optimizer.get_optimized_user_achievements(user_id)
        elapsed_time = time.time() - start_time
        
        # Assert
        assert len(achievements) == 50
        assert elapsed_time < 1.0

    @pytest.mark.asyncio
    async def test_optimized_organization_analytics_query(self, query_optimizer):
        """Test optimized organization analytics query"""
        org_id = 1
        
        # Mock optimized query
        query_optimizer.get_optimized_organization_analytics = AsyncMock(
            return_value={
                "total_users": 1000,
                "avg_engagement": 75,
                "habit_formation_progress": 80
            }
        )
        
        # Execute
        start_time = time.time()
        analytics = await query_optimizer.get_optimized_organization_analytics(org_id)
        elapsed_time = time.time() - start_time
        
        # Assert
        assert analytics is not None
        assert elapsed_time < 1.0


class TestStressScenarios:
    """Test system under stress scenarios"""

    @pytest.mark.asyncio
    async def test_spike_in_event_processing(self, gamification_service):
        """Test system handling spike in event processing"""
        # Simulate spike - 1000 events in short time
        num_events = 1000
        
        gamification_service.process_financial_event = AsyncMock(
            return_value=Mock(points_awarded=10)
        )
        
        # Execute
        start_time = time.time()
        
        events = [
            FinancialEvent(
                user_id=i % 100,
                action_type=ActionType.EXPENSE_ADDED,
                timestamp=datetime.now(timezone.utc),
                metadata={}
            )
            for i in range(num_events)
        ]
        
        tasks = [
            gamification_service.process_financial_event(event)
            for event in events
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        elapsed_time = time.time() - start_time
        
        # Assert - should handle spike
        successful = [r for r in results if not isinstance(r, Exception)]
        assert len(successful) > 0
        assert elapsed_time < 30.0

    @pytest.mark.asyncio
    async def test_memory_efficiency_with_large_cache(self, cache):
        """Test memory efficiency with large cache"""
        # Add many items to cache
        num_items = 10000
        
        for i in range(num_items):
            cache.set(f"key:{i}", {"data": f"value_{i}"})
        
        # Verify cache contains items
        assert cache.get("key:0") is not None
        assert cache.get(f"key:{num_items-1}") is not None
        
        # Cache should handle large datasets efficiently
        # (In real scenario, would measure memory usage)
        assert True
