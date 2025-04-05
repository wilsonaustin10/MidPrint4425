"""
Controller service for managing browser automation actions.
This service provides a registry of available actions and handles their execution.
"""
from typing import Dict, Any, Callable, Optional, List, Union, TypeVar, Generic
from enum import Enum
import inspect
import logging
from functools import wraps
from app.browser.browser import browser_manager
from app.core.config import settings

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
    
    def _register_default_actions(self) -> None:
        """
        Register default actions available in the controller.
        """
        # Register navigation actions
        self.registry.register(
            "go_to_url",
            self._go_to_url,
            ActionType.NAVIGATION,
            "Navigate to a specified URL",
            ["url"],
            {"wait_until": "networkidle"}
        )
        
        # Register interaction actions
        self.registry.register(
            "click_element",
            self._click_element,
            ActionType.INTERACTION,
            "Click on an element identified by CSS selector",
            ["selector"],
            {"timeout": 10000}
        )
        
        self.registry.register(
            "input_text",
            self._input_text,
            ActionType.INTERACTION,
            "Enter text into an input field",
            ["selector", "text"],
            {"delay": 50}
        )
        
        # Register extraction actions
        self.registry.register(
            "get_dom",
            self._get_dom,
            ActionType.EXTRACTION,
            "Get the current DOM of the page",
        )
        
        self.registry.register(
            "capture_screenshot",
            self._capture_screenshot,
            ActionType.EXTRACTION,
            "Take a screenshot of the current page",
            [],
            {"full_page": True}
        )
        
        # Register utility actions
        self.registry.register(
            "wait",
            self._wait,
            ActionType.UTILITY,
            "Wait for a specified amount of time",
            ["time"],
        )
        
        # Register system actions
        self.registry.register(
            "done",
            self._done,
            ActionType.SYSTEM,
            "Mark the current task as done",
        )
    
    async def execute_action(self, action_name: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute an action by name with the given parameters.
        
        Args:
            action_name: Name of the action to execute
            params: Parameters for the action
            
        Returns:
            Dictionary with action results
        """
        # Get the action from the registry
        action = self.registry.get_action(action_name)
        
        if not action:
            return {
                "status": "error",
                "message": f"Action '{action_name}' not found",
                "action": action_name
            }
        
        # Validate parameters
        validation_errors = self.registry.validate_params(action_name, params)
        if validation_errors:
            return {
                "status": "error",
                "message": "Parameter validation failed",
                "errors": validation_errors,
                "action": action_name
            }
        
        try:
            # Make sure the browser is initialized
            if not self.browser.is_initialized and action_name != "done":
                await self.browser.initialize()
            
            # Execute the action
            handler = action["handler"]
            result = await handler(**params)
            
            # Return the result
            return {
                "status": "success",
                "action": action_name,
                "result": result
            }
        except Exception as e:
            logger.error(f"Error executing action '{action_name}': {str(e)}")
            return {
                "status": "error",
                "message": f"Error executing action: {str(e)}",
                "action": action_name
            }
    
    async def _go_to_url(self, url: str, wait_until: str = "networkidle") -> Dict[str, Any]:
        """
        Navigate to a URL.
        
        Args:
            url: The URL to navigate to
            wait_until: Navigation wait condition
            
        Returns:
            Dictionary with navigation results
        """
        content = await self.browser.navigate(url)
        screenshot = await self.browser.capture_screenshot()
        page_state = await self.browser.get_page_state()
        
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
            
            await element.click()
            screenshot = await self.browser.capture_screenshot()
            
            return {
                "success": True,
                "selector": selector,
                "screenshot": screenshot
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
            
            await element.fill("")  # Clear the field first
            await element.type(text, delay=delay)
            screenshot = await self.browser.capture_screenshot()
            
            return {
                "success": True,
                "selector": selector,
                "text": text,
                "screenshot": screenshot
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
        screenshot = await self.browser.capture_screenshot(full_page=full_page)
        
        return {
            "screenshot": screenshot,
            "full_page": full_page
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

# Singleton instance
controller_service = ControllerService() 