"""
WebSocket routes for real-time updates.
"""
import asyncio
import json
import logging
from typing import Dict, Any, Optional
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, Query
import uuid
from fastapi import WebSocketState

from app.services.websocket_manager import websocket_manager
from app.services.task_manager import task_manager
from app.core.config import settings

# Set up logger
logger = logging.getLogger(__name__)

router = APIRouter()

@router.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    client_id: Optional[str] = Query(None)
):
    """
    WebSocket endpoint for real-time updates.
    
    Args:
        websocket: WebSocket connection
        client_id: Optional client identifier
    """
    # Generate a client ID if not provided
    if not client_id:
        client_id = str(uuid.uuid4())
    
    # Accept the connection first - this MUST be the first await call
    await websocket.accept()
    
    # Then connect to the manager
    await websocket_manager.connect(websocket, client_id)
    
    # Send initial message
    await websocket_manager.send_personal_message(
        {
            "type": "connection_established",
            "client_id": client_id,
            "message": "WebSocket connection established"
        },
        websocket
    )
    
    # Set up heartbeat task
    heartbeat_task = None
    
    try:
        # Start heartbeat task
        heartbeat_task = asyncio.create_task(send_heartbeat(websocket, client_id))
        
        # Process incoming messages
        while True:
            try:
                # Receive message from client
                data = await websocket.receive_json()
                
                # Process message based on type
                message_type = data.get("type")
                
                if message_type == "subscribe_task":
                    # Subscribe to task updates
                    task_id = data.get("task_id")
                    if task_id:
                        websocket_manager.subscribe_to_task(task_id, websocket)
                        
                        # Send current task state immediately
                        task = task_manager.get_task(task_id)
                        if task:
                            await websocket_manager.send_personal_message(
                                {
                                    "type": "task_update",
                                    "task_id": task_id,
                                    "data": task.to_dict()
                                },
                                websocket
                            )
                        
                        logger.debug(f"Client {client_id} subscribed to task {task_id}")
                
                elif message_type == "unsubscribe_task":
                    # Unsubscribe from task updates
                    task_id = data.get("task_id")
                    if task_id:
                        websocket_manager.unsubscribe_from_task(task_id, websocket)
                        logger.debug(f"Client {client_id} unsubscribed from task {task_id}")
                
                elif message_type == "ping":
                    # Respond to ping with pong
                    await websocket_manager.send_personal_message(
                        {"type": "pong", "timestamp": data.get("timestamp")},
                        websocket
                    )
                
                else:
                    # Unknown message type
                    logger.warning(f"Received unknown WebSocket message type: {message_type}")
                    await websocket_manager.send_personal_message(
                        {"type": "error", "message": f"Unknown message type: {message_type}"},
                        websocket
                    )
            
            except json.JSONDecodeError:
                # Invalid JSON
                logger.error("Received invalid JSON in WebSocket message")
                await websocket_manager.send_personal_message(
                    {"type": "error", "message": "Invalid JSON"},
                    websocket
                )
    
    except WebSocketDisconnect:
        # Client disconnected
        logger.info(f"WebSocket client {client_id} disconnected")
    
    except Exception as e:
        # Unexpected error
        logger.error(f"WebSocket error for client {client_id}: {str(e)}", exc_info=True)
        try:
            # Only send error message if connection is still open
            if websocket.client_state == WebSocketState.CONNECTED:
                await websocket_manager.send_personal_message(
                    {"type": "error", "message": "Internal server error"},
                    websocket
                )
        except Exception as inner_e:
            logger.error(f"Failed to send error message to client {client_id}: {str(inner_e)}")
    
    finally:
        # Cancel heartbeat task
        if heartbeat_task and not heartbeat_task.done():
            heartbeat_task.cancel()
            try:
                await heartbeat_task
            except asyncio.CancelledError:
                pass
        
        # Disconnect WebSocket
        try:
            # Log disconnection
            logger.info(f"Cleaning up connection for client {client_id}")
            websocket_manager.disconnect(websocket, client_id)
        except Exception as e:
            logger.error(f"Error during WebSocket cleanup for client {client_id}: {str(e)}")

async def send_heartbeat(websocket: WebSocket, client_id: str) -> None:
    """
    Send periodic heartbeat messages to keep the WebSocket connection alive.
    
    Args:
        websocket: WebSocket connection
        client_id: Client identifier
    """
    try:
        while True:
            await asyncio.sleep(settings.WEBSOCKET_HEARTBEAT_INTERVAL)
            try:
                await websocket_manager.send_personal_message(
                    {"type": "heartbeat", "timestamp": str(asyncio.get_event_loop().time())},
                    websocket
                )
            except Exception as e:
                # If sending fails, the connection may be closed
                logger.error(f"Error sending heartbeat to client {client_id}: {str(e)}")
                break
    except asyncio.CancelledError:
        # Task was canceled
        pass 