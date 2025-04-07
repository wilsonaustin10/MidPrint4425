"""
WebSocket connection manager for real-time updates.
"""
import json
import logging
from typing import Dict, List, Any, Set, Optional
from fastapi import WebSocket, WebSocketDisconnect
from starlette.websockets import WebSocketState

# Set up logger
logger = logging.getLogger(__name__)

class ConnectionManager:
    """
    WebSocket connection manager for real-time updates.
    Handles WebSocket connections, disconnections, and broadcasting messages.
    """
    
    def __init__(self):
        """Initialize the connection manager."""
        # All active connections
        self.active_connections: List[WebSocket] = []
        # Connections grouped by client ID
        self.client_connections: Dict[str, List[WebSocket]] = {}
        # Connections subscribed to specific tasks
        self.task_subscribers: Dict[str, List[WebSocket]] = {}
        logger.info("WebSocket ConnectionManager initialized")
    
    async def connect(self, websocket: WebSocket, client_id: str) -> None:
        """
        Store a WebSocket connection.
        
        Args:
            websocket: WebSocket connection (already accepted)
            client_id: Client identifier
        """
        # Don't call accept() - it's already called in the endpoint
        # await websocket.accept()
        
        self.active_connections.append(websocket)
        
        # Store connection by client ID
        if client_id not in self.client_connections:
            self.client_connections[client_id] = []
        self.client_connections[client_id].append(websocket)
        
        logger.info(f"WebSocket connected for client {client_id}")
    
    def disconnect(self, websocket: WebSocket, client_id: str) -> None:
        """
        Remove a WebSocket connection.
        
        Args:
            websocket: WebSocket connection
            client_id: Client identifier
        """
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        
        # Remove from client connections
        if client_id in self.client_connections:
            if websocket in self.client_connections[client_id]:
                self.client_connections[client_id].remove(websocket)
            if not self.client_connections[client_id]:
                del self.client_connections[client_id]
        
        # Remove from task subscribers
        for task_id, subscribers in list(self.task_subscribers.items()):
            if websocket in subscribers:
                subscribers.remove(websocket)
            if not subscribers:
                del self.task_subscribers[task_id]
        
        logger.info(f"WebSocket disconnected for client {client_id}")
    
    async def disconnect_all(self) -> None:
        """
        Disconnect all active WebSocket connections.
        """
        logger.info(f"Disconnecting all WebSocket connections ({len(self.active_connections)} active)")
        
        # Clear all stored connections
        self.active_connections = []
        self.client_connections = {}
        self.task_subscribers = {}
        
        logger.info("All WebSocket connections have been removed")
    
    async def send_personal_message(self, message: Dict[str, Any], websocket: WebSocket) -> None:
        """
        Send a message to a specific WebSocket connection.
        
        Args:
            message: Message to send
            websocket: WebSocket connection
        """
        try:
            # Check if the WebSocket is still connected before sending
            if websocket.client_state == WebSocketState.CONNECTED:
                await websocket.send_json(message)
            else:
                logger.debug(f"Skipped sending message - WebSocket state is {websocket.client_state}")
        except Exception as e:
            logger.error(f"Error sending personal WebSocket message: {str(e)}")
            # The connection might be broken, but we'll let the main loop
            # handle disconnection logic
    
    async def broadcast(self, message: Dict[str, Any]) -> None:
        """
        Broadcast a message to all active connections.
        
        Args:
            message: Message to broadcast
        """
        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.error(f"Error broadcasting WebSocket message: {str(e)}")
                disconnected.append(connection)
        
        # Clean up any connections that failed
        for connection in disconnected:
            if connection in self.active_connections:
                self.active_connections.remove(connection)
    
    async def broadcast_to_client(self, client_id: str, message: Dict[str, Any]) -> None:
        """
        Broadcast a message to all connections for a specific client.
        
        Args:
            client_id: Client identifier
            message: Message to broadcast
        """
        if client_id not in self.client_connections:
            return
        
        disconnected = []
        for connection in self.client_connections[client_id]:
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.error(f"Error broadcasting to client {client_id}: {str(e)}")
                disconnected.append(connection)
        
        # Clean up any connections that failed
        for connection in disconnected:
            if connection in self.client_connections[client_id]:
                self.client_connections[client_id].remove(connection)
        
        if not self.client_connections[client_id]:
            del self.client_connections[client_id]
    
    def subscribe_to_task(self, task_id: str, websocket: WebSocket) -> None:
        """
        Subscribe a WebSocket connection to a specific task.
        
        Args:
            task_id: Task identifier
            websocket: WebSocket connection
        """
        if task_id not in self.task_subscribers:
            self.task_subscribers[task_id] = []
        
        if websocket not in self.task_subscribers[task_id]:
            self.task_subscribers[task_id].append(websocket)
            logger.debug(f"WebSocket subscribed to task {task_id}")
    
    def unsubscribe_from_task(self, task_id: str, websocket: WebSocket) -> None:
        """
        Unsubscribe a WebSocket connection from a specific task.
        
        Args:
            task_id: Task identifier
            websocket: WebSocket connection
        """
        if task_id in self.task_subscribers and websocket in self.task_subscribers[task_id]:
            self.task_subscribers[task_id].remove(websocket)
            if not self.task_subscribers[task_id]:
                del self.task_subscribers[task_id]
            logger.debug(f"WebSocket unsubscribed from task {task_id}")
    
    async def broadcast_task_update(self, task_id: str, update: Dict[str, Any]) -> None:
        """
        Broadcast a task update to all subscribers.
        
        Args:
            task_id: Task identifier
            update: Task update data
        """
        if task_id not in self.task_subscribers:
            return
        
        message = {
            "type": "task_update",
            "task_id": task_id,
            "data": update
        }
        
        # Get list of subscribers to remove if they fail
        disconnected = []
        
        # Send update to all subscribers
        for websocket in self.task_subscribers[task_id]:
            try:
                if websocket.client_state == WebSocketState.CONNECTED:
                    await websocket.send_json(message)
                else:
                    disconnected.append(websocket)
            except Exception as e:
                logger.error(f"Error sending task update: {str(e)}")
                disconnected.append(websocket)
        
        # Clean up disconnected subscribers
        for websocket in disconnected:
            if websocket in self.task_subscribers[task_id]:
                self.task_subscribers[task_id].remove(websocket)
            
            # Remove from active connections
            if websocket in self.active_connections:
                self.active_connections.remove(websocket)
            
            # Remove from client connections
            for client_id, connections in list(self.client_connections.items()):
                if websocket in connections:
                    connections.remove(websocket)
                    if not connections:
                        del self.client_connections[client_id]
        
        # Remove task if no subscribers left
        if not self.task_subscribers[task_id]:
            del self.task_subscribers[task_id]

# Singleton instance
websocket_manager = ConnectionManager() 