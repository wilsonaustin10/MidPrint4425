import pytest
import asyncio
from app.controller.service import controller_service, ActionType
from app.browser.browser import browser_manager

@pytest.mark.asyncio
async def test_controller_initialization():
    """Test that controller service initializes correctly"""
    # Check if controller has a registry
    assert controller_service.registry is not None
    
    # Check if default actions are registered
    actions = controller_service.registry.list_actions()
    assert len(actions) > 0
    
    # Check if specific actions exist
    action_names = [action["name"] for action in actions]
    assert "go_to_url" in action_names
    assert "click_element" in action_names
    assert "input_text" in action_names
    assert "get_dom" in action_names
    assert "capture_screenshot" in action_names

@pytest.mark.asyncio
async def test_action_categorization():
    """Test that actions are correctly categorized"""
    # Get navigation actions
    nav_actions = controller_service.registry.list_actions(ActionType.NAVIGATION)
    nav_names = [action["name"] for action in nav_actions]
    assert "go_to_url" in nav_names
    
    # Get interaction actions
    int_actions = controller_service.registry.list_actions(ActionType.INTERACTION)
    int_names = [action["name"] for action in int_actions]
    assert "click_element" in int_names
    assert "input_text" in int_names
    
    # Get extraction actions
    ext_actions = controller_service.registry.list_actions(ActionType.EXTRACTION)
    ext_names = [action["name"] for action in ext_actions]
    assert "get_dom" in ext_names
    assert "capture_screenshot" in ext_names

@pytest.mark.asyncio
async def test_parameter_validation():
    """Test parameter validation for actions"""
    # Missing required parameter
    errors = controller_service.registry.validate_params("go_to_url", {})
    assert len(errors) > 0
    assert "url" in errors
    
    # Valid parameters
    errors = controller_service.registry.validate_params("go_to_url", {"url": "https://example.com"})
    assert len(errors) == 0
    
    # Invalid action
    errors = controller_service.registry.validate_params("non_existent_action", {})
    assert len(errors) > 0
    assert "action" in errors

@pytest.mark.asyncio
async def test_execute_navigation_action():
    """Test execution of navigation action"""
    try:
        # Close any existing browser instance to start fresh
        if browser_manager.is_initialized:
            await browser_manager.close()
        
        # Execute go_to_url action
        result = await controller_service.execute_action("go_to_url", {"url": "https://example.com"})
        
        # Check result
        assert result["status"] == "success"
        assert result["action"] == "go_to_url"
        assert "result" in result
        assert result["result"]["url"] == "https://example.com"
        assert "content" in result["result"]
        assert "screenshot" in result["result"]
        assert "page_state" in result["result"]
    finally:
        # Clean up
        if browser_manager.is_initialized:
            await browser_manager.close()

@pytest.mark.asyncio
async def test_execute_dom_action():
    """Test execution of DOM action"""
    try:
        # Navigate to a page first
        await controller_service.execute_action("go_to_url", {"url": "https://example.com"})
        
        # Execute get_dom action
        result = await controller_service.execute_action("get_dom", {})
        
        # Check result
        assert result["status"] == "success"
        assert result["action"] == "get_dom"
        assert "result" in result
        assert "content" in result["result"]
        assert "page_state" in result["result"]
    finally:
        # Clean up
        if browser_manager.is_initialized:
            await browser_manager.close()

@pytest.mark.asyncio
async def test_error_handling():
    """Test error handling in controller service"""
    # Non-existent action
    result = await controller_service.execute_action("non_existent_action", {})
    assert result["status"] == "error"
    assert "message" in result
    
    # Parameter validation error
    result = await controller_service.execute_action("go_to_url", {})
    assert result["status"] == "error"
    assert "message" in result
    assert "errors" in result 