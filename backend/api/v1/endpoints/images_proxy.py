"""
Image Proxy Endpoint
====================

Serves product images from private blob storage.
Since Azure Policy blocks public blob access, we proxy images through the backend.
Uses managed identity for authentication.
"""

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import StreamingResponse, RedirectResponse
from azure.storage.blob.aio import BlobServiceClient
from azure.identity.aio import DefaultAzureCredential
import structlog
import io

from config import settings

logger = structlog.get_logger(__name__)

router = APIRouter()

# Cache the credential and client
_credential = None
_blob_client = None

# Placeholder image URL when blob doesn't exist
PLACEHOLDER_IMAGE = "https://placehold.co/400x400/e2e8f0/64748b?text=Product+Image"


async def get_blob_client():
    """Get or create a blob client with managed identity."""
    global _credential, _blob_client
    
    if _blob_client is None:
        _credential = DefaultAzureCredential()
        account_url = f"https://{settings.azure_storage_account_name}.blob.core.windows.net"
        _blob_client = BlobServiceClient(account_url, credential=_credential)
    
    return _blob_client


@router.get("/{container}/{path:path}")
async def proxy_image(container: str, path: str, request: Request):
    """
    Proxy images from Azure Blob Storage.
    
    This endpoint serves images from private blob containers using managed identity.
    If the image doesn't exist, redirects to a placeholder.
    """
    # Only allow product-images and uploads containers
    allowed_containers = ["product-images", "uploads"]
    if container not in allowed_containers:
        raise HTTPException(status_code=403, detail="Container not allowed")
    
    try:
        # Get blob client with managed identity
        blob_service = await get_blob_client()
        container_client = blob_service.get_container_client(container)
        blob_client = container_client.get_blob_client(path)
        
        # Check if blob exists
        if not await blob_client.exists():
            logger.info("Image not found, returning placeholder", container=container, path=path)
            # Return a redirect to placeholder image
            return RedirectResponse(url=PLACEHOLDER_IMAGE, status_code=302)
        
        # Download the blob
        download = await blob_client.download_blob()
        content = await download.readall()
        
        # Get content type from blob properties
        properties = await blob_client.get_blob_properties()
        content_type = properties.content_settings.content_type or "image/jpeg"
        
        # Return as streaming response
        return StreamingResponse(
            io.BytesIO(content),
            media_type=content_type,
            headers={
                "Cache-Control": "public, max-age=86400",  # Cache for 24 hours
                "Content-Length": str(len(content))
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to proxy image", container=container, path=path, error=str(e))
        # On error, also redirect to placeholder
        return RedirectResponse(url=PLACEHOLDER_IMAGE, status_code=302)
        raise HTTPException(status_code=500, detail="Failed to retrieve image")
