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


class CreateProductRequest(BaseModel):
    """Create product request."""
    id: Optional[str] = None
    name: str
    description: str
    category: str
    subcategory: Optional[str] = None
    brand: str
    sku: str
    price: float
    sale_price: Optional[float] = None
    rating: Optional[float] = None
    review_count: Optional[int] = None
    in_stock: bool = True
    stock_quantity: Optional[int] = None
    image_url: Optional[str] = None
    featured: bool = False
    specifications: Optional[dict] = None


@router.post("/")
async def create_product(request: Request, product_request: CreateProductRequest):
    """Create a new product and index it in AI Search."""
    import uuid
    import httpx
    from datetime import datetime
    from azure.identity import DefaultAzureCredential, get_bearer_token_provider
    
    try:
        cosmos_service = request.app.state.cosmos
        search_service = request.app.state.search
        
        product = product_request.model_dump()
        if not product.get("id"):
            product["id"] = str(uuid.uuid4())
        product["created_at"] = datetime.utcnow().isoformat()
        product["updated_at"] = datetime.utcnow().isoformat()
        
        # Save to Cosmos DB
        await cosmos_service.create_product(product)
        
        logger.info("Product created", product_id=product["id"], name=product["name"])
        
        # Index in AI Search with text embedding
        try:
            # Setup Azure AD token provider for OpenAI
            credential = DefaultAzureCredential()
            token_provider = get_bearer_token_provider(
                credential,
                "https://cognitiveservices.azure.com/.default"
            )
            
            openai_endpoint = settings.azure_openai_endpoint
            embedding_deployment = getattr(settings, 'azure_openai_embedding_deployment', 'text-embedding-3-large')
            
            # Generate text embedding
            search_text = f"{product['name']} {product.get('description', '')} {product.get('category', '')} {product.get('subcategory', '')} {product.get('brand', '')}"
            
            url = f"{openai_endpoint.rstrip('/')}/openai/deployments/{embedding_deployment}/embeddings"
            params = {"api-version": "2024-02-15-preview"}
            token = token_provider()
            headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(url, params=params, headers=headers, json={"input": search_text})
                response.raise_for_status()
                result = response.json()
                text_embedding = result["data"][0]["embedding"]
            
            # Create search document
            search_doc = {
                "id": product["id"],
                "name": product["name"],
                "description": product.get("description", ""),
                "category": product.get("category", ""),
                "subcategory": product.get("subcategory", ""),
                "brand": product.get("brand", ""),
                "sku": product.get("sku", ""),
                "price": product.get("price", 0),
                "sale_price": product.get("sale_price"),
                "rating": product.get("rating", 0),
                "review_count": product.get("review_count", 0),
                "in_stock": product.get("in_stock", True),
                "featured": product.get("featured", False),
                "image_url": product.get("image_url", ""),
                "text_embedding": text_embedding,
                "image_embedding": []
            }
            
            await search_service.index_product(search_doc)
            logger.info("Product indexed in AI Search", product_id=product["id"])
            
        except Exception as index_error:
            # Log but don't fail - product was created, just not indexed
            logger.warning("Failed to index product in AI Search", product_id=product["id"], error=str(index_error))
        
        # Return the product data (not the MongoDB response)
        return {
            "id": product["id"],
            "name": product["name"],
            "brand": product["brand"],
            "category": product["category"],
            "price": product["price"],
            "created": True
        }
        
    except Exception as e:
        logger.error("Create product failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/bulk")
async def bulk_create_products(request: Request, products: List[CreateProductRequest]):
    """Bulk create products."""
    import uuid
    from datetime import datetime
    
    try:
        cosmos_service = request.app.state.cosmos
        
        product_list = []
        for p in products:
            product = p.model_dump()
            if not product.get("id"):
                product["id"] = str(uuid.uuid4())
            product["created_at"] = datetime.utcnow()
            product["updated_at"] = datetime.utcnow()
            product_list.append(product)
        
        count = await cosmos_service.bulk_insert_products(product_list)
        
        logger.info("Bulk products created", count=count)
        
        return {"created": count, "products": [p["id"] for p in product_list]}
        
    except Exception as e:
        logger.error("Bulk create failed", error=str(e))
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


@router.post("/index-by-subcategory/{subcategory}")
async def index_products_by_subcategory(
    request: Request,
    subcategory: str
):
    """
    Index products by subcategory to AI Search.
    
    Useful for indexing a specific category of newly added products.
    """
    import httpx
    from azure.identity import DefaultAzureCredential, get_bearer_token_provider
    
    try:
        cosmos_service = request.app.state.cosmos
        search_service = request.app.state.search
        
        # Setup Azure AD token provider for OpenAI
        credential = DefaultAzureCredential()
        token_provider = get_bearer_token_provider(
            credential,
            "https://cognitiveservices.azure.com/.default"
        )
        
        openai_endpoint = settings.azure_openai_endpoint
        embedding_deployment = getattr(settings, 'azure_openai_embedding_deployment', 'text-embedding-3-large')
        
        # Get products by subcategory
        all_products = []
        skip = 0
        limit = 100
        
        while True:
            batch = await cosmos_service.list_products(limit=limit, skip=skip)
            if not batch:
                break
            # Filter by subcategory
            filtered = [p for p in batch if p.get("subcategory") == subcategory]
            all_products.extend(filtered)
            skip += limit
            if len(batch) < limit:
                break
        
        if not all_products:
            return {"status": "no_products", "subcategory": subcategory, "count": 0}
        
        logger.info("Index by subcategory: Found products", subcategory=subcategory, count=len(all_products))
        
        indexed = 0
        failed = 0
        
        # Helper to get text embedding
        async def get_text_embedding(text: str) -> list:
            url = f"{openai_endpoint.rstrip('/')}/openai/deployments/{embedding_deployment}/embeddings"
            params = {"api-version": "2024-02-15-preview"}
            token = token_provider()
            headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(url, params=params, headers=headers, json={"input": text})
                response.raise_for_status()
                result = response.json()
                return result["data"][0]["embedding"]
        
        # Process products one by one
        for product in all_products:
            try:
                # Create search text
                search_text = f"{product['name']} {product.get('description', '')} {product.get('category', '')} {product.get('subcategory', '')} {product.get('brand', '')}"
                
                # Generate text embedding
                text_embedding = await get_text_embedding(search_text)
                
                # Create search document
                doc = {
                    "id": product["id"],
                    "name": product["name"],
                    "description": product.get("description", ""),
                    "category": product.get("category", ""),
                    "subcategory": product.get("subcategory", ""),
                    "brand": product.get("brand", ""),
                    "sku": product.get("sku", ""),
                    "price": product.get("price", 0),
                    "sale_price": product.get("sale_price"),
                    "rating": product.get("rating", 0),
                    "review_count": product.get("review_count", 0),
                    "in_stock": product.get("in_stock", True),
                    "featured": product.get("featured", False),
                    "image_url": product.get("image_url", ""),
                    "text_embedding": text_embedding,
                    "image_embedding": []
                }
                
                await search_service.index_product(doc)
                indexed += 1
                logger.info("Product indexed", product_id=product["id"], name=product["name"])
                
            except Exception as e:
                logger.warning("Failed to index product", product_id=product.get("id"), error=str(e))
                failed += 1
        
        return {
            "status": "completed",
            "subcategory": subcategory,
            "total_products": len(all_products),
            "indexed": indexed,
            "failed": failed
        }
        
    except Exception as e:
        logger.error("Index by subcategory failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/reindex")
async def reindex_products(
    request: Request,
    batch_size: int = Query(50, ge=1, le=100, description="Batch size for indexing")
):
    """
    Reindex all products from Cosmos DB to Azure AI Search.
    
    This is a long-running operation - use for manual reindexing after bulk updates.
    """
    import httpx
    from azure.identity import DefaultAzureCredential, get_bearer_token_provider
    
    try:
        cosmos_service = request.app.state.cosmos
        search_service = request.app.state.search
        
        # Get OpenAI settings for text embeddings
        openai_endpoint = settings.azure_openai_endpoint
        embedding_deployment = getattr(settings, 'azure_openai_embedding_deployment', 'text-embedding-3-large')
        
        # Setup Azure AD token provider for OpenAI
        credential = DefaultAzureCredential()
        token_provider = get_bearer_token_provider(
            credential,
            "https://cognitiveservices.azure.com/.default"
        )
        
        # Get all products from Cosmos DB
        all_products = []
        skip = 0
        limit = 100
        
        while True:
            batch = await cosmos_service.list_products(limit=limit, skip=skip)
            if not batch:
                break
            all_products.extend(batch)
            skip += limit
            if len(batch) < limit:
                break
        
        logger.info("Reindex: Found products", count=len(all_products))
        
        indexed = 0
        failed = 0
        
        # Helper to get text embedding
        async def get_text_embedding(text: str) -> list:
            url = f"{openai_endpoint.rstrip('/')}/openai/deployments/{embedding_deployment}/embeddings"
            params = {"api-version": "2024-02-15-preview"}
            
            token = token_provider()
            headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
            }
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    url,
                    params=params,
                    headers=headers,
                    json={"input": text}
                )
                response.raise_for_status()
                result = response.json()
                return result["data"][0]["embedding"]
        
        # Process in batches
        for i in range(0, len(all_products), batch_size):
            batch = all_products[i:i + batch_size]
            documents = []
            
            for product in batch:
                try:
                    # Create search text
                    search_text = f"{product['name']} {product.get('description', '')} {product.get('category', '')} {product.get('subcategory', '')} {product.get('brand', '')}"
                    
                    # Generate text embedding
                    text_embedding = await get_text_embedding(search_text)
                    
                    # Create search document
                    doc = {
                        "id": product["id"],
                        "name": product["name"],
                        "description": product.get("description", ""),
                        "category": product.get("category", ""),
                        "subcategory": product.get("subcategory", ""),
                        "brand": product.get("brand", ""),
                        "sku": product.get("sku", ""),
                        "price": product.get("price", 0),
                        "sale_price": product.get("sale_price"),
                        "rating": product.get("rating", 0),
                        "review_count": product.get("review_count", 0),
                        "in_stock": product.get("in_stock", True),
                        "featured": product.get("featured", False),
                        "image_url": product.get("image_url", ""),
                        "text_embedding": text_embedding,
                        "image_embedding": []  # Placeholder
                    }
                    documents.append(doc)
                    
                except Exception as e:
                    logger.warning("Reindex: Failed to process product", product_id=product.get("id"), error=str(e))
                    failed += 1
            
            # Upload batch to search
            if documents:
                try:
                    await search_service.index_products_batch(documents)
                    indexed += len(documents)
                except Exception as e:
                    logger.error("Reindex: Batch upload failed", error=str(e))
                    failed += len(documents)
            
            logger.info("Reindex: Progress", indexed=min(i + batch_size, len(all_products)), total=len(all_products))
        
        return {
            "status": "completed",
            "total_products": len(all_products),
            "indexed": indexed,
            "failed": failed
        }
        
    except Exception as e:
        logger.error("Reindex failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))
