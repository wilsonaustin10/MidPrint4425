"""
API routes for task management.
"""
import logging
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, HTTPException, Depends, Query, BackgroundTasks, Path
from pydantic import BaseModel

from app.services.task_manager import task_manager, TaskStatus
from app.api.auth import get_api_key, get_authenticated_user, admin_role, user_role
from app.core.config import settings

# Set up logger
logger = logging.getLogger(__name__)

router = APIRouter()

# Define request and response models
class TaskResponse(BaseModel):
    task_id: str
    description: str
    status: str
    created_at: str
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    progress: Optional[float] = None
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    logs: List[Dict[str, Any]] = []

@router.get("/tasks", response_model=List[TaskResponse])
async def get_tasks(
    status: Optional[str] = None,
    limit: int = Query(100, gt=0, le=1000),
    skip: int = Query(0, ge=0),
    user: Dict[str, Any] = Depends(get_authenticated_user)
):
    """
    Get a list of tasks with optional filtering by status.
    
    Args:
        status: Filter tasks by status (PENDING, RUNNING, COMPLETED, FAILED, CANCELED)
        limit: Maximum number of tasks to return
        skip: Number of tasks to skip
        
    Returns:
        List of task objects
    """
    logger.debug(f"Getting tasks with status: {status}, limit: {limit}, skip: {skip}")
    
    # Get all tasks
    tasks = task_manager.get_all_tasks()
    
    # Filter by status if provided
    if status:
        try:
            task_status = TaskStatus[status.upper()]
            # Handle tasks being either dictionary or Task objects
            if tasks and isinstance(tasks[0], dict):
                tasks = [task for task in tasks if task["status"] == task_status]
            else:
                tasks = [task for task in tasks if task.status == task_status]
        except KeyError:
            valid_statuses = [s.name for s in TaskStatus]
            raise HTTPException(
                status_code=400,
                detail=f"Invalid status '{status}'. Valid statuses are: {', '.join(valid_statuses)}"
            )
    
    # Apply pagination
    tasks = tasks[skip:skip+limit]
    
    # Convert tasks to response model - handle Task objects or dictionaries
    return [TaskResponse(**task) if isinstance(task, dict) else TaskResponse(**task.to_dict()) for task in tasks]

@router.get("/tasks/{task_id}", response_model=TaskResponse)
async def get_task(
    task_id: str = Path(..., description="Task ID"),
    user: Dict[str, Any] = Depends(get_authenticated_user)
):
    """
    Get details of a specific task.
    
    Args:
        task_id: Task ID
        
    Returns:
        Task object
    """
    logger.debug(f"Getting task with ID: {task_id}")
    
    # Get task
    task = task_manager.get_task(task_id)
    
    # Check if task exists
    if not task:
        raise HTTPException(
            status_code=404,
            detail=f"Task with ID '{task_id}' not found"
        )
    
    # Convert task to response model, handling dict or Task object
    if isinstance(task, dict):
        return TaskResponse(**task)
    return TaskResponse(**task.to_dict())

@router.delete("/tasks/{task_id}")
async def cancel_task(
    task_id: str = Path(..., description="Task ID"),
    user: Dict[str, Any] = Depends(get_authenticated_user)
):
    """
    Cancel a specific task.
    
    Args:
        task_id: Task ID
        
    Returns:
        Success message
    """
    logger.debug(f"Cancelling task with ID: {task_id}")
    
    # Get task
    task = task_manager.get_task(task_id)
    
    # Check if task exists
    if not task:
        raise HTTPException(
            status_code=404,
            detail=f"Task with ID '{task_id}' not found"
        )
    
    # Check if task can be cancelled
    if task.status not in [TaskStatus.PENDING, TaskStatus.RUNNING]:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot cancel task with status '{task.status.name}'"
        )
    
    # Cancel task
    task_manager.cancel_task(task_id)
    
    return {"message": f"Task with ID '{task_id}' cancelled successfully"}

@router.delete("/tasks")
async def clear_tasks(
    status: Optional[str] = Query(None, description="Clear tasks with this status only"),
    user: Dict[str, Any] = Depends(get_authenticated_user)
):
    """
    Clear completed or failed tasks.
    
    Args:
        status: Clear tasks with this status only
        
    Returns:
        Success message with count of cleared tasks
    """
    logger.debug(f"Clearing tasks with status: {status}")
    
    # Parse status if provided
    task_status = None
    if status:
        try:
            task_status = TaskStatus[status.upper()]
        except KeyError:
            valid_statuses = [s.name for s in TaskStatus]
            raise HTTPException(
                status_code=400,
                detail=f"Invalid status '{status}'. Valid statuses are: {', '.join(valid_statuses)}"
            )
    
    # Clear tasks
    count = task_manager.clear_tasks(task_status)
    
    status_text = f"with status '{status}'" if status else ""
    return {"message": f"Cleared {count} tasks {status_text}"}

@router.get("/tasks/metrics")
async def get_task_metrics(
    user: Dict[str, Any] = Depends(get_authenticated_user)
):
    """
    Get metrics about tasks.
    
    Returns:
        Task metrics
    """
    logger.debug("Getting task metrics")
    
    # Get all tasks
    tasks = task_manager.get_all_tasks()
    
    # Calculate metrics
    metrics = {status.name: 0 for status in TaskStatus}
    for task in tasks:
        metrics[task.status.name] += 1
    
    metrics["TOTAL"] = len(tasks)
    
    return {"metrics": metrics} 