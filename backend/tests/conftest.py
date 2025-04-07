import pytest
import os
import sys
from dotenv import load_dotenv

# Add application to Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Load environment variables from .env file
load_dotenv()

@pytest.fixture(scope="session")
def event_loop_policy():
    """Configure the event loop policy for tests"""
    import asyncio
    return asyncio.get_event_loop_policy()

@pytest.fixture
def event_loop(event_loop_policy):
    """Create an event loop for each test"""
    loop = event_loop_policy.new_event_loop()
    yield loop
    loop.close() 