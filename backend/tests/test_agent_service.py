"""
Tests for the Agent Service that handles browser actions.
"""
import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from app.agent.service import AgentService

@pytest.fixture
async def agent_service():
    """Fixture for agent service with mocked dependencies."""
    agent = AgentService()
    
    # Mock the browser manager
    agent.browser = AsyncMock()
    agent.browser.is_initialized = True
    agent.browser.initialize = AsyncMock(return_value=None)
    agent.browser.navigate = AsyncMock(return_value="<html><body>Test Page</body></html>")
    agent.browser.get_page_state = AsyncMock(return_value={"url": "https://example.com", "title": "Test Page"})
    agent.browser.capture_screenshot = AsyncMock(return_value="base64screenshot")
    agent.browser.close = AsyncMock(return_value=None)
    
    # Mock the controller service
    agent.controller = AsyncMock()
    
    # Mock action results
    navigate_result = {
        "status": "success",
        "result": {
            "content": "<html><body>Test Page</body></html>",
            "page_state": {"url": "https://example.com", "title": "Test Page"},
            "screenshot": "base64screenshot"
        }
    }
    
    click_result = {
        "status": "success",
        "result": {
            "screenshot": "base64screenshot"
        }
    }
    
    input_text_result = {
        "status": "success",
        "result": {
            "screenshot": "base64screenshot"
        }
    }
    
    dom_result = {
        "status": "success",
        "result": {
            "content": "<html><body>Test Page</body></html>",
            "page_state": {"url": "https://example.com", "title": "Test Page"}
        }
    }
    
    screenshot_result = {
        "status": "success",
        "result": {
            "screenshot": "base64screenshot"
        }
    }
    
    wait_result = {
        "status": "success",
        "result": {}
    }
    
    # Configure the controller mock to return appropriate results based on action
    async def mock_execute_action(action_name, params):
        if action_name == "go_to_url":
            return navigate_result
        elif action_name == "click_element":
            return click_result
        elif action_name == "input_text":
            return input_text_result
        elif action_name == "get_dom":
            return dom_result
        elif action_name == "capture_screenshot":
            return screenshot_result
        elif action_name == "wait":
            return wait_result
        else:
            return {"status": "error", "message": "Unknown action"}
    
    agent.controller.execute_action = mock_execute_action
    
    yield agent
    
    # Cleanup
    agent.browser = None
    agent.controller = None

@pytest.mark.asyncio
async def test_initialize(agent_service):
    """Test agent initialization."""
    result = await agent_service.initialize()
    
    assert result["status"] == "success"
    assert agent_service.current_state["initialized"] == True
    assert agent_service.current_state["task_id"] is not None
    
    # Verify browser was initialized
    agent_service.browser.initialize.assert_called_once()

@pytest.mark.asyncio
async def test_navigate_to_url(agent_service):
    """Test navigation to a URL."""
    result = await agent_service.navigate_to_url("https://example.com")
    
    assert result["status"] == "success"
    assert result["url"] == "https://example.com"
    assert "screenshot" in result
    assert "page_state" in result
    
    # Verify action was executed via controller
    assert agent_service.current_state["current_url"] == "https://example.com"
    assert len(agent_service.current_state["history"]) == 1
    assert agent_service.current_state["history"][0]["action"] == "navigate"

@pytest.mark.asyncio
async def test_click_element(agent_service):
    """Test clicking an element."""
    result = await agent_service.click_element("#test-button")
    
    assert result["status"] == "success"
    assert result["selector"] == "#test-button"
    assert "screenshot" in result
    
    # Verify history was updated
    assert len(agent_service.current_state["history"]) == 1
    assert agent_service.current_state["history"][0]["action"] == "click_element"

@pytest.mark.asyncio
async def test_input_text(agent_service):
    """Test inputting text into a field."""
    result = await agent_service.input_text("#input-field", "test text")
    
    assert result["status"] == "success"
    assert result["selector"] == "#input-field"
    assert result["text_length"] == 9  # "test text"
    assert "screenshot" in result
    
    # Verify history was updated
    assert len(agent_service.current_state["history"]) == 1
    assert agent_service.current_state["history"][0]["action"] == "input_text"

@pytest.mark.asyncio
async def test_get_dom(agent_service):
    """Test getting the DOM."""
    result = await agent_service.get_dom()
    
    assert result["status"] == "success"
    assert "content" in result
    assert "page_state" in result
    
    # Verify history was updated
    assert len(agent_service.current_state["history"]) == 1
    assert agent_service.current_state["history"][0]["action"] == "get_dom"

@pytest.mark.asyncio
async def test_capture_screenshot(agent_service):
    """Test capturing a screenshot."""
    result = await agent_service.capture_screenshot(full_page=True)
    
    assert result["status"] == "success"
    assert result["screenshot"] == "base64screenshot"
    assert result["full_page"] == True
    
    # Verify history was updated
    assert len(agent_service.current_state["history"]) == 1
    assert agent_service.current_state["history"][0]["action"] == "capture_screenshot"

@pytest.mark.asyncio
async def test_wait(agent_service):
    """Test waiting for a specific time."""
    result = await agent_service.wait(1000)
    
    assert result["status"] == "success"
    assert result["waited_ms"] == 1000
    
    # Verify history was updated
    assert len(agent_service.current_state["history"]) == 1
    assert agent_service.current_state["history"][0]["action"] == "wait"

@pytest.mark.asyncio
async def test_get_current_state(agent_service):
    """Test getting current state."""
    # First navigate to set some state
    await agent_service.navigate_to_url("https://example.com")
    
    result = await agent_service.get_current_state()
    
    assert result["status"] == "success"
    assert "agent_state" in result
    assert "page_state" in result
    assert "screenshot" in result
    
    # Verify agent state
    agent_state = result["agent_state"]
    assert agent_state["initialized"] == True
    assert agent_state["current_url"] == "https://example.com"
    assert agent_state["task_id"] is not None
    assert agent_state["action_count"] == 1

@pytest.mark.asyncio
async def test_execute_action_sequence(agent_service):
    """Test executing a sequence of actions."""
    actions = [
        {"name": "go_to_url", "params": {"url": "https://example.com"}},
        {"name": "click_element", "params": {"selector": "#login-button"}},
        {"name": "input_text", "params": {"selector": "#username", "text": "testuser"}}
    ]
    
    result = await agent_service.execute_action_sequence(actions)
    
    assert result["status"] == "success"
    assert "results" in result
    assert len(result["results"]) == 3
    
    # Verify all actions were executed
    assert result["results"][0]["action_name"] == "go_to_url"
    assert result["results"][1]["action_name"] == "click_element"
    assert result["results"][2]["action_name"] == "input_text"
    
    # Verify history contains all actions
    assert len(agent_service.current_state["history"]) == 3

@pytest.mark.asyncio
async def test_shutdown(agent_service):
    """Test shutting down the agent."""
    result = await agent_service.shutdown()
    
    assert result["status"] == "success"
    assert agent_service.current_state["initialized"] == False
    
    # Verify browser was closed
    agent_service.browser.close.assert_called_once()

@pytest.mark.asyncio
async def test_execute_action_sequence_with_failure(agent_service):
    """Test executing an action sequence with a failure."""
    # Override mock for click action to simulate failure
    async def mock_execute_action_with_failure(action_name, params):
        if action_name == "go_to_url":
            return {
                "status": "success",
                "result": {
                    "content": "<html><body>Test Page</body></html>",
                    "page_state": {"url": "https://example.com", "title": "Test Page"},
                    "screenshot": "base64screenshot"
                }
            }
        elif action_name == "click_element":
            return {"status": "error", "message": "Element not found"}
        else:
            return {"status": "success", "result": {}}
    
    # Apply the mock
    agent_service.controller.execute_action = mock_execute_action_with_failure
    
    actions = [
        {"name": "go_to_url", "params": {"url": "https://example.com"}},
        {"name": "click_element", "params": {"selector": "#nonexistent-button"}},
        {"name": "input_text", "params": {"selector": "#username", "text": "testuser"}}
    ]
    
    result = await agent_service.execute_action_sequence(actions)
    
    assert result["status"] == "error"
    assert len(result["results"]) == 2  # Only first two actions attempted
    assert result["results"][0]["action_name"] == "go_to_url"
    assert result["results"][1]["action_name"] == "click_element"
    assert result["results"][1]["result"]["status"] == "error"
    
    # Third action should not have been executed
    assert len(agent_service.current_state["history"]) == 1  # Only navigation succeeded 