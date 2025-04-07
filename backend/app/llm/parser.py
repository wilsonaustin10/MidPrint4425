"""
Parser for LLM responses to convert them into action plans.
"""
import json
import logging
import re
from typing import Dict, Any, List, Optional, Tuple, Union

# Set up logger
logger = logging.getLogger(__name__)

class ActionValidationError(Exception):
    """Exception raised when an action is invalid."""
    pass

class LLMResponseParser:
    """
    Parser for LLM responses to convert them into action plans.
    
    Handles parsing, validation, and conversion of LLM responses into executable actions.
    """
    
    # Define valid actions and their required parameters
    VALID_ACTIONS = {
        # Navigation actions
        "go_to_url": ["url"],
        
        # Interaction actions
        "click_element": ["selector"],
        "click_element_by_index": ["element_index"],
        "input_text": ["selector", "text"],
        
        # Extraction actions
        "get_dom": [],
        "capture_screenshot": [],
        
        # Utility actions
        "wait": ["time"],
        "done": [],
        
        # LLM planning actions
        "plan_task": ["steps", "thought"],
        "execute_step": ["step_index", "action", "parameters"]
    }
    
    def __init__(self):
        """Initialize the LLM response parser."""
        logger.info("LLMResponseParser initialized")
    
    def parse_response(self, response: str) -> Dict[str, Any]:
        """
        Parse an LLM response into an action plan.
        
        Args:
            response: The LLM response string
            
        Returns:
            Dictionary with the parsed action plan
            
        Raises:
            ActionValidationError: If the response cannot be parsed or is invalid
        """
        try:
            # First try to extract JSON directly
            action_plan = self._extract_json(response)
            
            # Validate the action plan
            self._validate_action_plan(action_plan)
            
            return action_plan
        except Exception as e:
            logger.error(f"Error parsing LLM response: {str(e)}")
            raise ActionValidationError(f"Failed to parse LLM response: {str(e)}")
    
    def _extract_json(self, text: str) -> Dict[str, Any]:
        """
        Extract JSON from text, handling different formats that LLMs might output.
        
        Args:
            text: The text containing JSON
            
        Returns:
            Parsed JSON as a dictionary
            
        Raises:
            ValueError: If no valid JSON is found
        """
        # Try to find JSON between triple backticks
        json_match = re.search(r"```(?:json)?\s*({.*?})\s*```", text, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group(1))
            except json.JSONDecodeError:
                logger.warning("Failed to parse JSON in code block, trying fallback methods")
        
        # Try to find JSON between single backticks
        json_match = re.search(r"`({.*?})`", text, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group(1))
            except json.JSONDecodeError:
                logger.warning("Failed to parse JSON in inline code, trying fallback methods")
        
        # Try to find any JSON-like structure
        json_match = re.search(r"{[^{]*\"thought\"[^}]*\"action\"[^}]*}", text, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group(0))
            except json.JSONDecodeError:
                logger.warning("Failed to parse JSON-like structure, trying full text")
        
        # Last resort: try parsing the entire text as JSON
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            error_msg = "No valid JSON found in LLM response"
            logger.error(error_msg)
            raise ValueError(error_msg)
    
    def _validate_action_plan(self, action_plan: Dict[str, Any]) -> None:
        """
        Validate an action plan.
        
        Args:
            action_plan: The action plan to validate
            
        Raises:
            ActionValidationError: If the action plan is invalid
        """
        # Check required fields
        if "action" not in action_plan:
            raise ActionValidationError("Action plan must contain an 'action' field")
        
        action = action_plan.get("action")
        
        # Check if action is valid
        if action not in self.VALID_ACTIONS:
            raise ActionValidationError(f"Invalid action: {action}")
        
        # Check parameters
        if "parameters" not in action_plan:
            action_plan["parameters"] = {}
        
        parameters = action_plan.get("parameters", {})
        
        # Check required parameters
        for param in self.VALID_ACTIONS[action]:
            if param not in parameters:
                raise ActionValidationError(f"Missing required parameter for {action}: {param}")
        
        # Type validation for specific parameters
        if action == "click_element_by_index":
            element_index = parameters.get("element_index")
            if not isinstance(element_index, int) and not (isinstance(element_index, str) and element_index.isdigit()):
                try:
                    parameters["element_index"] = int(element_index)
                except (ValueError, TypeError):
                    raise ActionValidationError(f"Invalid element_index: {element_index}, must be an integer")
        
        if action == "click_element":
            selector = parameters.get("selector")
            if not isinstance(selector, str) or not selector.strip():
                raise ActionValidationError(f"Invalid selector: {selector}, must be a non-empty string")
                
            # Add optional parameter validation
            if "timeout" in parameters:
                timeout = parameters.get("timeout")
                if not isinstance(timeout, int) and not (isinstance(timeout, str) and timeout.isdigit()):
                    try:
                        parameters["timeout"] = int(timeout)
                    except (ValueError, TypeError):
                        raise ActionValidationError(f"Invalid timeout: {timeout}, must be an integer")
        
        if action == "input_text":
            selector = parameters.get("selector")
            if not isinstance(selector, str) or not selector.strip():
                raise ActionValidationError(f"Invalid selector: {selector}, must be a non-empty string")
            
            text = parameters.get("text")
            if not isinstance(text, str):
                raise ActionValidationError(f"Invalid text: {text}, must be a string")
                
            # Add optional parameter validation
            if "delay" in parameters:
                delay = parameters.get("delay")
                if not isinstance(delay, int) and not (isinstance(delay, str) and delay.isdigit()):
                    try:
                        parameters["delay"] = int(delay)
                    except (ValueError, TypeError):
                        raise ActionValidationError(f"Invalid delay: {delay}, must be an integer")
        
        if action == "go_to_url":
            url = parameters.get("url")
            if not isinstance(url, str):
                raise ActionValidationError(f"Invalid url: {url}, must be a string")
            
            # Basic URL validation
            if not (url.startswith("http://") or url.startswith("https://")):
                # Try to fix the URL by adding https://
                if not url.startswith("www.") and "." in url:
                    parameters["url"] = f"https://{url}"
                else:
                    parameters["url"] = f"https://{url}"
                logger.info(f"Fixed URL: {parameters['url']}")
                
            # Add optional parameter validation
            if "wait_until" in parameters:
                wait_until = parameters.get("wait_until")
                valid_wait_options = ["networkidle", "load", "domcontentloaded"]
                if not isinstance(wait_until, str) or wait_until not in valid_wait_options:
                    # Default to networkidle if invalid
                    parameters["wait_until"] = "networkidle"
                    logger.info(f"Defaulting wait_until to 'networkidle'")
        
        if action == "wait":
            time_param = parameters.get("time")
            if not isinstance(time_param, int) and not (isinstance(time_param, str) and time_param.isdigit()):
                try:
                    parameters["time"] = int(time_param)
                except (ValueError, TypeError):
                    raise ActionValidationError(f"Invalid time: {time_param}, must be an integer (milliseconds)")
            
            # Ensure time is reasonable (between 100ms and 30s)
            time_value = int(parameters["time"])
            if time_value < 100:
                parameters["time"] = 100
                logger.info(f"Adjusted wait time to minimum 100ms")
            elif time_value > 30000:
                parameters["time"] = 30000
                logger.info(f"Adjusted wait time to maximum 30000ms (30s)")
                
        if action == "capture_screenshot":
            # Add optional parameter validation
            if "full_page" in parameters:
                full_page = parameters.get("full_page")
                if not isinstance(full_page, bool):
                    try:
                        # Convert string 'true'/'false' to boolean
                        if isinstance(full_page, str):
                            parameters["full_page"] = full_page.lower() == 'true'
                        else:
                            parameters["full_page"] = bool(full_page)
                    except (ValueError, TypeError):
                        # Default to True if conversion fails
                        parameters["full_page"] = True
                        logger.info(f"Defaulting full_page to True")
                
        if action == "plan_task":
            steps = parameters.get("steps")
            if not isinstance(steps, list):
                raise ActionValidationError(f"Invalid steps: {steps}, must be a list")
            
            if len(steps) == 0:
                raise ActionValidationError("Steps list cannot be empty")
            
            thought = parameters.get("thought")
            if not isinstance(thought, str):
                raise ActionValidationError(f"Invalid thought: {thought}, must be a string")
                
        if action == "execute_step":
            step_index = parameters.get("step_index")
            if not isinstance(step_index, int) and not (isinstance(step_index, str) and step_index.isdigit()):
                try:
                    parameters["step_index"] = int(step_index)
                except (ValueError, TypeError):
                    raise ActionValidationError(f"Invalid step_index: {step_index}, must be an integer")
            
            action_param = parameters.get("action")
            if not isinstance(action_param, str) or action_param not in self.VALID_ACTIONS:
                raise ActionValidationError(f"Invalid action in execute_step: {action_param}, must be a valid action")
            
            action_parameters = parameters.get("parameters")
            if not isinstance(action_parameters, dict):
                raise ActionValidationError(f"Invalid parameters in execute_step: {action_parameters}, must be a dictionary")
            
            # Validate the nested action parameters
            nested_action_plan = {
                "action": action_param,
                "parameters": action_parameters
            }
            try:
                # Create a temporary copy to avoid modifying the original action plan
                temp_plan = nested_action_plan.copy()
                self._validate_action_plan(temp_plan)
                # Update with any fixed parameters (like URL)
                parameters["parameters"] = temp_plan["parameters"]
            except ActionValidationError as e:
                raise ActionValidationError(f"Invalid nested action in execute_step: {e}")

    def format_action_for_execution(self, action_plan: Dict[str, Any]) -> Dict[str, Any]:
        """
        Format an action plan for execution by the agent.
        
        Args:
            action_plan: The validated action plan
            
        Returns:
            Dictionary with the action and parameters ready for execution
        """
        return {
            "action": action_plan["action"],
            "parameters": action_plan["parameters"]
        } 