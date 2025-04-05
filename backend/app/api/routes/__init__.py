"""
API routes module for the MidPrint backend application.
"""
from fastapi import APIRouter
from app.api.routes import agent, dom, llm, tasks, websocket

# Main API router
api_router = APIRouter()

# Include all route modules
api_router.include_router(agent.router, prefix="/agent", tags=["agent"])
api_router.include_router(dom.router, prefix="/dom", tags=["dom"])
api_router.include_router(llm.router, prefix="/llm", tags=["llm"])
api_router.include_router(tasks.router, prefix="/task", tags=["task"])
api_router.include_router(websocket.router, tags=["websocket"])

# Add additional routes/modules here as the application grows 