"""
Image Search API Endpoints
===========================

REST API for image upload and visual search.
Uses GPT-4o Vision to understand images and semantic search to find similar products.
"""

from typing import Optional, List
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query, Request, UploadFile, File
from pydantic import BaseModel, Field
import structlog
import uuid
import base64
import httpx
from azure.identity import DefaultAzureCredential

logger = structlog.get_logger(__name__)

router = APIRouter()


class ImageUploadResponse(BaseModel):
    """Image upload response."""
    image_id: str
    url: str
    message: str


class SimilarProductResponse(BaseModel):
    """Similar product from image search."""
    id: str
    name: str
    description: str
    category: str
    subcategory: Optional[str] = None
    brand: Optional[str] = None
    sku: Optional[str] = None
    price: float
    sale_price: Optional[float] = None
    rating: Optional[float] = 0
    review_count: Optional[int] = 0
    in_stock: Optional[bool] = True
    image_url: Optional[str] = None
    similarity_score: Optional[float] = 0.0


class ImageSearchResponse(BaseModel):
    """Image search response."""
    query_image_id: str
    products: List[SimilarProductResponse]
    total: int
    image_description: Optional[str] = None


async def analyze_image_with_gpt4o(image_data: bytes, openai_endpoint: str) -> str:
    """
    Use GPT-4o Vision to analyze the image and generate a product description.
    """
    # Encode image as base64
    image_base64 = base64.b64encode(image_data).decode("utf-8")
    
    # Get Azure AD token
    credential = DefaultAzureCredential()
    token = credential.get_token("https://cognitiveservices.azure.com/.default")
    
    headers = {
        "Authorization": f"Bearer {token.token}",
        "Content-Type": "application/json"
    }
    
    # Build GPT-4o Vision request
    payload = {
        "messages": [
            {
                "role": "system",
                "content": """You are a product identification expert for a home improvement store. 
                Analyze the image and describe the product in detail for search purposes.
                Focus on: product type, category, style, color, material, brand (if visible), and any distinctive features.
                Be concise but descriptive. Your description will be used to search for similar products.
                Example: "Modern brushed nickel kitchen faucet with pull-down sprayer, single handle design"
                Just provide the description, no explanations."""
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": "Describe this product for a home improvement store search:"
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{image_base64}"
                        }
                    }
                ]
            }
        ],
        "max_tokens": 200
    }
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        url = f"{openai_endpoint}/openai/deployments/gpt-4o/chat/completions?api-version=2024-02-15-preview"
        response = await client.post(url, headers=headers, json=payload)
        response.raise_for_status()
        
        result = response.json()
        description = result["choices"][0]["message"]["content"].strip()
        # Remove any surrounding quotes from GPT response
        description = description.strip('"').strip("'")
        logger.info("GPT-4o image analysis completed", description=description[:100])
        return description


@router.post("/search", response_model=ImageSearchResponse)
async def search_by_uploaded_image(
    request: Request,
    file: UploadFile = File(..., description="Image file to search with"),
    limit: int = Query(5, ge=1, le=20),
    category: Optional[str] = Query(None)
):
    """
    Upload an image and search for similar products.
    
    Uses GPT-4o Vision to understand the image content, then performs
    semantic search to find visually and functionally similar products.
    """
    logger.info("Image search request received", 
                filename=file.filename, 
                content_type=file.content_type)
    
    # Validate file type - be more lenient with content type detection
    allowed_types = ["image/jpeg", "image/png", "image/webp", "image/jpg", "image/avif", "image/gif", "image/bmp", "image/heic", "image/heif"]
    file_content_type = file.content_type or ""
    
    # Also check file extension if content_type is missing or generic
    filename = file.filename or ""
    extension = filename.lower().split(".")[-1] if "." in filename else ""
    valid_extensions = ["jpg", "jpeg", "png", "webp", "avif", "gif", "bmp", "heic", "heif"]
    
    if file_content_type not in allowed_types and extension not in valid_extensions:
        logger.warning("Invalid file type", 
                      content_type=file_content_type, 
                      filename=filename,
                      extension=extension)
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file type '{file_content_type}'. Allowed: JPEG, PNG, WebP, AVIF, GIF"
        )
    
    content = await file.read()
    
    if len(content) > 10 * 1024 * 1024:
        raise HTTPException(
            status_code=400,
            detail="File too large. Maximum size is 10MB."
        )
    
    try:
        from config import settings
        search_service = request.app.state.search
        
        # Step 1: Use GPT-4o Vision to analyze the image
        image_description = await analyze_image_with_gpt4o(
            content, 
            settings.azure_openai_endpoint
        )
        
        # Step 2: Search using semantic search with the description
        results = await search_service.search_products(
            query=image_description,
            category=category,
            limit=limit,
            use_semantic=True
        )
        
        products = [
            {
                "id": r["id"],
                "name": r["name"],
                "description": r.get("description", ""),
                "category": r.get("category", ""),
                "subcategory": r.get("subcategory", ""),
                "brand": r.get("brand", ""),
                "sku": r.get("sku", ""),
                "price": r.get("price", 0),
                "sale_price": r.get("sale_price"),
                "rating": r.get("rating", 0),
                "review_count": r.get("review_count", 0),
                "in_stock": r.get("in_stock", True),
                "image_url": r.get("image_url"),
                "similarity_score": r.get("@search.score", 0.0)
            }
            for r in results
        ]
        
        logger.info("Image search completed", 
                   description=image_description[:50], 
                   results=len(products))
        
        return {
            "products": products,
            "total": len(products),
            "query_image_id": str(uuid.uuid4()),
            "image_description": image_description
        }
        
    except Exception as e:
        logger.error("Image search failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/upload", response_model=ImageUploadResponse)
async def upload_image(
    request: Request,
    file: UploadFile = File(..., description="Image file to upload")
):
    """
    Upload an image for visual search.
    
    Note: This endpoint is deprecated. Use POST /search directly instead.
    Accepts: JPEG, PNG, WebP images
    Max size: 10MB
    """
    # Validate file type
    allowed_types = ["image/jpeg", "image/png", "image/webp"]
    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file type. Allowed: {allowed_types}"
        )
    
    # Read file content
    content = await file.read()
    
    # Check file size (10MB max)
    if len(content) > 10 * 1024 * 1024:
        raise HTTPException(
            status_code=400,
            detail="File too large. Maximum size is 10MB."
        )
    
    try:
        blob_service = request.app.state.blob
        
        # Generate unique ID
        image_id = str(uuid.uuid4())
        blob_name = f"uploads/{image_id}.{file.filename.split('.')[-1]}"
        
        # Upload to blob storage
        url = await blob_service.upload_image(
            content=content,
            blob_name=blob_name,
            content_type=file.content_type
        )
        
        logger.info("Image uploaded", image_id=image_id)
        
        return ImageUploadResponse(
            image_id=image_id,
            url=url,
            message="Image uploaded. Use POST /api/v1/images/search to search for similar products."
        )
        
    except Exception as e:
        logger.error("Image upload failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/search/{image_id}", response_model=ImageSearchResponse, deprecated=True)
async def search_by_image_id(
    request: Request,
    image_id: str,
    limit: int = Query(5, ge=1, le=20),
    category: Optional[str] = Query(None, description="Optional category filter")
):
    """
    DEPRECATED: Search for products similar to a previously uploaded image.
    
    Note: This endpoint is deprecated. Use POST /search with the image file directly instead.
    """
    raise HTTPException(
        status_code=410,
        detail="This endpoint is deprecated. Use POST /api/v1/images/search with the image file directly."
    )


@router.post("/search-direct")
async def search_by_image_direct(
    request: Request,
    file: UploadFile = File(..., description="Image file to search with"),
    limit: int = Query(5, ge=1, le=20),
    category: Optional[str] = Query(None)
):
    """
    Upload and search in one step - upload an image and immediately get similar products.
    Uses GPT-4o Vision for image analysis and semantic search for matching.
    """
    # Validate file type
    allowed_types = ["image/jpeg", "image/png", "image/webp", "image/avif", "image/gif"]
    file_content_type = file.content_type or ""
    filename = file.filename or ""
    extension = filename.lower().split(".")[-1] if "." in filename else ""
    valid_extensions = ["jpg", "jpeg", "png", "webp", "avif", "gif"]
    
    if file_content_type not in allowed_types and extension not in valid_extensions:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file type. Allowed: JPEG, PNG, WebP, AVIF, GIF"
        )
    
    content = await file.read()
    
    if len(content) > 10 * 1024 * 1024:
        raise HTTPException(
            status_code=400,
            detail="File too large. Maximum size is 10MB."
        )
    
    try:
        from config import settings
        search_service = request.app.state.search
        
        # Use GPT-4o Vision to analyze the image
        image_description = await analyze_image_with_gpt4o(
            content, 
            settings.azure_openai_endpoint
        )
        
        # Search using semantic search with the description
        results = await search_service.search_products(
            query=image_description,
            category=category,
            limit=limit,
            use_semantic=True
        )
        
        products = [
            SimilarProductResponse(
                id=r["id"],
                name=r["name"],
                description=r.get("description", ""),
                category=r.get("category", ""),
                subcategory=r.get("subcategory"),
                brand=r.get("brand"),
                sku=r.get("sku"),
                price=r.get("price", 0),
                sale_price=r.get("sale_price"),
                rating=r.get("rating", 0),
                review_count=r.get("review_count", 0),
                in_stock=r.get("in_stock", True),
                image_url=r.get("image_url"),
                similarity_score=r.get("@search.score", 0.0)
            )
            for r in results
        ]
        
        return {
            "products": products,
            "total": len(products),
            "image_description": image_description
        }
        
    except Exception as e:
        logger.error("Direct image search failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/search-url")
async def search_by_image_url(
    request: Request,
    image_url: str = Query(..., description="URL of the image to search with"),
    limit: int = Query(5, ge=1, le=20),
    category: Optional[str] = Query(None)
):
    """
    Search for similar products using an image URL.
    Uses GPT-4o Vision for image analysis and semantic search for matching.
    """
    try:
        from config import settings
        search_service = request.app.state.search
        
        # Fetch image from URL
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(image_url)
            if response.status_code != 200:
                raise HTTPException(
                    status_code=400,
                    detail=f"Failed to fetch image from URL: HTTP {response.status_code}"
                )
            image_data = response.content
        
        # Use GPT-4o Vision to analyze the image
        image_description = await analyze_image_with_gpt4o(
            image_data, 
            settings.azure_openai_endpoint
        )
        
        # Search using semantic search with the description
        results = await search_service.search_products(
            query=image_description,
            category=category,
            limit=limit,
            use_semantic=True
        )
        
        products = [
            SimilarProductResponse(
                id=r["id"],
                name=r["name"],
                description=r.get("description", ""),
                category=r.get("category", ""),
                subcategory=r.get("subcategory"),
                brand=r.get("brand"),
                sku=r.get("sku"),
                price=r.get("price", 0),
                sale_price=r.get("sale_price"),
                rating=r.get("rating", 0),
                review_count=r.get("review_count", 0),
                in_stock=r.get("in_stock", True),
                image_url=r.get("image_url"),
                similarity_score=r.get("@search.score", 0.0)
            )
            for r in results
        ]
        
        return {
            "query_url": image_url,
            "products": products,
            "total": len(products),
            "image_description": image_description
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("URL image search failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))
