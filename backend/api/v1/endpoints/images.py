"""
Image Search API Endpoints
===========================

REST API for image upload and visual search.
"""

from typing import Optional, List
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query, Request, UploadFile, File
from pydantic import BaseModel, Field
import structlog
import uuid
import base64

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
    price: float
    image_url: Optional[str]
    similarity_score: float


class ImageSearchResponse(BaseModel):
    """Image search response."""
    query_image_id: str
    results: List[SimilarProductResponse]
    total: int


@router.post("/search", response_model=ImageSearchResponse)
async def search_by_uploaded_image(
    request: Request,
    file: UploadFile = File(..., description="Image file to search with"),
    limit: int = Query(5, ge=1, le=20),
    category: Optional[str] = Query(None)
):
    """
    Upload an image and search for similar products.
    Primary endpoint for the frontend image search feature.
    """
    # Validate file type
    allowed_types = ["image/jpeg", "image/png", "image/webp"]
    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file type. Allowed: {allowed_types}"
        )
    
    content = await file.read()
    
    if len(content) > 10 * 1024 * 1024:
        raise HTTPException(
            status_code=400,
            detail="File too large. Maximum size is 10MB."
        )
    
    try:
        vision_service = request.app.state.vision
        search_service = request.app.state.search
        
        # Generate image embedding
        embedding = await vision_service.get_image_embedding(content)
        
        # Search using vector similarity
        results = await search_service.search_by_vector(
            embedding=embedding,
            limit=limit,
            category=category,
            field_name="image_embedding"
        )
        
        products = [
            {
                "id": r["id"],
                "name": r["name"],
                "description": r.get("description", ""),
                "category": r.get("category", ""),
                "subcategory": r.get("subcategory", ""),
                "brand": r.get("brand", ""),
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
        
        logger.info("Image search completed", results=len(products))
        
        return {
            "products": products,
            "total": len(products),
            "query_image_id": str(uuid.uuid4())  # For tracking
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
        vision_service = request.app.state.vision
        search_service = request.app.state.search
        
        # Generate unique ID
        image_id = str(uuid.uuid4())
        blob_name = f"uploads/{image_id}.{file.filename.split('.')[-1]}"
        
        # Upload to blob storage
        url = await blob_service.upload_image(
            content=content,
            blob_name=blob_name,
            content_type=file.content_type
        )
        
        # Generate image embedding for search
        embedding = await vision_service.get_image_embedding(content)
        
        # Store embedding for later search
        await search_service.store_query_embedding(image_id, embedding)
        
        logger.info("Image uploaded", image_id=image_id)
        
        return ImageUploadResponse(
            image_id=image_id,
            url=url,
            message="Image uploaded successfully. You can now search for similar products."
        )
        
    except Exception as e:
        logger.error("Image upload failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/search/{image_id}", response_model=ImageSearchResponse)
async def search_by_image(
    request: Request,
    image_id: str,
    limit: int = Query(5, ge=1, le=20),
    category: Optional[str] = Query(None, description="Optional category filter")
):
    """
    Search for products visually similar to an uploaded image.
    
    Uses Azure AI Vision embeddings and Azure AI Search vector search.
    """
    try:
        search_service = request.app.state.search
        
        # Perform vector search using stored embedding
        results = await search_service.search_by_image_embedding(
            image_id=image_id,
            limit=limit,
            category=category
        )
        
        similar_products = [
            SimilarProductResponse(
                id=r["id"],
                name=r["name"],
                description=r["description"],
                category=r["category"],
                price=r["price"],
                image_url=r.get("image_url"),
                similarity_score=r.get("@search.score", 0.0)
            )
            for r in results
        ]
        
        logger.info("Image search completed", image_id=image_id, results=len(similar_products))
        
        return ImageSearchResponse(
            query_image_id=image_id,
            results=similar_products,
            total=len(similar_products)
        )
        
    except Exception as e:
        logger.error("Image search failed", error=str(e), image_id=image_id)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/search-direct")
async def search_by_image_direct(
    request: Request,
    file: UploadFile = File(..., description="Image file to search with"),
    limit: int = Query(5, ge=1, le=20),
    category: Optional[str] = Query(None)
):
    """
    Upload and search in one step - upload an image and immediately get similar products.
    """
    # Validate file type
    allowed_types = ["image/jpeg", "image/png", "image/webp"]
    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file type. Allowed: {allowed_types}"
        )
    
    content = await file.read()
    
    if len(content) > 10 * 1024 * 1024:
        raise HTTPException(
            status_code=400,
            detail="File too large. Maximum size is 10MB."
        )
    
    try:
        vision_service = request.app.state.vision
        search_service = request.app.state.search
        
        # Generate embedding directly from uploaded image
        embedding = await vision_service.get_image_embedding(content)
        
        # Search using the embedding
        results = await search_service.search_by_vector(
            embedding=embedding,
            limit=limit,
            category=category
        )
        
        similar_products = [
            SimilarProductResponse(
                id=r["id"],
                name=r["name"],
                description=r["description"],
                category=r["category"],
                price=r["price"],
                image_url=r.get("image_url"),
                similarity_score=r.get("@search.score", 0.0)
            )
            for r in results
        ]
        
        return {
            "results": similar_products,
            "total": len(similar_products)
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
    """
    try:
        vision_service = request.app.state.vision
        search_service = request.app.state.search
        
        # Generate embedding from URL
        embedding = await vision_service.get_image_embedding_from_url(image_url)
        
        # Search using the embedding
        results = await search_service.search_by_vector(
            embedding=embedding,
            limit=limit,
            category=category
        )
        
        similar_products = [
            SimilarProductResponse(
                id=r["id"],
                name=r["name"],
                description=r["description"],
                category=r["category"],
                price=r["price"],
                image_url=r.get("image_url"),
                similarity_score=r.get("@search.score", 0.0)
            )
            for r in results
        ]
        
        return {
            "query_url": image_url,
            "results": similar_products,
            "total": len(similar_products)
        }
        
    except Exception as e:
        logger.error("URL image search failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))
