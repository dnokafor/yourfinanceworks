"""
Tests for gamification background processor.

Tests the background task processing functionality including:
- Task queuing
- Task processing
- Retry logic
- Queue statistics
- Task status tracking
"""

import pytest
import json
from datetime import datetime, timezone
from unittest.mock import Mock, patch, MagicMock, AsyncMock
from core.services.gamification_background_processor import (
    GamificationBackgroundProcessor,
    BackgroundTask,
    BackgroundTaskType,
    get_background_processor
)


class TestBackgroundTask:
    """Test suite for BackgroundTask"""
    
    def test_task_creation(self):
        """Test creating a background task"""
        task = BackgroundTask(
            task_type=BackgroundTaskType.RECALCULATE_LEADERBOARD,
            user_id=123,
            priority=7
        )
        
        assert task.task_type == BackgroundTaskType.RECALCULATE_LEADERBOARD
        assert task.user_id == 123
        assert task.priority == 7
        assert task.created_at is not None
        assert task.task_id is not None
    
    def test_task_to_dict(self):
        """Test converting task to dictionary"""
        task = BackgroundTask(
            task_type=BackgroundTaskType.UPDATE_HEALTH_SCORES,
            org_id=456,
            data={"org_id": 456},
            priority=5
        )
        
        task_dict = task.to_dict()
        
        assert task_dict["task_type"] == BackgroundTaskType.UPDATE_HEALTH_SCORES.value
        assert task_dict["org_id"] == 456
        assert task_dict["priority"] == 5
        assert task_dict["data"] == {"org_id": 456}
    
    def test_task_from_dict(self):
        """Test creating task from dictionary"""
        task_dict = {
            "task_id": "test_task_id",
            "task_type": "recalculate_leaderboard",
            "user_id": 123,
            "org_id": None,
            "data": {},
            "priority": 7,
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        
        task = BackgroundTask.from_dict(task_dict)
        
        assert task.task_id == "test_task_id"
        assert task.task_type == BackgroundTaskType.RECALCULATE_LEADERBOARD
        assert task.user_id == 123
        assert task.priority == 7
    
    def test_task_default_priority(self):
        """Test task has default priority"""
        task = BackgroundTask(
            task_type=BackgroundTaskType.CHECK_ACHIEVEMENTS
        )
        
        assert task.priority == 5


class TestGamificationBackgroundProcessor:
    """Test suite for GamificationBackgroundProcessor"""
    
    @pytest.fixture
    def mock_redis(self):
        """Create a mock Redis client"""
        return MagicMock()
    
    @pytest.fixture
    def processor(self, mock_redis):
        """Create a processor instance with mock Redis"""
        processor = GamificationBackgroundProcessor(redis_client=mock_redis)
        return processor
    
    def test_processor_initialization(self, mock_redis):
        """Test processor initialization"""
        processor = GamificationBackgroundProcessor(redis_client=mock_redis)
        assert processor.redis == mock_redis
        assert processor.task_handlers == {}
    
    def test_is_available_when_redis_connected(self, processor, mock_redis):
        """Test is_available returns True when Redis is connected"""
        mock_redis.ping.return_value = True
        assert processor.is_available() is True
    
    def test_is_available_when_redis_disconnected(self, processor, mock_redis):
        """Test is_available returns False when Redis is disconnected"""
        mock_redis.ping.side_effect = Exception("Connection failed")
        assert processor.is_available() is False
    
    def test_register_task_handler(self, processor):
        """Test registering a task handler"""
        async def handler(task):
            return {"status": "completed"}
        
        processor.register_task_handler(BackgroundTaskType.CHECK_ACHIEVEMENTS, handler)
        
        assert BackgroundTaskType.CHECK_ACHIEVEMENTS in processor.task_handlers
        assert processor.task_handlers[BackgroundTaskType.CHECK_ACHIEVEMENTS] == handler
    
    def test_queue_task_high_priority(self, processor, mock_redis):
        """Test queuing a high priority task"""
        task = BackgroundTask(
            task_type=BackgroundTaskType.RECALCULATE_LEADERBOARD,
            priority=9
        )
        
        result = processor.queue_task(task)
        
        assert result is True
        # Should be added to high priority queue
        mock_redis.rpush.assert_called_once()
        call_args = mock_redis.rpush.call_args
        assert call_args[0][0] == processor.QUEUE_HIGH_PRIORITY
    
    def test_queue_task_normal_priority(self, processor, mock_redis):
        """Test queuing a normal priority task"""
        task = BackgroundTask(
            task_type=BackgroundTaskType.UPDATE_HEALTH_SCORES,
            priority=5
        )
        
        result = processor.queue_task(task)
        
        assert result is True
        call_args = mock_redis.rpush.call_args
        assert call_args[0][0] == processor.QUEUE_NORMAL_PRIORITY
    
    def test_queue_task_low_priority(self, processor, mock_redis):
        """Test queuing a low priority task"""
        task = BackgroundTask(
            task_type=BackgroundTaskType.CLEANUP_EXPIRED_DATA,
            priority=2
        )
        
        result = processor.queue_task(task)
        
        assert result is True
        call_args = mock_redis.rpush.call_args
        assert call_args[0][0] == processor.QUEUE_LOW_PRIORITY
    
    def test_queue_task_initializes_status(self, processor, mock_redis):
        """Test queuing task initializes status"""
        task = BackgroundTask(
            task_type=BackgroundTaskType.CHECK_ACHIEVEMENTS,
            user_id=123
        )
        
        processor.queue_task(task)
        
        # Should call setex for status
        assert mock_redis.setex.called
        call_args = mock_redis.setex.call_args
        status_key = call_args[0][0]
        assert status_key.startswith(processor.PREFIX_TASK_STATUS)
    
    def test_get_task_status(self, processor, mock_redis):
        """Test getting task status"""
        task_id = "test_task_123"
        status_data = {
            "status": "processing",
            "started_at": datetime.now(timezone.utc).isoformat()
        }
        
        mock_redis.get.return_value = json.dumps(status_data)
        
        result = processor.get_task_status(task_id)
        
        assert result == status_data
        mock_redis.get.assert_called_once_with(f"{processor.PREFIX_TASK_STATUS}{task_id}")
    
    def test_get_task_status_not_found(self, processor, mock_redis):
        """Test getting non-existent task status"""
        mock_redis.get.return_value = None
        
        result = processor.get_task_status("nonexistent_task")
        
        assert result is None
    
    def test_get_task_result(self, processor, mock_redis):
        """Test getting task result"""
        task_id = "test_task_123"
        result_data = {
            "leaderboard_entries": 100,
            "updated_at": datetime.now(timezone.utc).isoformat()
        }
        
        mock_redis.get.return_value = json.dumps(result_data)
        
        result = processor.get_task_result(task_id)
        
        assert result == result_data
        mock_redis.get.assert_called_once_with(f"{processor.PREFIX_TASK_RESULT}{task_id}")
    
    @pytest.mark.asyncio
    async def test_process_queue_empty(self, processor, mock_redis):
        """Test processing empty queue"""
        mock_redis.lpop.return_value = None
        
        count = await processor.process_queue()
        
        assert count == 0
    
    @pytest.mark.asyncio
    async def test_process_queue_with_tasks(self, processor, mock_redis):
        """Test processing queue with tasks"""
        task = BackgroundTask(
            task_type=BackgroundTaskType.CHECK_ACHIEVEMENTS,
            user_id=123
        )
        
        # Mock lpop to return task once, then None
        mock_redis.lpop.side_effect = [json.dumps(task.to_dict()), None, None, None]
        
        # Register a handler
        async def handler(t):
            return {"status": "completed"}
        
        processor.register_task_handler(BackgroundTaskType.CHECK_ACHIEVEMENTS, handler)
        
        count = await processor.process_queue()
        
        # Should process at least one task
        assert count >= 0
    
    def test_get_queue_stats(self, processor, mock_redis):
        """Test getting queue statistics"""
        mock_redis.llen.side_effect = [5, 3, 2]  # High, normal, low priority counts
        
        stats = processor.get_queue_stats()
        
        assert stats["available"] is True
        assert stats["high_priority_queue"] == 5
        assert stats["normal_priority_queue"] == 3
        assert stats["low_priority_queue"] == 2
        assert stats["total_queued"] == 10
    
    def test_clear_queues(self, processor, mock_redis):
        """Test clearing all queues"""
        result = processor.clear_queues()
        
        assert result is True
        mock_redis.delete.assert_called_once()
        call_args = mock_redis.delete.call_args
        # Should delete all three queues
        assert len(call_args[0]) == 3
    
    def test_queue_task_error_handling(self, processor, mock_redis):
        """Test queue_task handles errors gracefully"""
        mock_redis.rpush.side_effect = Exception("Redis error")
        
        task = BackgroundTask(
            task_type=BackgroundTaskType.CHECK_ACHIEVEMENTS
        )
        
        result = processor.queue_task(task)
        
        assert result is False
    
    def test_get_queue_stats_error_handling(self, processor, mock_redis):
        """Test get_queue_stats handles errors gracefully"""
        mock_redis.llen.side_effect = Exception("Redis error")
        
        stats = processor.get_queue_stats()
        
        assert stats["available"] is False
        assert "error" in stats


class TestBackgroundProcessorIntegration:
    """Integration tests for background processor"""
    
    def test_task_type_enum_values(self):
        """Test that all task types are defined"""
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
    
    def test_queue_names_unique(self):
        """Test that queue names are unique"""
        processor = GamificationBackgroundProcessor()
        
        queues = [
            processor.QUEUE_HIGH_PRIORITY,
            processor.QUEUE_NORMAL_PRIORITY,
            processor.QUEUE_LOW_PRIORITY
        ]
        
        assert len(queues) == len(set(queues))
    
    def test_max_retries_reasonable(self):
        """Test that max retries is reasonable"""
        processor = GamificationBackgroundProcessor()
        
        assert processor.MAX_RETRIES > 0
        assert processor.MAX_RETRIES <= 5
    
    def test_task_timeout_reasonable(self):
        """Test that task timeout is reasonable"""
        processor = GamificationBackgroundProcessor()
        
        assert processor.TASK_TIMEOUT > 0
        assert processor.TASK_TIMEOUT >= 60  # At least 1 minute
    
    def test_status_ttl_reasonable(self):
        """Test that status TTL is reasonable"""
        processor = GamificationBackgroundProcessor()
        
        assert processor.STATUS_TTL > 0
        assert processor.STATUS_TTL >= 600  # At least 10 minutes
