#!/usr/bin/env python3
"""
Test FLOW-01: Search-click-extract workflow
Tests a multi-step workflow involving search, result selection, and data extraction.
"""
import sys
import os
import time
import json
import requests
import asyncio
import websockets
import logging
from datetime import datetime

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("test_flow_01.log"),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("test_flow_01")

# Configuration
API_BASE_URL = "http://localhost:8000/api/v1"
WS_URL = "ws://localhost:8000/api/v1/ws"
TEST_CLIENT_ID = "test-client-123"
TEST_SEARCH_URL = "https://www.wikipedia.org"
TEST_SEARCH_TERM = "Python programming language"

# Test metrics
metrics = {
    "start_time": None,
    "agent_execution_time": None,
    "first_screenshot_time": None,
    "navigation_time": None,
    "search_submission_time": None,
    "result_click_time": None,
    "extraction_time": None,
    "workflow_completion_time": None,
    "test_result": "FAILED",  # Will be set to "PASSED" if successful
    "action_feedback_received": 0,
    "screenshot_count": 0,
    "errors": []
}

class WorkflowStep:
    def __init__(self, name, required_action=None, completion_indicator=None):
        self.name = name
        self.required_action = required_action
        self.completion_indicator = completion_indicator
        self.completed = False
        self.start_time = None
        self.completion_time = None

class WebSocketClient:
    def __init__(self, url, client_id):
        self.url = f"{url}?client_id={client_id}"
        self.ws = None
        self.task_id = None
        self.messages = []
        
        # Define workflow steps
        self.steps = {
            "navigation": WorkflowStep(
                "Navigation",
                required_action="navigate",
                completion_indicator=lambda data: TEST_SEARCH_URL in data.get("currentUrl", "")
            ),
            "search": WorkflowStep(
                "Search",
                required_action="typing",
                completion_indicator=lambda data: TEST_SEARCH_TERM in data.get("content", "")
            ),
            "click_result": WorkflowStep(
                "Click Result",
                required_action="click",
                completion_indicator=lambda data: "python" in data.get("currentUrl", "").lower()
            ),
            "extract_data": WorkflowStep(
                "Extract Data",
                required_action="extract",
                completion_indicator=lambda data: "content" in data
            )
        }
        
    async def connect(self):
        logger.info(f"Connecting to WebSocket at {self.url}")
        try:
            self.ws = await websockets.connect(self.url)
            logger.info("WebSocket connection established")
            return True
        except Exception as e:
            logger.error(f"WebSocket connection failed: {e}")
            metrics["errors"].append(f"WebSocket connection error: {str(e)}")
            return False
            
    async def subscribe_to_task(self, task_id):
        if not self.ws:
            logger.error("No WebSocket connection")
            return False
            
        self.task_id = task_id
        logger.info(f"Subscribing to task {task_id}")
        
        try:
            message = {
                "type": "subscribe_task",
                "task_id": task_id
            }
            await self.ws.send(json.dumps(message))
            return True
        except Exception as e:
            logger.error(f"Failed to subscribe to task: {e}")
            metrics["errors"].append(f"Task subscription error: {str(e)}")
            return False
    
    async def listen(self, timeout=120):  # Longer timeout for multi-step workflow
        if not self.ws:
            logger.error("No WebSocket connection")
            return
            
        logger.info(f"Listening for WebSocket messages (timeout: {timeout}s)")
        start_time = time.time()
        
        try:
            while time.time() - start_time < timeout:
                try:
                    message = await asyncio.wait_for(self.ws.recv(), timeout=1.0)
                    await self.process_message(message)
                    
                    # Check if all steps are completed
                    if all(step.completed for step in self.steps.values()):
                        logger.info("All workflow steps completed")
                        metrics["workflow_completion_time"] = time.time()
                        break
                except asyncio.TimeoutError:
                    continue
                    
            # Check completion of each step
            for step_name, step in self.steps.items():
                if not step.completed:
                    logger.warning(f"Step {step_name} did not complete")
                    metrics["errors"].append(f"Step {step_name} did not complete")
                
        except Exception as e:
            logger.error(f"Error while listening for messages: {e}")
            metrics["errors"].append(f"WebSocket listener error: {str(e)}")
        finally:
            await self.close()
                
    async def process_message(self, message_str):
        try:
            message = json.loads(message_str)
            self.messages.append(message)
            
            if message.get("type") == "task_update":
                data = message.get("data", {})
                
                # Handle screenshot updates
                if data.get("type") == "browser_screenshot_update" and data.get("screenshot"):
                    metrics["screenshot_count"] += 1
                    if not metrics.get("first_screenshot_time"):
                        metrics["first_screenshot_time"] = time.time()
                
                # Handle browser state updates
                if data.get("type") == "browser_state_update":
                    self.check_step_completion("navigation", data)
                    self.check_step_completion("click_result", data)
                
                # Handle action feedback
                if data.get("type") == "browser_action_feedback":
                    metrics["action_feedback_received"] += 1
                    action_type = data.get("actionType")
                    action_data = data.get("data", {})
                    
                    # Check for step completion based on action type
                    if action_type == "typing":
                        self.check_step_completion("search", action_data)
                    elif action_type == "click":
                        self.check_step_completion("click_result", action_data)
                    elif action_type == "extract":
                        self.check_step_completion("extract_data", action_data)
                
                # Handle extracted content
                if data.get("type") == "extracted_content":
                    self.check_step_completion("extract_data", data)
                    
        except json.JSONDecodeError:
            logger.error(f"Failed to parse WebSocket message: {message_str}")
        except Exception as e:
            logger.error(f"Error processing message: {e}")
    
    def check_step_completion(self, step_name, data):
        step = self.steps.get(step_name)
        if step and not step.completed:
            if step.completion_indicator(data):
                step.completed = True
                step.completion_time = time.time()
                logger.info(f"Step {step_name} completed")
                
                # Update specific metrics based on step completion
                if step_name == "navigation":
                    metrics["navigation_time"] = step.completion_time
                elif step_name == "search":
                    metrics["search_submission_time"] = step.completion_time
                elif step_name == "click_result":
                    metrics["result_click_time"] = step.completion_time
                elif step_name == "extract_data":
                    metrics["extraction_time"] = step.completion_time
    
    async def close(self):
        if self.ws:
            await self.ws.close()
            logger.info("WebSocket connection closed")

async def execute_agent_task(prompt):
    """Execute an agent task via the API and return the task ID"""
    try:
        url = f"{API_BASE_URL}/agent/execute"
        payload = {
            "task": prompt,
            "model": "gpt-3.5-turbo",  # Use whatever model your backend supports
            "max_steps": 15  # Limit steps for testing
        }
        
        logger.info(f"Executing agent task with prompt: {prompt}")
        response = requests.post(url, json=payload)
        
        if response.status_code != 200:
            logger.error(f"Failed to execute task: {response.status_code} - {response.text}")
            metrics["errors"].append(f"API error: {response.status_code} - {response.text}")
            return None
            
        result = response.json()
        logger.info(f"Task created with ID: {result.get('task_id')}")
        return result.get("task_id")
    except Exception as e:
        logger.error(f"Error executing agent task: {e}")
        metrics["errors"].append(f"Task execution error: {str(e)}")
        return None

async def run_test():
    """Run the end-to-end test for the search-click-extract workflow"""
    logger.info("Starting FLOW-01 test: Search-click-extract workflow")
    metrics["start_time"] = time.time()
    
    # Step 1: Execute agent task with the multi-step workflow prompt
    prompt = (
        f"Go to {TEST_SEARCH_URL}, search for '{TEST_SEARCH_TERM}', "
        "click on the first relevant result, and extract the first paragraph "
        "of content about Python programming."
    )
    task_id = await execute_agent_task(prompt)
    
    if not task_id:
        logger.error("Test failed: Could not create task")
        return False
        
    metrics["agent_execution_time"] = time.time()
    
    # Step 2: Connect to WebSocket and listen for updates
    ws_client = WebSocketClient(WS_URL, TEST_CLIENT_ID)
    if not await ws_client.connect():
        logger.error("Test failed: Could not connect to WebSocket")
        return False
        
    # Step 3: Subscribe to task updates
    if not await ws_client.subscribe_to_task(task_id):
        logger.error("Test failed: Could not subscribe to task")
        return False
        
    # Step 4: Wait for workflow completion
    await ws_client.listen(timeout=120)
    
    # Step 5: Evaluate test results
    success = all(step.completed for step in ws_client.steps.values())
    
    if success:
        logger.info("Test FLOW-01 PASSED")
        metrics["test_result"] = "PASSED"
        return True
    else:
        logger.error("Test FLOW-01 FAILED")
        return False

def print_metrics():
    """Print test metrics in a readable format"""
    if not metrics["start_time"]:
        return
        
    print("\n--- TEST METRICS ---")
    print(f"Test Result: {metrics['test_result']}")
    
    start = metrics["start_time"]
    
    if metrics["agent_execution_time"]:
        agent_time = metrics["agent_execution_time"] - start
        print(f"API Response Time: {agent_time:.2f}s")
        
    if metrics["first_screenshot_time"]:
        screenshot_time = metrics["first_screenshot_time"] - start
        print(f"First Screenshot Time: {screenshot_time:.2f}s")
        
    if metrics["navigation_time"]:
        nav_time = metrics["navigation_time"] - start
        print(f"Navigation Time: {nav_time:.2f}s")
        
    if metrics["search_submission_time"]:
        search_time = metrics["search_submission_time"] - start
        print(f"Search Submission Time: {search_time:.2f}s")
        
    if metrics["result_click_time"]:
        click_time = metrics["result_click_time"] - start
        print(f"Result Click Time: {click_time:.2f}s")
        
    if metrics["extraction_time"]:
        extract_time = metrics["extraction_time"] - start
        print(f"Content Extraction Time: {extract_time:.2f}s")
        
    if metrics["workflow_completion_time"]:
        total_time = metrics["workflow_completion_time"] - start
        print(f"Total Workflow Time: {total_time:.2f}s")
    
    print(f"Screenshots Received: {metrics['screenshot_count']}")
    print(f"Action Feedback Messages: {metrics['action_feedback_received']}")
    
    if metrics["errors"]:
        print("\nErrors:")
        for error in metrics["errors"]:
            print(f"- {error}")
    
    print("-------------------\n")

async def main():
    try:
        success = await run_test()
        print_metrics()
        return 0 if success else 1
    except Exception as e:
        logger.error(f"Unhandled exception: {e}", exc_info=True)
        return 1

if __name__ == "__main__":
    result = asyncio.run(main())
    sys.exit(result) 