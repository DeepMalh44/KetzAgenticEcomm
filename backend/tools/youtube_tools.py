"""
YouTube Tools for Shopping Concierge Agent
==========================================

Provides DIY video search functionality for the voice assistant.
"""

from typing import Optional, List, Dict, Any
import structlog

from services.youtube_service import get_youtube_service

logger = structlog.get_logger(__name__)


async def get_diy_videos(
    product_name: str,
    category: Optional[str] = None,
    max_results: int = 3
) -> Dict[str, Any]:
    """
    Search for DIY tutorial videos related to a product.
    
    This tool finds highly-viewed YouTube tutorials that show how to
    install, replace, or use products. Useful for home improvement
    items like HVAC filters, flooring, plumbing fixtures, etc.
    
    Args:
        product_name: Name of the product (e.g., "HVAC air filter", "vinyl plank flooring")
        category: Optional product category for better search results
        max_results: Number of videos to return (default 3)
        
    Returns:
        Dictionary with videos list and a voice-friendly summary
    """
    print(f"[YOUTUBE TOOLS] get_diy_videos called: product={product_name}, category={category}")
    logger.info("Getting DIY videos", product=product_name, category=category)
    
    try:
        youtube_service = get_youtube_service()
        print(f"[YOUTUBE TOOLS] Service initialized: {youtube_service is not None}, youtube client: {youtube_service.youtube is not None}")
        videos = await youtube_service.search_diy_videos(
            product_name=product_name,
            category=category,
            max_results=max_results
        )
        print(f"[YOUTUBE TOOLS] Search returned {len(videos)} videos")
        
        if not videos:
            # Silent omission - return empty result without error
            print("[YOUTUBE TOOLS] No videos found, returning empty result")
            return {
                "found": 0,
                "videos": [],
                "summary": ""
            }
        
        # Create voice-friendly summary
        if len(videos) == 1:
            summary = f"I found a helpful DIY video: '{videos[0]['title']}' from {videos[0]['channel_name']} with {videos[0]['view_count_formatted']}."
        else:
            summary = f"I found {len(videos)} DIY tutorial videos for you. The most popular one is '{videos[0]['title']}' with {videos[0]['view_count_formatted']}."
        
        return {
            "found": len(videos),
            "videos": videos,
            "summary": summary
        }
        
    except Exception as e:
        logger.error("DIY video search failed", error=str(e))
        # Silent failure - return empty result
        return {
            "found": 0,
            "videos": [],
            "summary": ""
        }


# Tool definition for the GPT-4o Realtime API function calling
GET_DIY_VIDEOS_TOOL = {
    "type": "function",
    "name": "get_diy_videos",
    "description": """Search for DIY tutorial videos on YouTube related to a product. 
Use this tool when a user is looking at products that typically require installation or DIY work,
such as HVAC filters, flooring, plumbing fixtures, light fixtures, appliances, paint, etc.
Only call this when contextually relevant - don't use for every product search.
Returns popular, highly-viewed tutorial videos from the last 3 years.""",
    "parameters": {
        "type": "object",
        "properties": {
            "product_name": {
                "type": "string",
                "description": "The name of the product to find DIY tutorials for (e.g., 'HVAC air filter', 'vinyl plank flooring', 'bathroom faucet')"
            },
            "category": {
                "type": "string",
                "description": "Optional product category for better search results (e.g., 'hvac', 'flooring', 'plumbing', 'electrical', 'paint')"
            }
        },
        "required": ["product_name"]
    }
}
