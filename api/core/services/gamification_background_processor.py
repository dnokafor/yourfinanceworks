"""
Background processing service for gamification system.

This module handles asynchronous processing of complex gamification calculations
to avoid blocking the main request/response cycle. It uses Redis for task queuing
and manages:
- Leaderboard recalculation
- Financial health score updates
- Batch achievement checks
- Challenge progress aggregation
"""

import json
import logging
from typing import Optional, Dict, Any, List, Callable
from datetime import datetime, timezone, timedelta
from enum import Enum as PyEnum
import redis
from redis import Redis
import asyncio
from concurrent.futures import ThreadPoolExecutor

logger = logging.getLogger(__name__)


class BackgroundTaskType(str, PyEnum):
    """Types of background tasks"""
    RECALCULATE_LEADERBOARD = "recalculate_leaderboard"
    UPDATE_HEALTH_SCORES = "update_health_scores"
    CHECK_ACHIEVEMENTS = "check_achievements"
    AGGREGATE_CHALLENGE_PROGRESS = "aggregate_challenge_progress"
    PROCESS_STREAK_UPDATES = "process_streak_updates"
    GENERATE_RECOMMENDATIONS = "generate_recommendations"
    CLEANUP_EXPIRED_DATA = "cleanup_expired_data"


class BackgroundTask:
    """Represents a background task"""
    
    def __init__(
        self,
        task_type: BackgroundTaskType,
        user_id: Optional[int] = None,
        org_id: Optional[int] = None,
        data: Optional[Dict[str, Any]] = None,
        priority: int = 5
    ):
        self.task_type = task_type
        self.user_id = user_id
        self.org_id = org_id
        self.data = data or {}
        self.priority = priority  # 1-10, higher = more important
        self.created_at = datetime.now(timezone.utc)
        self.task_id = f"{task_type}:{user_id or org_id}:{self.created_at.timestamp()}"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert task to dictionary for serialization"""
        return {
            "task_id": self.task_id,
            "task_type": self.task_type.value,
            "user_id": self.user_id,
            "org_id": self.org_id,
            "data": self.data,
            "priority": self.priority,
            "created_at": self.created_at.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "BackgroundTask":
        """Create task from dictionary"""
        task = cls(
            task_type=BackgroundTaskType(data["task_type"]),
            user_id=data.get("user_id"),
            org_id=data.get("org_id"),
            data=data.get("data", {}),
            priority=data.get("priority", 5)
        )
        task.task_id = data.get("task_id", task.task_id)
        task.created_at = datetime.fromisoformat(data.get("created_at", task.created_at.isoformat()))
        return task


class GamificationBackgroundProcessor:
    """
    Manages background processing of gamification tasks.
    
    Uses Redis for task queuing and provides methods to:
    - Queue tasks for processing
    - Process tasks asynchronously
    - Track task status
    - Handle task failures and retries
    """
    
    # Queue names
    QUEUE_HIGH_PRIORITY = "gamif:queue:high"
    QUEUE_NORMAL_PRIORITY = "gamif:queue:normal"
    QUEUE_LOW_PRIORITY = "gamif:queue:low"
    
    # Status tracking
    PREFIX_TASK_STATUS = "gamif:task_status:"
    PREFIX_TASK_RESULT = "gamif:task_result:"
    
    # Configuration
    MAX_RETRIES = 3
    TASK_TIMEOUT = 300  # 5 minutes
    STATUS_TTL = 3600  # 1 hour
    
    def __init__(self, redis_client: Optional[Redis] = None):
        """
        Initialize the background processor.
        
        Args:
            redis_client: Redis client instance
        """
        self.redis = redis_client
        self._initialize_redis()
        self.task_handlers: Dict[BackgroundTaskType, Callable] = {}
        self._executor = ThreadPoolExecutor(max_workers=4)
    
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
                self.redis.ping()
                logger.info("Background processor Redis initialized successfully")
            except Exception as e:
                logger.warning(f"Failed to initialize Redis for background processor: {str(e)}")
                self.redis = None
    
    def is_available(self) -> bool:
        """Check if background processor is available"""
        if self.redis is None:
            return False
        try:
            self.redis.ping()
            return True
        except Exception:
            return False
    
    def register_task_handler(
        self,
        task_type: BackgroundTaskType,
        handler: Callable
    ) -> None:
        """
        Register a handler for a specific task type.
        
        Args:
            task_type: Type of task
            handler: Async function to handle the task
        """
        self.task_handlers[task_type] = handler
        logger.info(f"Registered handler for task type: {task_type.value}")
    
    def queue_task(self, task: BackgroundTask) -> bool:
        """
        Queue a background task for processing.
        
        Args:
            task: Task to queue
            
        Returns:
            True if queued successfully
        """
        if not self.is_available():
            logger.warning("Background processor not available, task not queued")
            return False
        
        try:
            # Determine queue based on priority
            if task.priority >= 8:
                queue = self.QUEUE_HIGH_PRIORITY
            elif task.priority >= 5:
                queue = self.QUEUE_NORMAL_PRIORITY
            else:
                queue = self.QUEUE_LOW_PRIORITY
            
            # Add task to queue
            task_data = json.dumps(task.to_dict())
            self.redis.rpush(queue, task_data)
            
            # Initialize task status
            status_key = f"{self.PREFIX_TASK_STATUS}{task.task_id}"
            self.redis.setex(
                status_key,
                self.STATUS_TTL,
                json.dumps({
                    "status": "queued",
                    "created_at": task.created_at.isoformat(),
                    "retries": 0
                })
            )
            
            logger.info(f"Queued task: {task.task_id} (priority: {task.priority})")
            return True
        except Exception as e:
            logger.error(f"Error queuing task: {str(e)}")
            return False
    
    def get_task_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """
        Get the status of a background task.
        
        Args:
            task_id: Task ID
            
        Returns:
            Task status or None if not found
        """
        if not self.is_available():
            return None
        
        try:
            status_key = f"{self.PREFIX_TASK_STATUS}{task_id}"
            status_data = self.redis.get(status_key)
            if status_data:
                return json.loads(status_data)
            return None
        except Exception as e:
            logger.error(f"Error getting task status: {str(e)}")
            return None
    
    def get_task_result(self, task_id: str) -> Optional[Dict[str, Any]]:
        """
        Get the result of a completed background task.
        
        Args:
            task_id: Task ID
            
        Returns:
            Task result or None if not found/not completed
        """
        if not self.is_available():
            return None
        
        try:
            result_key = f"{self.PREFIX_TASK_RESULT}{task_id}"
            result_data = self.redis.get(result_key)
            if result_data:
                return json.loads(result_data)
            return None
        except Exception as e:
            logger.error(f"Error getting task result: {str(e)}")
            return None
    
    async def process_queue(self) -> int:
        """
        Process tasks from the queue.
        
        Returns:
            Number of tasks processed
        """
        if not self.is_available():
            logger.warning("Background processor not available")
            return 0
        
        tasks_processed = 0
        
        # Process high priority queue first
        for queue in [self.QUEUE_HIGH_PRIORITY, self.QUEUE_NORMAL_PRIORITY, self.QUEUE_LOW_PRIORITY]:
            while True:
                try:
                    # Get next task from queue
                    task_data = self.redis.lpop(queue)
                    if not task_data:
                        break
                    
                    # Parse task
                    task_dict = json.loads(task_data)
                    task = BackgroundTask.from_dict(task_dict)
                    
                    # Process task
                    success = await self._process_task(task)
                    
                    if success:
                        tasks_processed += 1
                    else:
                        # Re-queue on failure (with retry limit)
                        await self._handle_task_failure(task)
                
                except Exception as e:
                    logger.error(f"Error processing queue: {str(e)}")
                    break
        
        return tasks_processed
    
    async def _process_task(self, task: BackgroundTask) -> bool:
        """
        Process a single background task.
        
        Args:
            task: Task to process
            
        Returns:
            True if processed successfully
        """
        try:
            # Update status to processing
            status_key = f"{self.PREFIX_TASK_STATUS}{task.task_id}"
            self.redis.setex(
                status_key,
                self.STATUS_TTL,
                json.dumps({
                    "status": "processing",
                    "started_at": datetime.now(timezone.utc).isoformat()
                })
            )
            
            # Get handler for this task type
            handler = self.task_handlers.get(task.task_type)
            if not handler:
                logger.warning(f"No handler registered for task type: {task.task_type.value}")
                return False
            
            # Execute handler
            result = await handler(task)
            
            # Store result
            result_key = f"{self.PREFIX_TASK_RESULT}{task.task_id}"
            self.redis.setex(
                result_key,
                self.STATUS_TTL,
                json.dumps(result, default=str)
            )
            
            # Update status to completed
            self.redis.setex(
                status_key,
                self.STATUS_TTL,
                json.dumps({
                    "status": "completed",
                    "completed_at": datetime.now(timezone.utc).isoformat()
                })
            )
            
            logger.info(f"Successfully processed task: {task.task_id}")
            return True
        
        except Exception as e:
            logger.error(f"Error processing task {task.task_id}: {str(e)}")
            
            # Update status to failed
            status_key = f"{self.PREFIX_TASK_STATUS}{task.task_id}"
            self.redis.setex(
                status_key,
                self.STATUS_TTL,
                json.dumps({
                    "status": "failed",
                    "error": str(e),
                    "failed_at": datetime.now(timezone.utc).isoformat()
                })
            )
            
            return False
    
    async def _handle_task_failure(self, task: BackgroundTask) -> None:
        """
        Handle task failure with retry logic.
        
        Args:
            task: Failed task
        """
        try:
            status_key = f"{self.PREFIX_TASK_STATUS}{task.task_id}"
            status_data = self.redis.get(status_key)
            
            if status_data:
                status = json.loads(status_data)
                retries = status.get("retries", 0)
                
                if retries < self.MAX_RETRIES:
                    # Re-queue task
                    task.data["retry_count"] = retries + 1
                    self.queue_task(task)
                    logger.info(f"Re-queued task {task.task_id} (retry {retries + 1}/{self.MAX_RETRIES})")
                else:
                    logger.error(f"Task {task.task_id} exceeded max retries")
        except Exception as e:
            logger.error(f"Error handling task failure: {str(e)}")
    
    def get_queue_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the task queues.
        
        Returns:
            Queue statistics
        """
        if not self.is_available():
            return {"available": False}
        
        try:
            high_priority_count = self.redis.llen(self.QUEUE_HIGH_PRIORITY)
            normal_priority_count = self.redis.llen(self.QUEUE_NORMAL_PRIORITY)
            low_priority_count = self.redis.llen(self.QUEUE_LOW_PRIORITY)
            
            return {
                "available": True,
                "high_priority_queue": high_priority_count,
                "normal_priority_queue": normal_priority_count,
                "low_priority_queue": low_priority_count,
                "total_queued": high_priority_count + normal_priority_count + low_priority_count
            }
        except Exception as e:
            logger.error(f"Error getting queue stats: {str(e)}")
            return {"available": False, "error": str(e)}
    
    def clear_queues(self) -> bool:
        """Clear all task queues (use with caution)"""
        if not self.is_available():
            return False
        
        try:
            self.redis.delete(
                self.QUEUE_HIGH_PRIORITY,
                self.QUEUE_NORMAL_PRIORITY,
                self.QUEUE_LOW_PRIORITY
            )
            logger.info("Cleared all task queues")
            return True
        except Exception as e:
            logger.error(f"Error clearing queues: {str(e)}")
            return False


# Global processor instance
_processor_instance: Optional[GamificationBackgroundProcessor] = None


def get_background_processor() -> GamificationBackgroundProcessor:
    """Get or create the global background processor instance"""
    global _processor_instance
    if _processor_instance is None:
        _processor_instance = GamificationBackgroundProcessor()
    return _processor_instance
