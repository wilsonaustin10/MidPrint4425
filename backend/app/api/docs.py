"""
OpenAPI documentation configuration for the MidPrint backend API.
"""
from fastapi.openapi.utils import get_openapi
from app.core.config import settings

def custom_openapi(app):
    """
    Generate custom OpenAPI schema with additional information.
    
    Args:
        app: FastAPI application instance
        
    Returns:
        OpenAPI schema
    """
    if app.openapi_schema:
        return app.openapi_schema
    
    openapi_schema = get_openapi(
        title=settings.API_TITLE,
        version=settings.API_VERSION,
        description="""
        MidPrint Backend API Documentation
        
        ## Authentication
        
        Most endpoints require authentication using an API key. The API key can be provided in one of three ways:
        
        1. As a header: `X-API-Key: your-api-key`
        2. As a query parameter: `?api_key=your-api-key`
        3. As a cookie: `api_key=your-api-key`
        
        ## WebSocket
        
        Real-time updates are available via WebSocket at `/api/v1/ws`. You can subscribe to specific task updates
        by sending a message with the following format:
        
        ```json
        {
            "type": "subscribe_task",
            "task_id": "task-id"
        }
        ```
        
        ## Task Management
        
        Tasks are long-running operations that can be monitored for status updates. Each task has a unique ID
        and goes through the following states:
        
        - PENDING: Task has been created but not yet started
        - RUNNING: Task is currently executing
        - COMPLETED: Task has finished successfully
        - FAILED: Task has encountered an error
        - CANCELED: Task was canceled by the user
        
        ## Browser Automation
        
        The agent endpoints allow controlling a browser remotely, including navigation, interaction with elements,
        and capturing screenshots or page content.
        """,
        routes=app.routes,
    )
    
    # Add API key auth component
    openapi_schema["components"] = {
        "securitySchemes": {
            "ApiKeyAuth": {
                "type": "apiKey",
                "in": "header",
                "name": "X-API-Key"
            }
        }
    }
    
    # Apply security globally
    openapi_schema["security"] = [{"ApiKeyAuth": []}]
    
    # Add custom response examples
    # Add response examples here if needed
    
    # Save the schema
    app.openapi_schema = openapi_schema
    return app.openapi_schema 