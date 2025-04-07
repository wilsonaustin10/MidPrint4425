"""
Agent service for handling browser automation tasks.
This service coordinates between the controller and browser manager.
"""
from typing import Dict, Any, Optional, List, Tuple
from app.browser.browser import browser_manager
from app.controller.service import controller_service
from app.core.config import settings
from app.llm.service import LLMService
from app.llm.parser import LLMResponseParser, ActionValidationError
from app.agent.message_manager import MessageManager
import base64
import logging
import json
import asyncio
import time
import os
from app.task.service import task_manager

# Set up logging
logger = logging.getLogger(__name__)

class AgentService:
    """
    Agent service that orchestrates browser automation tasks.
    Handles the execution of browser actions via the controller service.
    """
    
    def __init__(self):
        self.browser = browser_manager
        self.controller = controller_service
        self.current_state = {
            "initialized": False,
            "current_url": None,
            "last_screenshot": None,
            "last_error": None,
            "history": [],
            "task_id": None,
            "multi_step_tasks": {
                "active": False,
                "current_plan": None
            }
        }
        # Initialize LLM components
        self.llm_service = None
        self.message_manager = None
        self.response_parser = None
    
    async def initialize(self) -> Dict[str, Any]:
        """
        Initialize the agent, browser, and controller.
        Includes retry logic and proper error handling.
        
        Returns:
            Dictionary with initialization status
        """
        max_retries = 3
        retry_count = 0
        last_error = None
        
        while retry_count < max_retries:
            try:
                # Clean up any existing state
                await self._cleanup()
                
                # Initialize browser with retries
                await self.browser.initialize()
                
                # Initialize LLM components
                self.llm_service = LLMService()
                self.message_manager = MessageManager()
                self.response_parser = LLMResponseParser()
                
                # Set initial state
                self.current_state = {
                    "initialized": True,
                    "current_url": None,
                    "last_screenshot": None,
                    "last_error": None,
                    "history": [],
                    "task_id": f"task_{int(time.time())}",
                    "multi_step_tasks": {
                        "active": False,
                        "current_plan": None
                    }
                }
                
                logger.info(f"Agent initialized with task ID: {self.current_state['task_id']}")
                return {"status": "success", "message": "Agent initialized successfully"}
                
            except Exception as e:
                last_error = str(e)
                retry_count += 1
                
                logger.error(f"Initialization attempt {retry_count} failed: {last_error}")
                
                # Clean up resources before retry
                await self._cleanup()
                
                if retry_count < max_retries:
                    await asyncio.sleep(1)  # Wait before retrying
                
        error_msg = f"Failed to initialize agent after {max_retries} attempts. Last error: {last_error}"
        logger.error(error_msg)
        
        self.current_state = {
            "initialized": False,
            "current_url": None,
            "last_screenshot": None,
            "last_error": error_msg,
            "history": [],
            "task_id": None,
            "multi_step_tasks": {
                "active": False,
                "current_plan": None
            }
        }
        
        return {"status": "error", "message": error_msg}
    
    async def _cleanup(self) -> None:
        """
        Clean up agent resources and state.
        """
        try:
            # Reset state
            self.current_state = {
                "initialized": False,
                "current_url": None,
                "last_screenshot": None,
                "last_error": None,
                "history": [],
                "task_id": None,
                "multi_step_tasks": {
                    "active": False,
                    "current_plan": None
                }
            }
            
            # Clean up LLM components
            self.llm_service = None
            self.message_manager = None
            self.response_parser = None
            
            # Clean up browser if needed
            if self.browser and self.browser.is_initialized:
                await self.browser._cleanup()
                
        except Exception as e:
            logger.error(f"Error during cleanup: {str(e)}")
    
    def is_initialized(self) -> bool:
        """
        Check if the agent is properly initialized.
        
        Returns:
            True if initialized, False otherwise
        """
        return (
            self.current_state["initialized"] and
            self.browser and
            self.browser.is_initialized and
            self.llm_service is not None and
            self.message_manager is not None and
            self.response_parser is not None
        )
    
    async def ensure_initialized(self) -> Dict[str, Any]:
        """
        Ensure the agent is initialized, initializing it if necessary.
        
        Returns:
            Dictionary with initialization status
        """
        if not self.is_initialized():
            return await self.initialize()
        return {"status": "success", "message": "Agent already initialized"}
    
    async def navigate_to_url(self, url: str) -> Dict[str, Any]:
        """
        Navigate the browser to a URL.
        
        Args:
            url: The URL to navigate to
            
        Returns:
            Dictionary with navigation results including page content and screenshot
        """
        try:
            # Execute the action via the controller
            action_result = await self.controller.execute_action("go_to_url", {"url": url})
            
            if action_result["status"] != "success":
                self.current_state["last_error"] = action_result.get("message", "Navigation failed")
                return action_result
            
            # Update agent state
            result = action_result["result"]
            self.current_state["current_url"] = url
            self.current_state["last_screenshot"] = result["screenshot"]
            self.current_state["history"].append({
                "action": "navigate",
                "url": url,
                "timestamp": time.time()
            })
            
            logger.info(f"Navigated to URL: {url}")
            return {
                "status": "success",
                "url": url,
                "content_length": len(result["content"]) if "content" in result else 0,
                "screenshot": result["screenshot"],
                "page_state": result["page_state"]
            }
        except Exception as e:
            error_msg = f"Navigation error: {str(e)}"
            self.current_state["last_error"] = error_msg
            logger.error(error_msg)
            return {"status": "error", "message": error_msg}
    
    async def click_element(self, selector: str, index: int = 0, timeout: int = 10000) -> Dict[str, Any]:
        """
        Click on an element identified by selector and index.
        
        Args:
            selector: CSS selector of the element to click
            index: Index if multiple elements match the selector (0-based)
            timeout: Maximum time to wait for the element in milliseconds
            
        Returns:
            Dictionary with click results
        """
        try:
            # For clicking by index, we need to handle element selection differently
            if index > 0:
                # First, get all elements matching the selector
                page = self.browser.page
                elements = await page.query_selector_all(selector)
                
                if not elements or len(elements) <= index:
                    error_msg = f"Element at index {index} not found for selector: {selector}"
                    self.current_state["last_error"] = error_msg
                    return {"status": "error", "message": error_msg}
                
                # Click the element at the specific index
                await elements[index].click()
                
                # Capture screenshot after click
                screenshot = await self.browser.capture_screenshot()
                
                # Update agent state
                self.current_state["last_screenshot"] = screenshot
                self.current_state["history"].append({
                    "action": "click_element_by_index",
                    "selector": selector,
                    "index": index,
                    "timestamp": time.time()
                })
                
                logger.info(f"Clicked element at index {index} with selector: {selector}")
                return {
                    "status": "success",
                    "selector": selector,
                    "index": index,
                    "screenshot": screenshot
                }
            else:
                # Use the controller for regular element clicking
                action_result = await self.controller.execute_action("click_element", {
                    "selector": selector, 
                    "timeout": timeout
                })
                
                if action_result["status"] != "success":
                    self.current_state["last_error"] = action_result.get("message", "Click failed")
                    return action_result
                
                # Update agent state
                result = action_result["result"]
                self.current_state["last_screenshot"] = result.get("screenshot")
                self.current_state["history"].append({
                    "action": "click_element",
                    "selector": selector,
                    "timestamp": time.time()
                })
                
                logger.info(f"Clicked element with selector: {selector}")
                return {
                    "status": "success",
                    "selector": selector,
                    "screenshot": result.get("screenshot")
                }
        except Exception as e:
            error_msg = f"Click error: {str(e)}"
            self.current_state["last_error"] = error_msg
            logger.error(error_msg)
            return {"status": "error", "message": error_msg}
    
    async def input_text(self, selector: str, text: str, delay: int = 50) -> Dict[str, Any]:
        """
        Enter text into an input field.
        
        Args:
            selector: CSS selector of the input element
            text: Text to enter
            delay: Delay between keypresses in milliseconds
            
        Returns:
            Dictionary with input results
        """
        try:
            # Execute the action via the controller
            action_result = await self.controller.execute_action("input_text", {
                "selector": selector,
                "text": text,
                "delay": delay
            })
            
            if action_result["status"] != "success":
                self.current_state["last_error"] = action_result.get("message", "Input text failed")
                return action_result
            
            # Update agent state
            result = action_result["result"]
            self.current_state["last_screenshot"] = result.get("screenshot")
            self.current_state["history"].append({
                "action": "input_text",
                "selector": selector,
                "text_length": len(text),  # Store length, not the actual text for privacy
                "timestamp": time.time()
            })
            
            logger.info(f"Input text into element with selector: {selector}")
            return {
                "status": "success",
                "selector": selector,
                "text_length": len(text),
                "screenshot": result.get("screenshot")
            }
        except Exception as e:
            error_msg = f"Input text error: {str(e)}"
            self.current_state["last_error"] = error_msg
            logger.error(error_msg)
            return {"status": "error", "message": error_msg}
    
    async def get_dom(self) -> Dict[str, Any]:
        """
        Get the current DOM of the page.
        
        Returns:
            Dictionary with DOM content and status
        """
        try:
            # Execute the action via the controller
            action_result = await self.execute_action("get_dom", {})
            
            if action_result["status"] != "success":
                self.current_state["last_error"] = action_result.get("message", "Failed to get DOM")
                return action_result
            
            # Update agent state
            result = action_result["result"]
            self.current_state["history"].append({
                "action": "get_dom",
                "timestamp": time.time()
            })
            
            logger.info(f"Retrieved DOM content successfully")
            return {
                "status": "success",
                "content_length": len(result["content"]) if "content" in result else 0,
                "content": result.get("content", ""),
                "page_state": result.get("page_state", {})
            }
        except Exception as e:
            error_msg = f"DOM retrieval error: {str(e)}"
            self.current_state["last_error"] = error_msg
            logger.error(error_msg)
            return {"status": "error", "message": error_msg}
    
    async def capture_screenshot(self, full_page: bool = True) -> Dict[str, Any]:
        """
        Capture a screenshot of the current page.
        
        Args:
            full_page: Whether to capture the full page or just the viewport
            
        Returns:
            Dictionary with screenshot data and status
        """
        try:
            # Execute the action via the controller
            action_result = await self.execute_action("capture_screenshot", {"full_page": full_page})
            
            if action_result["status"] != "success":
                self.current_state["last_error"] = action_result.get("message", "Screenshot capture failed")
                return action_result
            
            # Update agent state
            result = action_result["result"]
            self.current_state["last_screenshot"] = result.get("screenshot")
            self.current_state["history"].append({
                "action": "capture_screenshot",
                "full_page": full_page,
                "timestamp": time.time()
            })
            
            logger.info(f"Captured screenshot successfully (full_page={full_page})")
            return {
                "status": "success",
                "screenshot": result.get("screenshot"),
                "page_state": result.get("page_state", {})
            }
        except Exception as e:
            error_msg = f"Screenshot capture error: {str(e)}"
            self.current_state["last_error"] = error_msg
            logger.error(error_msg)
            return {"status": "error", "message": error_msg}
    
    async def wait(self, time_ms: int) -> Dict[str, Any]:
        """
        Wait for a specified amount of time.
        
        Args:
            time_ms: Time to wait in milliseconds
            
        Returns:
            Dictionary with wait status
        """
        try:
            # Validate time parameter
            if not isinstance(time_ms, int):
                try:
                    time_ms = int(time_ms)
                except (ValueError, TypeError):
                    error_msg = f"Invalid time value: {time_ms}, must be an integer"
                    self.current_state["last_error"] = error_msg
                    return {"status": "error", "message": error_msg}
            
            # Ensure time is reasonable (between 100ms and 30s)
            if time_ms < 100:
                time_ms = 100
                logger.info(f"Adjusted wait time to minimum 100ms")
            elif time_ms > 30000:
                time_ms = 30000
                logger.info(f"Adjusted wait time to maximum 30000ms (30s)")
            
            # Execute the action via the controller
            action_result = await self.execute_action("wait", {"time": time_ms})
            
            if action_result["status"] != "success":
                self.current_state["last_error"] = action_result.get("message", "Wait operation failed")
                return action_result
            
            # Update agent state
            self.current_state["history"].append({
                "action": "wait",
                "time_ms": time_ms,
                "timestamp": time.time()
            })
            
            logger.info(f"Waited for {time_ms}ms successfully")
            return {
                "status": "success",
                "time_ms": time_ms
            }
        except Exception as e:
            error_msg = f"Wait error: {str(e)}"
            self.current_state["last_error"] = error_msg
            logger.error(error_msg)
            return {"status": "error", "message": error_msg}
    
    async def get_current_state(self) -> Dict[str, Any]:
        """
        Get the current state of the agent and browser.
        
        Returns:
            Dictionary with current agent state
        """
        try:
            if not self.browser.is_initialized:
                return {
                    "status": "not_initialized",
                    "message": "Agent not initialized"
                }
            
            # Get current page state from browser
            page_state = await self.browser.get_page_state()
            
            # Update current state
            self.current_state["current_url"] = page_state.get("url")
            
            # Get screenshot
            screenshot = await self.browser.capture_screenshot()
            self.current_state["last_screenshot"] = screenshot
            
            # Trim history to last 10 entries to keep response size manageable
            if len(self.current_state["history"]) > 10:
                self.current_state["history"] = self.current_state["history"][-10:]
            
            return {
                "status": "success",
                "agent_state": {
                    "initialized": self.current_state["initialized"],
                    "current_url": self.current_state["current_url"],
                    "task_id": self.current_state["task_id"],
                    "action_count": len(self.current_state["history"]),
                    "last_error": self.current_state["last_error"]
                },
                "page_state": page_state,
                "screenshot": screenshot
            }
        except Exception as e:
            error_msg = f"Error getting state: {str(e)}"
            self.current_state["last_error"] = error_msg
            logger.error(error_msg)
            return {"status": "error", "message": error_msg}
    
    async def execute_action_sequence(self, actions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Execute a sequence of actions in order.
        
        Args:
            actions: List of action objects with name and params keys
            
        Returns:
            Dictionary with results of all actions
        """
        if not actions:
            return {"status": "error", "message": "No actions provided"}
        
        results = []
        all_successful = True
        
        for i, action in enumerate(actions):
            action_name = action.get("name")
            action_params = action.get("params", {})
            
            if not action_name:
                return {"status": "error", "message": f"Action at index {i} missing name"}
            
            logger.info(f"Executing action {i+1}/{len(actions)}: {action_name}")
            
            # Execute the action using the appropriate method
            result = None
            if action_name == "navigate_to_url":
                result = await self.navigate_to_url(action_params.get("url", ""))
            elif action_name == "click_element":
                result = await self.click_element(
                    action_params.get("selector", ""), 
                    action_params.get("index", 0),
                    action_params.get("timeout", 10000)
                )
            elif action_name == "input_text":
                result = await self.input_text(
                    action_params.get("selector", ""),
                    action_params.get("text", ""),
                    action_params.get("delay", 50)
                )
            elif action_name == "get_dom":
                result = await self.get_dom()
            elif action_name == "capture_screenshot":
                result = await self.capture_screenshot(action_params.get("full_page", True))
            elif action_name == "wait":
                result = await self.wait(action_params.get("time", 1000))
            else:
                # For other actions, use the controller directly
                result = await self.controller.execute_action(action_name, action_params)
            
            results.append({
                "action_name": action_name,
                "action_index": i,
                "result": result
            })
            
            # If an action fails, stop the sequence
            if result.get("status") != "success":
                all_successful = False
                logger.error(f"Action sequence failed at step {i+1}: {action_name}")
                break
        
        return {
            "status": "success" if all_successful else "error",
            "message": f"Executed {len(results)}/{len(actions)} actions" + ("" if all_successful else " with errors"),
            "results": results
        }
    
    async def shutdown(self) -> Dict[str, Any]:
        """
        Shutdown the agent and close the browser.
        
        Returns:
            Dictionary with shutdown status
        """
        try:
            await self.browser.close()
            self.current_state["initialized"] = False
            logger.info("Agent shut down successfully")
            return {"status": "success", "message": "Agent shut down successfully"}
        except Exception as e:
            error_msg = f"Shutdown error: {str(e)}"
            self.current_state["last_error"] = error_msg
            logger.error(error_msg)
            return {"status": "error", "message": error_msg}
    
    async def interpret_task(self, task_description: str, page_state: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Use LLM to interpret a natural language task description and convert it to an action plan.
        
        Args:
            task_description: Natural language description of the task
            page_state: Optional current page state to provide context to the LLM
            
        Returns:
            Dictionary with the action plan
        """
        try:
            if not self.llm_service or not self.message_manager or not self.response_parser:
                raise ValueError("LLM components not initialized. Call initialize() first.")
                
            # Read system prompt
            system_prompt_path = os.path.join(os.path.dirname(__file__), "system_prompt.md")
            with open(system_prompt_path, "r") as f:
                system_prompt = f.read()
            
            # Add page state context if available
            if page_state:
                # Prepare a simplified representation of the page state for the LLM
                page_context = f"""
                Current page: {page_state.get('url', 'Unknown')}
                Page title: {page_state.get('title', 'Unknown')}
                Available elements:
                """
                
                # Add information about interactive elements if available
                if "elements" in page_state:
                    for i, element in enumerate(page_state["elements"]):
                        element_type = element.get("type", "unknown")
                        element_text = element.get("text", "")[:50]  # Truncate long text
                        page_context += f"  {i}: {element_type} - {element_text}\n"
                
                # Add page context to the task description
                augmented_task = f"Current page state:\n{page_context}\n\nUser task: {task_description}"
            else:
                augmented_task = task_description
                
            # Add user message to conversation history
            self.message_manager.add_user_message(task_description)
            
            # Generate LLM response
            llm_response = await self.llm_service.generate_response(
                system_prompt=system_prompt,
                user_input=augmented_task,
                conversation_history=self.message_manager.get_messages()[:-1]  # Exclude the message we just added
            )
            
            # Parse the response
            action_plan = self.response_parser.parse_response(llm_response)
            
            # Add assistant message to conversation history
            self.message_manager.add_assistant_message(llm_response)
            
            logger.info(f"Task interpreted: {task_description} -> {action_plan['action']}")
            return {
                "status": "success",
                "action_plan": action_plan,
                "raw_response": llm_response
            }
        except ActionValidationError as e:
            error_msg = f"Invalid action plan: {str(e)}"
            self.current_state["last_error"] = error_msg
            logger.error(error_msg)
            return {"status": "error", "message": error_msg, "raw_response": llm_response if 'llm_response' in locals() else None}
        except Exception as e:
            error_msg = f"Task interpretation error: {str(e)}"
            self.current_state["last_error"] = error_msg
            logger.error(error_msg)
            return {"status": "error", "message": error_msg}
    
    async def execute_from_natural_language(self, task_description: str, task_id: str = None) -> Dict[str, Any]:
        """
        Execute a task described in natural language.
        
        Args:
            task_description: Natural language description of the task
            task_id: Optional task ID for tracking
            
        Returns:
            Dictionary with execution results
        """
        try:
            # Ensure agent is initialized
            init_result = await self.ensure_initialized()
            if init_result["status"] != "success":
                error_msg = f"Failed to initialize agent: {init_result['message']}"
                logger.error(error_msg)
                task_manager.fail(task_id, error_msg)
                return {"status": "error", "message": error_msg}
            
            # Start task tracking
            if task_id:
                task_manager.start(task_id)
                task_manager.add_log(task_id, f"Starting task: {task_description}")
            
            # Get current page state for context
            try:
                page_state = await self.browser.get_page_state()
            except Exception as e:
                page_state = {"error": str(e)}
            
            # Update conversation history with task
            self.message_manager.add_user_message(task_description)
            
            # Get LLM response
            try:
                llm_response = await self.llm_service.get_response(
                    self.message_manager.get_messages(),
                    page_state
                )
                
                # Parse and validate response
                try:
                    action_plan = self.response_parser.parse_response(llm_response)
                except ActionValidationError as e:
                    error_msg = f"Invalid action plan: {str(e)}"
                    logger.error(error_msg)
                    if task_id:
                        task_manager.fail(task_id, error_msg)
                    return {"status": "error", "message": error_msg}
                
                # Execute each action in the plan
                results = []
                for action in action_plan:
                    try:
                        # Update task progress
                        if task_id:
                            progress = (len(results) + 1) / len(action_plan) * 100
                            task_manager.update_progress(task_id, progress, f"Executing action: {action['action']}")
                        
                        # Execute the action
                        action_result = await self.controller.execute_action(
                            action["action"],
                            action.get("params", {})
                        )
                        
                        # Handle action result
                        if action_result["status"] != "success":
                            error_msg = f"Action failed: {action_result.get('message', 'Unknown error')}"
                            logger.error(error_msg)
                            if task_id:
                                task_manager.fail(task_id, error_msg)
                            return {"status": "error", "message": error_msg}
                        
                        # Add result to history
                        results.append({
                            "action": action["action"],
                            "params": action.get("params", {}),
                            "result": action_result["result"]
                        })
                        
                        # Update conversation history
                        self.message_manager.add_assistant_message(
                            f"Executed {action['action']} successfully"
                        )
                        
                    except Exception as e:
                        error_msg = f"Error executing action {action['action']}: {str(e)}"
                        logger.error(error_msg)
                        if task_id:
                            task_manager.fail(task_id, error_msg)
                        return {"status": "error", "message": error_msg}
                
                # Complete task successfully
                if task_id:
                    task_manager.complete(task_id, {"results": results})
                
                return {
                    "status": "success",
                    "results": results,
                    "conversation": self.message_manager.get_messages()
                }
                
            except Exception as e:
                error_msg = f"LLM error: {str(e)}"
                logger.error(error_msg)
                if task_id:
                    task_manager.fail(task_id, error_msg)
                return {"status": "error", "message": error_msg}
            
        except Exception as e:
            error_msg = f"Task execution error: {str(e)}"
            logger.error(error_msg)
            if task_id:
                task_manager.fail(task_id, error_msg)
            return {"status": "error", "message": error_msg}
    
    async def _handle_plan_task(self, task_description: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle the plan_task action, which breaks down a complex task into steps.
        
        Args:
            task_description: The original task description from the user
            parameters: The action parameters, including 'steps' and 'thought'
            
        Returns:
            Dictionary with planning result information
        """
        try:
            steps = parameters.get("steps", [])
            thought = parameters.get("thought", "")
            
            if not steps:
                error_msg = "No steps provided in plan_task action"
                self.current_state["last_error"] = error_msg
                logger.error(error_msg)
                return {"status": "error", "message": error_msg}
            
            # Start task planning in the message manager
            self.message_manager.start_task_planning(task_description)
            self.message_manager.set_task_steps(steps)
            
            # Update the current state
            self.current_state["multi_step_tasks"]["active"] = True
            self.current_state["multi_step_tasks"]["current_plan"] = {
                "original_task": task_description,
                "steps": steps,
                "current_step_index": 0,
                "completed_steps": [],
                "status": "executing"
            }
            
            # Add to history
            self.current_state["history"].append({
                "task": task_description,
                "action": "plan_task",
                "timestamp": time.time(),
                "result": "success",
                "steps": steps
            })
            
            logger.info(f"Created task plan with {len(steps)} steps for: {task_description}")
            
            # Return information about the plan
            return {
                "status": "success",
                "message": f"Task plan created with {len(steps)} steps",
                "thought": thought,
                "action": "plan_task",
                "parameters": parameters,
                "plan": {
                    "steps": steps,
                    "current_step_index": 0,
                    "total_steps": len(steps)
                }
            }
        except Exception as e:
            error_msg = f"Error creating task plan: {str(e)}"
            self.current_state["last_error"] = error_msg
            logger.error(error_msg)
            return {"status": "error", "message": error_msg}
    
    async def _handle_execute_step(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle the execute_step action, which executes a step in a multi-step task plan.
        
        Args:
            parameters: The action parameters, including 'step_index', 'action', and 'parameters'
            
        Returns:
            Dictionary with execution result information
        """
        try:
            step_index = parameters.get("step_index", -1)
            action = parameters.get("action", "")
            action_parameters = parameters.get("parameters", {})
            
            # Check if there's an active task plan
            if not self.current_state["multi_step_tasks"]["active"]:
                error_msg = "No active task plan for execute_step action"
                self.current_state["last_error"] = error_msg
                logger.error(error_msg)
                return {"status": "error", "message": error_msg}
            
            # Check if the step index is valid
            if (step_index < 0 or 
                step_index >= len(self.current_state["multi_step_tasks"]["current_plan"]["steps"])):
                error_msg = f"Invalid step_index: {step_index}"
                self.current_state["last_error"] = error_msg
                logger.error(error_msg)
                return {"status": "error", "message": error_msg}
            
            # Get the current plan and step
            current_plan = self.current_state["multi_step_tasks"]["current_plan"]
            current_step = current_plan["steps"][step_index]
            
            # Log the step execution
            logger.info(f"Executing step {step_index + 1}: '{current_step}' with action: {action}")
            
            # Start the step in the message manager
            step_info = self.message_manager.start_step(step_index)
            if "error" in step_info:
                return {"status": "error", "message": step_info["error"]}
            
            # Execute the action for this step
            result = await self.execute_action(action, action_parameters)
            
            # Add to history
            self.current_state["history"].append({
                "task": f"Step {step_index + 1}: {current_step}",
                "action": action,
                "timestamp": time.time(),
                "result": result["status"],
                "step_index": step_index
            })
            
            # Handle success or failure
            if result["status"] == "success":
                # Complete the step in the message manager
                completion_info = self.message_manager.complete_step(step_index, result)
                
                # Update the current state
                current_plan["completed_steps"].append({
                    "index": step_index,
                    "description": current_step,
                    "action": action,
                    "parameters": action_parameters,
                    "result": result,
                    "timestamp": time.time()
                })
                
                # Check if there are more steps
                if "next_step" in completion_info:
                    # Move to the next step
                    next_step_index = completion_info["next_step"]["index"]
                    current_plan["current_step_index"] = next_step_index
                    
                    return {
                        "status": "success",
                        "message": f"Step {step_index + 1} completed successfully, moving to step {next_step_index + 1}",
                        "action": action,
                        "parameters": action_parameters,
                        "result": result,
                        "next_step": {
                            "index": next_step_index,
                            "description": current_plan["steps"][next_step_index]
                        }
                    }
                else:
                    # All steps completed
                    current_plan["status"] = "completed"
                    current_plan["current_step_index"] = -1  # No current step
                    
                    return {
                        "status": "success",
                        "message": "All steps completed successfully",
                        "action": action,
                        "parameters": action_parameters,
                        "result": result,
                        "task_completed": True,
                        "steps_executed": len(current_plan["completed_steps"])
                    }
            else:
                # Step failed
                error_message = result.get("message", "Unknown error")
                failure_info = self.message_manager.fail_step(step_index, error_message)
                
                # Update the current state
                current_plan["status"] = "failed"
                
                return {
                    "status": "error",
                    "message": f"Step {step_index + 1} failed: {error_message}",
                    "action": action,
                    "parameters": action_parameters,
                    "result": result,
                    "step_index": step_index
                }
        except Exception as e:
            error_msg = f"Error executing step: {str(e)}"
            self.current_state["last_error"] = error_msg
            logger.error(error_msg)
            return {"status": "error", "message": error_msg}
    
    async def get_task_plan_status(self) -> Dict[str, Any]:
        """
        Get the current status of the active task plan.
        
        Returns:
            Dictionary with task plan status information
        """
        if not self.message_manager:
            return {
                "status": "error",
                "message": "Message manager not initialized"
            }
            
        plan_status = self.message_manager.get_task_plan_status()
        
        return {
            "status": "success",
            "task_plan": plan_status
        }
    
    async def reset_task_plan(self) -> Dict[str, Any]:
        """
        Reset the current task plan.
        
        Returns:
            Dictionary with reset status
        """
        if not self.message_manager:
            return {
                "status": "error",
                "message": "Message manager not initialized"
            }
            
        # Reset the task plan in the message manager
        self.message_manager.task_plan = {
            "active": False,
            "steps": [],
            "current_step_index": -1,
            "completed_steps": [],
            "status": "idle",
            "original_task": None
        }
        
        # Reset the state in the agent
        self.current_state["multi_step_tasks"] = {
            "active": False,
            "current_plan": None
        }
        
        logger.info("Task plan reset")
        return {
            "status": "success",
            "message": "Task plan reset successfully"
        }
    
    async def execute_action(self, action: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a specific action with parameters.
        
        Args:
            action: Action name
            parameters: Action parameters
            
        Returns:
            Dictionary with action results, standardized format with 'status' field
        """
        try:
            # Log action execution with parameters (excluding sensitive data)
            safe_params = self._get_safe_params_for_logging(action, parameters)
            logger.info(f"Executing action: {action} with parameters: {safe_params}")
            
            # Get the current task_id for WebSocket broadcasts
            task_id = self.current_state.get("task_id")
            
            # Pass the task_id to the controller
            action_result = await self.controller.execute_action(action, parameters, task_id)
            
            # Handle success case
            if action_result["status"] == "success":
                logger.info(f"Action {action} executed successfully")
                return {
                    "status": "success",
                    "action": action,
                    "result": action_result["result"]
                }
            # Handle error case
            else:
                error_msg = action_result.get("message", "Unknown error")
                logger.error(f"Action {action} failed: {error_msg}")
                
                # Update error state
                self.current_state["last_error"] = error_msg
                
                return {
                    "status": "error",
                    "action": action,
                    "message": error_msg,
                    "details": action_result.get("errors", {})
                }
        except Exception as e:
            error_msg = f"Error executing action {action}: {str(e)}"
            logger.exception(error_msg)
            
            # Update error state
            self.current_state["last_error"] = error_msg
            
            return {
                "status": "error",
                "action": action,
                "message": error_msg
            }

    def _get_safe_params_for_logging(self, action: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Get a safe version of parameters for logging, with sensitive data redacted.
        
        Args:
            action: The action being executed
            parameters: The parameters for the action
            
        Returns:
            Dictionary with sensitive data redacted
        """
        # Create a copy to avoid modifying the original
        safe_params = parameters.copy()
        
        # Redact sensitive data based on action type
        if action == "input_text" and "text" in safe_params:
            # Redact text content but show length
            text_length = len(safe_params["text"])
            safe_params["text"] = f"[REDACTED - {text_length} chars]"
        
        # For nested parameters in execute_step
        if action == "execute_step" and "parameters" in safe_params:
            nested_action = safe_params.get("action", "")
            safe_params["parameters"] = self._get_safe_params_for_logging(
                nested_action, 
                safe_params["parameters"]
            )
        
        return safe_params

# Singleton instance
agent_service = AgentService() 