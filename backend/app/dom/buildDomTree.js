/**
 * DOM Tree extraction and analysis script.
 * Runs in the browser context to extract the DOM structure and identify interactive elements.
 * Returns a structured representation of the DOM with element metadata.
 */

/**
 * Main function to extract DOM tree and interactive elements
 * @param {Object} options - Configuration options
 * @param {boolean} options.includeText - Whether to include text content (default: true)
 * @param {boolean} options.includeAttributes - Whether to include element attributes (default: true)
 * @param {boolean} options.includeStyles - Whether to include computed styles (default: false)
 * @param {boolean} options.includePosition - Whether to include element positions (default: true)
 * @param {boolean} options.includeVisibility - Whether to check element visibility (default: true)
 * @param {boolean} options.includeAccessibility - Whether to include accessibility properties (default: true)
 * @param {string[]} options.attributeFilter - Specific attributes to include (if empty, include all)
 * @param {number} options.maxDepth - Maximum depth to traverse (default: 25)
 * @param {number} options.maxTextLength - Maximum text content length (default: 150)
 * @returns {Object} Structured DOM tree with element metadata
 */
function extractDomTree(options = {}) {
    // Default options
    const config = {
        includeText: options.includeText !== undefined ? options.includeText : true,
        includeAttributes: options.includeAttributes !== undefined ? options.includeAttributes : true,
        includeStyles: options.includeStyles !== undefined ? options.includeStyles : false,
        includePosition: options.includePosition !== undefined ? options.includePosition : true,
        includeVisibility: options.includeVisibility !== undefined ? options.includeVisibility : true,
        includeAccessibility: options.includeAccessibility !== undefined ? options.includeAccessibility : true,
        attributeFilter: options.attributeFilter || [],
        maxDepth: options.maxDepth || 25,
        maxTextLength: options.maxTextLength || 150
    };

    // Track all interactive elements for easy access
    const interactiveElements = {
        clickable: [],
        inputs: [],
        forms: [],
        navigational: []
    };

    // Element indexing to support unique identification
    let elementIndex = 0;
    const elementMap = new Map();

    /**
     * Check if an element is visible
     * @param {Element} element - DOM element to check
     * @returns {boolean} Whether the element is visible
     */
    function isElementVisible(element) {
        if (!config.includeVisibility) return true;
        
        if (!element || !element.getBoundingClientRect) return false;

        const style = window.getComputedStyle(element);
        if (style.display === 'none' || style.visibility === 'hidden' || style.opacity === '0') {
            return false;
        }

        const rect = element.getBoundingClientRect();
        const hasSize = rect.width > 0 && rect.height > 0;
        return hasSize;
    }

    /**
     * Check if an element is interactive
     * @param {Element} element - DOM element to check
     * @returns {Object} Object with interactive type and reason
     */
    function getInteractiveInfo(element) {
        // Not a real element, skip
        if (!element || element.nodeType !== Node.ELEMENT_NODE) {
            return { interactive: false };
        }

        const tagName = element.tagName.toLowerCase();
        const interactiveTypes = [];
        const clickable = isClickable(element);
        const isInput = isInputElement(element);
        const isFormElement = isPartOfForm(element);
        const isNavigation = isNavigational(element);

        if (clickable) interactiveTypes.push('clickable');
        if (isInput) interactiveTypes.push('input');
        if (isFormElement) interactiveTypes.push('form');
        if (isNavigation) interactiveTypes.push('navigation');

        return {
            interactive: interactiveTypes.length > 0,
            interactiveTypes: interactiveTypes,
            reasons: getReasonsForInteractive(element, clickable, isInput, isFormElement, isNavigation),
            role: element.getAttribute('role')
        };
    }

    /**
     * Check if an element is clickable
     * @param {Element} element - DOM element to check
     * @returns {boolean} Whether the element is clickable
     */
    function isClickable(element) {
        const tagName = element.tagName.toLowerCase();
        
        // Common clickable elements
        const clickableTags = ['a', 'button', 'input', 'select', 'textarea', 'summary', 'details'];
        if (clickableTags.includes(tagName)) {
            return true;
        }

        // Check for event listeners (limited to inline handlers)
        if (element.hasAttribute('onclick') || element.hasAttribute('onmousedown')) {
            return true;
        }

        // Check for roles
        const clickableRoles = ['button', 'link', 'checkbox', 'menuitem', 'tab', 'switch', 'option'];
        if (element.hasAttribute('role') && clickableRoles.includes(element.getAttribute('role'))) {
            return true;
        }

        // Check for other common patterns
        if (element.classList.contains('btn') || 
            element.classList.contains('button') ||
            element.id.includes('btn') || 
            element.id.includes('button')) {
            return true;
        }

        // Check cursor style for pointer (not perfect but helps identify clickable elements)
        const computedStyle = window.getComputedStyle(element);
        if (computedStyle && computedStyle.cursor === 'pointer') {
            return true;
        }

        return false;
    }

    /**
     * Check if an element is an input element
     * @param {Element} element - DOM element to check
     * @returns {boolean} Whether the element is an input element
     */
    function isInputElement(element) {
        const tagName = element.tagName.toLowerCase();
        
        // Form input elements
        const inputTags = ['input', 'textarea', 'select', 'option'];
        if (inputTags.includes(tagName)) {
            return true;
        }

        // Elements with editable content
        if (element.hasAttribute('contenteditable') && element.getAttribute('contenteditable') !== 'false') {
            return true;
        }

        // Check for input-related roles
        const inputRoles = ['textbox', 'searchbox', 'spinbutton', 'slider', 'checkbox', 'radio', 'combobox', 'option'];
        if (element.hasAttribute('role') && inputRoles.includes(element.getAttribute('role'))) {
            return true;
        }

        return false;
    }

    /**
     * Check if an element is part of a form
     * @param {Element} element - DOM element to check
     * @returns {boolean} Whether the element is part of a form
     */
    function isPartOfForm(element) {
        const tagName = element.tagName.toLowerCase();
        
        // Form elements
        if (tagName === 'form') {
            return true;
        }

        // Form-related elements
        const formTags = ['fieldset', 'legend', 'label'];
        if (formTags.includes(tagName)) {
            return true;
        }

        // Check if it's a child of a form
        const closestForm = element.closest('form');
        return !!closestForm;
    }

    /**
     * Check if an element is a navigational element
     * @param {Element} element - DOM element to check
     * @returns {boolean} Whether the element is a navigational element
     */
    function isNavigational(element) {
        const tagName = element.tagName.toLowerCase();
        
        // Navigation elements
        const navTags = ['a', 'nav', 'menu'];
        if (navTags.includes(tagName)) {
            return true;
        }

        // Check for navigation roles
        const navRoles = ['link', 'menu', 'menubar', 'menuitem', 'tab', 'tablist', 'tree', 'treeitem'];
        if (element.hasAttribute('role') && navRoles.includes(element.getAttribute('role'))) {
            return true;
        }

        // Check for common navigation classes
        const navClasses = ['nav', 'navbar', 'navigation', 'menu', 'sidebar', 'breadcrumb'];
        for (const className of navClasses) {
            if (element.classList.contains(className)) {
                return true;
            }
        }

        return false;
    }

    /**
     * Get reasons why an element is considered interactive
     * @param {Element} element - DOM element to check
     * @param {boolean} clickable - Whether the element is clickable
     * @param {boolean} isInput - Whether the element is an input element
     * @param {boolean} isFormElement - Whether the element is part of a form
     * @param {boolean} isNavigation - Whether the element is a navigational element
     * @returns {Object} Object with reasons for each interactive type
     */
    function getReasonsForInteractive(element, clickable, isInput, isFormElement, isNavigation) {
        const reasons = {};
        const tagName = element.tagName.toLowerCase();

        if (clickable) {
            const clickReasons = [];
            if (['a', 'button'].includes(tagName)) clickReasons.push(`tag: ${tagName}`);
            if (element.hasAttribute('onclick')) clickReasons.push('has onclick handler');
            if (element.hasAttribute('role') && ['button', 'link'].includes(element.getAttribute('role'))) {
                clickReasons.push(`role: ${element.getAttribute('role')}`);
            }
            if (window.getComputedStyle(element).cursor === 'pointer') clickReasons.push('cursor: pointer');
            reasons.clickable = clickReasons;
        }

        if (isInput) {
            const inputReasons = [];
            if (['input', 'textarea', 'select'].includes(tagName)) inputReasons.push(`tag: ${tagName}`);
            if (element.hasAttribute('contenteditable')) inputReasons.push('contenteditable');
            if (element.hasAttribute('role') && ['textbox', 'checkbox'].includes(element.getAttribute('role'))) {
                inputReasons.push(`role: ${element.getAttribute('role')}`);
            }
            if (tagName === 'input' && element.hasAttribute('type')) {
                inputReasons.push(`input type: ${element.getAttribute('type')}`);
            }
            reasons.input = inputReasons;
        }

        if (isFormElement) {
            const formReasons = [];
            if (tagName === 'form') formReasons.push('tag: form');
            if (['fieldset', 'legend', 'label'].includes(tagName)) formReasons.push(`tag: ${tagName}`);
            if (element.closest('form')) formReasons.push('inside form element');
            reasons.form = formReasons;
        }

        if (isNavigation) {
            const navReasons = [];
            if (['a', 'nav', 'menu'].includes(tagName)) navReasons.push(`tag: ${tagName}`);
            if (element.hasAttribute('role') && ['link', 'menu'].includes(element.getAttribute('role'))) {
                navReasons.push(`role: ${element.getAttribute('role')}`);
            }
            for (const className of element.classList) {
                if (['nav', 'navbar', 'menu'].includes(className)) {
                    navReasons.push(`class: ${className}`);
                    break;
                }
            }
            reasons.navigation = navReasons;
        }

        return reasons;
    }

    /**
     * Get element attributes
     * @param {Element} element - DOM element
     * @returns {Object} Object with element attributes
     */
    function getElementAttributes(element) {
        if (!config.includeAttributes || !element.hasAttributes || !element.hasAttributes()) {
            return {};
        }

        const attributes = {};
        const attrs = element.attributes;

        for (let i = 0; i < attrs.length; i++) {
            const attr = attrs[i];
            // Filter attributes if attributeFilter is specified
            if (config.attributeFilter.length === 0 || config.attributeFilter.includes(attr.name)) {
                attributes[attr.name] = attr.value;
            }
        }

        return attributes;
    }

    /**
     * Get element position information
     * @param {Element} element - DOM element
     * @returns {Object|null} Object with element position or null if not available
     */
    function getElementPosition(element) {
        if (!config.includePosition || !element.getBoundingClientRect) {
            return null;
        }

        try {
            const rect = element.getBoundingClientRect();
            return {
                x: Math.round(rect.left + window.scrollX),
                y: Math.round(rect.top + window.scrollY),
                width: Math.round(rect.width),
                height: Math.round(rect.height),
                viewportX: Math.round(rect.left),
                viewportY: Math.round(rect.top)
            };
        } catch (e) {
            return null;
        }
    }

    /**
     * Get accessibility properties for the element
     * @param {Element} element - DOM element
     * @returns {Object} Object with accessibility properties
     */
    function getAccessibilityInfo(element) {
        if (!config.includeAccessibility) {
            return {};
        }

        const accessibility = {};
        
        // Check for common accessibility attributes
        ['aria-label', 'aria-labelledby', 'aria-describedby', 'aria-hidden', 'aria-expanded', 'aria-haspopup', 'role'].forEach(attr => {
            if (element.hasAttribute(attr)) {
                accessibility[attr] = element.getAttribute(attr);
            }
        });

        // Check for tab index
        if (element.hasAttribute('tabindex')) {
            accessibility.tabindex = element.getAttribute('tabindex');
        }

        return Object.keys(accessibility).length > 0 ? accessibility : null;
    }

    /**
     * Generate a CSS selector for an element
     * @param {Element} element - DOM element
     * @returns {String} CSS selector for the element
     */
    function generateSelector(element) {
        if (!element || element.nodeType !== Node.ELEMENT_NODE) {
            return null;
        }

        let selector = element.tagName.toLowerCase();

        // Add ID if it exists
        if (element.id) {
            return `${selector}#${element.id}`;
        }

        // Add classes
        if (element.classList && element.classList.length > 0) {
            selector += Array.from(element.classList)
                .map(c => `.${c}`)
                .join('');
        }

        // Add more specific attributes for certain element types
        const specialAttributes = ['type', 'name', 'placeholder', 'value'];
        for (const attr of specialAttributes) {
            if (element.hasAttribute(attr)) {
                const value = element.getAttribute(attr);
                if (value && typeof value === 'string' && value.length < 30) {
                    selector += `[${attr}="${value}"]`;
                    break; // Only use one special attribute to avoid overly complex selectors
                }
            }
        }

        return selector;
    }

    /**
     * Generate an XPath selector for an element
     * @param {Element} element - DOM element
     * @returns {String} XPath selector for the element
     */
    function generateXPath(element) {
        if (!element) return null;
        
        // If element has an ID, use that for a simple, robust XPath
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

    /**
     * Process a DOM node and its children recursively
     * @param {Node} node - DOM node to process
     * @param {number} depth - Current depth in the tree
     * @returns {Object|null} Node representation or null if node should be skipped
     */
    function processNode(node, depth = 0) {
        // Skip if we've reached max depth
        if (depth > config.maxDepth) {
            return null;
        }

        // Handle text nodes
        if (node.nodeType === Node.TEXT_NODE) {
            const text = node.textContent.trim();
            if (text && config.includeText) {
                return {
                    type: 'text',
                    content: text.length > config.maxTextLength ? 
                        text.substring(0, config.maxTextLength) + '...' : 
                        text
                };
            }
            return null;
        }

        // Skip non-element nodes (comments, etc.)
        if (node.nodeType !== Node.ELEMENT_NODE) {
            return null;
        }

        // Check if element is visible
        const visible = isElementVisible(node);
        if (!visible && config.includeVisibility) {
            return null;
        }

        const tagName = node.tagName.toLowerCase();
        
        // Skip certain elements that are unlikely to be important for interaction
        const skipTags = ['script', 'style', 'noscript', 'svg', 'path'];
        if (skipTags.includes(tagName)) {
            return null;
        }

        // Get the element ID or create one if it doesn't exist
        let id = node.id;
        if (!id) {
            id = `el-${elementIndex++}`;
        }

        // Store element in map for later reference
        elementMap.set(id, node);

        // Create element representation
        const elementData = {
            id,
            type: 'element',
            tagName,
            attributes: getElementAttributes(node),
            position: getElementPosition(node),
            css_selector: generateSelector(node),
            xpath: generateXPath(node),
            accessibility: getAccessibilityInfo(node),
            children: []
        };

        // Get text content
        if (config.includeText && node.childNodes.length === 1 && node.firstChild.nodeType === Node.TEXT_NODE) {
            const text = node.textContent.trim();
            if (text) {
                elementData.textContent = text.length > config.maxTextLength ? 
                    text.substring(0, config.maxTextLength) + '...' : 
                    text;
            }
        }

        // Check if element is interactive
        const interactiveInfo = getInteractiveInfo(node);
        if (interactiveInfo.interactive) {
            elementData.interactive = true;
            elementData.interactiveTypes = interactiveInfo.interactiveTypes;
            elementData.interactiveReasons = interactiveInfo.reasons;
            
            // Add to interactive elements collection
            interactiveInfo.interactiveTypes.forEach(type => {
                if (interactiveElements[type]) {
                    interactiveElements[type].push({
                        id,
                        tagName,
                        selector: elementData.css_selector,
                        xpath: elementData.xpath,
                        interactiveReasons: interactiveInfo.reasons[type] || []
                    });
                }
            });
        }

        // Process child nodes
        if (node.childNodes && node.childNodes.length > 0) {
            for (let i = 0; i < node.childNodes.length; i++) {
                const childNode = processNode(node.childNodes[i], depth + 1);
                if (childNode) {
                    elementData.children.push(childNode);
                }
            }
        }

        return elementData;
    }

    // Start processing from the document body
    const domTree = processNode(document.body);

    return {
        url: window.location.href,
        title: document.title,
        timestamp: new Date().toISOString(),
        tree: domTree,
        interactiveElements
    };
}

// Export the function
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { extractDomTree };
} else {
    // When running in browser context
    window.extractDomTree = extractDomTree;
} 