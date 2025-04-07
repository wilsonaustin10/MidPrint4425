import pytest
import asyncio
import base64
from app.browser.browser import BrowserManager

@pytest.fixture
async def browser():
    """Fixture to provide a browser instance for tests"""
    browser_instance = BrowserManager()
    await browser_instance.initialize()
    try:
        return browser_instance
    finally:
        await browser_instance.close()

@pytest.mark.asyncio
async def test_browser_initialization():
    """Test that browser manager initializes correctly"""
    browser = BrowserManager()
    try:
        await browser.initialize()
        assert browser.is_initialized
        assert browser.page is not None
        assert browser.browser is not None
        assert browser.get_last_error() is None
    finally:
        await browser.close()

@pytest.mark.asyncio
async def test_browser_navigation():
    """Test browser navigation to a URL"""
    browser = BrowserManager()
    try:
        await browser.initialize()
        content = await browser.navigate("https://example.com")
        assert content is not None
        assert "<html" in content
        assert "Example Domain" in content
        
        page_state = await browser.get_page_state()
        assert page_state["url"] == "https://example.com/"
        assert "Example Domain" in page_state["title"]
    finally:
        await browser.close()

@pytest.mark.asyncio
async def test_screenshot_capture():
    """Test screenshot capture functionality"""
    browser = BrowserManager()
    try:
        await browser.initialize()
        await browser.navigate("https://example.com")
        screenshot = await browser.capture_screenshot()
        
        # Verify screenshot is a non-empty base64 string
        assert screenshot is not None
        assert len(screenshot) > 0
        
        # Verify it can be decoded
        decoded = base64.b64decode(screenshot)
        assert len(decoded) > 0
        assert decoded.startswith(b'\xff\xd8\xff')  # JPEG magic bytes 
    finally:
        await browser.close() 