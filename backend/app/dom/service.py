"""
DOM Processing Service for analyzing web page structures.
This service provides methods for extracting and analyzing DOM trees,
identifying interactive elements, and providing simplified representations.
"""
from typing import Dict, Any, List, Optional, Tuple, Union, Set
import logging
import json
import re
from collections import defaultdict, Counter
from functools import lru_cache

from app.dom.browser_executor import BrowserExecutor
from app.dom import browser_executor
from app.core.config import settings

logger = logging.getLogger(__name__)

class DOMProcessingService:
    """
    Service for processing and analyzing DOM structures.
    """
    
    def __init__(self, browser_executor: BrowserExecutor):
        """
        Initialize the DOM processing service.
        
        Args:
            browser_executor: The browser executor instance
        """
        self.browser_executor = browser_executor
    
    async def extract_dom(self, options: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Extract the DOM tree from the current page.
        
        Args:
            options: Optional configuration for the DOM extraction
            
        Returns:
            The extracted DOM tree structure
        """
        if options is None:
            options = {}
        
        # Set default options if not provided
        default_options = {
            "maxDepth": 25,
            "includeText": True,
            "includeAttributes": True,
            "includePosition": True,
            "includeVisibility": True,
            "includeAccessibility": True,
            "maxTextLength": 150
        }
        
        for key, value in default_options.items():
            if key not in options:
                options[key] = value
        
        try:
            # Use the browser executor to extract the DOM tree
            result = await self.browser_executor.extract_dom_tree(options)
            logger.info(f"Extracted DOM tree from {result.get('url', 'unknown URL')}")
            return result
        except Exception as e:
            logger.error(f"Error extracting DOM tree: {str(e)}")
            raise
    
    def get_interactive_elements(self, dom_tree: Dict[str, Any]) -> Dict[str, List[Dict[str, Any]]]:
        """
        Get the interactive elements from a DOM tree.
        
        Args:
            dom_tree: The DOM tree structure
            
        Returns:
            Dictionary of interactive elements by type
        """
        if not dom_tree or "interactiveElements" not in dom_tree:
            return {
                "clickable": [],
                "inputs": [],
                "forms": [],
                "navigational": []
            }
        
        return dom_tree["interactiveElements"]
    
    def get_element_by_id(self, dom_tree: Dict[str, Any], element_id: str) -> Optional[Dict[str, Any]]:
        """
        Find an element in the DOM tree by its ID.
        
        Args:
            dom_tree: The DOM tree structure
            element_id: The ID of the element to find
            
        Returns:
            The element if found, None otherwise
        """
        if not dom_tree or "tree" not in dom_tree:
            return None
        
        return self._find_element_by_id_recursive(dom_tree["tree"], element_id)
    
    def _find_element_by_id_recursive(self, node: Dict[str, Any], element_id: str) -> Optional[Dict[str, Any]]:
        """Recursively search for an element by ID in the DOM tree."""
        if not node:
            return None
        
        if node.get("id") == element_id:
            return node
        
        if "children" in node:
            for child in node["children"]:
                result = self._find_element_by_id_recursive(child, element_id)
                if result:
                    return result
        
        return None
    
    def get_elements_by_tag(self, dom_tree: Dict[str, Any], tag_name: str) -> List[Dict[str, Any]]:
        """
        Find elements in the DOM tree by tag name.
        
        Args:
            dom_tree: The DOM tree structure
            tag_name: The tag name to search for
            
        Returns:
            List of matching elements
        """
        if not dom_tree or "tree" not in dom_tree:
            return []
        
        results = []
        self._find_elements_by_tag_recursive(dom_tree["tree"], tag_name.lower(), results)
        return results
    
    def _find_elements_by_tag_recursive(self, node: Dict[str, Any], tag_name: str, results: List[Dict[str, Any]]) -> None:
        """Recursively search for elements by tag name in the DOM tree."""
        if not node or node.get("type") != "element":
            return
        
        if node.get("tagName", "").lower() == tag_name:
            results.append(node)
        
        if "children" in node:
            for child in node["children"]:
                self._find_elements_by_tag_recursive(child, tag_name, results)
    
    def count_element_types(self, dom_tree: Dict[str, Any]) -> Dict[str, int]:
        """
        Count the number of each element type in the DOM tree.
        
        Args:
            dom_tree: The DOM tree structure
            
        Returns:
            Dictionary with counts of each element type
        """
        if not dom_tree or "tree" not in dom_tree:
            return {}
        
        counter = Counter()
        self._count_element_types_recursive(dom_tree["tree"], counter)
        return dict(counter)
    
    def _count_element_types_recursive(self, node: Dict[str, Any], counter: Counter) -> None:
        """Recursively count element types in the DOM tree."""
        if not node:
            return
        
        if node.get("type") == "element" and "tagName" in node:
            counter[node["tagName"]] += 1
        
        if "children" in node:
            for child in node["children"]:
                self._count_element_types_recursive(child, counter)
    
    def find_elements_by_selector(self, dom_tree: Dict[str, Any], selector: str) -> List[Dict[str, Any]]:
        """
        Find elements by CSS selector, using selector heuristics from the local DOM representation.
        Note: This is not a full CSS selector implementation, but a simplified version.
        
        Args:
            dom_tree: The DOM tree structure
            selector: The CSS selector
            
        Returns:
            List of matching elements
        """
        if not dom_tree or "tree" not in dom_tree:
            return []
        
        # Break down the selector into its components
        selector = selector.strip()
        results = []
        
        # Handle ID selectors (#id)
        if selector.startswith('#'):
            element_id = selector[1:]
            element = self.get_element_by_id(dom_tree, element_id)
            if element:
                results.append(element)
            return results
        
        # Handle class selectors (.class)
        if selector.startswith('.'):
            class_name = selector[1:]
            all_elements = self._get_all_elements(dom_tree["tree"])
            for element in all_elements:
                attributes = element.get("attributes", {})
                if "class" in attributes and class_name in attributes["class"].split():
                    results.append(element)
            return results
        
        # Handle tag selectors (tag) - possibly with additional filters
        match = re.match(r'^(\w+)(?:\[([^\]]+)\])?$', selector)
        if match:
            tag_name = match.group(1)
            attr_filter = match.group(2)
            
            elements = self.get_elements_by_tag(dom_tree, tag_name)
            
            # Apply attribute filter if present
            if attr_filter:
                filtered_elements = []
                attr_match = re.match(r'^([^=]+)(?:=[\'\"]([^\'\"]+)[\'\"])?$', attr_filter)
                if attr_match:
                    attr_name = attr_match.group(1)
                    attr_value = attr_match.group(2)
                    
                    for element in elements:
                        attributes = element.get("attributes", {})
                        if attr_name in attributes:
                            if attr_value is None or attributes[attr_name] == attr_value:
                                filtered_elements.append(element)
                
                return filtered_elements
            
            return elements
        
        # For more complex selectors, find elements that have a matching css_selector property
        # This is a fallback and not a true selector engine
        all_elements = self._get_all_elements(dom_tree["tree"])
        for element in all_elements:
            if element.get("css_selector") == selector:
                results.append(element)
        
        return results
    
    def _get_all_elements(self, node: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Recursively get all elements in the DOM tree."""
        if not node:
            return []
        
        results = []
        if node.get("type") == "element":
            results.append(node)
        
        if "children" in node:
            for child in node["children"]:
                results.extend(self._get_all_elements(child))
        
        return results
    
    def analyze_page_structure(self, dom_tree: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze the page structure to identify key sections and layouts.
        
        Args:
            dom_tree: The DOM tree structure
            
        Returns:
            Dictionary with analysis results
        """
        if not dom_tree or "tree" not in dom_tree:
            return {"error": "Invalid DOM tree"}
        
        analysis = {
            "title": dom_tree.get("title", ""),
            "url": dom_tree.get("url", ""),
            "timestamp": dom_tree.get("timestamp", ""),
            "element_counts": self.count_element_types(dom_tree),
            "page_sections": self._identify_page_sections(dom_tree["tree"]),
            "interactive_elements": {
                "total": sum(len(elements) for elements in self.get_interactive_elements(dom_tree).values()),
                "by_type": {k: len(v) for k, v in self.get_interactive_elements(dom_tree).items()}
            }
        }
        
        # Add form analysis if forms are present
        forms = self.get_elements_by_tag(dom_tree, "form")
        if forms:
            analysis["forms"] = self._analyze_forms(forms)
        
        return analysis
    
    def _identify_page_sections(self, tree: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Identify major page sections like header, footer, main content, etc.
        
        Args:
            tree: The DOM tree structure
            
        Returns:
            List of identified sections
        """
        sections = []
        
        # Look for common section elements by ID, role, or tag
        section_identifiers = {
            "header": ["header", "head", "top", "banner"],
            "footer": ["footer", "foot", "bottom"],
            "main": ["main", "content", "main-content"],
            "navigation": ["nav", "navigation", "menu", "navbar"],
            "sidebar": ["sidebar", "side", "aside"],
        }
        
        all_elements = self._get_all_elements(tree)
        
        for section_type, identifiers in section_identifiers.items():
            for element in all_elements:
                # Check element id
                element_id = element.get("id", "").lower()
                if any(identifier in element_id for identifier in identifiers):
                    sections.append({
                        "type": section_type,
                        "element_id": element.get("id"),
                        "tag": element.get("tagName"),
                        "selector": element.get("css_selector"),
                        "reason": f"id contains '{next(i for i in identifiers if i in element_id)}'"
                    })
                    continue
                
                # Check element tag
                if element.get("tagName", "").lower() in identifiers:
                    sections.append({
                        "type": section_type,
                        "element_id": element.get("id"),
                        "tag": element.get("tagName"),
                        "selector": element.get("css_selector"),
                        "reason": f"tag is '{element.get('tagName', '').lower()}'"
                    })
                    continue
                
                # Check element class
                element_class = element.get("attributes", {}).get("class", "").lower()
                if any(identifier in element_class for identifier in identifiers):
                    sections.append({
                        "type": section_type,
                        "element_id": element.get("id"),
                        "tag": element.get("tagName"),
                        "selector": element.get("css_selector"),
                        "reason": f"class contains '{next(i for i in identifiers if i in element_class)}'"
                    })
                    continue
                
                # Check accessibility role
                element_role = element.get("accessibility", {}).get("role", "").lower()
                if element_role in identifiers:
                    sections.append({
                        "type": section_type,
                        "element_id": element.get("id"),
                        "tag": element.get("tagName"),
                        "selector": element.get("css_selector"),
                        "reason": f"role is '{element_role}'"
                    })
        
        return sections
    
    def _analyze_forms(self, forms: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Analyze forms in the DOM tree.
        
        Args:
            forms: List of form elements
            
        Returns:
            List of form analyses
        """
        form_analyses = []
        
        for form in forms:
            inputs = []
            buttons = []
            
            # Find inputs and buttons in the form
            if "children" in form:
                self._find_form_controls_recursive(form, inputs, buttons)
            
            form_analysis = {
                "id": form.get("id"),
                "selector": form.get("css_selector"),
                "input_count": len(inputs),
                "button_count": len(buttons),
                "inputs": [
                    {
                        "type": input_el.get("attributes", {}).get("type", "text"),
                        "name": input_el.get("attributes", {}).get("name"),
                        "id": input_el.get("id"),
                        "placeholder": input_el.get("attributes", {}).get("placeholder"),
                        "required": "required" in input_el.get("attributes", {})
                    }
                    for input_el in inputs
                ],
                "submission": next((
                    {
                        "type": "button",
                        "id": button.get("id"),
                        "text": button.get("textContent")
                    }
                    for button in buttons
                    if button.get("attributes", {}).get("type") == "submit" or
                    "submit" in button.get("textContent", "").lower()
                ), {"type": "unknown"})
            }
            
            form_analyses.append(form_analysis)
        
        return form_analyses
    
    def _find_form_controls_recursive(self, node: Dict[str, Any], inputs: List[Dict[str, Any]], buttons: List[Dict[str, Any]]) -> None:
        """Recursively find input and button elements in a form."""
        if not node:
            return
        
        if node.get("type") == "element":
            if node.get("tagName") == "input" or node.get("tagName") == "textarea" or node.get("tagName") == "select":
                inputs.append(node)
            elif node.get("tagName") == "button":
                buttons.append(node)
        
        if "children" in node:
            for child in node["children"]:
                self._find_form_controls_recursive(child, inputs, buttons)
    
    def find_clickable_path(self, dom_tree: Dict[str, Any], target_text: str) -> Optional[Dict[str, Any]]:
        """
        Find a clickable element that matches the target text.
        
        Args:
            dom_tree: The DOM tree structure
            target_text: The text to search for
            
        Returns:
            The matching clickable element, or None if not found
        """
        if not dom_tree or "tree" not in dom_tree:
            return None
        
        # Get all clickable elements from the interactive elements collection
        clickable_elements = self.get_interactive_elements(dom_tree).get("clickable", [])
        
        # First, try to find exact matches
        for element in clickable_elements:
            element_id = element.get("id")
            full_element = self.get_element_by_id(dom_tree, element_id) if element_id else None
            
            if full_element and "textContent" in full_element:
                if target_text.lower() == full_element["textContent"].lower():
                    return element
        
        # If no exact match, try partial matches
        for element in clickable_elements:
            element_id = element.get("id")
            full_element = self.get_element_by_id(dom_tree, element_id) if element_id else None
            
            if full_element and "textContent" in full_element:
                if target_text.lower() in full_element["textContent"].lower():
                    return element
        
        # If still no match, try to find elements with matching attributes
        for element in clickable_elements:
            element_id = element.get("id")
            full_element = self.get_element_by_id(dom_tree, element_id) if element_id else None
            
            if full_element:
                # Check various attributes that might contain text
                for attr_name in ["title", "alt", "aria-label", "placeholder"]:
                    attr_value = full_element.get("attributes", {}).get(attr_name, "")
                    if attr_value and target_text.lower() in attr_value.lower():
                        return element
        
        return None
    
    def get_navigation_path(self, dom_tree: Dict[str, Any], start_element: Dict[str, Any], end_element: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Find a path of navigable elements between two points in the DOM.
        
        Args:
            dom_tree: The DOM tree structure
            start_element: The starting element
            end_element: The target element
            
        Returns:
            List of elements forming a navigation path
        """
        if not dom_tree or "tree" not in dom_tree:
            return []
        
        # Get IDs of both elements
        start_id = start_element.get("id")
        end_id = end_element.get("id")
        
        if not start_id or not end_id:
            return []
        
        # Get full elements
        start_full = self.get_element_by_id(dom_tree, start_id)
        end_full = self.get_element_by_id(dom_tree, end_id)
        
        if not start_full or not end_full:
            return []
        
        # Build the DOM tree ancestry path for both elements
        start_path = self._build_ancestry_path(dom_tree["tree"], start_id)
        end_path = self._build_ancestry_path(dom_tree["tree"], end_id)
        
        if not start_path or not end_path:
            return []
        
        # Find the common ancestor
        common_ancestor_idx = 0
        min_len = min(len(start_path), len(end_path))
        
        while common_ancestor_idx < min_len and start_path[common_ancestor_idx]["id"] == end_path[common_ancestor_idx]["id"]:
            common_ancestor_idx += 1
        
        # Build the navigation path
        # Up from start to common ancestor, then down to end
        navigation_path = []
        
        # Go up from start to common ancestor (reversed)
        for i in range(len(start_path) - 1, common_ancestor_idx - 1, -1):
            navigation_path.append(start_path[i])
        
        # Go down from common ancestor to end
        for i in range(common_ancestor_idx, len(end_path)):
            navigation_path.append(end_path[i])
        
        return navigation_path
    
    def _build_ancestry_path(self, root: Dict[str, Any], target_id: str, current_path: Optional[List[Dict[str, Any]]] = None) -> Optional[List[Dict[str, Any]]]:
        """Build a path from the root to the target element."""
        if not root:
            return None
        
        # Initialize path
        if current_path is None:
            current_path = []
        
        # Add current node to path
        current_path.append(root)
        
        # If this is the target, return the path
        if root.get("id") == target_id:
            return current_path
        
        # If this node has children, search them
        if "children" in root:
            for child in root["children"]:
                if child.get("type") == "element":  # Only consider element nodes
                    child_path = self._build_ancestry_path(child, target_id, current_path.copy())
                    if child_path:
                        return child_path
        
        # If we get here, the target was not found in this subtree
        return None
    
    def find_input_field(self, dom_tree: Dict[str, Any], field_name: str) -> Optional[Dict[str, Any]]:
        """
        Find an input field by name, label, or placeholder.
        
        Args:
            dom_tree: The DOM tree structure
            field_name: The name of the field to find
            
        Returns:
            The matching input field, or None if not found
        """
        if not dom_tree or "tree" not in dom_tree:
            return None
        
        # Get all input elements
        input_elements = self.get_interactive_elements(dom_tree).get("inputs", [])
        
        # Try to match by name attribute
        for element in input_elements:
            element_id = element.get("id")
            full_element = self.get_element_by_id(dom_tree, element_id) if element_id else None
            
            if not full_element:
                continue
            
            attributes = full_element.get("attributes", {})
            name_attr = attributes.get("name", "")
            
            if name_attr.lower() == field_name.lower():
                return element
        
        # Try to match by placeholder attribute
        for element in input_elements:
            element_id = element.get("id")
            full_element = self.get_element_by_id(dom_tree, element_id) if element_id else None
            
            if not full_element:
                continue
            
            attributes = full_element.get("attributes", {})
            placeholder = attributes.get("placeholder", "")
            
            if placeholder.lower() == field_name.lower() or field_name.lower() in placeholder.lower():
                return element
        
        # Try to match by associated label
        # This is a simplified approach, a real implementation would need to follow label-for relationships
        all_elements = self._get_all_elements(dom_tree["tree"])
        for element in all_elements:
            if element.get("tagName") == "label":
                label_text = element.get("textContent", "")
                
                if label_text.lower() == field_name.lower() or field_name.lower() in label_text.lower():
                    # Get the for attribute
                    for_id = element.get("attributes", {}).get("for")
                    if for_id:
                        # Find the input element with this ID
                        input_el = self.get_element_by_id(dom_tree, for_id)
                        if input_el:
                            return {
                                "id": input_el.get("id"),
                                "tagName": input_el.get("tagName"),
                                "selector": input_el.get("css_selector"),
                                "xpath": input_el.get("xpath")
                            }
        
        # Try aria-label attributes as a last resort
        for element in input_elements:
            element_id = element.get("id")
            full_element = self.get_element_by_id(dom_tree, element_id) if element_id else None
            
            if not full_element:
                continue
            
            accessibility = full_element.get("accessibility", {})
            aria_label = accessibility.get("aria-label", "")
            
            if aria_label.lower() == field_name.lower() or field_name.lower() in aria_label.lower():
                return element
        
        return None
    
    def create_simplified_dom(self, dom_tree: Dict[str, Any], max_depth: int = 3) -> Dict[str, Any]:
        """
        Create a simplified representation of the DOM tree for use with LLMs.
        
        Args:
            dom_tree: The DOM tree structure
            max_depth: Maximum depth to include in the simplified tree
            
        Returns:
            Simplified DOM structure
        """
        if not dom_tree or "tree" not in dom_tree:
            return {"error": "Invalid DOM tree"}
        
        # Extract the basic page info
        simplified = {
            "url": dom_tree.get("url", ""),
            "title": dom_tree.get("title", ""),
            "timestamp": dom_tree.get("timestamp", ""),
            "tree": self._simplify_node(dom_tree["tree"], 0, max_depth),
            "interactive_summary": {}
        }
        
        # Add a summary of interactive elements
        interactive_elements = self.get_interactive_elements(dom_tree)
        interactive_summary = {
            "clickable_count": len(interactive_elements.get("clickable", [])),
            "input_count": len(interactive_elements.get("inputs", [])),
            "form_count": len(interactive_elements.get("forms", [])),
            "navigation_count": len(interactive_elements.get("navigational", [])),
            "top_clickable": [
                {
                    "tag": el.get("tagName", ""),
                    "text": self._get_element_text(dom_tree, el.get("id", "")),
                    "selector": el.get("selector", "")
                }
                for el in interactive_elements.get("clickable", [])[:5]  # Just include top 5
            ],
            "top_inputs": [
                {
                    "tag": el.get("tagName", ""),
                    "type": self._get_element_attribute(dom_tree, el.get("id", ""), "type"),
                    "name": self._get_element_attribute(dom_tree, el.get("id", ""), "name"),
                    "placeholder": self._get_element_attribute(dom_tree, el.get("id", ""), "placeholder"),
                    "selector": el.get("selector", "")
                }
                for el in interactive_elements.get("inputs", [])[:5]  # Just include top 5
            ]
        }
        
        simplified["interactive_summary"] = interactive_summary
        
        # Add page structure analysis
        page_sections = self._identify_page_sections(dom_tree["tree"])
        simplified["page_structure"] = {
            "sections": [
                {
                    "type": section["type"],
                    "selector": section["selector"]
                }
                for section in page_sections
            ]
        }
        
        return simplified
    
    def _simplify_node(self, node: Dict[str, Any], current_depth: int, max_depth: int) -> Optional[Dict[str, Any]]:
        """Recursively create a simplified version of a DOM node."""
        if not node or current_depth > max_depth:
            return None
        
        # Skip text nodes at deeper levels
        if node.get("type") == "text" and current_depth > 0:
            return {
                "type": "text",
                "content": node.get("content", "")[:50] + ("..." if len(node.get("content", "")) > 50 else "")
            }
        
        # For element nodes
        if node.get("type") == "element":
            # Create a simplified element representation
            simplified = {
                "type": "element",
                "tag": node.get("tagName", ""),
                "id": node.get("id", ""),
                "classes": node.get("attributes", {}).get("class", "").split() if "attributes" in node and "class" in node["attributes"] else [],
                "selector": node.get("css_selector", ""),
                "text": node.get("textContent", "")[:50] + ("..." if len(node.get("textContent", "")) > 50 else "")
            }
            
            # Add interactive info if present
            if node.get("interactive", False):
                simplified["interactive"] = True
                simplified["interactive_types"] = node.get("interactiveTypes", [])
            
            # Add children if within depth limit
            if "children" in node and current_depth < max_depth:
                children = []
                for child in node["children"]:
                    simplified_child = self._simplify_node(child, current_depth + 1, max_depth)
                    if simplified_child:
                        children.append(simplified_child)
                
                # Only add non-empty children array
                if children:
                    simplified["children"] = children
                elif node.get("textContent"):
                    # If no children but has text, include it
                    simplified["text"] = node.get("textContent", "")[:50] + ("..." if len(node.get("textContent", "")) > 50 else "")
            
            # Remove empty values
            simplified = {k: v for k, v in simplified.items() if v}
            
            return simplified
        
        return None
    
    def _get_element_text(self, dom_tree: Dict[str, Any], element_id: str) -> str:
        """Get text content of an element by ID."""
        element = self.get_element_by_id(dom_tree, element_id)
        if element:
            return element.get("textContent", "")
        return ""
    
    def _get_element_attribute(self, dom_tree: Dict[str, Any], element_id: str, attribute: str) -> str:
        """Get an attribute of an element by ID."""
        element = self.get_element_by_id(dom_tree, element_id)
        if element and "attributes" in element:
            return element["attributes"].get(attribute, "")
        return ""
    
    async def highlight_elements(self, selectors: List[str], duration_ms: int = 2000) -> Dict[str, Any]:
        """
        Highlight multiple elements in the browser.
        
        Args:
            selectors: List of CSS selectors to highlight
            duration_ms: Duration of the highlighting in milliseconds
            
        Returns:
            Dictionary with results for each selector
        """
        results = {}
        
        for selector in selectors:
            try:
                success = await self.browser_executor.highlight_element(
                    selector,
                    highlight_style={
                        "outline": "2px solid red",
                        "background-color": "rgba(255, 0, 0, 0.2)",
                        "transition": "outline 0.1s, background-color 0.1s"
                    },
                    duration_ms=duration_ms
                )
                results[selector] = success
            except Exception as e:
                logger.error(f"Error highlighting element {selector}: {str(e)}")
                results[selector] = False
        
        return results
    
    @lru_cache(maxsize=128)
    def get_element_xpath(self, dom_tree: Dict[str, Any], selector: str) -> Optional[str]:
        """
        Get the XPath for an element identified by a CSS selector.
        
        Args:
            dom_tree: The DOM tree structure
            selector: CSS selector to find the element
            
        Returns:
            XPath string or None if element not found
        """
        elements = self.find_elements_by_selector(dom_tree, selector)
        if not elements:
            return None
        
        return elements[0].get("xpath")
    
    @lru_cache(maxsize=128)
    def get_element_selector(self, dom_tree: Dict[str, Any], xpath: str) -> Optional[str]:
        """
        Get the CSS selector for an element identified by XPath.
        
        Args:
            dom_tree: The DOM tree structure
            xpath: XPath to find the element
            
        Returns:
            CSS selector string or None if element not found
        """
        all_elements = self._get_all_elements(dom_tree["tree"])
        for element in all_elements:
            if element.get("xpath") == xpath:
                return element.get("css_selector")
        
        return None
    
    def classify_page_type(self, dom_tree: Dict[str, Any]) -> Dict[str, float]:
        """
        Attempt to classify the type of page based on its structure and content.
        
        Args:
            dom_tree: The DOM tree structure
            
        Returns:
            Dictionary with page type classifications and confidence scores
        """
        if not dom_tree or "tree" not in dom_tree:
            return {"unknown": 1.0}
        
        # Define features for different page types
        page_types = {
            "login": ["login", "sign in", "signin", "username", "password", "email", "forgot password"],
            "product": ["product", "price", "buy", "add to cart", "purchase", "shipping"],
            "article": ["article", "blog", "news", "author", "published", "date", "comments"],
            "search": ["search", "results", "query", "filter", "sort", "no results"],
            "form": ["form", "submit", "input", "required", "select", "radio", "checkbox"],
            "landing": ["hero", "cta", "sign up", "free trial", "learn more", "get started"],
            "listing": ["list", "grid", "pagination", "next", "previous", "showing"]
        }
        
        # Extract page text
        page_text = self._extract_all_text(dom_tree["tree"]).lower()
        page_html = json.dumps(dom_tree).lower()  # Include structure in analysis
        
        # Count occurrences of each feature
        scores = {}
        for page_type, features in page_types.items():
            score = 0
            for feature in features:
                text_count = page_text.count(feature.lower())
                html_count = page_html.count(feature.lower())
                score += text_count * 2 + html_count
            
            scores[page_type] = score
        
        # Normalize scores to add up to 1.0
        total_score = sum(scores.values())
        if total_score == 0:
            return {"unknown": 1.0}
        
        normalized_scores = {
            page_type: score / total_score
            for page_type, score in scores.items()
            if score > 0  # Only include non-zero scores
        }
        
        # If no scores, return unknown
        if not normalized_scores:
            return {"unknown": 1.0}
        
        return normalized_scores
    
    def _extract_all_text(self, node: Dict[str, Any]) -> str:
        """Extract all text from a DOM node recursively."""
        if not node:
            return ""
        
        if node.get("type") == "text":
            return node.get("content", "")
        
        if node.get("type") == "element":
            text = node.get("textContent", "")
            
            if "children" in node:
                for child in node["children"]:
                    text += " " + self._extract_all_text(child)
            
            return text
        
        return ""

# Create a singleton instance
dom_processing_service = DOMProcessingService(browser_executor) 