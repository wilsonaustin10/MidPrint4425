"""
Message manager for handling conversation context and message history.
"""
import json
import logging
from typing import Dict, List, Any, Optional

# Set up logger
logger = logging.getLogger(__name__)

class MessageManager:
    """
    Manages conversation context and message history for the LLM.
    Maintains the state of the conversation and provides methods for adding and retrieving messages.
    """
    
    def __init__(self, max_history_length: int = 10):
        """
        Initialize the message manager.
        
        Args:
            max_history_length: Maximum number of messages to keep in history
        """
        self.messages = []
        self.max_history_length = max_history_length
        self.state = {}
        
        # New fields for multi-step task planning
        self.task_plan = {
            "active": False,
            "steps": [],
            "current_step_index": -1,
            "completed_steps": [],
            "status": "idle",  # idle, planning, executing, completed, failed
            "original_task": None
        }
        
        logger.info(f"MessageManager initialized with max_history_length={max_history_length}")
    
    def add_user_message(self, content: str) -> None:
        """
        Add a user message to the conversation history.
        
        Args:
            content: The content of the user message
        """
        message = {"role": "user", "content": content}
        self.messages.append(message)
        self._trim_history()
        logger.debug(f"Added user message: {content}")
    
    def add_assistant_message(self, content: str) -> None:
        """
        Add an assistant message to the conversation history.
        
        Args:
            content: The content of the assistant message
        """
        message = {"role": "assistant", "content": content}
        self.messages.append(message)
        self._trim_history()
        logger.debug(f"Added assistant message: {content}")
    
    def add_system_message(self, content: str) -> None:
        """
        Add a system message to the conversation history.
        
        Args:
            content: The content of the system message
        """
        message = {"role": "system", "content": content}
        self.messages.append(message)
        self._trim_history()
        logger.debug(f"Added system message: {content}")
    
    def get_messages(self) -> List[Dict[str, str]]:
        """
        Get all messages in the conversation history.
        
        Returns:
            List of message dictionaries with 'role' and 'content' keys
        """
        return self.messages.copy()
    
    def clear_history(self) -> None:
        """Clear the conversation history."""
        self.messages = []
        logger.info("Conversation history cleared")
    
    def _trim_history(self) -> None:
        """Trim the conversation history to the maximum length."""
        if len(self.messages) > self.max_history_length:
            # Keep the most recent messages
            self.messages = self.messages[-self.max_history_length:]
            logger.debug(f"Trimmed conversation history to {self.max_history_length} messages")
    
    def update_state(self, key: str, value: Any) -> None:
        """
        Update the state with a key-value pair.
        
        Args:
            key: The state key
            value: The state value
        """
        self.state[key] = value
        logger.debug(f"Updated state: {key}={value}")
    
    def get_state(self, key: str, default: Any = None) -> Any:
        """
        Get a value from the state.
        
        Args:
            key: The state key
            default: Default value to return if key is not found
            
        Returns:
            The state value or default if key is not found
        """
        return self.state.get(key, default)
    
    def get_full_state(self) -> Dict[str, Any]:
        """
        Get the full state dictionary.
        
        Returns:
            The current state dictionary
        """
        return self.state.copy()
    
    def clear_state(self) -> None:
        """Clear the state."""
        self.state = {}
        logger.info("State cleared")
    
    # New methods for multi-step task planning
    
    def start_task_planning(self, original_task: str) -> None:
        """
        Start planning a multi-step task.
        
        Args:
            original_task: The original task description from the user
        """
        self.task_plan = {
            "active": True,
            "steps": [],
            "current_step_index": -1,
            "completed_steps": [],
            "status": "planning",
            "original_task": original_task
        }
        logger.info(f"Started task planning for: {original_task}")
        
    def set_task_steps(self, steps: List[str]) -> None:
        """
        Set the steps for a task plan.
        
        Args:
            steps: List of step descriptions
        """
        if not self.task_plan["active"]:
            logger.warning("Attempted to set task steps when no task plan is active")
            return
            
        self.task_plan["steps"] = steps
        self.task_plan["status"] = "executing"
        self.task_plan["current_step_index"] = 0
        
        # Add system message with the plan
        steps_text = "\n".join([f"Step {i+1}: {step}" for i, step in enumerate(steps)])
        plan_message = f"I've broken down this task into the following steps:\n{steps_text}"
        self.add_system_message(plan_message)
        
        logger.info(f"Set {len(steps)} task steps: {steps}")
    
    def start_step(self, step_index: int) -> Dict[str, Any]:
        """
        Start executing a specific step in the task plan.
        
        Args:
            step_index: The index of the step to execute
            
        Returns:
            Dictionary with step information
        """
        if not self.task_plan["active"]:
            logger.warning("Attempted to start step when no task plan is active")
            return {"error": "No active task plan"}
            
        if step_index >= len(self.task_plan["steps"]):
            logger.warning(f"Attempted to start step {step_index} but only {len(self.task_plan['steps'])} steps exist")
            return {"error": f"Step index {step_index} out of range"}
        
        self.task_plan["current_step_index"] = step_index
        current_step = self.task_plan["steps"][step_index]
        
        # Add system message about starting this step
        step_message = f"Starting step {step_index + 1}: {current_step}"
        self.add_system_message(step_message)
        
        logger.info(f"Starting step {step_index}: {current_step}")
        return {
            "index": step_index,
            "description": current_step,
            "status": "in_progress"
        }
    
    def complete_step(self, step_index: int, result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Mark a step as completed and store its result.
        
        Args:
            step_index: The index of the completed step
            result: The result of the step execution
            
        Returns:
            Dictionary with next step information or completion status
        """
        if not self.task_plan["active"]:
            logger.warning("Attempted to complete step when no task plan is active")
            return {"error": "No active task plan"}
            
        if step_index >= len(self.task_plan["steps"]):
            logger.warning(f"Attempted to complete step {step_index} but only {len(self.task_plan['steps'])} steps exist")
            return {"error": f"Step index {step_index} out of range"}
        
        # Record the completion
        completion = {
            "index": step_index,
            "description": self.task_plan["steps"][step_index],
            "result": result,
            "status": "completed"
        }
        self.task_plan["completed_steps"].append(completion)
        
        # Add system message about completing this step
        step_message = f"Completed step {step_index + 1}: {self.task_plan['steps'][step_index]}"
        if "status" in result:
            step_message += f" - Result: {result['status']}"
        self.add_system_message(step_message)
        
        logger.info(f"Completed step {step_index}")
        
        # Determine next step or completion
        if step_index + 1 < len(self.task_plan["steps"]):
            self.task_plan["current_step_index"] = step_index + 1
            return {
                "next_step": {
                    "index": step_index + 1,
                    "description": self.task_plan["steps"][step_index + 1]
                }
            }
        else:
            # All steps completed
            self.task_plan["status"] = "completed"
            self.add_system_message("All task steps completed successfully")
            logger.info("All task steps completed")
            return {
                "task_completed": True,
                "steps_executed": len(self.task_plan["completed_steps"])
            }
    
    def fail_step(self, step_index: int, error: str) -> Dict[str, Any]:
        """
        Mark a step as failed.
        
        Args:
            step_index: The index of the failed step
            error: The error message
            
        Returns:
            Dictionary with failure information
        """
        if not self.task_plan["active"]:
            logger.warning("Attempted to fail step when no task plan is active")
            return {"error": "No active task plan"}
            
        self.task_plan["status"] = "failed"
        
        # Add system message about the failure
        step_message = f"Failed step {step_index + 1}: {self.task_plan['steps'][step_index]} - Error: {error}"
        self.add_system_message(step_message)
        
        logger.info(f"Failed step {step_index}: {error}")
        return {
            "failed": True,
            "step_index": step_index,
            "error": error
        }
    
    def get_task_plan_status(self) -> Dict[str, Any]:
        """
        Get the current status of the task plan.
        
        Returns:
            Dictionary with task plan status
        """
        return {
            "active": self.task_plan["active"],
            "status": self.task_plan["status"],
            "original_task": self.task_plan["original_task"],
            "total_steps": len(self.task_plan["steps"]),
            "current_step": self.task_plan["current_step_index"],
            "completed_steps": len(self.task_plan["completed_steps"]),
            "steps": self.task_plan["steps"]
        }
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the message manager to a dictionary.
        
        Returns:
            Dictionary representation of the message manager
        """
        return {
            "messages": self.messages,
            "state": self.state,
            "task_plan": self.task_plan
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any], max_history_length: int = 10) -> 'MessageManager':
        """
        Create a message manager from a dictionary.
        
        Args:
            data: Dictionary representation of the message manager
            max_history_length: Maximum number of messages to keep in history
            
        Returns:
            A new MessageManager instance
        """
        manager = cls(max_history_length=max_history_length)
        manager.messages = data.get("messages", [])
        manager.state = data.get("state", {})
        manager.task_plan = data.get("task_plan", {
            "active": False,
            "steps": [],
            "current_step_index": -1,
            "completed_steps": [],
            "status": "idle",
            "original_task": None
        })
        return manager
    
    def serialize(self) -> str:
        """
        Serialize the message manager to a JSON string.
        
        Returns:
            JSON string representation of the message manager
        """
        return json.dumps(self.to_dict())
    
    @classmethod
    def deserialize(cls, json_str: str, max_history_length: int = 10) -> 'MessageManager':
        """
        Create a message manager from a JSON string.
        
        Args:
            json_str: JSON string representation of the message manager
            max_history_length: Maximum number of messages to keep in history
            
        Returns:
            A new MessageManager instance
        """
        data = json.loads(json_str)
        return cls.from_dict(data, max_history_length=max_history_length) 