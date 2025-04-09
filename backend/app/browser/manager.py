import logging
import asyncio
from playwright.async_api import async_playwright

logger = logging.getLogger(__name__)

class BrowserManager:
    def __init__(self, settings):
        self.settings = settings
        self.browser = None
        self.playwright = None

    async def launch_browser(self) -> None:
        """Launch the browser."""
        if self.browser is not None:
            return

        logger.info(f"Launching browser with headless={self.settings.HEADLESS}")
        
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(
            headless=self.settings.HEADLESS,
            slow_mo=self.settings.SLOW_MO
        )
        
    async def close(self) -> None:
        """Close the browser and playwright."""
        if self.browser:
            await self.browser.close()
            self.browser = None
            
        if self.playwright:
            await self.playwright.stop()
            self.playwright = None 