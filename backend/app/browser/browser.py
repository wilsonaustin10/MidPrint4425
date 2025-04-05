import os
import base64
from typing import Optional, Dict, Any, Tuple
from playwright.async_api import async_playwright, Browser, BrowserContext, Page, ElementHandle
from app.core.config import settings

class BrowserManager:
    """
    Manages browser instances and provides core functionality for browser automation.
    This class handles browser lifecycle, configuration, and core navigation capabilities.
    """
    
    def __init__(self):
        self.playwright = None
        self.browser = None
        self.context = None
        self.page = None
        self.is_initialized = False
        self.last_error = None
        
    async def initialize(self) -> None:
        """
        Initialize the Playwright browser with the configured browser type.
        Sets up the browser with appropriate arguments and configuration.
        """
        if self.is_initialized:
            return
            
        try:
            self.playwright = await async_playwright().start()
            
            # Determine which browser type to use
            browser_type = settings.BROWSER_TYPE.lower()
            browser_launcher = None
            
            if browser_type == "chromium":
                browser_launcher = self.playwright.chromium
            elif browser_type == "firefox":
                browser_launcher = self.playwright.firefox
            elif browser_type == "webkit":
                browser_launcher = self.playwright.webkit
            else:
                browser_launcher = self.playwright.chromium
            
            # Set up browser arguments and launch options
            browser_args = []
            
            # Add browser-specific arguments
            if browser_type == "chromium":
                browser_args = [
                    '--disable-web-security',
                    '--disable-features=IsolateOrigins,site-per-process',
                    '--disable-site-isolation-trials',
                    '--disable-features=BlockInsecurePrivateNetworkRequests',
                    '--disable-blink-features=AutomationControlled',  # Avoid detection
                ]
            
            # Launch the browser with configured options
            self.browser = await browser_launcher.launch(
                headless=settings.HEADLESS,
                args=browser_args
            )
            
            # Create a browser context with additional options
            context_options = {
                "viewport": {"width": 1280, "height": 800},
                "ignore_https_errors": True,
                "java_script_enabled": True,
            }
            
            self.context = await self.browser.new_context(**context_options)
            
            # Set up page and event listeners
            self.page = await self.context.new_page()
            
            # Configure page timeouts
            self.page.set_default_navigation_timeout(30000)  # 30 seconds
            self.page.set_default_timeout(10000)  # 10 seconds for other operations
            
            self.is_initialized = True
            self.last_error = None
            
        except Exception as e:
            self.last_error = str(e)
            raise
    
    async def navigate(self, url: str) -> str:
        """
        Navigate to a URL and return the page content.
        
        Args:
            url: The URL to navigate to
            
        Returns:
            The HTML content of the page
        """
        if not self.is_initialized:
            await self.initialize()
        
        try:
            response = await self.page.goto(url, wait_until="networkidle")
            return await self.page.content()
        except Exception as e:
            self.last_error = f"Navigation error: {str(e)}"
            raise
    
    async def get_dom(self) -> str:
        """
        Get the current DOM content of the page.
        
        Returns:
            The HTML content of the current page
        """
        if not self.is_initialized:
            await self.initialize()
            
        try:
            return await self.page.content()
        except Exception as e:
            self.last_error = f"Error getting DOM: {str(e)}"
            raise
    
    async def capture_screenshot(self, full_page: bool = True) -> str:
        """
        Capture a screenshot of the current page.
        
        Args:
            full_page: Whether to capture the full page or just the viewport
            
        Returns:
            Base64-encoded string of the screenshot image
        """
        if not self.is_initialized:
            await self.initialize()
            
        try:
            screenshot_bytes = await self.page.screenshot(full_page=full_page, type="png")
            return base64.b64encode(screenshot_bytes).decode('utf-8')
        except Exception as e:
            self.last_error = f"Screenshot error: {str(e)}"
            raise
    
    async def get_page_state(self) -> Dict[str, Any]:
        """
        Get the current state of the page including URL, title, and viewport size.
        
        Returns:
            Dictionary with page state information
        """
        if not self.is_initialized:
            await self.initialize()
            
        try:
            return {
                "url": self.page.url,
                "title": await self.page.title(),
                "viewport_size": self.page.viewport_size,
                "content_size": await self.page.evaluate("() => { return { width: document.documentElement.scrollWidth, height: document.documentElement.scrollHeight }; }"),
                "ready_state": await self.page.evaluate("() => document.readyState")
            }
        except Exception as e:
            self.last_error = f"Error getting page state: {str(e)}"
            return {"error": str(e)}
    
    async def close(self) -> None:
        """
        Close the browser and clean up resources.
        """
        try:
            if self.page:
                await self.page.close()
            if self.context:
                await self.context.close()
            if self.browser:
                await self.browser.close()
            if self.playwright:
                await self.playwright.stop()
            
            self.is_initialized = False
        except Exception as e:
            self.last_error = f"Error closing browser: {str(e)}"
            raise
    
    def get_last_error(self) -> Optional[str]:
        """
        Get the last error that occurred during browser operations.
        
        Returns:
            The last error message or None if no error occurred
        """
        return self.last_error

# Singleton instance
browser_manager = BrowserManager() 