from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, HttpUrl
from app.services.browser import browser_service

router = APIRouter(prefix="/browser", tags=["browser"])

class BrowserNavigateRequest(BaseModel):
    url: HttpUrl

class BrowserResponse(BaseModel):
    content: str

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