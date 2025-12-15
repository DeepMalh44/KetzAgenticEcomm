# =============================================================================
# KetzAgenticEcomm - Product Tools
# =============================================================================
"""
Product-related tools for the voice assistant.
"""

import logging
from typing import Any, Dict, List, Optional

from services.ai_search import AISearchService
from services.cosmos_db import CosmosDBService

logger = logging.getLogger(__name__)


async def search_products(
    query: str,
    category: Optional[str] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    min_rating: Optional[float] = None,
    in_stock: bool = True,
    limit: int = 5,
    ai_search: Optional[AISearchService] = None,
) -> Dict[str, Any]:
    """
    Search for products using Azure AI Search.
    
    Args:
        query: Search query (e.g., "bathroom faucet chrome")
        category: Filter by category
        min_price: Minimum price filter
        max_price: Maximum price filter
        min_rating: Minimum rating filter
        in_stock: Only show in-stock items
        limit: Maximum number of results
        ai_search: AISearchService instance
        
    Returns:
        Dictionary with products and metadata
    """
    try:
        if not ai_search:
            return {
                "success": False,
                "error": "Search service not available",
                "products": []
            }
        
        # Build filters
        filters = []
        if category:
            filters.append(f"category eq '{category}'")
        if min_price is not None:
            filters.append(f"price ge {min_price}")
        if max_price is not None:
            filters.append(f"price le {max_price}")
        if min_rating is not None:
            filters.append(f"rating ge {min_rating}")
        if in_stock:
            filters.append("stock_quantity gt 0")
        
        filter_str = " and ".join(filters) if filters else None
        
        # Perform search
        results = await ai_search.search_products(
            query=query,
            filter=filter_str,
            top=limit
        )
        
        # Format results for voice response
        products = []
        for result in results:
            products.append({
                "id": result.get("id"),
                "name": result.get("name"),
                "description": result.get("description"),
                "price": result.get("price"),
                "category": result.get("category"),
                "brand": result.get("brand"),
                "rating": result.get("rating"),
                "stock_quantity": result.get("stock_quantity"),
                "image_url": result.get("image_url"),
                "sku": result.get("sku"),
            })
        
        return {
            "success": True,
            "count": len(products),
            "products": products,
            "query": query,
            "filters_applied": {
                "category": category,
                "price_range": [min_price, max_price] if min_price or max_price else None,
                "min_rating": min_rating,
                "in_stock_only": in_stock
            }
        }
        
    except Exception as e:
        logger.error(f"Product search error: {e}")
        return {
            "success": False,
            "error": str(e),
            "products": []
        }


async def get_product_details(
    product_id: str,
    cosmos_db: Optional[CosmosDBService] = None,
) -> Dict[str, Any]:
    """
    Get detailed information about a specific product.
    
    Args:
        product_id: The product ID
        cosmos_db: CosmosDBService instance
        
    Returns:
        Dictionary with product details
    """
    try:
        if not cosmos_db:
            return {
                "success": False,
                "error": "Database service not available"
            }
        
        product = await cosmos_db.get_product(product_id)
        
        if not product:
            return {
                "success": False,
                "error": f"Product {product_id} not found"
            }
        
        return {
            "success": True,
            "product": {
                "id": product.get("id"),
                "name": product.get("name"),
                "description": product.get("description"),
                "detailed_description": product.get("detailed_description"),
                "price": product.get("price"),
                "category": product.get("category"),
                "subcategory": product.get("subcategory"),
                "brand": product.get("brand"),
                "rating": product.get("rating"),
                "review_count": product.get("review_count"),
                "stock_quantity": product.get("stock_quantity"),
                "specifications": product.get("specifications", {}),
                "features": product.get("features", []),
                "image_url": product.get("image_url"),
                "sku": product.get("sku"),
                "warranty": product.get("warranty"),
                "dimensions": product.get("dimensions"),
                "weight": product.get("weight"),
            }
        }
        
    except Exception as e:
        logger.error(f"Get product details error: {e}")
        return {
            "success": False,
            "error": str(e)
        }


async def get_recommendations(
    product_id: Optional[str] = None,
    category: Optional[str] = None,
    user_history: Optional[List[str]] = None,
    limit: int = 5,
    cosmos_db: Optional[CosmosDBService] = None,
    ai_search: Optional[AISearchService] = None,
) -> Dict[str, Any]:
    """
    Get product recommendations based on context.
    
    Args:
        product_id: Base product for "similar items"
        category: Category to recommend from
        user_history: List of previously viewed product IDs
        limit: Maximum recommendations
        cosmos_db: CosmosDBService instance
        ai_search: AISearchService instance
        
    Returns:
        Dictionary with recommended products
    """
    try:
        recommendations = []
        
        # If product_id is provided, find similar products
        if product_id and cosmos_db and ai_search:
            product = await cosmos_db.get_product(product_id)
            if product:
                # Use the product name and category for similarity search
                query = f"{product.get('name')} {product.get('category')}"
                results = await ai_search.search_products(
                    query=query,
                    filter=f"id ne '{product_id}'",
                    top=limit
                )
                recommendations = results
        
        # If category is provided, get top-rated in category
        elif category and ai_search:
            results = await ai_search.search_products(
                query=category,
                filter=f"category eq '{category}'",
                top=limit,
                order_by="rating desc"
            )
            recommendations = results
        
        # General recommendations
        elif ai_search:
            results = await ai_search.search_products(
                query="popular best seller",
                top=limit,
                order_by="rating desc"
            )
            recommendations = results
        
        # Format results
        formatted = []
        for rec in recommendations:
            formatted.append({
                "id": rec.get("id"),
                "name": rec.get("name"),
                "price": rec.get("price"),
                "rating": rec.get("rating"),
                "category": rec.get("category"),
                "image_url": rec.get("image_url"),
            })
        
        return {
            "success": True,
            "count": len(formatted),
            "recommendations": formatted,
            "context": {
                "based_on_product": product_id,
                "category": category,
            }
        }
        
    except Exception as e:
        logger.error(f"Get recommendations error: {e}")
        return {
            "success": False,
            "error": str(e),
            "recommendations": []
        }
