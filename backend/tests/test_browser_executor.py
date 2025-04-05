"""
Tests for the browser executor module that handles JavaScript execution in the browser.
"""
import pytest
import asyncio
import os
from unittest.mock import MagicMock, AsyncMock, patch

from app.dom.browser_executor import BrowserExecutor

@pytest.fixture
def mock_browser_manager():
    """Fixture for creating a mock browser manager"""
    browser = AsyncMock()
    browser.is_initialized = True
    browser.page = AsyncMock()
    return browser

@pytest.fixture
def browser_executor(mock_browser_manager):
    """Fixture for creating a browser executor with a mock browser manager"""
    executor = BrowserExecutor(mock_browser_manager)
    
    # Mock the load_script method to avoid file I/O
    executor.load_script = AsyncMock(return_value="""
        function extractDomTree(options) {
            return {
                url: "https://example.com",
                title: "Example Domain",
                timestamp: new Date().toISOString(),
                tree: {
                    id: "body",
                    type: "element",
                    tagName: "body",
                    children: [
                        {
                            id: "el-1",
                            type: "element",
                            tagName: "div",
                            css_selector: "div#main",
                            xpath: "/html/body/div[1]",
                            children: [
                                {
                                    type: "text",
                                    content: "Example content"
                                }
                            ]
                        },
                        {
                            id: "el-2",
                            type: "element",
                            tagName: "button",
                            css_selector: "button.btn",
                            xpath: "/html/body/button[1]",
                            interactive: true,
                            interactiveTypes: ["clickable"],
                            interactiveReasons: {
                                clickable: ["tag: button"]
                            },
                            children: []
                        }
                    ]
                },
                interactiveElements: {
                    clickable: [
                        {
                            id: "el-2",
                            tagName: "button",
                            selector: "button.btn",
                            xpath: "/html/body/button[1]",
                            interactiveReasons: ["tag: button"]
                        }
                    ],
                    inputs: [],
                    forms: [],
                    navigational: []
                }
            };
        }
    """)
    
    return executor

@pytest.mark.asyncio
async def test_extract_dom_tree(browser_executor, mock_browser_manager):
    """Test extracting DOM tree from the browser"""
    # Mock the execute_script method to return a sample response
    browser_executor.execute_script = AsyncMock(return_value={
        "url": "https://example.com",
        "title": "Example Domain",
        "timestamp": "2023-01-01T00:00:00.000Z",
        "tree": {
            "id": "body",
            "type": "element",
            "tagName": "body",
            "children": [
                {
                    "id": "el-1",
                    "type": "element",
                    "tagName": "div",
                    "css_selector": "div#main",
                    "xpath": "/html/body/div[1]",
                    "children": [
                        {
                            "type": "text",
                            "content": "Example content"
                        }
                    ]
                },
                {
                    "id": "el-2",
                    "type": "element",
                    "tagName": "button",
                    "css_selector": "button.btn",
                    "xpath": "/html/body/button[1]",
                    "interactive": True,
                    "interactiveTypes": ["clickable"],
                    "interactiveReasons": {
                        "clickable": ["tag: button"]
                    },
                    "children": []
                }
            ]
        },
        "interactiveElements": {
            "clickable": [
                {
                    "id": "el-2",
                    "tagName": "button",
                    "selector": "button.btn",
                    "xpath": "/html/body/button[1]",
                    "interactiveReasons": ["tag: button"]
                }
            ],
            "inputs": [],
            "forms": [],
            "navigational": []
        }
    })
    
    # Call the extract_dom_tree method
    result = await browser_executor.extract_dom_tree({"maxDepth": 10})
    
    # Assert execute_script was called (the mocked executor would return our test data)
    browser_executor.execute_script.assert_called_once()
    
    # Verify the result structure
    assert result["url"] == "https://example.com"
    assert result["title"] == "Example Domain"
    assert "timestamp" in result
    assert "tree" in result
    assert "interactiveElements" in result
    
    # Verify the tree structure
    tree = result["tree"]
    assert tree["id"] == "body"
    assert tree["type"] == "element"
    assert tree["tagName"] == "body"
    assert len(tree["children"]) == 2
    
    # Verify the interactive elements detection
    interactive_elements = result["interactiveElements"]
    assert len(interactive_elements["clickable"]) == 1
    assert interactive_elements["clickable"][0]["tagName"] == "button"
    assert len(interactive_elements["inputs"]) == 0
    assert len(interactive_elements["forms"]) == 0
    assert len(interactive_elements["navigational"]) == 0
    
    # Verify the metadata of the button
    button = tree["children"][1]
    assert button["tagName"] == "button"
    assert button["interactive"] == True
    assert "clickable" in button["interactiveTypes"]
    assert "tag: button" in button["interactiveReasons"]["clickable"]

@pytest.mark.asyncio
async def test_highlight_element(browser_executor, mock_browser_manager):
    """Test highlighting an element in the browser"""
    # Mock the execute_script method to return success
    browser_executor.execute_script = AsyncMock(return_value=True)
    
    # Call the highlight_element method
    result = await browser_executor.highlight_element("button.btn")
    
    # Assert execute_script was called
    browser_executor.execute_script.assert_called_once()
    
    # Verify the result
    assert result == True

@pytest.mark.asyncio
async def test_get_element_by_selector(browser_executor, mock_browser_manager):
    """Test getting an element by CSS selector"""
    # Mock the execute_script method to return an element
    browser_executor.execute_script = AsyncMock(return_value={
        "tagName": "button",
        "id": "submit-btn",
        "classes": ["btn", "btn-primary"],
        "xpath": "/html/body/div/form/button",
        "position": {
            "x": 100,
            "y": 200,
            "width": 120,
            "height": 40
        },
        "textContent": "Submit",
        "attributes": {
            "id": "submit-btn",
            "class": "btn btn-primary",
            "type": "submit"
        }
    })
    
    # Call the get_element_by_selector method
    result = await browser_executor.get_element_by_selector("button#submit-btn")
    
    # Assert execute_script was called
    browser_executor.execute_script.assert_called_once()
    
    # Verify the result
    assert result["tagName"] == "button"
    assert result["id"] == "submit-btn"
    assert "btn" in result["classes"]
    assert "btn-primary" in result["classes"]
    assert result["xpath"] == "/html/body/div/form/button"
    assert result["position"]["x"] == 100
    assert result["position"]["y"] == 200
    assert result["textContent"] == "Submit"
    assert result["attributes"]["type"] == "submit"

@pytest.mark.asyncio
async def test_find_elements_by_text(browser_executor, mock_browser_manager):
    """Test finding elements by text content"""
    # Mock the execute_script method to return a list of elements
    browser_executor.execute_script = AsyncMock(return_value=[
        {
            "tagName": "p",
            "id": None,
            "classes": ["intro"],
            "selector": "p.intro",
            "text": "Welcome to the example site!",
            "position": {
                "x": 50,
                "y": 100,
                "width": 300,
                "height": 20
            },
            "matchedText": "Welcome to the example site!"
        },
        {
            "tagName": "a",
            "id": "learn-more",
            "classes": ["link"],
            "selector": "a#learn-more",
            "text": "Learn more about our examples",
            "position": {
                "x": 50,
                "y": 150,
                "width": 200,
                "height": 30
            },
            "matchedText": "Learn more about our examples"
        }
    ])
    
    # Call the find_elements_by_text method
    result = await browser_executor.find_elements_by_text("example")
    
    # Assert execute_script was called
    browser_executor.execute_script.assert_called_once()
    
    # Verify the result
    assert len(result) == 2
    assert result[0]["tagName"] == "p"
    assert "intro" in result[0]["classes"]
    assert "Welcome to the example site!" in result[0]["text"]
    
    assert result[1]["tagName"] == "a"
    assert result[1]["id"] == "learn-more"
    assert "Learn more about our examples" in result[1]["text"] 