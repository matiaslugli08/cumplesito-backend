"""
URL Metadata extraction endpoint
"""
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, HttpUrl

from app.utils.url_metadata import extract_url_metadata

router = APIRouter(prefix="/metadata", tags=["Metadata"])


class URLMetadataRequest(BaseModel):
    """Request schema for URL metadata extraction"""
    url: str


class URLMetadataResponse(BaseModel):
    """Response schema for URL metadata"""
    title: str | None = None
    image: str | None = None
    description: str | None = None
    price: str | None = None


@router.post("/extract", response_model=URLMetadataResponse)
async def extract_metadata(request: URLMetadataRequest):
    """
    Extract metadata (title, image, description) from a product URL

    This endpoint scrapes Open Graph tags and other metadata from the provided URL
    to automatically populate product information.

    Args:
        request: URL to extract metadata from

    Returns:
        Extracted metadata (title, image URL, description, price if available)

    Raises:
        HTTPException: If URL is invalid or metadata extraction fails
    """
    try:
        # Validate URL format
        if not request.url.startswith(('http://', 'https://')):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="URL must start with http:// or https://"
            )

        # Extract metadata
        metadata = extract_url_metadata(request.url)

        # Check if we got at least some metadata
        if not any(metadata.values()):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Could not extract metadata from the provided URL. The site may be blocking scraping."
            )

        return URLMetadataResponse(**metadata)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error extracting metadata: {str(e)}"
        )
