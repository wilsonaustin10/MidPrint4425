"""
Controller service for managing browser automation actions.
This service provides a registry of available actions and handles their execution.
"""
from typing import Dict, Any, Callable, Optional, List, Union, TypeVar, Generic
from enum import Enum
import inspect
import logging
from functools import wraps
import base64
from app.browser.browser import browser_manager
from app.core.config import settings
from app.services.websocket_manager import websocket_manager
from app.services.task_manager import task_manager
import time
import asyncio
from datetime import datetime

# Set up logging
logger = logging.getLogger(__name__)

# Type definitions
T = TypeVar('T')
ActionFunction = Callable[..., Any]
ActionHandler = Callable[..., Any]


class ActionType(str, Enum):
    """
    Enum for different types of browser actions.
    """
    NAVIGATION = "navigation"
    INTERACTION = "interaction"
    EXTRACTION = "extraction"
    UTILITY = "utility"
    SYSTEM = "system"


class ActionRegistry:
    """
    Registry for browser automation actions.
    Stores available actions and their metadata for dynamic execution.
    """
    
    def __init__(self):
        self.actions: Dict[str, Dict[str, Any]] = {}
    
    def register(self, 
                 name: str, 
                 handler: ActionHandler, 
                 action_type: ActionType = ActionType.UTILITY,
                 description: str = "",
                 required_params: List[str] = None,
                 optional_params: Dict[str, Any] = None) -> None:
        """
        Register a new action in the registry.
        
        Args:
            name: Unique name of the action
            handler: Function that implements the action
            action_type: Category of the action
            description: Human-readable description
            required_params: List of required parameter names
            optional_params: Dictionary of optional parameters with default values
        """
        if required_params is None:
            required_params = []
        
        if optional_params is None:
            optional_params = {}
        
        # Check if action with this name already exists
        if name in self.actions:
            logger.warning(f"Action '{name}' is being overridden")
        
        # Extract parameters from function signature if not provided
        if not required_params and not optional_params:
            sig = inspect.signature(handler)
            for param_name, param in sig.parameters.items():
                if param_name == 'self':
                    continue
                    
                if param.default == inspect.Parameter.empty:
                    required_params.append(param_name)
                else:
                    optional_params[param_name] = param.default
        
        # Register the action
        self.actions[name] = {
            "handler": handler,
            "type": action_type,
            "description": description,
            "required_params": required_params,
            "optional_params": optional_params
        }
        
        logger.info(f"Registered action '{name}' of type '{action_type}'")
    
    def get_action(self, name: str) -> Optional[Dict[str, Any]]:
        """
        Get an action by name.
        
        Args:
            name: Name of the action to retrieve
            
        Returns:
            Action details or None if not found
        """
        return self.actions.get(name)
    
    def list_actions(self, action_type: Optional[ActionType] = None) -> List[Dict[str, Any]]:
        """
        List all registered actions, optionally filtered by type.
        
        Args:
            action_type: Optional type to filter by
            
        Returns:
            List of action details
        """
        if action_type:
            return [
                {
                    "name": name,
                    "type": details["type"],
                    "description": details["description"],
                    "required_params": details["required_params"],
                    "optional_params": details["optional_params"]
                }
                for name, details in self.actions.items()
                if details["type"] == action_type
            ]
        else:
            return [
                {
                    "name": name,
                    "type": details["type"],
                    "description": details["description"],
                    "required_params": details["required_params"],
                    "optional_params": details["optional_params"]
                }
                for name, details in self.actions.items()
            ]
    
    def validate_params(self, action_name: str, params: Dict[str, Any]) -> Dict[str, str]:
        """
        Validate parameters for an action.
        
        Args:
            action_name: Name of the action to validate parameters for
            params: Parameters to validate
            
        Returns:
            Dictionary of validation errors, empty if valid
        """
        errors = {}
        action = self.get_action(action_name)
        
        if not action:
            return {"action": f"Action '{action_name}' not found"}
        
        # Check required parameters
        for param in action["required_params"]:
            if param not in params:
                errors[param] = f"Missing required parameter: {param}"
        
        return errors


class ControllerService:
    """
    Controller service that manages browser actions through the action registry.
    """
    
    def __init__(self):
        self.registry = ActionRegistry()
        self.browser = browser_manager
        self._register_default_actions()
        self._last_screenshot_time = 0
        self._screenshot_debounce_interval = 100  # ms
        self._last_screenshot_cache = None
        self._page_state_cache = None
        self._last_screenshot_format = "jpeg"
        self._last_screenshot_quality = 75
        self.screenshot_config = {
            "full_page": True,
            "format": "jpeg",
            "quality": 75  # Default quality (0-100)
        }
    
    def _register_default_actions(self) -> None:
        """
        Register default actions that can be executed via the API.
        Each action is mapped to a method in this class.
        """
        self.actions = {
            "go_to_url": self._go_to_url,
            "click_element": self._click_element,
            "input_text": self._input_text,
            "get_dom": self._get_dom,
            "capture_screenshot": self._capture_screenshot,
            "wait": self._wait,
            "done": self._done,
            "set_screenshot_config": self.set_screenshot_config,
        }
    
    async def execute_action(self, action_name: str, params: Dict[str, Any], task_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Execute a registered browser action.
        
        Args:
            action_name: Name of the action to execute
            params: Parameters for the action
            task_id: Optional task ID to associate with the action
            
        Returns:
            Result of the action execution
        """
        try:
            # Get the action handler
            if action_name not in self.actions:
                return {"success": False, "message": f"Unknown action: {action_name}"}
                
            action_handler = self.actions[action_name]
            
            # Initialize browser if needed
            if not self.browser.is_initialized:
                await self.browser.initialize()
            
            # Log the action execution
            logger.info(f"Executing action '{action_name}' with params: {params}")
            
            # Execute the action with the provided parameters
            result = await action_handler(**params)
            
            # Include additional metadata in the result
            if isinstance(result, dict):
                if "success" not in result:
                    result["success"] = True
                result["action"] = action_name
                result["timestamp"] = int(time.time() * 1000)  # Current time in milliseconds
            
            return result
            
        except Exception as e:
            logger.error(f"Error executing action '{action_name}': {str(e)}")
            return {"success": False, "message": str(e), "action": action_name}
    
    async def _go_to_url(self, url: str, wait_until: str = "networkidle") -> Dict[str, Any]:
        """
        Navigate to a URL.
        
        Args:
            url: The URL to navigate to
            wait_until: Navigation wait condition
            
        Returns:
            Dictionary with navigation results
        """
        # Start navigation
        content = await self.browser.navigate(url)
        screenshot = await self.browser.capture_screenshot()
        page_state = await self.browser.get_page_state()
        
        # Broadcast screenshot and page state updates if a task is active
        task_id = await self._get_current_task_id()
        if task_id:
            # Send regular updates
            await self._broadcast_screenshot_update(task_id, screenshot)
            await self._broadcast_browser_state_update(task_id, page_state)
            
            # Send navigation action feedback
            action_data = {
                "url": url,
                "pageTitle": page_state.get("title", ""),
                "timestamp": int(time.time() * 1000)
            }
            await self._broadcast_action_feedback(task_id, "navigation", action_data)
        
        return {
            "url": url,
            "content": content,
            "screenshot": screenshot,
            "page_state": page_state
        }
    
    async def _click_element(self, selector: str, timeout: int = 10000) -> Dict[str, Any]:
        """
        Click on an element identified by selector.
        
        Args:
            selector: CSS selector of the element to click
            timeout: Maximum time to wait for the element
            
        Returns:
            Dictionary with click results
        """
        page = self.browser.page
        try:
            element = await page.wait_for_selector(selector, timeout=timeout)
            if not element:
                return {"success": False, "message": f"Element not found: {selector}"}
            
            # Get element position before clicking for action feedback
            position = await element.bounding_box()
            
            # Click the element
            await element.click()
            
            # Capture updated state
            screenshot = await self.browser.capture_screenshot()
            page_state = await self.browser.get_page_state()
            
            # Broadcast updates if a task is active
            task_id = await self._get_current_task_id()
            if task_id:
                # Broadcast screenshot and page state
                await self._broadcast_screenshot_update(task_id, screenshot)
                await self._broadcast_browser_state_update(task_id, page_state)
                
                # Broadcast action feedback with click coordinates
                if position:
                    action_data = {
                        "selector": selector,
                        "x": position["x"] + (position["width"] / 2),  # Center X of element
                        "y": position["y"] + (position["height"] / 2),  # Center Y of element
                        "width": position["width"],
                        "height": position["height"]
                    }
                    await self._broadcast_action_feedback(task_id, "click", action_data)
            
            return {
                "success": True,
                "selector": selector,
                "screenshot": screenshot,
                "page_state": page_state
            }
        except Exception as e:
            return {"success": False, "message": str(e)}
    
    async def _input_text(self, selector: str, text: str, delay: int = 50) -> Dict[str, Any]:
        """
        Enter text into an input field.
        
        Args:
            selector: CSS selector of the input element
            text: Text to enter
            delay: Delay between keypresses in milliseconds
            
        Returns:
            Dictionary with input results
        """
        page = self.browser.page
        try:
            element = await page.wait_for_selector(selector)
            if not element:
                return {"success": False, "message": f"Element not found: {selector}"}
            
            # Get element position before typing for action feedback
            position = await element.bounding_box()
            
            # Clear the field and type the text
            await element.fill("")  # Clear the field first
            await element.type(text, delay=delay)
            
            # Capture updated state
            screenshot = await self.browser.capture_screenshot()
            page_state = await self.browser.get_page_state()
            
            # Broadcast updates if a task is active
            task_id = await self._get_current_task_id()
            if task_id:
                # Broadcast screenshot and page state
                await self._broadcast_screenshot_update(task_id, screenshot)
                await self._broadcast_browser_state_update(task_id, page_state)
                
                # Broadcast action feedback with typing information
                if position:
                    action_data = {
                        "selector": selector,
                        "x": position["x"] + (position["width"] / 2),  # Center X of element
                        "y": position["y"] + (position["height"] / 2),  # Center Y of element
                        "content": text,
                        "width": position["width"],
                        "height": position["height"]
                    }
                    await self._broadcast_action_feedback(task_id, "typing", action_data)
            
            return {
                "success": True,
                "selector": selector,
                "text": text,
                "screenshot": screenshot,
                "page_state": page_state
            }
        except Exception as e:
            return {"success": False, "message": str(e)}
    
    async def _get_dom(self) -> Dict[str, Any]:
        """
        Get the current DOM of the page.
        
        Returns:
            Dictionary with DOM content
        """
        content = await self.browser.get_dom()
        page_state = await self.browser.get_page_state()
        
        return {
            "content": content,
            "page_state": page_state
        }
    
    async def _capture_screenshot(self, full_page: bool = True) -> Dict[str, Any]:
        """
        Take a screenshot of the current page.
        
        Args:
            full_page: Whether to capture the full page or just the viewport
            
        Returns:
            Dictionary with screenshot data
        """
        # Use previously configured screenshot settings
        format = self.screenshot_config.get("format", "jpeg")
        quality = self.screenshot_config.get("quality", 75)
        
        # Store format and quality for reference in broadcast
        self._last_screenshot_format = format
        self._last_screenshot_quality = quality
        
        screenshot = await self.browser.capture_screenshot(
            full_page=full_page, 
            quality=quality,
            format=format
        )
        page_state = await self.browser.get_page_state()
        
        # Cache the results
        self._last_screenshot_cache = screenshot
        self._page_state_cache = page_state
        
        # Broadcast screenshot and page state updates if a task is active
        task_id = await self._get_current_task_id()
        if task_id:
            await self._broadcast_screenshot_update(task_id, screenshot)
            await self._broadcast_browser_state_update(task_id, page_state)
        
        return {
            "screenshot": screenshot,
            "full_page": full_page,
            "page_state": page_state,
            "format": format,
            "quality": quality
        }
    
    async def _wait(self, time: int) -> Dict[str, Any]:
        """
        Wait for a specified amount of time.
        
        Args:
            time: Time to wait in milliseconds
            
        Returns:
            Dictionary with wait results
        """
        page = self.browser.page
        await page.wait_for_timeout(time)
        
        return {
            "waited_ms": time
        }
    
    async def _done(self) -> Dict[str, Any]:
        """
        Mark the current task as done.
        
        Returns:
            Dictionary with done status
        """
        # This is a no-op action that can be used to signal completion
        return {
            "done": True
        }

    async def _broadcast_screenshot_update(self, task_id: str, screenshot_base64: str) -> None:
        """
        Broadcast a screenshot update via WebSocket.
        
        Args:
            task_id: The ID of the task
            screenshot_base64: Base64-encoded screenshot data
        """
        if not task_id or not screenshot_base64:
            logger.warning("Cannot broadcast screenshot update: missing task_id or screenshot data")
            return
            
        try:
            # Check if enough time has passed since the last screenshot
            current_time = int(time.time() * 1000)  # Current time in milliseconds
            
            # If we've sent a screenshot recently, don't send another one yet
            if current_time - self._last_screenshot_time < self._screenshot_debounce_interval:
                logger.debug(f"Debouncing screenshot update for task {task_id}, too soon after last update")
                return
                
            self._last_screenshot_time = current_time
            self._last_screenshot_cache = screenshot_base64
            
            # Prepare the update message
            screenshot_update = {
                "type": "browser_screenshot_update",
                "screenshot": screenshot_base64,
                "format": self._last_screenshot_format,
                "timestamp": current_time
            }
            
            # Broadcast the update to task subscribers
            await websocket_manager.broadcast_task_update(task_id, screenshot_update)
            logger.debug(f"Screenshot update broadcast for task {task_id}")
        except Exception as e:
            logger.error(f"Error broadcasting screenshot update: {str(e)}")
    
    async def _broadcast_browser_state_update(self, task_id: str, state: Dict[str, Any]) -> None:
        """
        Broadcast a browser state update via WebSocket.
        
        Args:
            task_id: The ID of the task
            state: Browser state data including URL and page title
        """
        if not task_id or not state:
            logger.warning("Cannot broadcast browser state update: missing task_id or state data")
            return
            
        try:
            # Prepare the update message with URL and page title
            browser_state_update = {
                "type": "browser_state_update",
                "currentUrl": state.get("url", ""),
                "pageTitle": state.get("title", "")
            }
            
            # Broadcast the update to task subscribers
            await websocket_manager.broadcast_task_update(task_id, browser_state_update)
            logger.debug(f"Browser state update broadcast for task {task_id}")
        except Exception as e:
            logger.error(f"Error broadcasting browser state update: {str(e)}")
            
    async def _get_current_task_id(self) -> Optional[str]:
        """
        Get the ID of the current task from the agent service.
        
        Returns:
            Task ID or None if no task is active
        """
        # Check in the global context for the current task
        for task_id, task in task_manager.tasks.items():
            if task.status == "running":
                return task_id
        
        # If no running task found, return None
        return None

    async def _broadcast_action_feedback(self, task_id: str, action_type: str, action_data: Dict[str, Any]) -> None:
        """
        Broadcast action feedback via WebSocket for visual indicators.
        
        Args:
            task_id: The ID of the task
            action_type: Type of action (click, type, navigate, scroll, etc.)
            action_data: Data related to the action (coordinates, selectors, etc.)
        """
        if not task_id or not action_type:
            logger.warning("Cannot broadcast action feedback: missing task_id or action_type")
            return
        
        try:
            # Prepare the update message with action data
            action_feedback = {
                "type": "browser_action_feedback",
                "actionType": action_type,
                "timestamp": int(time.time() * 1000),  # Current time in milliseconds
                "data": action_data
            }
            
            # Broadcast the update to task subscribers
            await websocket_manager.broadcast_task_update(task_id, action_feedback)
            logger.debug(f"Action feedback broadcast for task {task_id}: {action_type}")
        except Exception as e:
            logger.error(f"Error broadcasting action feedback: {str(e)}")

    async def set_screenshot_config(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Configure screenshot capture settings.
        
        Args:
            config: Dictionary with configuration options
                - format: 'jpeg' or 'png'
                - quality: 0-100 (JPEG only)
                - full_page: Whether to capture the full page
                
        Returns:
            Current screenshot configuration
        """
        # Update config with new values
        if "format" in config:
            format = config["format"].lower()
            if format in ["jpeg", "png"]:
                self.screenshot_config["format"] = format
                
        if "quality" in config and isinstance(config["quality"], int):
            quality = max(0, min(100, config["quality"]))  # Clamp to 0-100
            self.screenshot_config["quality"] = quality
            
        if "full_page" in config and isinstance(config["full_page"], bool):
            self.screenshot_config["full_page"] = config["full_page"]
            
        if "debounce_interval" in config and isinstance(config["debounce_interval"], int):
            self._screenshot_debounce_interval = max(0, min(1000, config["debounce_interval"]))
            
        # Return current config
        return {
            "success": True,
            "config": self.screenshot_config,
            "debounce_interval": self._screenshot_debounce_interval
        }

# Singleton instance
controller_service = ControllerService() 