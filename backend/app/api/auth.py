"""
Authentication module for API key-based authentication.
"""
import logging
from typing import Optional, Dict, List, Any, Callable
from fastapi import HTTPException, Depends, Security, status
from fastapi.security.api_key import APIKeyHeader, APIKeyCookie, APIKeyQuery
from starlette.requests import Request
from starlette.status import HTTP_403_FORBIDDEN

from app.core.config import settings

# Set up logger
logger = logging.getLogger(__name__)

# API Key security schemes
API_KEY_NAME = "X-API-Key"
api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=False)
api_key_query = APIKeyQuery(name=API_KEY_NAME, auto_error=False)
api_key_cookie = APIKeyCookie(name=API_KEY_NAME, auto_error=False)

def get_api_key(
    api_key_header: Optional[str] = Security(api_key_header),
    api_key_query: Optional[str] = Security(api_key_query),
    api_key_cookie: Optional[str] = Security(api_key_cookie),
) -> str:
    """
    Get the API key from header, query parameter, or cookie.
    
    Args:
        api_key_header: API key from header
        api_key_query: API key from query parameter
        api_key_cookie: API key from cookie
        
    Returns:
        API key if valid, raises HTTPException otherwise
    """
    if settings.API_KEY is None or settings.API_KEY == "":
        # If no API key is set in settings, don't require authentication
        return "no_auth_required"
    
    api_key = api_key_header or api_key_query or api_key_cookie
    if api_key == settings.API_KEY:
        return api_key
    
    raise HTTPException(
        status_code=HTTP_403_FORBIDDEN,
        detail="Invalid API key or not provided"
    )

def get_authenticated_user(api_key: str = Depends(get_api_key)) -> Dict[str, Any]:
    """
    Get the authenticated user based on the API key.
    
    Args:
        api_key: The API key
        
    Returns:
        Dictionary with user information
    """
    # In this simple implementation, we just return a basic user object
    # In a production environment, this could look up the user from a database
    if api_key == "no_auth_required":
        return {"id": "anonymous", "role": "user"}
    
    # Here we could look up user details based on the API key
    return {"id": "authenticated_user", "role": "admin"}

class RoleChecker:
    """
    Role-based permission checker for API endpoints.
    """
    
    def __init__(self, allowed_roles: List[str]):
        """
        Initialize the role checker.
        
        Args:
            allowed_roles: List of allowed roles
        """
        self.allowed_roles = allowed_roles

    def __call__(self, user: Dict[str, Any] = Depends(get_authenticated_user)) -> Dict[str, Any]:
        """
        Check if the user has one of the allowed roles.
        
        Args:
            user: User information
            
        Returns:
            User information if allowed, raises HTTPException otherwise
        """
        if user["role"] not in self.allowed_roles:
            logger.warning(f"User with role {user['role']} attempted to access restricted endpoint")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have enough permissions"
            )
        return user

# Predefined role checkers
admin_role = RoleChecker(["admin"])
user_role = RoleChecker(["admin", "user"]) 