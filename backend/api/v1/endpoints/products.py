"""
Products API Endpoints
=======================

REST API for product search and management.
"""

from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel, Field
import structlog
import re

from config import settings

logger = structlog.get_logger(__name__)

router = APIRouter()


def transform_image_url(image_url: Optional[str], request: Request) -> Optional[str]:
    """
    Transform blob storage URLs to use the image proxy.
    
    Converts: https://storage.blob.core.windows.net/product-images/path/image.jpg
    To: https://backend-url/api/v1/img/product-images/path/image.jpg
    """
    if not image_url:
        return None
    
    # Pattern to match blob storage URLs
    pattern = r'https://[^/]+\.blob\.core\.windows\.net/([^/]+)/(.+)'
    match = re.match(pattern, image_url)
    
    if match:
        container = match.group(1)
        path = match.group(2)
        # Get the base URL from the request, ensure https
        base_url = str(request.base_url).rstrip('/')
        # Force https in production (Container Apps terminates TLS at ingress)
        if base_url.startswith('http://'):
            base_url = base_url.replace('http://', 'https://', 1)
        return f"{base_url}/api/v1/img/{container}/{path}"
    
    return image_url


def transform_product(product: dict, request: Request) -> dict:
    """Transform product dict with proxied image URL."""
    if 'image_url' in product:
        product['image_url'] = transform_image_url(product.get('image_url'), request)
    return product


class ProductSearchRequest(BaseModel):
    """Product search request."""
    query: str = Field(..., description="Search query")
    category: Optional[str] = Field(None, description="Category filter")
    min_price: Optional[float] = Field(None, ge=0)
    max_price: Optional[float] = Field(None, ge=0)
    limit: int = Field(10, ge=1, le=50)


class ProductResponse(BaseModel):
    """Product response model."""
    id: str
    name: str
    description: str
    category: str
    subcategory: Optional[str] = None
    price: float
    sale_price: Optional[float] = None
    brand: str
    sku: str
    image_url: Optional[str] = None
    rating: Optional[float] = None
    review_count: Optional[int] = None
    in_stock: bool = True
    stock_quantity: Optional[int] = None


class ProductListResponse(BaseModel):
    """Product list response."""
    products: List[ProductResponse]
    total: int
    query: str


@router.get("/search", response_model=ProductListResponse)
async def search_products(
    request: Request,
    query: str = Query(..., description="Search query"),
    category: Optional[str] = Query(None, description="Category filter"),
    min_price: Optional[float] = Query(None, ge=0),
    max_price: Optional[float] = Query(None, ge=0),
    limit: int = Query(10, ge=1, le=50)
):
    """
    Search for products using Azure AI Search.
    
    Supports:
    - Full-text search
    - Semantic search
    - Vector search
    - Category filtering
    - Price range filtering
    """
    try:
        search_service = request.app.state.search
        
        results = await search_service.search_products(
            query=query,
            category=category,
            min_price=min_price,
            max_price=max_price,
            limit=limit
        )
        
        # Transform image URLs to use proxy
        transformed = [transform_product(p, request) for p in results]
        
        return ProductListResponse(
            products=[ProductResponse(**p) for p in transformed],
            total=len(transformed),
            query=query
        )
        
    except Exception as e:
        logger.error("Search failed", error=str(e), query=query)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{product_id}", response_model=ProductResponse)
async def get_product(request: Request, product_id: str):
    """Get a single product by ID."""
    try:
        cosmos_service = request.app.state.cosmos
        product = await cosmos_service.get_product(product_id)
        
        if not product:
            raise HTTPException(status_code=404, detail="Product not found")
        
        transformed = transform_product(product, request)
        return ProductResponse(**transformed)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Get product failed", error=str(e), product_id=product_id)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/category/{category}")
async def get_products_by_category(
    request: Request,
    category: str,
    limit: int = Query(20, ge=1, le=100)
):
    """Get products by category."""
    try:
        cosmos_service = request.app.state.cosmos
        products = await cosmos_service.get_products_by_category(category, limit)
        
        # Transform image URLs to use proxy
        transformed = [transform_product(p, request) for p in products]
        
        return {
            "products": transformed,
            "total": len(transformed),
            "category": category
        }
        
    except Exception as e:
        logger.error("Get by category failed", error=str(e), category=category)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/")
async def list_products(
    request: Request,
    limit: int = Query(20, ge=1, le=100),
    skip: int = Query(0, ge=0)
):
    """List all products with pagination."""
    try:
        cosmos_service = request.app.state.cosmos
        products = await cosmos_service.list_products(limit=limit, skip=skip)
        
        # Transform image URLs to use proxy
        transformed = [transform_product(p, request) for p in products]
        
        return {
            "products": transformed,
            "limit": limit,
            "skip": skip
        }
        
    except Exception as e:
        logger.error("List products failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/featured")
async def get_featured_products(request: Request):
    """Get featured/popular products."""
    try:
        cosmos_service = request.app.state.cosmos
        products = await cosmos_service.get_featured_products()
        
        # Transform image URLs to use proxy
        transformed = [transform_product(p, request) for p in products]
        
        return {
            "products": transformed,
            "total": len(transformed)
        }
        
    except Exception as e:
        logger.error("Get featured failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))
