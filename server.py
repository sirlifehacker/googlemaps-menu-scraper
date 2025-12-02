import os
from typing import List

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, HttpUrl
from scrape_menu import scrape_menu_images
import uvicorn

app = FastAPI(
    title="Google Maps Menu Scraper API",
    description="API to scrape menu images from Google Maps place listings",
    version="1.0.0"
)

# Add CORS middleware for public API access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, you might want to restrict this
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ScrapeRequest(BaseModel):
    url: HttpUrl


class ScrapeResponse(BaseModel):
    status: str
    place_url: str
    menu_image_urls: List[str]


@app.get("/")
async def root():
    """Health check endpoint"""
    return {"message": "Google Maps Menu Scraper API is running"}


@app.post("/scrape-menu", response_model=ScrapeResponse)
async def scrape_menu(req: ScrapeRequest):
    """
    Scrape menu images from a Google Maps place URL.
    
    Returns JSON in the format:
    {
        "status": "ok",
        "place_url": "https://www.google.com/maps/place/...",
        "menu_image_urls": ["https://...", "https://..."]
    }
    """
    try:
        urls = await scrape_menu_images(str(req.url))
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Scrape failed: {str(e)}"
        )

    # Set status based on results
    status = "ok"
    if len(urls) == 0:
        status = "no_menu_found"

    return ScrapeResponse(
        status=status,
        place_url=str(req.url),
        menu_image_urls=urls,
    )


if __name__ == "__main__":
    # Read PORT from environment variable (for Render.com, Heroku, etc.)
    # Default to 8000 for local development
    port = int(os.getenv("PORT", 8000))
    host = os.getenv("HOST", "0.0.0.0")
    
    # Run with: python server.py
    uvicorn.run(app, host=host, port=port)
