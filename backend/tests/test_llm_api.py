"""
Tests for the LLM DOM API endpoints.
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock

from app.main import app
from app.dom.service import dom_processing_service

client = TestClient(app)

@pytest.fixture
def mock_dom_tree():
    """Sample DOM tree for testing."""
    return {
        "url": "https://example.com",
        "title": "Example Page",
        "timestamp": "2023-06-15T12:00:00Z",
        "tree": {
            "type": "element",
            "tagName": "html",
            "id": "html-1",
            "css_selector": "html",
            "xpath": "/html",
            "children": [
                {
                    "type": "element",
                    "tagName": "body",
                    "id": "body-1",
                    "css_selector": "body",
                    "xpath": "/html/body",
                    "children": [
                        {
                            "type": "element",
                            "tagName": "button",
                            "id": "login-button",
                            "attributes": {"class": "primary-button"},
                            "css_selector": "button#login-button",
                            "xpath": "/html/body/button",
                            "textContent": "Log In",
                            "children": []
                        },
                        {
                            "type": "element",
                            "tagName": "input",
                            "id": "username",
                            "attributes": {
                                "type": "text",
                                "name": "username",
                                "placeholder": "Enter username"
                            },
                            "css_selector": "input#username",
                            "xpath": "/html/body/input[1]",
                            "children": []
                        }
                    ]
                }
            ]
        },
        "interactiveElements": {
            "clickable": [
                {
                    "id": "login-button",
                    "tagName": "button",
                    "selector": "button#login-button",
                    "xpath": "/html/body/button",
                    "reason": "Buttons are clickable"
                }
            ],
            "inputs": [
                {
                    "id": "username",
                    "tagName": "input",
                    "selector": "input#username",
                    "xpath": "/html/body/input[1]",
                    "reason": "Input fields accept user input"
                }
            ],
            "forms": [],
            "navigational": []
        }
    }

@pytest.fixture
def mock_dom_processing_service():
    with patch("app.api.routes.llm.dom_processing_service") as mock_service:
        yield mock_service

class TestLLMDomAPI:
    def test_extract_dom_for_llm(self, mock_dom_processing_service, mock_dom_tree):
        """Test the extract-for-llm endpoint."""
        # Configure mocks
        mock_dom_processing_service.extract_dom.return_value = mock_dom_tree
        mock_dom_processing_service.get_interactive_elements.return_value = mock_dom_tree["interactiveElements"]
        mock_dom_processing_service.classify_page_type.return_value = {"login": 0.8, "form": 0.2}
        mock_dom_processing_service.analyze_page_structure.return_value = {
            "element_counts": {"html": 1, "body": 1, "button": 1, "input": 1},
            "page_sections": []
        }
        mock_dom_processing_service.create_simplified_dom.return_value = {
            "url": mock_dom_tree["url"],
            "title": mock_dom_tree["title"],
            "tree": {"tag": "html", "children": [{"tag": "body"}]}
        }
        
        # Make request with default parameters
        response = client.post("/api/llm/extract-for-llm", json={})
        
        # Check response
        assert response.status_code == 200
        data = response.json()
        
        # Verify basic structure
        assert data["url"] == "https://example.com"
        assert data["title"] == "Example Page"
        assert "page_type" in data
        assert "interactive_elements_summary" in data
        assert "dom" in data
        assert "page_analysis" in data
        
        # Check that simplified DOM is used by default
        assert mock_dom_processing_service.create_simplified_dom.called
        
        # Check with include_interactive_only=True
        response = client.post("/api/llm/extract-for-llm", json={"include_interactive_only": True})
        assert response.status_code == 200
        data = response.json()
        
        # Verify that only interactive elements are included
        assert "elements" in data
        assert "clickable" in data["elements"]
        assert "inputs" in data["elements"]
        assert len(data["elements"]["clickable"]) == 1
        assert len(data["elements"]["inputs"]) == 1
        
        # Check with simplify=False
        response = client.post("/api/llm/extract-for-llm", json={"simplify": False})
        assert response.status_code == 200
        data = response.json()
        
        # Verify that full DOM is included
        assert "dom" in data
        assert "tree" in data["dom"]
        
        # Check error handling
        mock_dom_processing_service.extract_dom.side_effect = Exception("Test error")
        response = client.post("/api/llm/extract-for-llm", json={})
        assert response.status_code == 500
        assert "error" in response.json()["detail"].lower()
    
    def test_find_element_for_llm(self, mock_dom_processing_service, mock_dom_tree):
        """Test the find-element endpoint."""
        # Configure mocks
        mock_dom_processing_service.extract_dom.return_value = mock_dom_tree
        mock_dom_processing_service.get_interactive_elements.return_value = mock_dom_tree["interactiveElements"]
        mock_dom_processing_service.get_element_by_id.side_effect = lambda dom, id: next(
            (element for element in [mock_dom_tree["tree"]["children"][0]["children"][0],
                                     mock_dom_tree["tree"]["children"][0]["children"][1]]
             if element["id"] == id), None
        )
        mock_dom_processing_service._get_all_elements.return_value = [
            mock_dom_tree["tree"]["children"][0]["children"][0],
            mock_dom_tree["tree"]["children"][0]["children"][1]
        ]
        
        # Make request for clickable element
        response = client.post("/api/llm/find-element", json={"query": "log in", "element_type": "clickable"})
        
        # Check response
        assert response.status_code == 200
        data = response.json()
        
        # Verify results
        assert len(data) == 1
        assert data[0]["id"] == "login-button"
        assert data[0]["tag"] == "button"
        assert "match_score" in data[0]
        
        # Make request for input element
        response = client.post("/api/llm/find-element", json={"query": "username", "element_type": "input"})
        
        # Check response
        assert response.status_code == 200
        data = response.json()
        
        # Verify results
        assert len(data) == 1
        assert data[0]["id"] == "username"
        assert data[0]["tag"] == "input"
        
        # Check with no results
        response = client.post("/api/llm/find-element", json={"query": "does not exist"})
        assert response.status_code == 200
        assert len(response.json()) == 0
        
        # Check error handling
        mock_dom_processing_service.extract_dom.side_effect = Exception("Test error")
        response = client.post("/api/llm/find-element", json={"query": "log in"})
        assert response.status_code == 500
        assert "error" in response.json()["detail"].lower()
    
    def test_suggest_action_for_llm(self, mock_dom_processing_service, mock_dom_tree):
        """Test the suggest-action endpoint."""
        # Configure mocks
        mock_dom_processing_service.extract_dom.return_value = mock_dom_tree
        mock_dom_processing_service.get_interactive_elements.return_value = mock_dom_tree["interactiveElements"]
        mock_dom_processing_service.get_element_by_id.side_effect = lambda dom, id: next(
            (element for element in [mock_dom_tree["tree"]["children"][0]["children"][0],
                                     mock_dom_tree["tree"]["children"][0]["children"][1]]
             if element["id"] == id), None
        )
        
        # For button element
        response = client.post("/api/llm/suggest-action", json={"query": "log in"})
        
        # Check response
        assert response.status_code == 200
        data = response.json()
        
        # Verify suggested action
        assert data["success"] is True
        assert data["suggestion"]["action"] == "click"
        assert data["suggestion"]["element"]["id"] == "login-button"
        
        # For input element
        response = client.post("/api/llm/suggest-action", json={"query": "username"})
        
        # Check response
        assert response.status_code == 200
        data = response.json()
        
        # Verify suggested action
        assert data["success"] is True
        assert data["suggestion"]["action"] == "input"
        assert data["suggestion"]["element"]["id"] == "username"
        assert "text" in data["suggestion"]["parameters"]
        
        # With no matching elements
        response = client.post("/api/llm/suggest-action", json={"query": "does not exist"})
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is False
        assert data["suggestion"] is None
        
        # Check error handling
        mock_dom_processing_service.extract_dom.side_effect = Exception("Test error")
        response = client.post("/api/llm/suggest-action", json={"query": "log in"})
        assert response.status_code == 500
        assert "error" in response.json()["detail"].lower() 