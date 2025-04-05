"""
API routes for DOM processing functionality.
"""
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from app.dom.service import dom_processing_service

router = APIRouter()

class DOMExtractionOptions(BaseModel):
    """Options for DOM tree extraction."""
    max_depth: Optional[int] = Field(25, description="Maximum depth of the DOM tree to extract")
    include_text: Optional[bool] = Field(True, description="Include text content of elements")
    include_attributes: Optional[bool] = Field(True, description="Include HTML attributes of elements")
    include_position: Optional[bool] = Field(True, description="Include element positions")
    include_visibility: Optional[bool] = Field(True, description="Include visibility information")
    include_accessibility: Optional[bool] = Field(True, description="Include accessibility information")
    max_text_length: Optional[int] = Field(150, description="Maximum length of text content to include")

    def to_dict(self) -> Dict[str, Any]:
        """Convert to camelCase dictionary for browser script."""
        return {
            "maxDepth": self.max_depth,
            "includeText": self.include_text,
            "includeAttributes": self.include_attributes,
            "includePosition": self.include_position,
            "includeVisibility": self.include_visibility,
            "includeAccessibility": self.include_accessibility,
            "maxTextLength": self.max_text_length
        }

class ElementHighlightRequest(BaseModel):
    """Request to highlight elements on the page."""
    selectors: List[str] = Field(..., description="CSS selectors of elements to highlight")
    duration_ms: Optional[int] = Field(2000, description="Duration of highlighting in milliseconds")

class ElementFindRequest(BaseModel):
    """Request to find elements by text."""
    text: str = Field(..., description="Text to search for")
    exact_match: Optional[bool] = Field(False, description="Whether to require exact text match")

class SimplifiedDOMRequest(BaseModel):
    """Request to create a simplified DOM representation."""
    max_depth: Optional[int] = Field(3, description="Maximum depth to include in simplified tree")

@router.post("/extract", response_model=Dict[str, Any])
async def extract_dom(options: Optional[DOMExtractionOptions] = None):
    """
    Extract the DOM tree from the current page.
    """
    try:
        options_dict = options.to_dict() if options else None
        result = await dom_processing_service.extract_dom(options_dict)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to extract DOM tree: {str(e)}")

@router.get("/interactive-elements", response_model=Dict[str, List[Dict[str, Any]]])
async def get_interactive_elements():
    """
    Get all interactive elements from the current page.
    """
    try:
        # First extract the DOM
        dom_tree = await dom_processing_service.extract_dom()
        
        # Then get the interactive elements
        interactive_elements = dom_processing_service.get_interactive_elements(dom_tree)
        return interactive_elements
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get interactive elements: {str(e)}")

@router.post("/analyze", response_model=Dict[str, Any])
async def analyze_page():
    """
    Analyze the structure of the current page.
    """
    try:
        # First extract the DOM
        dom_tree = await dom_processing_service.extract_dom()
        
        # Then analyze the page structure
        analysis = dom_processing_service.analyze_page_structure(dom_tree)
        return analysis
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to analyze page: {str(e)}")

@router.post("/highlight", response_model=Dict[str, bool])
async def highlight_elements(request: ElementHighlightRequest):
    """
    Highlight elements on the page by CSS selector.
    """
    try:
        result = await dom_processing_service.highlight_elements(
            request.selectors, 
            request.duration_ms
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to highlight elements: {str(e)}")

@router.post("/find-clickable", response_model=Optional[Dict[str, Any]])
async def find_clickable_element(request: ElementFindRequest):
    """
    Find a clickable element by its text content.
    """
    try:
        # First extract the DOM
        dom_tree = await dom_processing_service.extract_dom()
        
        # Then find the element
        element = dom_processing_service.find_clickable_path(dom_tree, request.text)
        if element is None:
            return None
        return element
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to find clickable element: {str(e)}")

@router.post("/find-input", response_model=Optional[Dict[str, Any]])
async def find_input_field(request: ElementFindRequest):
    """
    Find an input field by its name, label, or placeholder.
    """
    try:
        # First extract the DOM
        dom_tree = await dom_processing_service.extract_dom()
        
        # Then find the input field
        element = dom_processing_service.find_input_field(dom_tree, request.text)
        if element is None:
            return None
        return element
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to find input field: {str(e)}")

@router.post("/simplified", response_model=Dict[str, Any])
async def get_simplified_dom(request: SimplifiedDOMRequest):
    """
    Get a simplified representation of the DOM tree.
    """
    try:
        # First extract the DOM
        dom_tree = await dom_processing_service.extract_dom()
        
        # Then create the simplified representation
        simplified = dom_processing_service.create_simplified_dom(dom_tree, request.max_depth)
        return simplified
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create simplified DOM: {str(e)}")

@router.get("/page-type", response_model=Dict[str, float])
async def get_page_type():
    """
    Classify the type of the current page.
    """
    try:
        # First extract the DOM
        dom_tree = await dom_processing_service.extract_dom()
        
        # Then classify the page type
        page_type = dom_processing_service.classify_page_type(dom_tree)
        return page_type
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to classify page type: {str(e)}")

@router.get("/element-count", response_model=Dict[str, int])
async def count_elements():
    """
    Count the number of each element type on the page.
    """
    try:
        # First extract the DOM
        dom_tree = await dom_processing_service.extract_dom()
        
        # Then count the elements
        element_counts = dom_processing_service.count_element_types(dom_tree)
        return element_counts
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to count elements: {str(e)}")

@router.get("/forms", response_model=List[Dict[str, Any]])
async def get_forms():
    """
    Get all forms on the page with analysis of their inputs and submission methods.
    """
    try:
        # First extract the DOM
        dom_tree = await dom_processing_service.extract_dom()
        
        # Get form elements
        forms = dom_processing_service.get_elements_by_tag(dom_tree, "form")
        
        # Analyze forms
        form_analyses = dom_processing_service._analyze_forms(forms)
        return form_analyses
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to analyze forms: {str(e)}") 