#!/usr/bin/env python3
"""
Test FORM-01: Login form completion (username/password)
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
        logging.FileHandler("test_form_01.log"),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("test_form_01")

# Configuration
API_BASE_URL = "http://localhost:8000/api/v1"
WS_URL = "ws://localhost:8000/api/v1/ws"
TEST_CLIENT_ID = "test-client-123"
TEST_URL = "https://httpbin.org/forms/post"  # Public form test page
TEST_USERNAME = "testuser"
TEST_PASSWORD = "testpassword123"

# Test metrics
metrics = {
    "start_time": None,
    "agent_execution_time": None,
    "first_screenshot_time": None,
    "typing_indicator_time": None,
    "form_completion_time": None,
    "test_result": "FAILED",  # Will be set to "PASSED" if successful
    "typing_indicators_received": 0,
    "action_feedback_received": 0,
    "errors": []
}

class WebSocketClient:
    def __init__(self, url, client_id):
        self.url = f"{url}?client_id={client_id}"
        self.ws = None
        self.task_id = None
        self.received_screenshot = False
        self.received_typing_indicator = False
        self.form_submitted = False
        self.messages = []
        
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
    
    async def listen(self, timeout=60):
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
                    
                    # Check if we've received everything we need
                    if self.received_screenshot and self.received_typing_indicator and self.form_submitted:
                        logger.info("All required form actions completed")
                        metrics["form_completion_time"] = time.time()
                        break
                except asyncio.TimeoutError:
                    # This is just a timeout for the current recv() call
                    # We continue listening until the overall timeout
                    continue
                    
            # Check what data we received
            if not self.received_screenshot:
                logger.warning("No screenshot update received")
                metrics["errors"].append("No screenshot update received")
                
            if not self.received_typing_indicator:
                logger.warning("No typing indicators received")
                metrics["errors"].append("No typing feedback received")
                
            if not self.form_submitted:
                logger.warning("Form submission not detected")
                metrics["errors"].append("Form submission action not detected")
                
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
                    logger.info("Received screenshot update")
                    if not self.received_screenshot:
                        self.received_screenshot = True
                        metrics["first_screenshot_time"] = time.time()
                
                # Handle action feedback (typing, clicks, etc.)
                if data.get("type") == "browser_action_feedback":
                    action_type = data.get("actionType")
                    action_data = data.get("data", {})
                    
                    metrics["action_feedback_received"] += 1
                    logger.info(f"Received action feedback: {action_type}")
                    
                    # Track typing indicators
                    if action_type == "typing":
                        metrics["typing_indicators_received"] += 1
                        content = action_data.get("content", "")
                        logger.info(f"Typing indicator content: {content}")
                        
                        # Check if our test username or password was typed
                        if TEST_USERNAME in content or TEST_PASSWORD in content:
                            logger.info("Test credentials detected in typing indicator")
                            
                        if not self.received_typing_indicator:
                            self.received_typing_indicator = True
                            metrics["typing_indicator_time"] = time.time()
                    
                    # Track click actions for form submission
                    if action_type == "click":
                        # If we get a click after typing, assume it might be form submission
                        if self.received_typing_indicator and not self.form_submitted:
                            logger.info("Potential form submission click detected")
                            self.form_submitted = True
                
                # Check for form submission in URL changes
                if data.get("type") == "browser_state_update":
                    url = data.get("currentUrl", "")
                    if "post" in url.lower() and not self.form_submitted:
                        logger.info(f"Form submission detected through URL change: {url}")
                        self.form_submitted = True
                        
        except json.JSONDecodeError:
            logger.error(f"Failed to parse WebSocket message: {message_str}")
        except Exception as e:
            logger.error(f"Error processing message: {e}")
    
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
            "max_steps": 10  # Limit steps for testing
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
    """Run the end-to-end test for form interaction"""
    logger.info("Starting FORM-01 test: Login form completion")
    metrics["start_time"] = time.time()
    
    # Step 1: Execute agent task to fill and submit the form
    prompt = f"Go to {TEST_URL}, fill out the form with username '{TEST_USERNAME}' and password '{TEST_PASSWORD}', then submit the form."
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
        
    # Step 4: Wait for form completion and action updates
    await ws_client.listen(timeout=60)
    
    # Step 5: Evaluate test results
    success = (
        ws_client.received_screenshot and 
        ws_client.received_typing_indicator and 
        ws_client.form_submitted and
        metrics["typing_indicators_received"] >= 2  # At least username and password
    )
    
    if success:
        logger.info("Test FORM-01 PASSED")
        metrics["test_result"] = "PASSED"
        return True
    else:
        logger.error("Test FORM-01 FAILED")
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
        
    if metrics["typing_indicator_time"]:
        typing_time = metrics["typing_indicator_time"] - start
        print(f"First Typing Indicator Time: {typing_time:.2f}s")
        
    if metrics["form_completion_time"]:
        completion_time = metrics["form_completion_time"] - start
        print(f"Form Completion Time: {completion_time:.2f}s")
    
    print(f"Typing Indicators Received: {metrics['typing_indicators_received']}")
    print(f"Total Action Feedback Messages: {metrics['action_feedback_received']}")
    
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