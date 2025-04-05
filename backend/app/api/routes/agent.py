"""
API routes for agent browser automation.
"""
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
import logging
import asyncio
import uuid

from app.agent.service import agent_service
from app.services.task_manager import task_manager, Task, TaskStatus
from app.api.auth import get_api_key, get_authenticated_user
from app.core.config import settings
from app.browser.browser import browser_manager

# Setup logging
logger = logging.getLogger(__name__)

router = APIRouter()

# Request/Response models
class InitializeRequest(BaseModel):
    """Initialize agent request"""
    pass  # No parameters needed for initialization

class NavigateRequest(BaseModel):
    """Navigate to URL request"""
    url: str = Field(..., description="URL to navigate to")

class ClickElementRequest(BaseModel):
    """Click element request"""
    selector: str = Field(..., description="CSS selector of element to click")
    index: int = Field(0, description="Index if multiple elements match (0-based)")
    timeout: int = Field(10000, description="Timeout in milliseconds")

class InputTextRequest(BaseModel):
    """Input text request"""
    selector: str = Field(..., description="CSS selector of input element")
    text: str = Field(..., description="Text to input")
    delay: int = Field(50, description="Delay between keypresses in milliseconds")

class GetDOMRequest(BaseModel):
    """Get DOM request"""
    include_state: bool = Field(True, description="Include page state in response")

class CaptureScreenshotRequest(BaseModel):
    """Capture screenshot request"""
    full_page: bool = Field(True, description="Capture full page or just viewport")

class WaitRequest(BaseModel):
    """Wait request"""
    time: int = Field(..., description="Time to wait in milliseconds")

class ActionSequenceItem(BaseModel):
    """A single action in an action sequence"""
    name: str = Field(..., description="Action name")
    params: Dict[str, Any] = Field(default_factory=dict, description="Action parameters")

class ActionSequenceRequest(BaseModel):
    """Execute multiple actions in sequence"""
    actions: List[ActionSequenceItem] = Field(..., description="List of actions to execute")

class NaturalLanguageTaskRequest(BaseModel):
    """Execute a task described in natural language"""
    task: str = Field(..., description="Natural language description of the task to execute")
    include_raw_response: bool = Field(False, description="Include raw LLM response in the result")
    enable_multi_step: bool = Field(True, description="Enable multi-step task planning for complex tasks")

class AgentResponse(BaseModel):
    """Base response model for agent actions"""
    status: str
    message: Optional[str] = None

class TaskResponse(BaseModel):
    """Response model for tasks"""
    task_id: str

class TaskPlanResponse(BaseModel):
    """Response model for task plans"""
    active: bool = Field(..., description="Whether a task plan is currently active")
    status: str = Field(..., description="Current status of the task plan")
    original_task: Optional[str] = Field(None, description="The original task description")
    total_steps: int = Field(0, description="Total number of steps in the plan")
    current_step: int = Field(-1, description="Index of the current step")
    completed_steps: int = Field(0, description="Number of completed steps")
    steps: List[str] = Field([], description="List of step descriptions")

# Helper function to run agent actions as background tasks
async def run_agent_action(task_id: str, action_name: str, action_func, *args, **kwargs):
    """
    Execute an agent action as a background task and update task status.
    
    Args:
        task_id: Task ID
        action_name: Name of the action being executed
        action_func: Async function to execute
        args: Positional arguments for the function
        kwargs: Keyword arguments for the function
    """
    try:
        # Get the task
        task = task_manager.get_task(task_id)
        if not task:
            logger.error(f"Task {task_id} not found")
            return
        
        # Start the task
        task.start()
        task.log(f"Executing {action_name}")
        
        # Execute the action
        result = await action_func(*args, **kwargs)
        
        # Update task based on result
        if result.get("status") == "success":
            task.complete(result)
            task.log(f"Successfully executed {action_name}")
        else:
            error_msg = result.get("message", f"Failed to execute {action_name}")
            task.fail(error_msg)
            task.log(f"Error: {error_msg}")
        
    except Exception as e:
        logger.error(f"Error executing {action_name}: {str(e)}")
        
        # Update task with error
        task = task_manager.get_task(task_id)
        if task:
            task.fail(str(e))
            task.log(f"Exception: {str(e)}")

# API routes
@router.post("/initialize", response_model=TaskResponse)
async def initialize_agent(
    background_tasks: BackgroundTasks,
    user: Dict[str, Any] = Depends(get_authenticated_user)
):
    """Initialize the browser agent."""
    try:
        # Create a task
        task_id = str(uuid.uuid4())
        task = Task(id=task_id, description="Initialize browser agent")
        task_manager.add_task(task)
        
        # Schedule the task
        background_tasks.add_task(
            run_agent_action,
            task_id=task_id,
            action_name="initialize",
            action_func=agent_service.initialize
        )
        
        return {"task_id": task_id}
    except Exception as e:
        logger.error(f"Error scheduling agent initialization: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error scheduling agent initialization: {str(e)}")

@router.post("/navigate", response_model=TaskResponse)
async def navigate_to_url(
    request: NavigateRequest,
    background_tasks: BackgroundTasks,
    user: Dict[str, Any] = Depends(get_authenticated_user)
):
    """Navigate to a URL."""
    try:
        # Create a task
        task_id = str(uuid.uuid4())
        task = Task(id=task_id, description=f"Navigate to {request.url}")
        task_manager.add_task(task)
        
        # Schedule the task
        background_tasks.add_task(
            run_agent_action,
            task_id,
            "navigate",
            agent_service.navigate_to_url,
            request.url
        )
        
        return {"task_id": task_id}
    except Exception as e:
        logger.error(f"Error scheduling navigation: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error scheduling navigation: {str(e)}")

@router.post("/click", response_model=TaskResponse)
async def click_element(
    request: ClickElementRequest,
    background_tasks: BackgroundTasks,
    user: Dict[str, Any] = Depends(get_authenticated_user)
):
    """Click an element on the page."""
    try:
        # Create a task
        task_id = str(uuid.uuid4())
        task = Task(id=task_id, description=f"Click element '{request.selector}'")
        task_manager.add_task(task)
        
        # Schedule the task
        background_tasks.add_task(
            run_agent_action,
            task_id,
            "click",
            agent_service.click_element,
            request.selector,
            index=request.index,
            timeout=request.timeout
        )
        
        return {"task_id": task_id}
    except Exception as e:
        logger.error(f"Error scheduling click: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error scheduling click: {str(e)}")

@router.post("/input", response_model=TaskResponse)
async def input_text(
    request: InputTextRequest,
    background_tasks: BackgroundTasks,
    user: Dict[str, Any] = Depends(get_authenticated_user)
):
    """Input text into an element."""
    try:
        # Create a task
        task_id = str(uuid.uuid4())
        task = Task(id=task_id, description=f"Input text into '{request.selector}'")
        task_manager.add_task(task)
        
        # Schedule the task
        background_tasks.add_task(
            run_agent_action,
            task_id,
            "input",
            agent_service.input_text,
            request.selector,
            request.text,
            delay=request.delay
        )
        
        return {"task_id": task_id}
    except Exception as e:
        logger.error(f"Error scheduling input: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error scheduling input: {str(e)}")

@router.post("/get-dom", response_model=TaskResponse)
async def get_dom(
    request: GetDOMRequest,
    background_tasks: BackgroundTasks,
    user: Dict[str, Any] = Depends(get_authenticated_user)
):
    """Get the current DOM of the page."""
    try:
        # Create a task
        task_id = str(uuid.uuid4())
        task = Task(id=task_id, description="Get DOM")
        task_manager.add_task(task)
        
        # Schedule the task
        background_tasks.add_task(
            run_agent_action,
            task_id,
            "get_dom",
            agent_service.get_dom
        )
        
        return {"task_id": task_id}
    except Exception as e:
        logger.error(f"Error scheduling DOM retrieval: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error scheduling DOM retrieval: {str(e)}")

@router.post("/screenshot", response_model=TaskResponse)
async def capture_screenshot(
    request: CaptureScreenshotRequest,
    background_tasks: BackgroundTasks,
    user: Dict[str, Any] = Depends(get_authenticated_user)
):
    """Capture a screenshot of the current page."""
    try:
        # Create a task
        task_id = str(uuid.uuid4())
        task = Task(id=task_id, description="Capture screenshot")
        task_manager.add_task(task)
        
        # Schedule the task
        background_tasks.add_task(
            run_agent_action,
            task_id,
            "screenshot",
            agent_service.capture_screenshot,
            full_page=request.full_page
        )
        
        return {"task_id": task_id}
    except Exception as e:
        logger.error(f"Error scheduling screenshot: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error scheduling screenshot: {str(e)}")

@router.post("/wait", response_model=TaskResponse)
async def wait(
    request: WaitRequest,
    background_tasks: BackgroundTasks,
    user: Dict[str, Any] = Depends(get_authenticated_user)
):
    """Wait for a specified amount of time."""
    try:
        # Create a task
        task_id = str(uuid.uuid4())
        task = Task(id=task_id, description=f"Wait for {request.time}ms")
        task_manager.add_task(task)
        
        # Schedule the task
        background_tasks.add_task(
            run_agent_action,
            task_id,
            "wait",
            agent_service.wait,
            request.time
        )
        
        return {"task_id": task_id}
    except Exception as e:
        logger.error(f"Error scheduling wait: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error scheduling wait: {str(e)}")

@router.post("/execute-sequence", response_model=TaskResponse)
async def execute_action_sequence(
    request: ActionSequenceRequest,
    background_tasks: BackgroundTasks,
    user: Dict[str, Any] = Depends(get_authenticated_user)
):
    """Execute a sequence of actions."""
    try:
        # Create a task
        task_id = str(uuid.uuid4())
        task = Task(id=task_id, description=f"Execute sequence of {len(request.actions)} actions")
        task_manager.add_task(task)
        
        # Schedule the task
        background_tasks.add_task(
            run_agent_action,
            task_id,
            "execute_sequence",
            agent_service.execute_action_sequence,
            [{"name": action.name, "params": action.params} for action in request.actions]
        )
        
        return {"task_id": task_id}
    except Exception as e:
        logger.error(f"Error scheduling action sequence: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error scheduling action sequence: {str(e)}")

@router.get("/status", response_model=Dict[str, Any])
async def get_browser_status(
    user: Dict[str, Any] = Depends(get_authenticated_user)
):
    """Get the current browser status synchronously."""
    try:
        if not agent_service.current_state["initialized"]:
            return {
                "is_browser_open": False,
                "current_url": None,
                "title": None,
                "message": "Browser not initialized"
            }
        
        state = await agent_service.get_current_state()
        page_state = state.get("page_state", {})
        
        return {
            "is_browser_open": agent_service.current_state["initialized"],
            "current_url": page_state.get("url"),
            "title": page_state.get("title"),
            "status": "ready"
        }
    except Exception as e:
        logger.error(f"Error getting browser status: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error getting browser status: {str(e)}")

@router.post("/shutdown", response_model=TaskResponse)
async def shutdown_agent(
    background_tasks: BackgroundTasks,
    user: Dict[str, Any] = Depends(get_authenticated_user)
):
    """Shutdown the agent and close the browser."""
    try:
        # Create a task
        task_id = str(uuid.uuid4())
        task = Task(id=task_id, description="Shutdown browser agent")
        task_manager.add_task(task)
        
        # Schedule the task
        background_tasks.add_task(
            run_agent_action,
            task_id,
            "shutdown",
            agent_service.shutdown
        )
        
        return {"task_id": task_id}
    except Exception as e:
        logger.error(f"Error scheduling shutdown: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error scheduling shutdown: {str(e)}")

@router.post("/execute", response_model=TaskResponse)
async def execute_natural_language_task(
    request: NaturalLanguageTaskRequest,
    background_tasks: BackgroundTasks,
    user: Dict[str, Any] = Depends(get_authenticated_user)
):
    """Execute a task described in natural language."""
    try:
        # Create a task
        task_id = str(uuid.uuid4())
        task = Task(id=task_id, description=f"Execute task: {request.task}")
        task_manager.add_task(task)
        
        # Define the execution function
        async def execute_llm_task():
            try:
                # Start the task
                task = task_manager.get_task(task_id)
                if not task:
                    logger.error(f"Task {task_id} not found")
                    return
                
                task.start()
                task.log(f"Executing natural language task: {request.task}")
                
                # Execute the task with multi-step option
                if request.enable_multi_step:
                    task.log("Multi-step planning enabled")
                
                # Execute the task
                result = await agent_service.execute_from_natural_language(request.task)
                
                # Update the task based on the result
                if result.get("status") == "success":
                    # Filter out raw response if not requested
                    if not request.include_raw_response and "raw_response" in result:
                        del result["raw_response"]
                    
                    task.complete(result)
                    task.log(f"Successfully executed task")
                else:
                    error_msg = result.get("message", "Failed to execute task")
                    task.fail(error_msg)
                    task.log(f"Error: {error_msg}")
            
            except Exception as e:
                logger.error(f"Error executing task: {str(e)}")
                
                # Update task with error
                task = task_manager.get_task(task_id)
                if task:
                    task.fail(str(e))
                    task.log(f"Exception: {str(e)}")
        
        # Schedule the task
        background_tasks.add_task(execute_llm_task)
        
        return {"task_id": task_id}
    except Exception as e:
        logger.error(f"Error scheduling task execution: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error scheduling task execution: {str(e)}")

@router.get("/task-plan", response_model=TaskPlanResponse)
async def get_task_plan(
    user: Dict[str, Any] = Depends(get_authenticated_user)
):
    """Get the current status of the active task plan."""
    try:
        result = await agent_service.get_task_plan_status()
        
        if result.get("status") == "error":
            logger.error(f"Error getting task plan: {result.get('message')}")
            raise HTTPException(status_code=500, detail=result.get("message", "Error getting task plan"))
        
        # Extract task plan data from result
        task_plan = result.get("task_plan", {})
        
        return TaskPlanResponse(
            active=task_plan.get("active", False),
            status=task_plan.get("status", "idle"),
            original_task=task_plan.get("original_task"),
            total_steps=task_plan.get("total_steps", 0),
            current_step=task_plan.get("current_step", -1),
            completed_steps=task_plan.get("completed_steps", 0),
            steps=task_plan.get("steps", [])
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting task plan: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error getting task plan: {str(e)}")

@router.post("/reset-task-plan", response_model=AgentResponse)
async def reset_task_plan(
    user: Dict[str, Any] = Depends(get_authenticated_user)
):
    """Reset the current task plan."""
    try:
        result = await agent_service.reset_task_plan()
        
        if result.get("status") == "error":
            logger.error(f"Error resetting task plan: {result.get('message')}")
            raise HTTPException(status_code=500, detail=result.get("message", "Error resetting task plan"))
        
        return {
            "status": result.get("status", "success"),
            "message": result.get("message", "Task plan reset successfully")
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error resetting task plan: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error resetting task plan: {str(e)}")

@router.get("/available-actions", response_model=Dict[str, Any])
async def list_available_actions(
    user: Dict[str, Any] = Depends(get_authenticated_user)
):
    """List all available actions that can be executed by the agent."""
    try:
        # Make sure agent is initialized first
        if not agent_service.current_state["initialized"]:
            await agent_service.initialize()
            
        # Get the list of actions from the controller
        actions = agent_service.controller.list_actions()
        
        # Categorize actions
        navigation_actions = []
        interaction_actions = []
        extraction_actions = []
        utility_actions = []
        
        for action_name, action_info in actions.items():
            category = action_info.get("category", "utility")
            action_data = {
                "name": action_name,
                "description": action_info.get("description", ""),
                "parameters": action_info.get("parameters", {})
            }
            
            if category == "navigation":
                navigation_actions.append(action_data)
            elif category == "interaction":
                interaction_actions.append(action_data)
            elif category == "extraction":
                extraction_actions.append(action_data)
            else:
                utility_actions.append(action_data)
                
        return {
            "actions": {
                "navigation": navigation_actions,
                "interaction": interaction_actions,
                "extraction": extraction_actions,
                "utility": utility_actions
            }
        }
    except Exception as e:
        logger.error(f"Error listing actions: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error listing actions: {str(e)}")

@router.get("/screenshot", response_model=Dict[str, Any])
async def get_current_screenshot(
    user: Dict[str, Any] = Depends(get_authenticated_user)
):
    """Get the most recent screenshot."""
    try:
        # Check if browser is initialized
        if not browser_manager.is_initialized:
            # Return a service unavailable status code instead of a bad request
            # since this is a temporary condition that can be resolved
            raise HTTPException(
                status_code=503, 
                detail="Browser not initialized. Please try again later or initialize the browser first."
            )
            
        screenshot = await agent_service.capture_screenshot(full_page=True)
        return {
            "status": "success",
            "screenshot": screenshot.get("screenshot")
        }
    except HTTPException:
        # Re-raise HTTP exceptions as-is to preserve status codes
        raise
    except Exception as e:
        logger.error(f"Error getting screenshot: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error getting screenshot: {str(e)}") 