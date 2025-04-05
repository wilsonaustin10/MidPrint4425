"""
Main application module for the MidPrint backend.
"""
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from app.api.routes import api_router
from app.core.config import settings
from app.services.websocket_manager import websocket_manager
from app.services.task_manager import task_manager
from app.browser.browser import browser_manager
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

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan manager for the FastAPI application.
    Handles startup and shutdown events.
    """
    # --- STARTUP ---
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
    
    # Initialize the browser
    logger.info("Initializing browser...")
    try:
        await browser_manager.initialize()
        logger.info("Browser initialized successfully.")
    except Exception as e:
        logger.error(f"CRITICAL: Failed to initialize browser on startup: {e}", exc_info=True)
        # We don't raise an error here to allow the app to continue running
        # even if the browser initialization fails
    
    logger.info(f"API available at {settings.API_V1_STR}")
    logger.info(f"API documentation available at {settings.API_V1_STR}/docs")
    
    # Application runs during yield
    yield
    
    # --- SHUTDOWN ---
    logger.info(f"Shutting down {settings.API_TITLE}")
    
    # Close browser gracefully
    logger.info("Closing browser...")
    try:
        await browser_manager.close()
        logger.info("Browser closed.")
    except Exception as e:
        logger.error(f"Error closing browser: {e}")
    
    # Clean up task manager
    logger.info("Cleaning up task manager")
    task_manager.remove_subscriber("websocket")
    
    # Clean up WebSocket manager
    logger.info("Cleaning up WebSocket connections")
    await websocket_manager.disconnect_all()

# Initialize FastAPI app
app = FastAPI(
    title=settings.API_TITLE,
    description=settings.API_DESCRIPTION,
    version=settings.API_VERSION,
    lifespan=lifespan,
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

# Entry point for running the application directly
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True) 