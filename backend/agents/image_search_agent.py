"""
Image Search Agent
===================

Handles visual similarity search using GPT-4o Vision and semantic search.
"""

from typing import Optional, Dict, Any
import structlog
import base64
import httpx
from azure.identity import DefaultAzureCredential

logger = structlog.get_logger(__name__)


class ImageSearchAgent:
    """Agent for image-based product search using GPT-4o Vision."""
    
    def __init__(self, app_state, openai_endpoint: str = None):
        """Initialize the image search agent."""
        self.search = app_state.search
        self.blob = app_state.blob
        self.openai_endpoint = openai_endpoint
        logger.info("ImageSearchAgent initialized with GPT-4o Vision")
    
    async def analyze_image(self, image_data: bytes) -> str:
        """
        Use GPT-4o Vision to analyze the image and generate a product description.
        """
        if not self.openai_endpoint:
            raise ValueError("OpenAI endpoint not configured")
            
        # Encode image as base64
        image_base64 = base64.b64encode(image_data).decode("utf-8")
        
        # Get Azure AD token
        credential = DefaultAzureCredential()
        token = credential.get_token("https://cognitiveservices.azure.com/.default")
        
        headers = {
            "Authorization": f"Bearer {token.token}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "messages": [
                {
                    "role": "system",
                    "content": """You are a product identification expert for a home improvement store. 
                    Analyze the image and describe the product in detail for search purposes.
                    Focus on: product type, category, style, color, material, brand (if visible).
                    Be concise but descriptive.
                    Just provide the description, no explanations."""
                },
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": "Describe this product:"},
                        {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_base64}"}}
                    ]
                }
            ],
            "max_tokens": 200
        }
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            url = f"{self.openai_endpoint}/openai/deployments/gpt-4o/chat/completions?api-version=2024-02-15-preview"
            response = await client.post(url, headers=headers, json=payload)
            response.raise_for_status()
            
            result = response.json()
            description = result["choices"][0]["message"]["content"].strip().strip('"').strip("'")
            logger.info("Image analyzed", description=description[:100])
            return description
    
    async def search_by_image(
        self,
        image_data: bytes,
        limit: int = 5,
        category: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Search for products similar to an uploaded image.
        
        Args:
            image_data: Raw image bytes
            limit: Maximum number of results
            category: Optional category filter
        """
        logger.info("Searching by image", limit=limit, category=category)
        
        try:
            # Step 1: Analyze image with GPT-4o Vision
            image_description = await self.analyze_image(image_data)
            
            # Step 2: Semantic search with the description
            results = await self.search.search_products(
                query=image_description,
                category=category,
                limit=limit,
                use_semantic=True
            )
            
            if not results:
                return {
                    "found": 0,
                    "products": [],
                    "image_description": image_description,
                    "summary": "I couldn't find any products matching that image. Try a different image or describe what you're looking for."
                }
            
            # Format results
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
                    "similarity_score": r.get("@search.score", 0)
                }
                for r in results
            ]
            
            # Create summary
            top_match = products[0]
            summary = f"I found {len(products)} products matching your image. The best match is {top_match['name']} at ${top_match['price']:.2f}."
            
            return {
                "found": len(products),
                "products": products,
                "image_description": image_description,
                "summary": summary
            }
            
        except Exception as e:
            logger.error("Image search failed", error=str(e))
            return {
                "found": 0,
                "products": [],
                "error": str(e),
                "summary": f"Sorry, I encountered an error while searching: {str(e)}"
            }
    
    async def find_similar_products(
        self,
        product_id: str,
        limit: int = 5
    ) -> Dict[str, Any]:
        """
        Find products similar to an existing product.
        
        Args:
            product_id: ID of the source product
            limit: Maximum number of results
        """
        logger.info("Finding similar products", product_id=product_id)
        
        try:
            # Get source product
            source = await self.search.get_document(product_id)
            if not source:
                return {
                    "found": 0,
                    "products": [],
                    "error": f"Product {product_id} not found"
                }
            
            # Search using product description
            query = f"{source.get('name', '')} {source.get('description', '')}"
            results = await self.search.search_products(
                query=query,
                category=source.get('category'),
                limit=limit + 1,
                use_semantic=True
            )
            
            # Filter out source product
            products = [
                {
                    "id": r["id"],
                    "name": r["name"],
                    "price": r.get("price", 0),
                    "category": r.get("category", ""),
                    "image_url": r.get("image_url"),
                    "similarity_score": r.get("@search.score", 0)
                }
                for r in results if r["id"] != product_id
            ][:limit]
            
            return {
                "source_product": source.get("name"),
                "found": len(products),
                "products": products,
                "summary": f"Found {len(products)} products similar to {source.get('name')}."
            }
            
        except Exception as e:
            logger.error("Similar product search failed", error=str(e))
            return {
                "found": 0,
                "products": [],
                "error": str(e)
            }
