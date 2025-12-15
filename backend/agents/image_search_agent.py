"""
Image Search Agent
===================

Handles visual similarity search using Azure AI Vision embeddings.
"""

from typing import Optional, List, Dict, Any
import structlog

logger = structlog.get_logger(__name__)


class ImageSearchAgent:
    """Agent for image-based product search."""
    
    def __init__(self, app_state):
        """Initialize the image search agent."""
        self.search = app_state.search
        self.vision = app_state.vision
        self.blob = app_state.blob
        logger.info("ImageSearchAgent initialized")
    
    async def search_similar(
        self,
        image_id: str,
        limit: int = 5,
        category: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Search for products visually similar to an uploaded image.
        
        Args:
            image_id: ID of a previously uploaded image
            limit: Maximum number of results
            category: Optional category filter
        """
        logger.info("Searching similar products", image_id=image_id, limit=limit)
        
        try:
            # Search using stored embedding
            results = await self.search.search_by_image_embedding(
                image_id=image_id,
                limit=limit,
                category=category
            )
            
            if not results:
                return {
                    "found": 0,
                    "products": [],
                    "summary": "I couldn't find any products similar to that image. Try uploading a clearer image or describing what you're looking for."
                }
            
            # Format results
            products = [
                {
                    "id": r["id"],
                    "name": r["name"],
                    "description": r.get("description", ""),
                    "category": r.get("category", ""),
                    "price": r.get("price", 0),
                    "image_url": r.get("image_url"),
                    "similarity_score": r.get("@search.score", 0)
                }
                for r in results
            ]
            
            # Create summary
            top_match = products[0]
            summary = f"I found {len(products)} products similar to your image. "
            summary += f"The best match is {top_match['name']} "
            summary += f"at ${top_match['price']:.2f}. "
            
            if len(products) > 1:
                other_names = [p["name"] for p in products[1:3]]
                summary += f"Other similar items include: {', '.join(other_names)}."
            
            return {
                "found": len(products),
                "image_id": image_id,
                "products": products,
                "summary": summary
            }
            
        except Exception as e:
            logger.error("Image search failed", error=str(e), image_id=image_id)
            return {
                "error": str(e),
                "summary": "I had trouble searching for similar products. Please try again."
            }
    
    async def search_by_text_for_image(
        self,
        query: str,
        limit: int = 5,
        category: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Search for products using text-to-image matching.
        
        Uses Vision API's text embedding to find visually similar products.
        """
        logger.info("Searching by text for images", query=query)
        
        try:
            # Get text embedding from Vision API
            text_embedding = await self.vision.get_text_embedding(query)
            
            # Search using the embedding against image_embedding field
            results = await self.search.search_by_vector(
                embedding=text_embedding,
                limit=limit,
                category=category,
                field_name="image_embedding"
            )
            
            if not results:
                return {
                    "found": 0,
                    "products": [],
                    "summary": f"I couldn't find products visually matching '{query}'. Try a different description."
                }
            
            products = [
                {
                    "id": r["id"],
                    "name": r["name"],
                    "description": r.get("description", ""),
                    "price": r.get("price", 0),
                    "image_url": r.get("image_url"),
                    "similarity_score": r.get("@search.score", 0)
                }
                for r in results
            ]
            
            summary = f"I found {len(products)} products that visually match '{query}'. "
            summary += f"Top result: {products[0]['name']} at ${products[0]['price']:.2f}."
            
            return {
                "found": len(products),
                "query": query,
                "products": products,
                "summary": summary
            }
            
        except Exception as e:
            logger.error("Text-to-image search failed", error=str(e))
            return {
                "error": str(e),
                "summary": "I had trouble with the visual search. Please try again."
            }
    
    async def analyze_uploaded_image(
        self,
        image_id: str
    ) -> Dict[str, Any]:
        """
        Analyze an uploaded image to describe what's in it.
        
        Useful for helping users understand what they've uploaded.
        """
        logger.info("Analyzing uploaded image", image_id=image_id)
        
        try:
            # Download image from blob storage
            blob_name = f"uploads/{image_id}"
            
            # Try different extensions
            image_data = None
            for ext in [".jpg", ".jpeg", ".png", ".webp"]:
                image_data = await self.blob.download_image(blob_name + ext)
                if image_data:
                    break
            
            if not image_data:
                return {
                    "success": False,
                    "summary": "I couldn't find the uploaded image. Please upload it again."
                }
            
            # Analyze with Vision API
            analysis = await self.vision.analyze_image(image_data)
            
            # Create summary
            caption = analysis.get("caption", "an image")
            tags = [t["name"] for t in analysis.get("tags", [])[:5]]
            
            summary = f"I see {caption}. "
            if tags:
                summary += f"Key features: {', '.join(tags)}. "
            summary += "Would you like me to find similar products?"
            
            return {
                "success": True,
                "image_id": image_id,
                "caption": caption,
                "confidence": analysis.get("confidence", 0),
                "tags": analysis.get("tags", []),
                "objects": analysis.get("objects", []),
                "summary": summary
            }
            
        except Exception as e:
            logger.error("Image analysis failed", error=str(e))
            return {
                "success": False,
                "error": str(e),
                "summary": "I had trouble analyzing that image. Please try again."
            }
    
    async def find_products_from_photo(
        self,
        image_data: bytes,
        limit: int = 5,
        category: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Direct image search - takes raw image data and finds similar products.
        
        Combines image analysis and search in one step.
        """
        logger.info("Finding products from photo")
        
        try:
            # Get image embedding
            embedding = await self.vision.get_image_embedding(image_data)
            
            # Search for similar products
            results = await self.search.search_by_vector(
                embedding=embedding,
                limit=limit,
                category=category,
                field_name="image_embedding"
            )
            
            # Also analyze the image for context
            try:
                analysis = await self.vision.analyze_image(image_data)
                caption = analysis.get("caption", "")
                tags = [t["name"] for t in analysis.get("tags", [])[:3]]
            except:
                caption = ""
                tags = []
            
            if not results:
                summary = "I couldn't find products matching that image. "
                if caption:
                    summary += f"I see {caption}. "
                summary += "Try describing what you're looking for instead."
                
                return {
                    "found": 0,
                    "products": [],
                    "analysis": {"caption": caption, "tags": tags},
                    "summary": summary
                }
            
            products = [
                {
                    "id": r["id"],
                    "name": r["name"],
                    "description": r.get("description", ""),
                    "category": r.get("category", ""),
                    "price": r.get("price", 0),
                    "image_url": r.get("image_url"),
                    "similarity_score": r.get("@search.score", 0)
                }
                for r in results
            ]
            
            summary = ""
            if caption:
                summary = f"I see {caption}. "
            summary += f"Here are {len(products)} matching products. "
            summary += f"Best match: {products[0]['name']} at ${products[0]['price']:.2f}."
            
            return {
                "found": len(products),
                "products": products,
                "analysis": {"caption": caption, "tags": tags},
                "summary": summary
            }
            
        except Exception as e:
            logger.error("Find products from photo failed", error=str(e))
            return {
                "error": str(e),
                "summary": "I had trouble processing that image. Please try again or describe what you're looking for."
            }
