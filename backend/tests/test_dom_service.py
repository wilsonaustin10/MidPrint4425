"""
Tests for the DOM processing service.
"""
import pytest
import asyncio
from unittest.mock import MagicMock, patch
from app.dom.service import DOMProcessingService

# Sample DOM tree for testing
@pytest.fixture
def sample_dom_tree():
    return {
        "url": "https://example.com",
        "title": "Example Page",
        "timestamp": "2023-06-15T12:00:00Z",
        "tree": {
            "type": "element",
            "tagName": "html",
            "id": "html-1",
            "attributes": {},
            "css_selector": "html",
            "xpath": "/html",
            "children": [
                {
                    "type": "element",
                    "tagName": "head",
                    "id": "head-1",
                    "attributes": {},
                    "css_selector": "head",
                    "xpath": "/html/head",
                    "children": []
                },
                {
                    "type": "element",
                    "tagName": "body",
                    "id": "body-1",
                    "attributes": {},
                    "css_selector": "body",
                    "xpath": "/html/body",
                    "children": [
                        {
                            "type": "element",
                            "tagName": "header",
                            "id": "header-1",
                            "attributes": {"class": "site-header"},
                            "css_selector": "header.site-header",
                            "xpath": "/html/body/header",
                            "children": [
                                {
                                    "type": "element",
                                    "tagName": "h1",
                                    "id": "title-1",
                                    "attributes": {"class": "site-title"},
                                    "css_selector": "h1.site-title",
                                    "xpath": "/html/body/header/h1",
                                    "textContent": "Example Website",
                                    "children": []
                                },
                                {
                                    "type": "element",
                                    "tagName": "nav",
                                    "id": "nav-1",
                                    "attributes": {"class": "main-nav"},
                                    "css_selector": "nav.main-nav",
                                    "xpath": "/html/body/header/nav",
                                    "children": [
                                        {
                                            "type": "element",
                                            "tagName": "ul",
                                            "id": "menu-1",
                                            "attributes": {"class": "menu"},
                                            "css_selector": "ul.menu",
                                            "xpath": "/html/body/header/nav/ul",
                                            "children": [
                                                {
                                                    "type": "element",
                                                    "tagName": "li",
                                                    "id": "menu-item-1",
                                                    "attributes": {"class": "menu-item"},
                                                    "css_selector": "li.menu-item",
                                                    "xpath": "/html/body/header/nav/ul/li[1]",
                                                    "children": [
                                                        {
                                                            "type": "element",
                                                            "tagName": "a",
                                                            "id": "link-1",
                                                            "attributes": {
                                                                "href": "/",
                                                                "class": "nav-link"
                                                            },
                                                            "css_selector": "a.nav-link",
                                                            "xpath": "/html/body/header/nav/ul/li[1]/a",
                                                            "textContent": "Home",
                                                            "children": []
                                                        }
                                                    ]
                                                },
                                                {
                                                    "type": "element",
                                                    "tagName": "li",
                                                    "id": "menu-item-2",
                                                    "attributes": {"class": "menu-item"},
                                                    "css_selector": "li.menu-item",
                                                    "xpath": "/html/body/header/nav/ul/li[2]",
                                                    "children": [
                                                        {
                                                            "type": "element",
                                                            "tagName": "a",
                                                            "id": "link-2",
                                                            "attributes": {
                                                                "href": "/about",
                                                                "class": "nav-link"
                                                            },
                                                            "css_selector": "a.nav-link",
                                                            "xpath": "/html/body/header/nav/ul/li[2]/a",
                                                            "textContent": "About",
                                                            "children": []
                                                        }
                                                    ]
                                                }
                                            ]
                                        }
                                    ]
                                }
                            ]
                        },
                        {
                            "type": "element",
                            "tagName": "main",
                            "id": "main-1",
                            "attributes": {"class": "main-content"},
                            "css_selector": "main.main-content",
                            "xpath": "/html/body/main",
                            "children": [
                                {
                                    "type": "element",
                                    "tagName": "form",
                                    "id": "form-1",
                                    "attributes": {
                                        "action": "/submit",
                                        "method": "post",
                                        "class": "contact-form"
                                    },
                                    "css_selector": "form.contact-form",
                                    "xpath": "/html/body/main/form",
                                    "children": [
                                        {
                                            "type": "element",
                                            "tagName": "div",
                                            "id": "form-group-1",
                                            "attributes": {"class": "form-group"},
                                            "css_selector": "div.form-group",
                                            "xpath": "/html/body/main/form/div[1]",
                                            "children": [
                                                {
                                                    "type": "element",
                                                    "tagName": "label",
                                                    "id": "label-1",
                                                    "attributes": {"for": "name-input"},
                                                    "css_selector": "label[for=name-input]",
                                                    "xpath": "/html/body/main/form/div[1]/label",
                                                    "textContent": "Name",
                                                    "children": []
                                                },
                                                {
                                                    "type": "element",
                                                    "tagName": "input",
                                                    "id": "name-input",
                                                    "attributes": {
                                                        "type": "text",
                                                        "name": "name",
                                                        "placeholder": "Enter your name",
                                                        "required": "true"
                                                    },
                                                    "css_selector": "input#name-input",
                                                    "xpath": "/html/body/main/form/div[1]/input",
                                                    "children": []
                                                }
                                            ]
                                        },
                                        {
                                            "type": "element",
                                            "tagName": "div",
                                            "id": "form-group-2",
                                            "attributes": {"class": "form-group"},
                                            "css_selector": "div.form-group",
                                            "xpath": "/html/body/main/form/div[2]",
                                            "children": [
                                                {
                                                    "type": "element",
                                                    "tagName": "label",
                                                    "id": "label-2",
                                                    "attributes": {"for": "email-input"},
                                                    "css_selector": "label[for=email-input]",
                                                    "xpath": "/html/body/main/form/div[2]/label",
                                                    "textContent": "Email",
                                                    "children": []
                                                },
                                                {
                                                    "type": "element",
                                                    "tagName": "input",
                                                    "id": "email-input",
                                                    "attributes": {
                                                        "type": "email",
                                                        "name": "email",
                                                        "placeholder": "Enter your email",
                                                        "required": "true"
                                                    },
                                                    "css_selector": "input#email-input",
                                                    "xpath": "/html/body/main/form/div[2]/input",
                                                    "children": []
                                                }
                                            ]
                                        },
                                        {
                                            "type": "element",
                                            "tagName": "button",
                                            "id": "submit-button",
                                            "attributes": {
                                                "type": "submit",
                                                "class": "btn btn-primary"
                                            },
                                            "css_selector": "button.btn.btn-primary",
                                            "xpath": "/html/body/main/form/button",
                                            "textContent": "Submit",
                                            "children": []
                                        }
                                    ]
                                }
                            ]
                        },
                        {
                            "type": "element",
                            "tagName": "footer",
                            "id": "footer-1",
                            "attributes": {"class": "site-footer"},
                            "css_selector": "footer.site-footer",
                            "xpath": "/html/body/footer",
                            "children": [
                                {
                                    "type": "element",
                                    "tagName": "p",
                                    "id": "copyright",
                                    "attributes": {"class": "copyright"},
                                    "css_selector": "p.copyright",
                                    "xpath": "/html/body/footer/p",
                                    "textContent": "© 2023 Example Website",
                                    "children": []
                                }
                            ]
                        }
                    ]
                }
            ]
        },
        "interactiveElements": {
            "clickable": [
                {
                    "id": "link-1",
                    "tagName": "a",
                    "selector": "a.nav-link",
                    "xpath": "/html/body/header/nav/ul/li[1]/a",
                    "reason": "Links are clickable"
                },
                {
                    "id": "link-2",
                    "tagName": "a",
                    "selector": "a.nav-link",
                    "xpath": "/html/body/header/nav/ul/li[2]/a",
                    "reason": "Links are clickable"
                },
                {
                    "id": "submit-button",
                    "tagName": "button",
                    "selector": "button.btn.btn-primary",
                    "xpath": "/html/body/main/form/button",
                    "reason": "Buttons are clickable"
                }
            ],
            "inputs": [
                {
                    "id": "name-input",
                    "tagName": "input",
                    "selector": "input#name-input",
                    "xpath": "/html/body/main/form/div[1]/input",
                    "reason": "Input fields accept user input"
                },
                {
                    "id": "email-input",
                    "tagName": "input",
                    "selector": "input#email-input",
                    "xpath": "/html/body/main/form/div[2]/input",
                    "reason": "Input fields accept user input"
                }
            ],
            "forms": [
                {
                    "id": "form-1",
                    "tagName": "form",
                    "selector": "form.contact-form",
                    "xpath": "/html/body/main/form",
                    "reason": "Forms collect user data"
                }
            ],
            "navigational": [
                {
                    "id": "nav-1",
                    "tagName": "nav",
                    "selector": "nav.main-nav",
                    "xpath": "/html/body/header/nav",
                    "reason": "Navigation elements help users move through the site"
                }
            ]
        }
    }

@pytest.fixture
def mock_browser_executor():
    executor = MagicMock()
    return executor

@pytest.fixture
def dom_service(mock_browser_executor):
    return DOMProcessingService(mock_browser_executor)

class TestDOMProcessingService:
    def test_initialization(self, dom_service, mock_browser_executor):
        """Test the initialization of the DOM processing service."""
        assert dom_service.browser_executor == mock_browser_executor
    
    async def test_extract_dom(self, dom_service, mock_browser_executor, sample_dom_tree):
        """Test the extract_dom method."""
        # Configure the mock browser executor to return the sample DOM tree
        mock_browser_executor.extract_dom_tree.return_value = sample_dom_tree
        
        # Call the method with default options
        result = await dom_service.extract_dom()
        
        # Verify the result
        assert result == sample_dom_tree
        
        # Verify the browser executor was called with correct parameters
        mock_browser_executor.extract_dom_tree.assert_called_once()
        called_options = mock_browser_executor.extract_dom_tree.call_args[0][0]
        assert called_options["maxDepth"] == 25
        assert called_options["includeText"] is True
        
        # Test with custom options
        custom_options = {"maxDepth": 10, "includeText": False}
        await dom_service.extract_dom(custom_options)
        
        # Verify the custom options were passed through
        second_call_options = mock_browser_executor.extract_dom_tree.call_args[0][0]
        assert second_call_options["maxDepth"] == 10
        assert second_call_options["includeText"] is False
        
        # Ensure default options were applied where not specified
        assert second_call_options["includeAttributes"] is True
    
    def test_get_interactive_elements(self, dom_service, sample_dom_tree):
        """Test the get_interactive_elements method."""
        # Get the interactive elements
        interactive_elements = dom_service.get_interactive_elements(sample_dom_tree)
        
        # Verify the result
        assert "clickable" in interactive_elements
        assert "inputs" in interactive_elements
        assert "forms" in interactive_elements
        assert "navigational" in interactive_elements
        
        assert len(interactive_elements["clickable"]) == 3
        assert len(interactive_elements["inputs"]) == 2
        assert len(interactive_elements["forms"]) == 1
        assert len(interactive_elements["navigational"]) == 1
        
        # Test with invalid input
        assert dom_service.get_interactive_elements({}) == {
            "clickable": [],
            "inputs": [],
            "forms": [],
            "navigational": []
        }
    
    def test_get_element_by_id(self, dom_service, sample_dom_tree):
        """Test the get_element_by_id method."""
        # Get an element by ID
        header = dom_service.get_element_by_id(sample_dom_tree, "header-1")
        
        # Verify the result
        assert header is not None
        assert header["tagName"] == "header"
        assert header["attributes"]["class"] == "site-header"
        
        # Get another element
        input_element = dom_service.get_element_by_id(sample_dom_tree, "name-input")
        
        # Verify the result
        assert input_element is not None
        assert input_element["tagName"] == "input"
        assert input_element["attributes"]["name"] == "name"
        
        # Test with invalid ID
        assert dom_service.get_element_by_id(sample_dom_tree, "non-existent-id") is None
        
        # Test with invalid input
        assert dom_service.get_element_by_id({}, "header-1") is None
    
    def test_get_elements_by_tag(self, dom_service, sample_dom_tree):
        """Test the get_elements_by_tag method."""
        # Get elements by tag name
        inputs = dom_service.get_elements_by_tag(sample_dom_tree, "input")
        
        # Verify the result
        assert len(inputs) == 2
        assert inputs[0]["id"] == "name-input"
        assert inputs[1]["id"] == "email-input"
        
        # Get another tag
        links = dom_service.get_elements_by_tag(sample_dom_tree, "a")
        
        # Verify the result
        assert len(links) == 2
        assert links[0]["textContent"] == "Home"
        assert links[1]["textContent"] == "About"
        
        # Test case insensitivity
        assert len(dom_service.get_elements_by_tag(sample_dom_tree, "INPUT")) == 2
        
        # Test with tag that doesn't exist
        assert dom_service.get_elements_by_tag(sample_dom_tree, "article") == []
        
        # Test with invalid input
        assert dom_service.get_elements_by_tag({}, "input") == []
    
    def test_count_element_types(self, dom_service, sample_dom_tree):
        """Test the count_element_types method."""
        # Count element types
        counts = dom_service.count_element_types(sample_dom_tree)
        
        # Verify the result
        assert counts["html"] == 1
        assert counts["body"] == 1
        assert counts["header"] == 1
        assert counts["footer"] == 1
        assert counts["input"] == 2
        assert counts["button"] == 1
        assert counts["a"] == 2
        assert counts["form"] == 1
        
        # Test with invalid input
        assert dom_service.count_element_types({}) == {}
    
    def test_find_elements_by_selector(self, dom_service, sample_dom_tree):
        """Test the find_elements_by_selector method."""
        # Find by ID selector
        submit_button = dom_service.find_elements_by_selector(sample_dom_tree, "#submit-button")
        
        # Verify the result
        assert len(submit_button) == 1
        assert submit_button[0]["tagName"] == "button"
        assert submit_button[0]["textContent"] == "Submit"
        
        # Find by class selector
        form_groups = dom_service.find_elements_by_selector(sample_dom_tree, ".form-group")
        
        # Verify the result
        assert len(form_groups) == 2
        
        # Find by tag selector
        inputs = dom_service.find_elements_by_selector(sample_dom_tree, "input")
        
        # Verify the result
        assert len(inputs) == 2
        
        # Find by tag and attribute
        email_input = dom_service.find_elements_by_selector(sample_dom_tree, "input[type=\"email\"]")
        
        # Verify the result
        assert len(email_input) == 1
        assert email_input[0]["id"] == "email-input"
        
        # Test with selector that doesn't match
        assert dom_service.find_elements_by_selector(sample_dom_tree, ".non-existent-class") == []
        
        # Test with invalid input
        assert dom_service.find_elements_by_selector({}, ".form-group") == []
    
    def test_analyze_page_structure(self, dom_service, sample_dom_tree):
        """Test the analyze_page_structure method."""
        # Analyze page structure
        analysis = dom_service.analyze_page_structure(sample_dom_tree)
        
        # Verify the result structure
        assert "title" in analysis
        assert "url" in analysis
        assert "timestamp" in analysis
        assert "element_counts" in analysis
        assert "page_sections" in analysis
        assert "interactive_elements" in analysis
        assert "forms" in analysis
        
        # Verify content
        assert analysis["title"] == "Example Page"
        assert analysis["url"] == "https://example.com"
        
        # Check element counts
        assert analysis["element_counts"]["input"] == 2
        assert analysis["element_counts"]["button"] == 1
        
        # Check page sections
        sections_by_type = {section["type"]: section for section in analysis["page_sections"]}
        assert "header" in sections_by_type
        assert "footer" in sections_by_type
        assert "main" in sections_by_type
        assert "navigation" in sections_by_type
        
        # Check interactive elements
        assert analysis["interactive_elements"]["total"] == 7
        assert analysis["interactive_elements"]["by_type"]["clickable"] == 3
        assert analysis["interactive_elements"]["by_type"]["inputs"] == 2
        
        # Check form analysis
        assert len(analysis["forms"]) == 1
        assert analysis["forms"][0]["input_count"] == 2
        assert analysis["forms"][0]["button_count"] == 1
        
        # Test with invalid input
        assert dom_service.analyze_page_structure({}) == {"error": "Invalid DOM tree"}
    
    def test_find_clickable_path(self, dom_service, sample_dom_tree):
        """Test the find_clickable_path method."""
        # Find a clickable path by exact text
        about_link = dom_service.find_clickable_path(sample_dom_tree, "About")
        
        # Verify the result
        assert about_link is not None
        assert about_link["id"] == "link-2"
        
        # Find a clickable path by partial text
        submit_button = dom_service.find_clickable_path(sample_dom_tree, "Subm")
        
        # Verify the result
        assert submit_button is not None
        assert submit_button["id"] == "submit-button"
        
        # Test with text that doesn't match
        assert dom_service.find_clickable_path(sample_dom_tree, "Contact Us") is None
        
        # Test with invalid input
        assert dom_service.find_clickable_path({}, "About") is None
    
    def test_find_input_field(self, dom_service, sample_dom_tree):
        """Test the find_input_field method."""
        # Find input field by name attribute
        name_field = dom_service.find_input_field(sample_dom_tree, "name")
        
        # Verify the result
        assert name_field is not None
        assert name_field["id"] == "name-input"
        
        # Find input field by label text
        email_field = dom_service.find_input_field(sample_dom_tree, "Email")
        
        # Verify the result
        assert email_field is not None
        assert email_field["id"] == "email-input"
        
        # Find input field by placeholder
        name_field_by_placeholder = dom_service.find_input_field(sample_dom_tree, "Enter your name")
        
        # Verify the result
        assert name_field_by_placeholder is not None
        assert name_field_by_placeholder["id"] == "name-input"
        
        # Test with field that doesn't exist
        assert dom_service.find_input_field(sample_dom_tree, "Phone") is None
        
        # Test with invalid input
        assert dom_service.find_input_field({}, "Email") is None
    
    def test_create_simplified_dom(self, dom_service, sample_dom_tree):
        """Test the create_simplified_dom method."""
        # Create simplified DOM
        simplified = dom_service.create_simplified_dom(sample_dom_tree, max_depth=2)
        
        # Verify the result structure
        assert "url" in simplified
        assert "title" in simplified
        assert "timestamp" in simplified
        assert "tree" in simplified
        assert "interactive_summary" in simplified
        assert "page_structure" in simplified
        
        # Verify content
        assert simplified["url"] == "https://example.com"
        assert simplified["title"] == "Example Page"
        
        # Check tree structure
        assert simplified["tree"]["tag"] == "html"
        assert "children" in simplified["tree"]
        assert len(simplified["tree"]["children"]) == 2  # head and body
        
        # Check interactive summary
        assert simplified["interactive_summary"]["clickable_count"] == 3
        assert simplified["interactive_summary"]["input_count"] == 2
        assert len(simplified["interactive_summary"]["top_clickable"]) <= 5
        
        # Check page structure
        section_types = [section["type"] for section in simplified["page_structure"]["sections"]]
        assert "header" in section_types
        assert "footer" in section_types
        assert "main" in section_types
        assert "navigation" in section_types
        
        # Test with different depth
        simplified_shallow = dom_service.create_simplified_dom(sample_dom_tree, max_depth=1)
        
        # Verify the depth restriction
        body_node = next((child for child in simplified_shallow["tree"]["children"] 
                          if child.get("tag") == "body"), None)
        assert body_node is not None
        assert "children" not in body_node or len(body_node["children"]) == 0
        
        # Test with invalid input
        assert dom_service.create_simplified_dom({}) == {"error": "Invalid DOM tree"}
    
    async def test_highlight_elements(self, dom_service, mock_browser_executor):
        """Test the highlight_elements method."""
        # Configure the mock
        mock_browser_executor.highlight_element.return_value = True
        
        # Call the method
        selectors = ["#header-1", ".site-footer", "input[type='email']"]
        result = await dom_service.highlight_elements(selectors)
        
        # Verify the result
        assert all(result.values())
        assert set(result.keys()) == set(selectors)
        
        # Verify the browser executor was called correctly
        assert mock_browser_executor.highlight_element.call_count == 3
        
        # Test with an error
        mock_browser_executor.highlight_element.side_effect = Exception("Test error")
        result = await dom_service.highlight_elements(["#header-1"])
        
        # Verify the result
        assert result["#header-1"] is False
    
    def test_get_element_xpath_and_selector(self, dom_service, sample_dom_tree):
        """Test the get_element_xpath and get_element_selector methods."""
        # Get xpath for a selector
        xpath = dom_service.get_element_xpath(sample_dom_tree, "input#name-input")
        
        # Verify the result
        assert xpath == "/html/body/main/form/div[1]/input"
        
        # Get selector for an xpath
        selector = dom_service.get_element_selector(sample_dom_tree, "/html/body/main/form/div[1]/input")
        
        # Verify the result
        assert selector == "input#name-input"
        
        # Test with invalid inputs
        assert dom_service.get_element_xpath(sample_dom_tree, ".non-existent") is None
        assert dom_service.get_element_selector(sample_dom_tree, "/non/existent/path") is None
    
    def test_classify_page_type(self, dom_service, sample_dom_tree):
        """Test the classify_page_type method."""
        # Classify the page type
        classification = dom_service.classify_page_type(sample_dom_tree)
        
        # Verify the result
        assert isinstance(classification, dict)
        assert sum(classification.values()) > 0.99  # Allow for floating point error
        assert sum(classification.values()) < 1.01
        
        # The sample page should be classified primarily as a form page
        assert "form" in classification
        
        # Test with invalid input
        assert dom_service.classify_page_type({}) == {"unknown": 1.0}

# Run the tests with pytest
# To run: pytest -xvs test_dom_service.py 