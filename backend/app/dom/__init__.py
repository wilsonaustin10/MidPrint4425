"""
DOM processing module for extracting and analyzing web page structures.
"""
from app.browser.browser import browser_manager
from app.dom.browser_executor import BrowserExecutor

# Create a browser executor instance to be used throughout the application
browser_executor = BrowserExecutor(browser_manager) 