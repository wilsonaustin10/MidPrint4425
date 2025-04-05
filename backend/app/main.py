"""
Main application module for the MidPrint backend.
"""
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from app.api.routes import api_router
from app.core.config import settings
from app.services.websocket_manager import websocket_manager
from app.services.task_manager import task_manager
from app.api.docs import custom_openapi
import logging

# Load environment variables
load_dotenv()

# Setup logging
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format=settings.LOG_FORMAT
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title=settings.API_TITLE,
    description=settings.API_DESCRIPTION,
    version=settings.API_VERSION,
)

# Set custom OpenAPI schema
app.openapi = lambda: custom_openapi(app)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with actual origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(api_router, prefix=settings.API_V1_STR)

@app.get("/", tags=["health"])
async def health_check():
    """
    Health check endpoint.
    """
    return {
        "status": "ok",
        "version": settings.API_VERSION,
        "api_root": settings.API_V1_STR
    }

@app.on_event("startup")
async def startup_event():
    """
    Actions to run on application startup.
    """
    logger.info(f"Starting up {settings.API_TITLE} v{settings.API_VERSION}")
    
    # Ensure required directories exist
    os.makedirs(settings.TEMP_DIR, exist_ok=True)
    os.makedirs(settings.SCREENSHOT_DIR, exist_ok=True)
    
    # Initialize the WebSocket manager
    logger.info("Initializing WebSocket manager")
    
    # Initialize the task manager
    logger.info("Initializing task manager")
    
    # Set up task manager to broadcast updates via WebSocket
    task_manager.add_subscriber("websocket", websocket_manager.broadcast_task_update)
    
    logger.info(f"API available at {settings.API_V1_STR}")
    logger.info(f"API documentation available at {settings.API_V1_STR}/docs")

@app.on_event("shutdown")
async def shutdown_event():
    """
    Actions to run on application shutdown.
    """
    logger.info(f"Shutting down {settings.API_TITLE}")
    
    # Clean up task manager
    logger.info("Cleaning up task manager")
    task_manager.remove_subscriber("websocket")
    
    # Clean up WebSocket manager
    logger.info("Cleaning up WebSocket connections")
    await websocket_manager.disconnect_all()

# Add router imports and include_router calls here as they are developed

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True) 