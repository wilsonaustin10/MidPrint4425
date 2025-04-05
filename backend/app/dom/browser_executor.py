"""
Browser script executor for DOM processing.
This module handles the execution of JavaScript in the browser context.
"""
import os
import json
import logging
from typing import Dict, Any, Optional
from pathlib import Path

logger = logging.getLogger(__name__)

class BrowserExecutor:
    """
    Executes JavaScript in the browser context and returns the results.
    """
    
    def __init__(self, browser_manager):
        """
        Initialize the browser executor.
        
        Args:
            browser_manager: The browser manager instance
        """
        self.browser = browser_manager
        self._script_cache = {}
        
        # Get the path to the DOM extraction script
        self.script_dir = Path(os.path.dirname(os.path.abspath(__file__)))
        self.dom_extraction_script_path = self.script_dir / "buildDomTree.js"
    
    async def load_script(self, script_path: Path) -> str:
        """
        Load a JavaScript script from file, with caching for performance.
        
        Args:
            script_path: Path to the JavaScript file
            
        Returns:
            The script content as a string
        """
        if script_path in self._script_cache:
            return self._script_cache[script_path]
        
        try:
            with open(script_path, "r", encoding="utf-8") as file:
                script = file.read()
            
            self._script_cache[script_path] = script
            return script
        except Exception as e:
            logger.error(f"Error loading script {script_path}: {str(e)}")
            raise
    
    async def execute_script(self, script: str, args: Optional[list] = None) -> Any:
        """
        Execute JavaScript in the browser context.
        
        Args:
            script: JavaScript to execute
            args: Optional arguments to pass to the script
            
        Returns:
            The result of the script execution
        """
        if not self.browser.is_initialized:
            logger.error("Browser is not initialized, cannot execute script")
            raise RuntimeError("Browser is not initialized")
        
        try:
            if args is None:
                args = []
            
            result = await self.browser.page.evaluate(script, *args)
            return result
        except Exception as e:
            logger.error(f"Error executing script: {str(e)}")
            raise
    
    async def extract_dom_tree(self, options: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Extract the DOM tree of the current page using the DOM extraction script.
        
        Args:
            options: Optional configuration for the DOM extraction
            
        Returns:
            The extracted DOM tree structure
        """
        if options is None:
            options = {}
        
        try:
            # Load the DOM extraction script
            script = await self.load_script(self.dom_extraction_script_path)
            
            # Create a script that first loads the extraction function, then calls it with options
            execution_script = f"""
            {script}
            return extractDomTree({json.dumps(options)});
            """
            
            # Execute the script in the browser context
            result = await self.execute_script(execution_script)
            
            return result
        except Exception as e:
            logger.error(f"Error extracting DOM tree: {str(e)}")
            raise
    
    async def highlight_element(self, selector: str, highlight_style: Optional[Dict[str, str]] = None, 
                               duration_ms: int = 2000) -> bool:
        """
        Temporarily highlight an element in the browser for visualization.
        
        Args:
            selector: CSS selector for the element to highlight
            highlight_style: Optional styling for the highlight
            duration_ms: Duration to show the highlight in milliseconds
            
        Returns:
            True if successful, False otherwise
        """
        if highlight_style is None:
            highlight_style = {
                "outline": "2px solid red",
                "background-color": "rgba(255, 0, 0, 0.2)",
                "transition": "outline 0.1s, background-color 0.1s"
            }
        
        style_str = json.dumps(highlight_style)
        
        script = f"""
        (selector, style, duration) => {{
            const element = document.querySelector(selector);
            if (!element) return false;
            
            // Store original styles
            const originalStyles = {{}};
            for (const prop in style) {{
                originalStyles[prop] = element.style[prop];
            }}
            
            // Apply highlight styles
            Object.assign(element.style, style);
            
            // Restore original styles after duration
            setTimeout(() => {{
                for (const prop in originalStyles) {{
                    element.style[prop] = originalStyles[prop];
                }}
            }}, duration);
            
            return true;
        }}
        """
        
        return await self.execute_script(script, [selector, highlight_style, duration_ms])
    
    async def get_element_by_xpath(self, xpath: str) -> Dict[str, Any]:
        """
        Get an element by XPath and return its basic properties.
        
        Args:
            xpath: XPath selector for the element
            
        Returns:
            Object with element properties, or null if element not found
        """
        script = """
        (xpath) => {
            const element = document.evaluate(
                xpath, 
                document, 
                null, 
                XPathResult.FIRST_ORDERED_NODE_TYPE, 
                null
            ).singleNodeValue;
            
            if (!element) return null;
            
            // Get bounding rectangle
            const rect = element.getBoundingClientRect();
            
            // Build selector
            let selector = element.tagName.toLowerCase();
            if (element.id) selector += `#${element.id}`;
            
            // Get class info
            const classList = Array.from(element.classList || []);
            
            // Get text content
            const textContent = element.textContent ? element.textContent.trim() : '';
            
            return {
                tagName: element.tagName.toLowerCase(),
                id: element.id || null,
                classes: classList,
                selector: selector,
                position: {
                    x: Math.round(rect.left + window.scrollX),
                    y: Math.round(rect.top + window.scrollY),
                    width: Math.round(rect.width),
                    height: Math.round(rect.height)
                },
                textContent: textContent.length > 100 ? textContent.substring(0, 100) + '...' : textContent,
                attributes: Array.from(element.attributes || []).reduce((obj, attr) => {
                    obj[attr.name] = attr.value;
                    return obj;
                }, {})
            };
        }
        """
        
        return await self.execute_script(script, [xpath])
    
    async def get_element_by_selector(self, selector: str) -> Dict[str, Any]:
        """
        Get an element by CSS selector and return its basic properties.
        
        Args:
            selector: CSS selector for the element
            
        Returns:
            Object with element properties, or null if element not found
        """
        script = """
        (selector) => {
            const element = document.querySelector(selector);
            if (!element) return null;
            
            // Get bounding rectangle
            const rect = element.getBoundingClientRect();
            
            // Get class info
            const classList = Array.from(element.classList || []);
            
            // Get text content
            const textContent = element.textContent ? element.textContent.trim() : '';
            
            return {
                tagName: element.tagName.toLowerCase(),
                id: element.id || null,
                classes: classList,
                xpath: getElementXPath(element),
                position: {
                    x: Math.round(rect.left + window.scrollX),
                    y: Math.round(rect.top + window.scrollY),
                    width: Math.round(rect.width),
                    height: Math.round(rect.height)
                },
                textContent: textContent.length > 100 ? textContent.substring(0, 100) + '...' : textContent,
                attributes: Array.from(element.attributes || []).reduce((obj, attr) => {
                    obj[attr.name] = attr.value;
                    return obj;
                }, {})
            };
            
            // Helper function to get XPath
            function getElementXPath(element) {
                if (!element) return null;
                
                if (element.id) {
                    return `//*[@id="${element.id}"]`;
                }
                
                let path = '';
                let currentElement = element;
                
                while (currentElement && currentElement.nodeType === Node.ELEMENT_NODE) {
                    let siblings = Array.from(currentElement.parentNode.children).filter(
                        child => child.tagName === currentElement.tagName
                    );
                    
                    let position = siblings.indexOf(currentElement) + 1;
                    
                    let tagName = currentElement.tagName.toLowerCase();
                    let pathSegment = siblings.length > 1 ? 
                                     `${tagName}[${position}]` : 
                                     tagName;
                    
                    path = path === '' ? pathSegment : `${pathSegment}/${path}`;
                    currentElement = currentElement.parentNode;
                }
                
                return `/${path}`;
            }
        }
        """
        
        return await self.execute_script(script, [selector])
    
    async def find_elements_by_text(self, text: str, exact_match: bool = False) -> list:
        """
        Find elements that contain specific text.
        
        Args:
            text: Text to search for
            exact_match: Whether to require exact text match (default: False)
            
        Returns:
            List of elements containing the text
        """
        script = """
        (text, exactMatch) => {
            const results = [];
            
            // Helper function to get basic element info
            function getElementInfo(element) {
                const rect = element.getBoundingClientRect();
                const tagName = element.tagName.toLowerCase();
                
                let selector = tagName;
                if (element.id) selector += `#${element.id}`;
                else if (element.classList && element.classList.length) {
                    selector += '.' + Array.from(element.classList).join('.');
                }
                
                return {
                    tagName,
                    id: element.id || null,
                    classes: Array.from(element.classList || []),
                    selector,
                    text: element.textContent.trim(),
                    position: {
                        x: Math.round(rect.left + window.scrollX),
                        y: Math.round(rect.top + window.scrollY),
                        width: Math.round(rect.width),
                        height: Math.round(rect.height)
                    }
                };
            }
            
            // Create a tree walker to efficiently search all text nodes
            const walker = document.createTreeWalker(
                document.body,
                NodeFilter.SHOW_TEXT,
                null,
                false
            );
            
            const searchText = text.toLowerCase();
            
            // Process all text nodes
            let node;
            while (node = walker.nextNode()) {
                const nodeText = node.nodeValue.trim();
                
                // Skip empty nodes
                if (!nodeText) continue;
                
                const matches = exactMatch 
                    ? nodeText === text
                    : nodeText.toLowerCase().includes(searchText);
                
                if (matches) {
                    // Get closest element
                    const element = node.parentElement;
                    
                    // Skip if already found (avoid duplicates)
                    if (results.some(r => r.element === element)) {
                        continue;
                    }
                    
                    results.push({
                        element,
                        ...getElementInfo(element),
                        matchedText: nodeText
                    });
                }
            }
            
            // Return only the info, not the actual elements
            return results.map(({ element, ...info }) => info);
        }
        """
        
        return await self.execute_script(script, [text, exact_match]) 