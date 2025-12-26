"""
Tests for gamification query optimizer.

Tests the optimized database query functionality including:
- Leaderboard queries
- Streak aggregation
- Challenge statistics
- Health score distribution
- Engagement metrics
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
from datetime import datetime, timezone, timedelta
from core.services.gamification_query_optimizer import (
    GamificationQueryOptimizer,
    get_query_optimizer
)


class TestGamificationQueryOptimizer:
    """Test suite for GamificationQueryOptimizer"""
    
    @pytest.fixture
    def mock_db(self):
        """Create a mock database session"""
        return MagicMock()
    
    @pytest.fixture
    def optimizer(self, mock_db):
        """Create an optimizer instance with mock database"""
        return GamificationQueryOptimizer(db=mock_db)
    
    def test_optimizer_initialization(self, mock_db):
        """Test optimizer initialization"""
        optimizer = GamificationQueryOptimizer(db=mock_db)
        assert optimizer.db == mock_db
    
    def test_get_global_leaderboard_basic(self, optimizer, mock_db):
        """Test getting global leaderboard"""
        # Mock query chain
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.join.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.offset.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = [
            (1, 5, 1000, 75.0, "user1@example.com"),
            (2, 4, 900, 70.0, "user2@example.com")
        ]
        
        result = optimizer.get_global_leaderboard(limit=10, offset=0)
        
        assert len(result) == 2
        assert result[0]["rank"] == 1
        assert result[0]["user_id"] == 1
        assert result[0]["level"] == 5
        assert result[0]["experience_points"] == 1000
    
    def test_get_global_leaderboard_with_stats(self, optimizer, mock_db):
        """Test getting global leaderboard with stats"""
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.join.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.offset.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = [
            (1, 5, 1000, 75.0, "user1@example.com")
        ]
        
        with patch.object(optimizer, '_get_user_stats', return_value={"active_streaks": 2}):
            result = optimizer.get_global_leaderboard(limit=10, include_stats=True)
        
        assert len(result) == 1
        assert "active_streaks" in result[0]
    
    def test_get_organization_leaderboard(self, optimizer, mock_db):
        """Test getting organization leaderboard"""
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.join.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.offset.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = [
            (1, 5, 1000, 75.0, "user1@example.com")
        ]
        
        result = optimizer.get_organization_leaderboard(org_id=456, limit=10)
        
        assert len(result) == 1
        assert result[0]["rank"] == 1
    
    def test_get_user_leaderboard_rank(self, optimizer, mock_db):
        """Test getting user's leaderboard rank"""
        # Mock user profile query
        mock_profile = MagicMock()
        mock_profile.user_id = 1
        mock_profile.level = 5
        mock_profile.total_experience_points = 1000
        mock_profile.financial_health_score = 75.0
        mock_profile.module_enabled = True
        
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = mock_profile
        
        # Mock rank query
        mock_rank_query = MagicMock()
        mock_db.query.return_value = mock_rank_query
        mock_rank_query.filter.return_value = mock_rank_query
        mock_rank_query.scalar.return_value = 5
        
        result = optimizer.get_user_leaderboard_rank(user_id=1)
        
        assert result is not None
        assert result["user_id"] == 1
        assert result["rank"] == 6  # 5 users ahead + 1
    
    def test_get_user_leaderboard_rank_disabled(self, optimizer, mock_db):
        """Test getting rank for user with disabled gamification"""
        mock_profile = MagicMock()
        mock_profile.module_enabled = False
        
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = mock_profile
        
        result = optimizer.get_user_leaderboard_rank(user_id=1)
        
        assert result is None
    
    def test_get_active_streaks_summary(self, optimizer, mock_db):
        """Test getting active streaks summary"""
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.join.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.group_by.return_value = mock_query
        
        # Mock streak data
        mock_habit_type = MagicMock()
        mock_habit_type.value = "daily_expense_tracking"
        
        mock_query.all.return_value = [
            (mock_habit_type, 50, 7.5, 30, 100)
        ]
        
        result = optimizer.get_active_streaks_summary()
        
        assert "daily_expense_tracking" in result
        assert result["daily_expense_tracking"]["active_users"] == 50
        assert result["daily_expense_tracking"]["average_length"] == 7.5
    
    def test_get_challenge_completion_stats(self, optimizer, mock_db):
        """Test getting challenge completion statistics"""
        # Mock challenge query
        mock_challenge = MagicMock()
        mock_challenge.id = 1
        mock_challenge.name = "Track All Expenses"
        
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.side_effect = [
            mock_challenge,  # Challenge query
            (100, 75, 85.0)  # Stats query (total, completed, avg_progress)
        ]
        
        result = optimizer.get_challenge_completion_stats(challenge_id=1)
        
        assert result["challenge_id"] == 1
        assert result["total_participants"] == 100
        assert result["completed"] == 75
        assert result["completion_rate"] == 75.0
    
    def test_get_health_score_distribution(self, optimizer, mock_db):
        """Test getting health score distribution"""
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = (1000, 72.5, 10.0, 100.0, 15.0)
        
        with patch.object(optimizer, '_get_score_distribution_buckets', return_value={
            "0-20": 10,
            "21-40": 50,
            "41-60": 200,
            "61-80": 500,
            "81-100": 240
        }):
            result = optimizer.get_health_score_distribution()
        
        assert result["total_users"] == 1000
        assert result["average_score"] == 72.5
        assert result["min_score"] == 10.0
        assert result["max_score"] == 100.0
        assert "distribution_buckets" in result
    
    def test_get_score_distribution_buckets(self, optimizer, mock_db):
        """Test getting score distribution buckets"""
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.scalar.side_effect = [10, 50, 200, 500, 240]
        
        result = optimizer._get_score_distribution_buckets()
        
        assert result["0-20"] == 10
        assert result["21-40"] == 50
        assert result["41-60"] == 200
        assert result["61-80"] == 500
        assert result["81-100"] == 240
    
    def test_get_user_stats(self, optimizer, mock_db):
        """Test getting user statistics"""
        mock_profile = MagicMock()
        mock_profile.id = 1
        
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = mock_profile
        
        # Mock streak count query
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.scalar.side_effect = [2, 5]  # active_streaks, achievements
        
        result = optimizer._get_user_stats(user_id=1)
        
        assert result["active_streaks"] == 2
        assert result["achievements_unlocked"] == 5
    
    def test_get_engagement_metrics(self, optimizer, mock_db):
        """Test getting engagement metrics"""
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = (500, 2000, 50000)  # active_users, total_actions, total_points
        
        result = optimizer.get_engagement_metrics(days=30)
        
        assert result["period_days"] == 30
        assert result["active_users"] == 500
        assert result["total_actions"] == 2000
        assert result["total_points_awarded"] == 50000
        assert result["average_points_per_action"] == 25.0
        assert result["average_actions_per_user"] == 4.0
    
    def test_get_engagement_metrics_with_org(self, optimizer, mock_db):
        """Test getting engagement metrics for organization"""
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.join.return_value = mock_query
        mock_query.first.return_value = (100, 500, 10000)
        
        result = optimizer.get_engagement_metrics(org_id=456, days=30)
        
        assert result["active_users"] == 100
        assert result["total_actions"] == 500
    
    def test_error_handling_leaderboard(self, optimizer, mock_db):
        """Test error handling in leaderboard query"""
        mock_db.query.side_effect = Exception("Database error")
        
        result = optimizer.get_global_leaderboard()
        
        assert result == []
    
    def test_error_handling_streaks(self, optimizer, mock_db):
        """Test error handling in streaks query"""
        mock_db.query.side_effect = Exception("Database error")
        
        result = optimizer.get_active_streaks_summary()
        
        assert result == {}
    
    def test_error_handling_challenge_stats(self, optimizer, mock_db):
        """Test error handling in challenge stats query"""
        mock_db.query.side_effect = Exception("Database error")
        
        result = optimizer.get_challenge_completion_stats(challenge_id=1)
        
        assert result == {}
    
    def test_error_handling_health_distribution(self, optimizer, mock_db):
        """Test error handling in health distribution query"""
        mock_db.query.side_effect = Exception("Database error")
        
        result = optimizer.get_health_score_distribution()
        
        assert result == {}


class TestQueryOptimizerIntegration:
    """Integration tests for query optimizer"""
    
    def test_get_query_optimizer(self):
        """Test getting query optimizer instance"""
        mock_db = MagicMock()
        optimizer = get_query_optimizer(mock_db)
        
        assert isinstance(optimizer, GamificationQueryOptimizer)
        assert optimizer.db == mock_db
    
    def test_leaderboard_pagination(self):
        """Test leaderboard pagination logic"""
        mock_db = MagicMock()
        optimizer = GamificationQueryOptimizer(db=mock_db)
        
        # Verify pagination parameters are used
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.join.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.offset.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = []
        
        optimizer.get_global_leaderboard(limit=50, offset=100)
        
        # Verify offset and limit were called
        mock_query.offset.assert_called_with(100)
        mock_query.limit.assert_called_with(50)
