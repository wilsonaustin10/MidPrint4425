import pytest
import asyncio
from app.services.browser import BrowserService

@pytest.mark.asyncio
async def test_browser_initialization():
    """Test that browser service initializes correctly"""
    browser = BrowserService()
    assert not browser.is_initialized
    
    try:
        await browser.initialize()
        assert browser.is_initialized
        assert browser.page is not None
        assert browser.browser is not None
    finally:
        await browser.close()
        assert not browser.is_initialized

@pytest.mark.asyncio
async def test_browser_navigation():
    """Test browser navigation to a URL"""
    browser = BrowserService()
    
    try:
        content = await browser.navigate("https://example.com")
        assert content is not None
        assert "<html" in content
        assert "Example Domain" in content
    finally:
        await browser.close() 