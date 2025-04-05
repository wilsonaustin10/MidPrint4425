"""
Integration tests for the MidPrint API endpoints.
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import MagicMock, patch
import uuid
import json

from app.main import app
from app.services.task_manager import task_manager, Task, TaskStatus
from app.services.agent_service import AgentService
from app.services.websocket_manager import websocket_manager

# Test client
client = TestClient(app)

# Mock API key for authentication
TEST_API_KEY = "test-api-key"

@pytest.fixture
def mock_config():
    """Mock configuration with test API key."""
    with patch("app.core.config.settings") as mock_settings:
        mock_settings.API_KEY = TEST_API_KEY
        yield mock_settings

@pytest.fixture
def mock_agent():
    """Mock agent service."""
    with patch("app.api.routes.agent.agent_service") as mock_agent:
        # Mock browser status
        mock_agent.get_browser_status.return_value = {
            "current_url": "https://example.com",
            "title": "Example Domain",
            "is_browser_open": True
        }
        
        # Mock navigation
        mock_agent.navigate_to.return_value = "task-123"
        
        # Mock task execution
        mock_agent.execute_task.return_value = "task-456"
        
        yield mock_agent

@pytest.fixture
def sample_task():
    """Create a sample task for testing."""
    task_id = str(uuid.uuid4())
    task = Task(id=task_id, description="Test task")
    task_manager.tasks[task_id] = task
    yield task
    # Clean up
    if task_id in task_manager.tasks:
        del task_manager.tasks[task_id]

def test_health_check():
    """Test health check endpoint."""
    response = client.get("/")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"

def test_unauthorized_access():
    """Test that endpoints require authentication."""
    # Without API key
    response = client.get("/api/v1/agent/status")
    assert response.status_code == 403
    
    # With wrong API key
    response = client.get("/api/v1/agent/status", headers={"X-API-Key": "wrong-key"})
    assert response.status_code == 403

def test_agent_status(mock_config, mock_agent):
    """Test agent status endpoint."""
    response = client.get("/api/v1/agent/status", headers={"X-API-Key": TEST_API_KEY})
    assert response.status_code == 200
    data = response.json()
    assert data["current_url"] == "https://example.com"
    assert data["title"] == "Example Domain"
    assert data["is_browser_open"] is True

def test_agent_navigate(mock_config, mock_agent):
    """Test agent navigation endpoint."""
    response = client.post(
        "/api/v1/agent/navigate",
        json={"url": "https://example.org"},
        headers={"X-API-Key": TEST_API_KEY}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["task_id"] == "task-123"
    mock_agent.navigate_to.assert_called_once_with("https://example.org")

def test_agent_execute(mock_config, mock_agent):
    """Test agent task execution endpoint."""
    response = client.post(
        "/api/v1/agent/execute",
        json={"task": "Click the submit button"},
        headers={"X-API-Key": TEST_API_KEY}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["task_id"] == "task-456"
    mock_agent.execute_task.assert_called_once_with("Click the submit button")

def test_task_endpoints(mock_config, sample_task):
    """Test task management endpoints."""
    # Get all tasks
    response = client.get("/api/v1/task/tasks", headers={"X-API-Key": TEST_API_KEY})
    assert response.status_code == 200
    tasks = response.json()
    assert len(tasks) == 1
    assert tasks[0]["id"] == sample_task.id
    
    # Get specific task
    response = client.get(f"/api/v1/task/tasks/{sample_task.id}", headers={"X-API-Key": TEST_API_KEY})
    assert response.status_code == 200
    task = response.json()
    assert task["id"] == sample_task.id
    assert task["status"] == "PENDING"
    
    # Update task progress
    sample_task.start()
    sample_task.update_progress(50)
    
    # Get updated task
    response = client.get(f"/api/v1/task/tasks/{sample_task.id}", headers={"X-API-Key": TEST_API_KEY})
    task = response.json()
    assert task["status"] == "RUNNING"
    assert task["progress"] == 50
    
    # Cancel task
    response = client.delete(f"/api/v1/task/tasks/{sample_task.id}", headers={"X-API-Key": TEST_API_KEY})
    assert response.status_code == 200
    
    # Verify task is canceled
    response = client.get(f"/api/v1/task/tasks/{sample_task.id}", headers={"X-API-Key": TEST_API_KEY})
    task = response.json()
    assert task["status"] == "CANCELED"
    
    # Get task metrics
    response = client.get("/api/v1/task/tasks/metrics", headers={"X-API-Key": TEST_API_KEY})
    assert response.status_code == 200
    metrics = response.json()["metrics"]
    assert metrics["CANCELED"] == 1
    assert metrics["TOTAL"] == 1
    
    # Clear tasks
    response = client.delete("/api/v1/task/tasks", headers={"X-API-Key": TEST_API_KEY})
    assert response.status_code == 200
    
    # Verify tasks are cleared
    response = client.get("/api/v1/task/tasks", headers={"X-API-Key": TEST_API_KEY})
    tasks = response.json()
    assert len(tasks) == 0

@pytest.mark.asyncio
async def test_websocket(mock_config):
    """Test WebSocket connection."""
    # This is a simple test that doesn't actually test the full WebSocket functionality
    # In a real test, you would use a WebSocket client library to test the full flow
    
    # Create a task that we'll use for WebSocket notifications
    task_id = str(uuid.uuid4())
    task = Task(id=task_id, description="WebSocket test task")
    task_manager.tasks[task_id] = task
    
    # Set up mock for broadcast_task_update
    original_broadcast = websocket_manager.broadcast_task_update
    broadcast_mock = MagicMock()
    websocket_manager.broadcast_task_update = broadcast_mock
    
    try:
        # Update task to trigger WebSocket notification
        task.start()
        task.update_progress(75)
        
        # Check if broadcast was called
        broadcast_mock.assert_called()
        args = broadcast_mock.call_args[0]
        assert args[0] == task_id
        task_dict = args[1]
        assert task_dict["id"] == task_id
        assert task_dict["status"] == "RUNNING"
        assert task_dict["progress"] == 75
        
    finally:
        # Clean up
        websocket_manager.broadcast_task_update = original_broadcast
        if task_id in task_manager.tasks:
            del task_manager.tasks[task_id] 