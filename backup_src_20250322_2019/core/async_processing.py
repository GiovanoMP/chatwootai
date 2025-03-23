"""
Asynchronous processing system for the hub-and-spoke architecture.

This module implements a message queue system for asynchronous processing,
allowing the system to handle high volumes of messages efficiently.
"""

import logging
import asyncio
import json
import time
from typing import Dict, List, Any, Optional, Callable, Union
from enum import Enum
import redis
from redis import Redis

logger = logging.getLogger(__name__)


class TaskStatus(Enum):
    """Status of a task in the queue."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    RETRY = "retry"


class TaskPriority(Enum):
    """Priority of a task in the queue."""
    LOW = 0
    NORMAL = 1
    HIGH = 2
    URGENT = 3


class AsyncTaskProcessor:
    """Processor for asynchronous tasks using Redis as a message queue."""
    
    def __init__(self, 
                 redis_client: Redis,
                 queue_prefix: str = "async_task",
                 max_retries: int = 3,
                 retry_delay: int = 5):
        """
        Initialize the asynchronous task processor.
        
        Args:
            redis_client: Redis client instance
            queue_prefix: Prefix for Redis queue keys
            max_retries: Maximum number of retries for failed tasks
            retry_delay: Delay between retries in seconds
        """
        self.redis = redis_client
        self.queue_prefix = queue_prefix
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.handlers = {}
        self.running = False
    
    def register_handler(self, task_type: str, handler: Callable):
        """
        Register a handler for a task type.
        
        Args:
            task_type: Type of task
            handler: Handler function
        """
        self.handlers[task_type] = handler
    
    def enqueue_task(self, 
                    task_type: str,
                    payload: Dict[str, Any],
                    priority: Union[TaskPriority, int, str] = TaskPriority.NORMAL,
                    delay: int = 0) -> str:
        """
        Enqueue a task for asynchronous processing.
        
        Args:
            task_type: Type of task
            payload: Task payload
            priority: Priority of the task
            delay: Delay before processing in seconds
            
        Returns:
            Task ID
        """
        # Generate task ID
        task_id = f"{int(time.time())}-{task_type}-{id(payload)}"
        
        # Normalize priority
        if isinstance(priority, str):
            try:
                priority = TaskPriority[priority].value
            except KeyError:
                priority = TaskPriority.NORMAL.value
        elif isinstance(priority, TaskPriority):
            priority = priority.value
        
        # Create task
        task = {
            "id": task_id,
            "type": task_type,
            "payload": payload,
            "status": TaskStatus.PENDING.value,
            "priority": priority,
            "created_at": time.time(),
            "process_after": time.time() + delay,
            "attempts": 0,
            "last_error": None
        }
        
        # Store task in Redis
        self.redis.set(f"{self.queue_prefix}:task:{task_id}", json.dumps(task))
        
        # Add to priority queue
        self.redis.zadd(f"{self.queue_prefix}:queue", {task_id: priority})
        
        # Add to delayed queue if needed
        if delay > 0:
            self.redis.zadd(f"{self.queue_prefix}:delayed", {task_id: task["process_after"]})
        else:
            # Add to ready queue
            self.redis.lpush(f"{self.queue_prefix}:ready", task_id)
        
        return task_id
    
    def get_task_status(self, task_id: str) -> Dict[str, Any]:
        """
        Get the status of a task.
        
        Args:
            task_id: ID of the task
            
        Returns:
            Task status
        """
        task_json = self.redis.get(f"{self.queue_prefix}:task:{task_id}")
        
        if not task_json:
            return {"status": "not_found", "id": task_id}
        
        return json.loads(task_json)
    
    async def process_tasks(self):
        """Process tasks from the queue."""
        self.running = True
        
        while self.running:
            # Move ready delayed tasks
            await self._move_delayed_tasks()
            
            # Get a task from the ready queue
            task_id = self.redis.rpop(f"{self.queue_prefix}:ready")
            
            if not task_id:
                # No tasks, wait a bit
                await asyncio.sleep(0.1)
                continue
            
            # Get task details
            task_json = self.redis.get(f"{self.queue_prefix}:task:{task_id}")
            
            if not task_json:
                # Task not found, skip
                continue
            
            task = json.loads(task_json)
            
            # Update status
            task["status"] = TaskStatus.PROCESSING.value
            task["started_at"] = time.time()
            self.redis.set(f"{self.queue_prefix}:task:{task_id}", json.dumps(task))
            
            # Process the task
            try:
                handler = self.handlers.get(task["type"])
                
                if not handler:
                    logger.warning(f"No handler for task type: {task['type']}")
                    task["status"] = TaskStatus.FAILED.value
                    task["last_error"] = "No handler registered for this task type"
                else:
                    result = await self._call_handler(handler, task["payload"])
                    task["status"] = TaskStatus.COMPLETED.value
                    task["result"] = result
                    task["completed_at"] = time.time()
            
            except Exception as e:
                logger.error(f"Error processing task {task_id}: {e}")
                task["status"] = TaskStatus.FAILED.value
                task["last_error"] = str(e)
                
                # Retry if not exceeded max retries
                if task["attempts"] < self.max_retries:
                    task["status"] = TaskStatus.RETRY.value
                    task["attempts"] += 1
                    task["process_after"] = time.time() + self.retry_delay * task["attempts"]
                    
                    # Add to delayed queue
                    self.redis.zadd(f"{self.queue_prefix}:delayed", {task_id: task["process_after"]})
            
            # Update task in Redis
            self.redis.set(f"{self.queue_prefix}:task:{task_id}", json.dumps(task))
    
    async def _move_delayed_tasks(self):
        """Move delayed tasks that are ready to the ready queue."""
        now = time.time()
        
        # Get tasks that are ready
        ready_tasks = self.redis.zrangebyscore(
            f"{self.queue_prefix}:delayed",
            0,
            now
        )
        
        if not ready_tasks:
            return
        
        # Remove from delayed queue
        self.redis.zremrangebyscore(
            f"{self.queue_prefix}:delayed",
            0,
            now
        )
        
        # Add to ready queue
        self.redis.lpush(f"{self.queue_prefix}:ready", *ready_tasks)
    
    async def _call_handler(self, handler: Callable, payload: Dict[str, Any]) -> Any:
        """
        Call a handler function.
        
        Args:
            handler: Handler function
            payload: Task payload
            
        Returns:
            Result of the handler
        """
        if asyncio.iscoroutinefunction(handler):
            return await handler(payload)
        else:
            return handler(payload)
    
    def stop(self):
        """Stop processing tasks."""
        self.running = False


class NotificationSystem:
    """System for sending notifications about completed tasks."""
    
    def __init__(self, redis_client: Redis, queue_prefix: str = "async_task"):
        """
        Initialize the notification system.
        
        Args:
            redis_client: Redis client instance
            queue_prefix: Prefix for Redis queue keys
        """
        self.redis = redis_client
        self.queue_prefix = queue_prefix
        self.subscribers = {}
    
    def subscribe(self, task_id: str, callback: Callable):
        """
        Subscribe to notifications for a task.
        
        Args:
            task_id: ID of the task
            callback: Callback function
        """
        self.subscribers[task_id] = callback
    
    async def check_notifications(self):
        """Check for and send notifications about completed tasks."""
        for task_id, callback in list(self.subscribers.items()):
            task_json = self.redis.get(f"{self.queue_prefix}:task:{task_id}")
            
            if not task_json:
                # Task not found, remove subscriber
                self.subscribers.pop(task_id, None)
                continue
            
            task = json.loads(task_json)
            
            if task["status"] in [TaskStatus.COMPLETED.value, TaskStatus.FAILED.value]:
                # Task is done, notify subscriber
                try:
                    if asyncio.iscoroutinefunction(callback):
                        await callback(task)
                    else:
                        callback(task)
                except Exception as e:
                    logger.error(f"Error in notification callback for task {task_id}: {e}")
                
                # Remove subscriber
                self.subscribers.pop(task_id, None)


class MessageQueue:
    """Queue for processing messages asynchronously."""
    
    def __init__(self, async_processor: AsyncTaskProcessor):
        """
        Initialize the message queue.
        
        Args:
            async_processor: Asynchronous task processor
        """
        self.processor = async_processor
        
        # Register handlers
        self.processor.register_handler("process_message", self._process_message_handler)
    
    def enqueue_message(self, 
                       message: Dict[str, Any],
                       channel_type: str,
                       priority: Union[TaskPriority, int, str] = TaskPriority.NORMAL) -> str:
        """
        Enqueue a message for processing.
        
        Args:
            message: The message to process
            channel_type: Type of channel
            priority: Priority of the message
            
        Returns:
            Task ID
        """
        payload = {
            "message": message,
            "channel_type": channel_type
        }
        
        return self.processor.enqueue_task(
            task_type="process_message",
            payload=payload,
            priority=priority
        )
    
    async def _process_message_handler(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handler for processing messages.
        
        Args:
            payload: Task payload
            
        Returns:
            Result of processing
        """
        message = payload["message"]
        channel_type = payload["channel_type"]
        
        # This is a placeholder - in the actual implementation, we would
        # get the appropriate channel crew and process the message
        
        # Simulate processing
        await asyncio.sleep(0.5)
        
        return {
            "status": "processed",
            "channel_type": channel_type,
            "message_id": message.get("id")
        }
