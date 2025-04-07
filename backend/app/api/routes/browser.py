from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, HttpUrl, Field, validator
from typing import Dict, Any, Optional
from app.services.browser import browser_service
from app.controller.service import controller_service

router = APIRouter(prefix="/browser", tags=["browser"])

class BrowserNavigateRequest(BaseModel):
    url: HttpUrl

class BrowserResponse(BaseModel):
    content: str

class ScreenshotConfigRequest(BaseModel):
    format: Optional[str] = Field(
        None, description="Image format: 'jpeg' or 'png'"
    )
    quality: Optional[int] = Field(
        None, description="JPEG quality (0-100)", ge=0, le=100
    )
    full_page: Optional[bool] = Field(
        None, description="Whether to capture the full page"
    )
    debounce_interval: Optional[int] = Field(
        None, description="Minimum interval between screenshots (ms)", ge=0, le=1000
    )
    
    @validator('format')
    def validate_format(cls, v):
        if v and v.lower() not in ['jpeg', 'png']:
            raise ValueError('Format must be either "jpeg" or "png"')
        return v.lower() if v else v

class ScreenshotConfigResponse(BaseModel):
    success: bool
    config: Dict[str, Any]
    debounce_interval: Optional[int] = None

@router.post("/navigate", response_model=BrowserResponse)
async def navigate_to_url(request: BrowserNavigateRequest):
    """Navigate the browser to a URL and return the page content"""
    try:
        content = await browser_service.navigate(str(request.url))
        return BrowserResponse(content=content)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Browser navigation failed: {str(e)}")

@router.get("/dom", response_model=BrowserResponse)
async def get_dom():
    """Get the current DOM content of the browser"""
    try:
        content = await browser_service.get_dom()
        return BrowserResponse(content=content)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get DOM: {str(e)}")

@router.post("/screenshot/config", response_model=ScreenshotConfigResponse)
async def set_screenshot_config(request: ScreenshotConfigRequest):
    """Configure screenshot capture settings"""
    try:
        # Create a config dictionary with only the provided fields
        config = {}
        if request.format is not None:
            config["format"] = request.format
        if request.quality is not None:
            config["quality"] = request.quality
        if request.full_page is not None:
            config["full_page"] = request.full_page
        if request.debounce_interval is not None:
            config["debounce_interval"] = request.debounce_interval
            
        # Update the screenshot configuration
        result = await controller_service.set_screenshot_config(config)
        return ScreenshotConfigResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update screenshot config: {str(e)}") 