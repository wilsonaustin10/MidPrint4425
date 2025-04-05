"""
Example API client for the MidPrint backend.

This file provides examples of how to interact with the MidPrint API
for frontend developers or testing purposes.
"""
import requests
import websocket
import json
import asyncio
import logging
from typing import Dict, Any, List, Optional, Callable

# Configure logger
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("midprint-client")

class MidPrintClient:
    """
    Client for interacting with the MidPrint API.
    """
    
    def __init__(self, base_url: str = "http://localhost:8000/api/v1", api_key: Optional[str] = None):
        """
        Initialize the client.
        
        Args:
            base_url: Base URL of the API
            api_key: API key for authentication
        """
        self.base_url = base_url
        self.api_key = api_key
        self.headers = {"X-API-Key": api_key} if api_key else {}
        self.ws = None
        self.ws_url = base_url.replace("http://", "ws://").replace("https://", "wss://") + "/ws"
        self.task_callbacks = {}
        
    def get_browser_status(self) -> Dict[str, Any]:
        """
        Get the current browser status.
        
        Returns:
            Browser status
        """
        response = requests.get(f"{self.base_url}/agent/status", headers=self.headers)
        response.raise_for_status()
        return response.json()
    
    def navigate_to(self, url: str) -> Dict[str, Any]:
        """
        Navigate to a URL.
        
        Args:
            url: URL to navigate to
            
        Returns:
            Task information
        """
        response = requests.post(
            f"{self.base_url}/agent/navigate",
            json={"url": url},
            headers=self.headers
        )
        response.raise_for_status()
        return response.json()
    
    def execute_task(self, task: str) -> Dict[str, Any]:
        """
        Execute a task using natural language.
        
        Args:
            task: Natural language task description
            
        Returns:
            Task information
        """
        response = requests.post(
            f"{self.base_url}/agent/execute",
            json={"task": task},
            headers=self.headers
        )
        response.raise_for_status()
        return response.json()
    
    def get_screenshot(self) -> bytes:
        """
        Get a screenshot of the current page.
        
        Returns:
            Screenshot data as bytes
        """
        response = requests.get(f"{self.base_url}/agent/screenshot", headers=self.headers)
        response.raise_for_status()
        return response.content
    
    def get_task(self, task_id: str) -> Dict[str, Any]:
        """
        Get information about a specific task.
        
        Args:
            task_id: Task ID
            
        Returns:
            Task information
        """
        response = requests.get(f"{self.base_url}/task/tasks/{task_id}", headers=self.headers)
        response.raise_for_status()
        return response.json()
    
    def get_tasks(self, status: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get a list of tasks.
        
        Args:
            status: Filter by status
            
        Returns:
            List of tasks
        """
        params = {"status": status} if status else {}
        response = requests.get(f"{self.base_url}/task/tasks", params=params, headers=self.headers)
        response.raise_for_status()
        return response.json()
    
    def cancel_task(self, task_id: str) -> Dict[str, Any]:
        """
        Cancel a task.
        
        Args:
            task_id: Task ID
            
        Returns:
            Success message
        """
        response = requests.delete(f"{self.base_url}/task/tasks/{task_id}", headers=self.headers)
        response.raise_for_status()
        return response.json()
    
    def clear_tasks(self, status: Optional[str] = None) -> Dict[str, Any]:
        """
        Clear completed or failed tasks.
        
        Args:
            status: Clear tasks with this status only
            
        Returns:
            Success message
        """
        params = {"status": status} if status else {}
        response = requests.delete(f"{self.base_url}/task/tasks", params=params, headers=self.headers)
        response.raise_for_status()
        return response.json()
    
    def connect_websocket(self) -> None:
        """
        Connect to the WebSocket for real-time updates.
        """
        if self.ws:
            return
        
        def on_message(ws, message):
            try:
                data = json.loads(message)
                if data.get("type") == "task_update":
                    task_id = data.get("task_id")
                    if task_id in self.task_callbacks:
                        for callback in self.task_callbacks[task_id]:
                            callback(data.get("data"))
            except Exception as e:
                logger.error(f"Error processing WebSocket message: {e}")
        
        def on_error(ws, error):
            logger.error(f"WebSocket error: {error}")
        
        def on_close(ws, close_status_code, close_msg):
            logger.info(f"WebSocket closed: {close_status_code} - {close_msg}")
        
        def on_open(ws):
            logger.info("WebSocket connection established")
        
        headers = {"X-API-Key": self.api_key} if self.api_key else {}
        self.ws = websocket.WebSocketApp(
            self.ws_url,
            on_message=on_message,
            on_error=on_error,
            on_close=on_close,
            on_open=on_open,
            header=headers
        )
        
        # Start WebSocket connection in a background thread
        import threading
        thread = threading.Thread(target=self.ws.run_forever)
        thread.daemon = True
        thread.start()
    
    def disconnect_websocket(self) -> None:
        """
        Disconnect from the WebSocket.
        """
        if self.ws:
            self.ws.close()
            self.ws = None
    
    def subscribe_to_task(self, task_id: str, callback: Callable[[Dict[str, Any]], None]) -> None:
        """
        Subscribe to task updates.
        
        Args:
            task_id: Task ID
            callback: Function to call when task is updated
        """
        if task_id not in self.task_callbacks:
            self.task_callbacks[task_id] = []
        
        self.task_callbacks[task_id].append(callback)
        
        # Make sure WebSocket is connected
        self.connect_websocket()
        
        # Send subscription message
        if self.ws and self.ws.sock and self.ws.sock.connected:
            self.ws.send(json.dumps({
                "type": "subscribe_task",
                "task_id": task_id
            }))
    
    def unsubscribe_from_task(self, task_id: str, callback: Optional[Callable] = None) -> None:
        """
        Unsubscribe from task updates.
        
        Args:
            task_id: Task ID
            callback: Specific callback to unsubscribe, or None to unsubscribe all
        """
        if task_id in self.task_callbacks:
            if callback:
                self.task_callbacks[task_id].remove(callback)
                if not self.task_callbacks[task_id]:
                    del self.task_callbacks[task_id]
            else:
                del self.task_callbacks[task_id]
        
        # Send unsubscription message if still connected
        if self.ws and self.ws.sock and self.ws.sock.connected:
            self.ws.send(json.dumps({
                "type": "unsubscribe_task",
                "task_id": task_id
            }))

# Example usage
if __name__ == "__main__":
    # Initialize client
    client = MidPrintClient(api_key="test-api-key")
    
    # Define a callback for task updates
    def task_updated(task_data):
        print(f"Task updated: {task_data['status']}")
        print(f"Progress: {task_data.get('progress', 0)}%")
        if task_data.get('logs'):
            print(f"Latest log: {task_data['logs'][-1]['message']}")
    
    # Execute a task
    result = client.execute_task("Navigate to example.com and click the first link")
    task_id = result["task_id"]
    print(f"Task created with ID: {task_id}")
    
    # Subscribe to task updates
    client.subscribe_to_task(task_id, task_updated)
    
    # Wait for task to complete
    while True:
        task = client.get_task(task_id)
        if task["status"] in ["COMPLETED", "FAILED", "CANCELED"]:
            break
        import time
        time.sleep(1)
    
    # Clean up
    client.disconnect_websocket() 