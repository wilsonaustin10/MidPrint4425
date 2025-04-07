"""
Common test fixtures and utilities for end-to-end tests.
"""
import os
import sys
import pytest
import asyncio
import requests
from pathlib import Path

# Add project paths
PROJECT_ROOT = Path(__file__).parent.parent
BACKEND_PATH = PROJECT_ROOT / "backend"
FRONTEND_PATH = PROJECT_ROOT / "frontend"

# Ensure paths are in Python path
if str(BACKEND_PATH) not in sys.path:
    sys.path.append(str(BACKEND_PATH))
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="session")
async def backend_server():
    """Ensure backend server is running for tests."""
    # Check if server is already running
    try:
        response = requests.get("http://localhost:8000/health")
        if response.status_code == 200:
            yield "http://localhost:8000"
            return
    except Exception:
        pass

    # Start the server
    server_process = await asyncio.create_subprocess_exec(
        sys.executable,
        "app/main.py",
        cwd=str(BACKEND_PATH),
        env={
            **os.environ,
            "PYTHONPATH": f"{str(BACKEND_PATH)}:{os.environ.get('PYTHONPATH', '')}"
        }
    )

    # Wait for server to start
    for _ in range(30):  # 30 second timeout
        try:
            response = requests.get("http://localhost:8000/health")
            if response.status_code == 200:
                break
        except Exception:
            await asyncio.sleep(1)
    else:
        raise Exception("Failed to start backend server")

    yield "http://localhost:8000"

    # Cleanup
    server_process.terminate()
    await server_process.wait()

@pytest.fixture(scope="session")
def api_client(backend_server):
    """Create a session-scoped API client."""
    class APIClient:
        def __init__(self, base_url):
            self.base_url = base_url
            self.session = requests.Session()

        def get(self, path, **kwargs):
            return self.session.get(f"{self.base_url}{path}", **kwargs)

        def post(self, path, **kwargs):
            return self.session.post(f"{self.base_url}{path}", **kwargs)

        def put(self, path, **kwargs):
            return self.session.put(f"{self.base_url}{path}", **kwargs)

        def delete(self, path, **kwargs):
            return self.session.delete(f"{self.base_url}{path}", **kwargs)

        def ws_connect(self, path):
            """Create a WebSocket connection."""
            from websockets import connect
            return connect(f"ws://localhost:8000{path}")

    return APIClient(backend_server)

@pytest.fixture
def browser_manager():
    """Get the browser manager instance."""
    from app.browser.browser import browser_manager
    return browser_manager

@pytest.fixture
def agent_service():
    """Get the agent service instance."""
    from app.agent.service import agent_service
    return agent_service

@pytest.fixture
def task_manager():
    """Get the task manager instance."""
    from app.task.service import task_manager
    return task_manager

@pytest.fixture(autouse=True)
async def cleanup_after_test(agent_service, task_manager):
    """Cleanup after each test."""
    yield
    # Reset agent state
    await agent_service._cleanup()
    # Clear tasks
    task_manager.tasks.clear() 