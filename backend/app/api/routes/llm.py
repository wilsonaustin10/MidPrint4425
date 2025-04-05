"""
API routes for LLM interactions with the DOM.
"""
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from app.dom.service import dom_processing_service
from app.core.config import settings

router = APIRouter()

class DOMQueryRequest(BaseModel):
    """Request to extract DOM information for LLM processing."""
    query: Optional[str] = Field(None, description="Optional query to focus the extraction on relevant parts")
    simplify: bool = Field(True, description="Whether to return a simplified DOM representation")
    max_depth: int = Field(3, description="Maximum depth of the DOM tree to include")
    include_interactive_only: bool = Field(False, description="Whether to limit the response to interactive elements only")
    include_page_analysis: bool = Field(True, description="Whether to include page structure analysis")

class DOMElementQueryRequest(BaseModel):
    """Request to find elements in the DOM based on a natural language query."""
    query: str = Field(..., description="Natural language query describing the element to find")
    element_type: Optional[str] = Field(None, description="Type of element to focus on (clickable, input, form)")
    limit: int = Field(5, description="Maximum number of elements to return")

@router.post("/extract-for-llm", response_model=Dict[str, Any])
async def extract_dom_for_llm(request: DOMQueryRequest):
    """
    Extract DOM information optimized for LLM processing.
    """
    try:
        # First extract the full DOM tree
        dom_tree = await dom_processing_service.extract_dom()
        
        # Prepare the LLM-oriented response
        response = {
            "url": dom_tree.get("url", ""),
            "title": dom_tree.get("title", ""),
            "timestamp": dom_tree.get("timestamp", "")
        }
        
        # Add the page classification
        page_type = dom_processing_service.classify_page_type(dom_tree)
        response["page_type"] = page_type
        
        # Add interactive elements summary
        interactive_elements = dom_processing_service.get_interactive_elements(dom_tree)
        response["interactive_elements_summary"] = {
            "clickable_count": len(interactive_elements.get("clickable", [])),
            "input_count": len(interactive_elements.get("inputs", [])),
            "form_count": len(interactive_elements.get("forms", [])),
            "navigation_count": len(interactive_elements.get("navigational", []))
        }
        
        # If requested, include only interactive elements
        if request.include_interactive_only:
            response["elements"] = {
                "clickable": [
                    {
                        "id": el.get("id", ""),
                        "tag": el.get("tagName", ""),
                        "text": dom_processing_service._get_element_text(dom_tree, el.get("id", "")),
                        "selector": el.get("selector", ""),
                        "xpath": el.get("xpath", "")
                    }
                    for el in interactive_elements.get("clickable", [])
                ],
                "inputs": [
                    {
                        "id": el.get("id", ""),
                        "tag": el.get("tagName", ""),
                        "type": dom_processing_service._get_element_attribute(dom_tree, el.get("id", ""), "type"),
                        "name": dom_processing_service._get_element_attribute(dom_tree, el.get("id", ""), "name"),
                        "placeholder": dom_processing_service._get_element_attribute(dom_tree, el.get("id", ""), "placeholder"),
                        "selector": el.get("selector", ""),
                        "xpath": el.get("xpath", "")
                    }
                    for el in interactive_elements.get("inputs", [])
                ],
                "forms": [
                    {
                        "id": el.get("id", ""),
                        "tag": el.get("tagName", ""),
                        "selector": el.get("selector", ""),
                        "xpath": el.get("xpath", "")
                    }
                    for el in interactive_elements.get("forms", [])
                ]
            }
        # Otherwise include the simplified DOM tree if requested
        elif request.simplify:
            simplified_dom = dom_processing_service.create_simplified_dom(dom_tree, request.max_depth)
            response["dom"] = simplified_dom
        # Otherwise include the full DOM tree
        else:
            response["dom"] = dom_tree
        
        # Include page analysis if requested
        if request.include_page_analysis:
            analysis = dom_processing_service.analyze_page_structure(dom_tree)
            response["page_analysis"] = {
                "element_counts": analysis.get("element_counts", {}),
                "page_sections": analysis.get("page_sections", [])
            }
            
            # Add form analysis if available
            if "forms" in analysis:
                response["page_analysis"]["forms"] = analysis["forms"]
        
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to extract DOM for LLM: {str(e)}")

@router.post("/find-element", response_model=List[Dict[str, Any]])
async def find_element_for_llm(request: DOMElementQueryRequest):
    """
    Find elements in the DOM based on a natural language query.
    Combines different search strategies to find the most relevant elements.
    """
    try:
        # Extract the DOM tree
        dom_tree = await dom_processing_service.extract_dom()
        
        results = []
        query = request.query.lower()
        
        # Use different strategies based on the element type
        if request.element_type == "clickable" or not request.element_type:
            # Find clickable elements matching the query
            clickable_elements = dom_processing_service.get_interactive_elements(dom_tree).get("clickable", [])
            
            for element in clickable_elements:
                element_id = element.get("id")
                full_element = dom_processing_service.get_element_by_id(dom_tree, element_id) if element_id else None
                
                if not full_element:
                    continue
                
                # Check text content
                text_content = full_element.get("textContent", "").lower()
                if query in text_content:
                    results.append({
                        "id": element_id,
                        "tag": element.get("tagName", ""),
                        "text": full_element.get("textContent", ""),
                        "selector": element.get("selector", ""),
                        "xpath": element.get("xpath", ""),
                        "match_reason": "Text content contains the query",
                        "match_score": 1.0 if query == text_content else 0.8
                    })
                
                # Check attributes
                attributes = full_element.get("attributes", {})
                for attr_name, attr_value in attributes.items():
                    if isinstance(attr_value, str) and query in attr_value.lower():
                        results.append({
                            "id": element_id,
                            "tag": element.get("tagName", ""),
                            "text": full_element.get("textContent", ""),
                            "selector": element.get("selector", ""),
                            "xpath": element.get("xpath", ""),
                            "match_reason": f"Attribute '{attr_name}' contains the query",
                            "match_score": 0.7
                        })
                        break
        
        if request.element_type == "input" or not request.element_type:
            # Find input elements matching the query
            input_elements = dom_processing_service.get_interactive_elements(dom_tree).get("inputs", [])
            
            for element in input_elements:
                element_id = element.get("id")
                full_element = dom_processing_service.get_element_by_id(dom_tree, element_id) if element_id else None
                
                if not full_element:
                    continue
                
                attributes = full_element.get("attributes", {})
                
                # Check placeholder
                placeholder = attributes.get("placeholder", "").lower()
                if query in placeholder:
                    results.append({
                        "id": element_id,
                        "tag": element.get("tagName", ""),
                        "type": attributes.get("type", "text"),
                        "name": attributes.get("name", ""),
                        "placeholder": attributes.get("placeholder", ""),
                        "selector": element.get("selector", ""),
                        "xpath": element.get("xpath", ""),
                        "match_reason": "Placeholder contains the query",
                        "match_score": 0.9
                    })
                
                # Check name attribute
                name = attributes.get("name", "").lower()
                if query in name:
                    results.append({
                        "id": element_id,
                        "tag": element.get("tagName", ""),
                        "type": attributes.get("type", "text"),
                        "name": attributes.get("name", ""),
                        "placeholder": attributes.get("placeholder", ""),
                        "selector": element.get("selector", ""),
                        "xpath": element.get("xpath", ""),
                        "match_reason": "Name attribute contains the query",
                        "match_score": 0.85
                    })
                
                # Check for associated label
                all_elements = dom_processing_service._get_all_elements(dom_tree["tree"])
                for label_el in all_elements:
                    if label_el.get("tagName") == "label" and label_el.get("attributes", {}).get("for") == element_id:
                        label_text = label_el.get("textContent", "").lower()
                        if query in label_text:
                            results.append({
                                "id": element_id,
                                "tag": element.get("tagName", ""),
                                "type": attributes.get("type", "text"),
                                "name": attributes.get("name", ""),
                                "placeholder": attributes.get("placeholder", ""),
                                "selector": element.get("selector", ""),
                                "xpath": element.get("xpath", ""),
                                "match_reason": "Associated label contains the query",
                                "match_score": 0.95
                            })
                            break
        
        if request.element_type == "form" or not request.element_type:
            # Find form elements matching the query
            forms = dom_processing_service.get_elements_by_tag(dom_tree, "form")
            
            for form in forms:
                form_id = form.get("id")
                
                # Check form attributes
                attributes = form.get("attributes", {})
                for attr_name, attr_value in attributes.items():
                    if isinstance(attr_value, str) and query in attr_value.lower():
                        results.append({
                            "id": form_id,
                            "tag": "form",
                            "action": attributes.get("action", ""),
                            "method": attributes.get("method", "get"),
                            "selector": form.get("css_selector", ""),
                            "xpath": form.get("xpath", ""),
                            "match_reason": f"Form attribute '{attr_name}' contains the query",
                            "match_score": 0.75
                        })
                        break
                
                # Check for input fields within the form that match the query
                inputs = []
                dom_processing_service._find_form_controls_recursive(form, inputs, [])
                
                for input_el in inputs:
                    input_attributes = input_el.get("attributes", {})
                    
                    # Check name and placeholder
                    input_name = input_attributes.get("name", "").lower()
                    input_placeholder = input_attributes.get("placeholder", "").lower()
                    
                    if query in input_name or query in input_placeholder:
                        results.append({
                            "id": form_id,
                            "tag": "form",
                            "action": attributes.get("action", ""),
                            "method": attributes.get("method", "get"),
                            "selector": form.get("css_selector", ""),
                            "xpath": form.get("xpath", ""),
                            "match_reason": "Form contains an input field matching the query",
                            "match_score": 0.7
                        })
                        break
        
        # Sort by match score and limit results
        results.sort(key=lambda x: x.get("match_score", 0), reverse=True)
        results = results[:request.limit]
        
        # Deduplicate by ID
        seen_ids = set()
        unique_results = []
        for result in results:
            if result["id"] not in seen_ids:
                seen_ids.add(result["id"])
                unique_results.append(result)
        
        return unique_results
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to find element for LLM: {str(e)}")

@router.post("/suggest-action", response_model=Dict[str, Any])
async def suggest_action_for_llm(request: DOMElementQueryRequest):
    """
    Suggest the most appropriate action to take for a given query.
    This endpoint analyzes the DOM and suggests what elements to interact with
    and what actions to take (click, input text, etc.).
    """
    try:
        # Find relevant elements
        elements = await find_element_for_llm(request)
        
        if not elements:
            return {
                "success": False,
                "message": "No matching elements found",
                "suggestion": None
            }
        
        # Get the top matching element
        best_match = elements[0]
        tag_name = best_match.get("tag", "").lower()
        
        # Generate a suggested action based on the element type
        suggestion = {
            "element": best_match,
            "action": None,
            "parameters": {}
        }
        
        if tag_name in ["a", "button", "div", "span", "li"]:
            suggestion["action"] = "click"
        elif tag_name in ["input", "textarea", "select"]:
            input_type = best_match.get("type", "text").lower()
            
            if input_type in ["checkbox", "radio"]:
                suggestion["action"] = "check"
                suggestion["parameters"]["check"] = True
            elif input_type in ["submit", "button"]:
                suggestion["action"] = "click"
            else:
                suggestion["action"] = "input"
                suggestion["parameters"]["text"] = ""
        elif tag_name == "form":
            suggestion["action"] = "fill_form"
            suggestion["parameters"]["fields"] = {}
        
        return {
            "success": True,
            "message": f"Found matching {tag_name} element",
            "suggestion": suggestion
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to suggest action: {str(e)}") 