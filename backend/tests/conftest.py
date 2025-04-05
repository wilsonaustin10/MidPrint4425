import pytest
import os
import sys
from dotenv import load_dotenv

# Add application to Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Load environment variables from .env file
load_dotenv()

@pytest.fixture(scope="session")
def event_loop():
    """Create an event loop for asyncio tests"""
    import asyncio
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close() 