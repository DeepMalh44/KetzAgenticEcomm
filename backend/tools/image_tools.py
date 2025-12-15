# =============================================================================
# KetzAgenticEcomm - Image Search Tools
# =============================================================================
"""
Image-based search tools for the voice assistant.
Uses Azure AI Vision (Florence model) for image embeddings.
"""

import logging
from typing import Any, Dict, Optional

from services.ai_search import AISearchService
from services.blob_storage import BlobStorageService
from services.vision_embeddings import VisionEmbeddingService

logger = logging.getLogger(__name__)


async def search_by_image(
    image_data: bytes,
    content_type: str = "image/jpeg",
    category: Optional[str] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    limit: int = 5,
    vision_service: Optional[VisionEmbeddingService] = None,
    ai_search: Optional[AISearchService] = None,
    blob_storage: Optional[BlobStorageService] = None,
) -> Dict[str, Any]:
    """
    Search for products similar to an uploaded image.
    
    Uses Azure AI Vision (Florence model) to generate image embeddings,
    then performs vector similarity search in Azure AI Search.
    
    Args:
        image_data: Raw image bytes
        content_type: MIME type of the image
        category: Optional category filter
        min_price: Optional minimum price filter
        max_price: Optional maximum price filter
        limit: Maximum number of results
        vision_service: VisionEmbeddingService instance
        ai_search: AISearchService instance
        blob_storage: BlobStorageService instance
        
    Returns:
        Dictionary with similar products
    """
    try:
        if not vision_service or not ai_search:
            return {
                "success": False,
                "error": "Vision or search service not available",
                "products": []
            }
        
        # Step 1: Generate embedding for the uploaded image
        logger.info("Generating image embedding...")
        embedding = await vision_service.get_image_embedding(image_data)
        
        if not embedding:
            return {
                "success": False,
                "error": "Failed to generate image embedding",
                "products": []
            }
        
        # Step 2: Optionally store the uploaded image
        upload_url = None
        if blob_storage:
            try:
                import uuid
                filename = f"searches/{uuid.uuid4().hex}.jpg"
                upload_url = await blob_storage.upload_image(
                    image_data,
                    filename,
                    container="uploads"
                )
            except Exception as e:
                logger.warning(f"Failed to store search image: {e}")
        
        # Step 3: Build filters
        filters = []
        if category:
            filters.append(f"category eq '{category}'")
        if min_price is not None:
            filters.append(f"price ge {min_price}")
        if max_price is not None:
            filters.append(f"price le {max_price}")
        
        filter_str = " and ".join(filters) if filters else None
        
        # Step 4: Perform vector search
        logger.info("Performing vector similarity search...")
        results = await ai_search.vector_search(
            vector=embedding,
            vector_field="image_embedding",
            filter=filter_str,
            top=limit
        )
        
        # Step 5: Format results
        products = []
        for result in results:
            similarity = result.get("@search.score", 0)
            products.append({
                "id": result.get("id"),
                "name": result.get("name"),
                "description": result.get("description"),
                "price": result.get("price"),
                "category": result.get("category"),
                "brand": result.get("brand"),
                "rating": result.get("rating"),
                "image_url": result.get("image_url"),
                "sku": result.get("sku"),
                "similarity_score": round(similarity, 3),
            })
        
        return {
            "success": True,
            "count": len(products),
            "products": products,
            "search_image_url": upload_url,
            "filters_applied": {
                "category": category,
                "price_range": [min_price, max_price] if min_price or max_price else None,
            },
            "message": f"Found {len(products)} visually similar products."
        }
        
    except Exception as e:
        logger.error(f"Image search error: {e}")
        return {
            "success": False,
            "error": str(e),
            "products": []
        }


async def search_by_image_url(
    image_url: str,
    category: Optional[str] = None,
    limit: int = 5,
    vision_service: Optional[VisionEmbeddingService] = None,
    ai_search: Optional[AISearchService] = None,
) -> Dict[str, Any]:
    """
    Search for products similar to an image by URL.
    
    Args:
        image_url: URL of the image
        category: Optional category filter
        limit: Maximum number of results
        vision_service: VisionEmbeddingService instance
        ai_search: AISearchService instance
        
    Returns:
        Dictionary with similar products
    """
    try:
        if not vision_service or not ai_search:
            return {
                "success": False,
                "error": "Vision or search service not available",
                "products": []
            }
        
        # Fetch image from URL
        import aiohttp
        async with aiohttp.ClientSession() as session:
            async with session.get(image_url) as response:
                if response.status != 200:
                    return {
                        "success": False,
                        "error": f"Failed to fetch image: HTTP {response.status}",
                        "products": []
                    }
                image_data = await response.read()
        
        # Use the main search function
        return await search_by_image(
            image_data=image_data,
            category=category,
            limit=limit,
            vision_service=vision_service,
            ai_search=ai_search,
        )
        
    except Exception as e:
        logger.error(f"Image URL search error: {e}")
        return {
            "success": False,
            "error": str(e),
            "products": []
        }


async def get_similar_products(
    product_id: str,
    limit: int = 5,
    ai_search: Optional[AISearchService] = None,
) -> Dict[str, Any]:
    """
    Find products visually similar to an existing product.
    
    Uses the stored image embedding of the product for similarity search.
    
    Args:
        product_id: The product ID to find similar items for
        limit: Maximum number of results
        ai_search: AISearchService instance
        
    Returns:
        Dictionary with similar products
    """
    try:
        if not ai_search:
            return {
                "success": False,
                "error": "Search service not available",
                "products": []
            }
        
        # Get the product's embedding
        source_product = await ai_search.get_document(product_id)
        
        if not source_product:
            return {
                "success": False,
                "error": f"Product {product_id} not found",
                "products": []
            }
        
        embedding = source_product.get("image_embedding")
        
        if not embedding:
            return {
                "success": False,
                "error": "Product does not have an image embedding",
                "products": []
            }
        
        # Perform vector search excluding the source product
        results = await ai_search.vector_search(
            vector=embedding,
            vector_field="image_embedding",
            filter=f"id ne '{product_id}'",
            top=limit
        )
        
        # Format results
        products = []
        for result in results:
            similarity = result.get("@search.score", 0)
            products.append({
                "id": result.get("id"),
                "name": result.get("name"),
                "price": result.get("price"),
                "category": result.get("category"),
                "rating": result.get("rating"),
                "image_url": result.get("image_url"),
                "similarity_score": round(similarity, 3),
            })
        
        return {
            "success": True,
            "source_product": {
                "id": source_product.get("id"),
                "name": source_product.get("name"),
                "image_url": source_product.get("image_url"),
            },
            "count": len(products),
            "similar_products": products,
            "message": f"Found {len(products)} products similar to {source_product.get('name')}."
        }
        
    except Exception as e:
        logger.error(f"Similar products search error: {e}")
        return {
            "success": False,
            "error": str(e),
            "products": []
        }
