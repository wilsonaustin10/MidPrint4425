import asyncio
from playwright.async_api import async_playwright
from app.core.config import settings

class BrowserService:
    """Service for browser automation using Playwright"""
    
    def __init__(self):
        self.playwright = None
        self.browser = None
        self.context = None
        self.page = None
        self.is_initialized = False
    
    async def initialize(self):
        """Initialize the browser"""
        if self.is_initialized:
            return
            
        self.playwright = await async_playwright().start()
        
        browser_type = settings.BROWSER_TYPE.lower()
        if browser_type == "chromium":
            self.browser = await self.playwright.chromium.launch(headless=settings.HEADLESS)
        elif browser_type == "firefox":
            self.browser = await self.playwright.firefox.launch(headless=settings.HEADLESS)
        elif browser_type == "webkit":
            self.browser = await self.playwright.webkit.launch(headless=settings.HEADLESS)
        else:
            self.browser = await self.playwright.chromium.launch(headless=settings.HEADLESS)
        
        self.context = await self.browser.new_context()
        self.page = await self.context.new_page()
        self.is_initialized = True
        
    async def navigate(self, url):
        """Navigate to a URL"""
        if not self.is_initialized:
            await self.initialize()
            
        await self.page.goto(url)
        return await self.page.content()
    
    async def get_dom(self):
        """Get the DOM content of the current page"""
        if not self.is_initialized:
            await self.initialize()
            
        return await self.page.content()
    
    async def close(self):
        """Close the browser"""
        if self.page:
            await self.page.close()
        if self.context:
            await self.context.close()
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()
        
        self.is_initialized = False

# Singleton instance
browser_service = BrowserService() 