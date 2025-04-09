"""
Configuration settings for the application.
Manages environment variables and application defaults.
"""
import os
from typing import Dict, Any, Optional
from pydantic_settings import BaseSettings
from pydantic import Field

class Settings(BaseSettings):
    """
    Application settings for the browser automation agent.
    
    These settings are loaded from environment variables, with fallbacks to defaults.
    """
    
    # API Settings
    API_V1_STR: str = "/api/v1"
    API_TITLE: str = "Browser Automation API"
    API_DESCRIPTION: str = "API for browser automation using natural language instructions"
    API_VERSION: str = "0.1.0"
    API_KEY: Optional[str] = Field(default=None, description="API key for authentication")
    
    # Browser Settings
    BROWSER_TYPE: str = "chromium"
    # Default headless mode, but allow for override via environment variable
    HEADLESS: bool = os.getenv("HEADLESS", "False").lower() in ("true", "1", "t")
    BROWSER_VIEWPORT_SIZE: str = os.getenv("BROWSER_VIEWPORT_SIZE", "1280,720")
    DEFAULT_VIEWPORT_WIDTH: int = Field(default=1280, description="Default viewport width")
    DEFAULT_VIEWPORT_HEIGHT: int = Field(default=800, description="Default viewport height")
    DEFAULT_TIMEOUT: int = Field(default=30000, description="Default timeout for browser operations in milliseconds")
    DEFAULT_NAVIGATION_TIMEOUT: int = Field(default=30000, description="Default timeout for navigation in milliseconds")
    SLOW_MO: int = Field(default=50, description="Slow down browser operations by the specified amount of milliseconds")
    USER_AGENT: Optional[str] = Field(
        default="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36",
        description="User agent string to use in the browser"
    )
    
    # LLM Settings
    OPENAI_API_KEY: Optional[str] = Field(default=None, description="OpenAI API key for language model integration")
    ANTHROPIC_API_KEY: Optional[str] = Field(default=None, description="Anthropic API key for language model integration")
    LLM_MODEL: str = Field(default="gpt-4", description="Language model to use for instruction processing")
    
    # Logging Settings
    LOG_LEVEL: str = Field(default="INFO", description="Logging level")
    LOG_FORMAT: str = Field(default="%(asctime)s - %(name)s - %(levelname)s - %(message)s", description="Log format")
    
    # Paths and Directories
    TEMP_DIR: str = Field(default="/tmp/browser-automation", description="Directory for temporary files")
    SCREENSHOT_DIR: str = Field(default="/tmp/browser-automation/screenshots", description="Directory for screenshot files")
    
    # WebSocket Settings
    WEBSOCKET_HEARTBEAT_INTERVAL: int = Field(default=30, description="WebSocket heartbeat interval in seconds")
    
    # Task Management Settings
    TASK_CLEANUP_INTERVAL: int = Field(default=3600, description="Task cleanup interval in seconds")
    TASK_MAX_AGE: int = Field(default=86400, description="Maximum age of completed tasks in seconds (1 day)")
    
    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": True,
        "extra": "ignore"
    }

# Create global settings instance
settings = Settings()

# Ensure required directories exist
os.makedirs(settings.TEMP_DIR, exist_ok=True)
os.makedirs(settings.SCREENSHOT_DIR, exist_ok=True) 