"""
Task manager service for handling and tracking asynchronous tasks.
"""
import asyncio
import logging
import time
import uuid
from enum import Enum
from typing import Dict, Any, List, Optional, Callable, Awaitable
from datetime import datetime

# Set up logger
logger = logging.getLogger(__name__)

class TaskStatus(str, Enum):
    """Enum for task status."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELED = "canceled"

class Task:
    """
    Represents an asynchronous task with status tracking and results.
    """
    
    def __init__(self, task_id: str, description: str):
        """
        Initialize a task.
        
        Args:
            task_id: Unique identifier for the task
            description: Human-readable description of the task
        """
        self.task_id = task_id
        self.description = description
        self.status = TaskStatus.PENDING
        self.created_at = datetime.now()
        self.started_at: Optional[datetime] = None
        self.completed_at: Optional[datetime] = None
        self.result: Dict[str, Any] = {}
        self.error: Optional[str] = None
        self.progress: float = 0.0
        self.logs: List[Dict[str, Any]] = []
        
        # For WebSocket notifications
        self.subscribers: List[str] = []
    
    def start(self) -> None:
        """Mark the task as running."""
        self.status = TaskStatus.RUNNING
        self.started_at = datetime.now()
        self.add_log("Task started")
    
    def complete(self, result: Dict[str, Any]) -> None:
        """
        Mark the task as completed with the given result.
        
        Args:
            result: Result data from the task
        """
        self.status = TaskStatus.COMPLETED
        self.completed_at = datetime.now()
        self.result = result
        self.progress = 100.0
        self.add_log("Task completed")
    
    def fail(self, error: str) -> None:
        """
        Mark the task as failed with the given error.
        
        Args:
            error: Error message
        """
        self.status = TaskStatus.FAILED
        self.completed_at = datetime.now()
        self.error = error
        self.add_log(f"Task failed: {error}")
    
    def cancel(self) -> None:
        """Mark the task as canceled."""
        self.status = TaskStatus.CANCELED
        self.completed_at = datetime.now()
        self.add_log("Task canceled")
    
    def update_progress(self, progress: float, message: Optional[str] = None) -> None:
        """
        Update the progress of the task.
        
        Args:
            progress: Progress percentage (0-100)
            message: Optional progress message
        """
        self.progress = min(max(progress, 0.0), 100.0)
        if message:
            self.add_log(message)
    
    def add_log(self, message: str) -> None:
        """
        Add a log message to the task.
        
        Args:
            message: Log message
        """
        self.logs.append({
            "timestamp": datetime.now().isoformat(),
            "message": message
        })
        logger.debug(f"Task {self.task_id}: {message}")
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the task to a dictionary.
        
        Returns:
            Dictionary representation of the task
        """
        return {
            "task_id": self.task_id,
            "description": self.description,
            "status": self.status,
            "created_at": self.created_at.isoformat(),
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "progress": self.progress,
            "result": self.result,
            "error": self.error,
            "logs": self.logs
        }

class TaskManager:
    """
    Manager for asynchronous tasks with status tracking and notification.
    """
    
    def __init__(self):
        """Initialize the task manager."""
        self.tasks: Dict[str, Task] = {}
        self.running_tasks: Dict[str, asyncio.Task] = {}
        self.task_notify_callbacks: Dict[str, List[Callable[[Dict[str, Any]], Awaitable[None]]]] = {}
        self.subscribers: Dict[str, Callable[[str, Dict[str, Any]], Awaitable[None]]] = {}
        logger.info("TaskManager initialized")
    
    def add_subscriber(self, key: str, callback: Callable[[str, Dict[str, Any]], Awaitable[None]]) -> None:
        """
        Add a subscriber to receive task updates.
        
        Args:
            key: Unique identifier for the subscriber
            callback: Callback function to call when a task is updated
        """
        logger.info(f"Adding subscriber '{key}' to TaskManager")
        self.subscribers[key] = callback
    
    def remove_subscriber(self, key: str) -> None:
        """
        Remove a subscriber.
        
        Args:
            key: Unique identifier for the subscriber
        """
        if key in self.subscribers:
            logger.info(f"Removing subscriber '{key}' from TaskManager")
            del self.subscribers[key]
    
    def create_task(self, description: str) -> str:
        """
        Create a new task.
        
        Args:
            description: Human-readable description of the task
            
        Returns:
            Task ID
        """
        task_id = str(uuid.uuid4())
        task = Task(task_id, description)
        self.tasks[task_id] = task
        logger.info(f"Created task {task_id}: {description}")
        return task_id
    
    def get_task(self, task_id: str) -> Optional[Task]:
        """
        Get a task by ID.
        
        Args:
            task_id: Task ID
            
        Returns:
            Task object or None if not found
        """
        return self.tasks.get(task_id)
    
    def get_all_tasks(self) -> List[Dict[str, Any]]:
        """
        Get all tasks.
        
        Returns:
            List of task dictionaries
        """
        return [task.to_dict() for task in self.tasks.values()]
    
    def cancel_task(self, task_id: str) -> bool:
        """
        Cancel a running task.
        
        Args:
            task_id: Task ID
            
        Returns:
            True if canceled successfully, False otherwise
        """
        task = self.tasks.get(task_id)
        if not task:
            return False
        
        running_task = self.running_tasks.get(task_id)
        if running_task and not running_task.done():
            running_task.cancel()
        
        task.cancel()
        if task_id in self.running_tasks:
            del self.running_tasks[task_id]
            
        # Notify subscribers of task update
        asyncio.create_task(self._notify_task_update(task_id))
        
        return True
    
    def clear_completed_tasks(self, max_age_seconds: int = 3600) -> int:
        """
        Clear completed, failed, or canceled tasks older than the specified age.
        
        Args:
            max_age_seconds: Maximum age in seconds (default: 1 hour)
            
        Returns:
            Number of tasks cleared
        """
        now = datetime.now()
        task_ids_to_remove = []
        
        for task_id, task in self.tasks.items():
            if task.status in (TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELED):
                if task.completed_at and (now - task.completed_at).total_seconds() > max_age_seconds:
                    task_ids_to_remove.append(task_id)
        
        for task_id in task_ids_to_remove:
            if task_id in self.running_tasks:
                del self.running_tasks[task_id]
            del self.tasks[task_id]
        
        logger.info(f"Cleared {len(task_ids_to_remove)} completed tasks")
        return len(task_ids_to_remove)
    
    async def run_task(self, task_id: str, coroutine: Awaitable[Dict[str, Any]]) -> None:
        """
        Run a coroutine as a tracked task.
        
        Args:
            task_id: Task ID
            coroutine: Coroutine to run
        """
        task = self.tasks.get(task_id)
        if not task:
            logger.error(f"Task {task_id} not found")
            return
        
        task.start()
        self._notify_task_update(task_id)
        
        try:
            # Create an asyncio task and store it
            running_task = asyncio.create_task(coroutine)
            self.running_tasks[task_id] = running_task
            
            # Wait for the task to complete
            result = await running_task
            
            # Mark as completed with the result
            task.complete(result)
        except asyncio.CancelledError:
            # Task was canceled
            task.cancel()
        except Exception as e:
            # Task failed with an error
            error_msg = str(e)
            logger.error(f"Task {task_id} failed: {error_msg}")
            task.fail(error_msg)
        finally:
            # Notify about the final state
            self._notify_task_update(task_id)
            
            # Clean up
            if task_id in self.running_tasks:
                del self.running_tasks[task_id]
    
    def subscribe_to_task(self, task_id: str, callback: Callable[[Dict[str, Any]], Awaitable[None]]) -> bool:
        """
        Subscribe to task updates.
        
        Args:
            task_id: Task ID
            callback: Async callback function to be called with task updates
            
        Returns:
            True if subscribed successfully, False otherwise
        """
        if task_id not in self.tasks:
            return False
        
        if task_id not in self.task_notify_callbacks:
            self.task_notify_callbacks[task_id] = []
        
        self.task_notify_callbacks[task_id].append(callback)
        return True
    
    def unsubscribe_from_task(self, task_id: str, callback: Callable[[Dict[str, Any]], Awaitable[None]]) -> bool:
        """
        Unsubscribe from task updates.
        
        Args:
            task_id: Task ID
            callback: Callback function to unsubscribe
            
        Returns:
            True if unsubscribed successfully, False otherwise
        """
        if task_id not in self.task_notify_callbacks:
            return False
        
        callbacks = self.task_notify_callbacks[task_id]
        if callback in callbacks:
            callbacks.remove(callback)
            if not callbacks:
                del self.task_notify_callbacks[task_id]
            return True
        
        return False
    
    async def _notify_task_update(self, task_id: str) -> None:
        """
        Notify subscribers of task updates.
        
        Args:
            task_id: Task ID
        """
        task = self.get_task(task_id)
        if not task:
            return
            
        # Notify standard subscribers
        for subscriber_key, subscriber_callback in self.subscribers.items():
            try:
                await subscriber_callback(task_id, task.to_dict())
            except Exception as e:
                logger.error(f"Error notifying subscriber '{subscriber_key}' about task {task_id}: {str(e)}")
        
        # Continue with existing notification code for task-specific subscribers
        task_subscribers = self.task_notify_callbacks.get(task_id, [])
        for callback in task_subscribers:
            try:
                await callback(task.to_dict())
            except Exception as e:
                logger.error(f"Error notifying task subscriber about task {task_id}: {str(e)}")

# Singleton instance
task_manager = TaskManager() 