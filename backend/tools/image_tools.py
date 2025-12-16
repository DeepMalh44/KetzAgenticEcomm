# =============================================================================
# KetzAgenticEcomm - Image Search Tools
# =============================================================================
"""
Image-based search tools for the voice assistant.
Uses GPT-4o Vision for image understanding and semantic search for matching.
"""

import logging
import base64
import httpx
from typing import Any, Dict, Optional

from services.ai_search import AISearchService
from services.blob_storage import BlobStorageService
from azure.identity import DefaultAzureCredential

logger = logging.getLogger(__name__)


async def analyze_image_with_gpt4o(image_data: bytes, openai_endpoint: str) -> str:
    """
    Use GPT-4o Vision to analyze the image and generate a product description.
    
    Args:
        image_data: Raw image bytes
        openai_endpoint: Azure OpenAI endpoint
        
    Returns:
        Product description string
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
        logger.info(f"GPT-4o image analysis: {description[:100]}")
        return description


async def search_by_image(
    image_data: bytes,
    content_type: str = "image/jpeg",
    category: Optional[str] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    limit: int = 5,
    openai_endpoint: Optional[str] = None,
    ai_search: Optional[AISearchService] = None,
    blob_storage: Optional[BlobStorageService] = None,
) -> Dict[str, Any]:
    """
    Search for products similar to an uploaded image.
    
    Uses GPT-4o Vision to understand the image, then performs
    semantic search to find similar products.
    
    Args:
        image_data: Raw image bytes
        content_type: MIME type of the image
        category: Optional category filter
        min_price: Optional minimum price filter
        max_price: Optional maximum price filter
        limit: Maximum number of results
        openai_endpoint: Azure OpenAI endpoint
        ai_search: AISearchService instance
        blob_storage: BlobStorageService instance
        
    Returns:
        Dictionary with similar products
    """
    try:
        if not openai_endpoint or not ai_search:
            return {
                "success": False,
                "error": "OpenAI or search service not available",
                "products": []
            }
        
        # Step 1: Use GPT-4o Vision to understand the image
        logger.info("Analyzing image with GPT-4o Vision...")
        image_description = await analyze_image_with_gpt4o(image_data, openai_endpoint)
        
        if not image_description:
            return {
                "success": False,
                "error": "Failed to analyze image",
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
        
        # Step 3: Perform semantic search with the description
        logger.info(f"Searching for: {image_description}")
        results = await ai_search.search_products(
            query=image_description,
            category=category,
            min_price=min_price,
            max_price=max_price,
            limit=limit,
            use_semantic=True
        )
        
        # Step 4: Format results
        products = []
        for result in results:
            score = result.get("@search.score", 0)
            products.append({
                "id": result.get("id"),
                "name": result.get("name"),
                "description": result.get("description"),
                "price": result.get("price"),
                "sale_price": result.get("sale_price"),
                "category": result.get("category"),
                "subcategory": result.get("subcategory"),
                "brand": result.get("brand"),
                "rating": result.get("rating", 0),
                "review_count": result.get("review_count", 0),
                "in_stock": result.get("in_stock", True),
                "image_url": result.get("image_url"),
                "sku": result.get("sku"),
                "similarity_score": round(score, 3),
            })
        
        return {
            "success": True,
            "count": len(products),
            "products": products,
            "image_description": image_description,
            "search_image_url": upload_url,
            "filters_applied": {
                "category": category,
                "price_range": [min_price, max_price] if min_price or max_price else None,
            },
            "message": f"Found {len(products)} products matching your image."
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
    openai_endpoint: Optional[str] = None,
    ai_search: Optional[AISearchService] = None,
) -> Dict[str, Any]:
    """
    Search for products similar to an image by URL.
    
    Args:
        image_url: URL of the image
        category: Optional category filter
        limit: Maximum number of results
        openai_endpoint: Azure OpenAI endpoint
        ai_search: AISearchService instance
        
    Returns:
        Dictionary with similar products
    """
    try:
        if not openai_endpoint or not ai_search:
            return {
                "success": False,
                "error": "OpenAI or search service not available",
                "products": []
            }
        
        # Fetch image from URL
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(image_url)
            if response.status_code != 200:
                return {
                    "success": False,
                    "error": f"Failed to fetch image: HTTP {response.status_code}",
                    "products": []
                }
            image_data = response.content
        
        # Use the main search function
        return await search_by_image(
            image_data=image_data,
            category=category,
            limit=limit,
            openai_endpoint=openai_endpoint,
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
    Find products similar to an existing product using text-based similarity.
    
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
        
        # Get the source product
        source_product = await ai_search.get_document(product_id)
        
        if not source_product:
            return {
                "success": False,
                "error": f"Product {product_id} not found",
                "products": []
            }
        
        # Use product name and description for similarity search
        query = f"{source_product.get('name', '')} {source_product.get('description', '')}"
        
        # Perform semantic search excluding the source product
        results = await ai_search.search_products(
            query=query,
            category=source_product.get('category'),
            limit=limit + 1,  # Get one extra to filter out source
            use_semantic=True
        )
        
        # Format results, excluding the source product
        products = []
        for result in results:
            if result.get("id") == product_id:
                continue
            if len(products) >= limit:
                break
                
            score = result.get("@search.score", 0)
            products.append({
                "id": result.get("id"),
                "name": result.get("name"),
                "price": result.get("price"),
                "category": result.get("category"),
                "rating": result.get("rating"),
                "image_url": result.get("image_url"),
                "similarity_score": round(score, 3),
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
