#!/usr/bin/env python3
"""
Test NAV-01: Simple URL navigation via chat prompt
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
        logging.FileHandler("test_nav_01.log"),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("test_nav_01")

# Configuration
API_BASE_URL = "http://localhost:8000/api/v1"
WS_URL = "ws://localhost:8000/api/v1/ws"
TEST_CLIENT_ID = "test-client-123"
TEST_URL = "https://www.example.com"

# Test metrics
metrics = {
    "start_time": None,
    "agent_execution_time": None,
    "first_screenshot_time": None,
    "navigation_completion_time": None,
    "url_sync_time": None,
    "title_sync_time": None,
    "test_result": "FAILED",  # Will be set to "PASSED" if successful
    "errors": []
}

class WebSocketClient:
    def __init__(self, url, client_id):
        self.url = f"{url}?client_id={client_id}"
        self.ws = None
        self.task_id = None
        self.received_screenshot = False
        self.received_state_update = False
        self.url_synced = False
        self.title_synced = False
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
    
    async def listen(self, timeout=30):
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
                    if self.received_screenshot and self.url_synced and self.title_synced:
                        logger.info("All required updates received")
                        break
                except asyncio.TimeoutError:
                    # This is just a timeout for the current recv() call
                    # We continue listening until the overall timeout
                    continue
                    
            # Check what data we received
            if not self.received_screenshot:
                logger.warning("No screenshot update received")
                metrics["errors"].append("No screenshot update received")
                
            if not self.url_synced:
                logger.warning("No URL state synchronization")
                metrics["errors"].append("URL state not synchronized")
                
            if not self.title_synced:
                logger.warning("No page title synchronization")
                metrics["errors"].append("Page title not synchronized")
                
        except Exception as e:
            logger.error(f"Error while listening for messages: {e}")
            metrics["errors"].append(f"WebSocket listener error: {str(e)}")
        finally:
            await self.close()
                
    async def process_message(self, message_str):
        try:
            message = json.loads(message_str)
            self.messages.append(message)
            logger.debug(f"Received message: {message['type']}")
            
            if message.get("type") == "task_update":
                data = message.get("data", {})
                
                # Handle screenshot updates
                if data.get("type") == "browser_screenshot_update" and data.get("screenshot"):
                    logger.info("Received screenshot update")
                    if not self.received_screenshot:
                        self.received_screenshot = True
                        metrics["first_screenshot_time"] = time.time()
                
                # Handle browser state updates
                if data.get("type") == "browser_state_update":
                    logger.info(f"Received state update: URL={data.get('currentUrl')}, Title={data.get('pageTitle')}")
                    
                    # Check if URL matches test URL
                    if data.get("currentUrl") == TEST_URL:
                        logger.info("URL correctly synchronized")
                        self.url_synced = True
                        metrics["url_sync_time"] = time.time()
                    
                    # Check if we got a page title (any non-empty title is fine for example.com)
                    if data.get("pageTitle") and len(data.get("pageTitle")) > 0:
                        logger.info(f"Title synchronized: {data.get('pageTitle')}")
                        self.title_synced = True
                        metrics["title_sync_time"] = time.time()
                    
                    self.received_state_update = True
                
                # Handle action feedback
                if data.get("type") == "browser_action_feedback":
                    logger.info(f"Received action feedback: {data.get('actionType')}")
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
            "max_steps": 5  # Limit steps for testing
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
    """Run the end-to-end test for simple URL navigation"""
    logger.info("Starting NAV-01 test: Simple URL navigation via chat prompt")
    metrics["start_time"] = time.time()
    
    # Step 1: Execute agent task
    prompt = f"Navigate to {TEST_URL}"
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
        
    # Step 4: Wait for navigation completion and state synchronization
    await ws_client.listen(timeout=30)
    
    # Step 5: Evaluate test results
    success = (
        ws_client.received_screenshot and 
        ws_client.url_synced and 
        ws_client.title_synced
    )
    
    if success:
        logger.info("Test NAV-01 PASSED")
        metrics["test_result"] = "PASSED"
        metrics["navigation_completion_time"] = time.time()
        return True
    else:
        logger.error("Test NAV-01 FAILED")
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
        
    if metrics["url_sync_time"]:
        url_time = metrics["url_sync_time"] - start
        print(f"URL Synchronization Time: {url_time:.2f}s")
        
    if metrics["title_sync_time"]:
        title_time = metrics["title_sync_time"] - start
        print(f"Title Synchronization Time: {title_time:.2f}s")
        
    if metrics["navigation_completion_time"]:
        total_time = metrics["navigation_completion_time"] - start
        print(f"Total Completion Time: {total_time:.2f}s")
        
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