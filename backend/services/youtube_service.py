"""
YouTube DIY Video Service
=========================

Searches YouTube for DIY tutorial videos related to products.
Uses YouTube Data API v3 to find highly-viewed, recent tutorials.
"""

from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import asyncio
from concurrent.futures import ThreadPoolExecutor
import structlog
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from config.settings import settings

logger = structlog.get_logger(__name__)

# Thread pool for running synchronous YouTube API calls
_executor = ThreadPoolExecutor(max_workers=3)


class YouTubeService:
    """Service for searching YouTube DIY tutorial videos."""
    
    def __init__(self):
        """Initialize YouTube API client."""
        self.api_key = settings.youtube_api_key
        self.youtube = None
        print(f"[YOUTUBE SERVICE] Initializing with API key: {self.api_key[:20]}..." if self.api_key else "[YOUTUBE SERVICE] No API key!")
        if self.api_key:
            try:
                self.youtube = build('youtube', 'v3', developerKey=self.api_key)
                print("[YOUTUBE SERVICE] Successfully built YouTube client")
                logger.info("YouTube service initialized")
            except Exception as e:
                print(f"[YOUTUBE SERVICE] Failed to build client: {e}")
                logger.warning("Failed to initialize YouTube service", error=str(e))
    
    async def search_diy_videos(
        self,
        product_name: str,
        category: Optional[str] = None,
        max_results: int = 3
    ) -> List[Dict[str, Any]]:
        """
        Search for DIY tutorial videos related to a product.
        
        Args:
            product_name: Name of the product to find tutorials for
            category: Optional product category for better search context
            max_results: Maximum number of videos to return (default 3)
            
        Returns:
            List of video dictionaries with id, title, url, thumbnail, view_count, channel_name
        """
        if not self.youtube:
            print("[YOUTUBE SERVICE] YouTube client is None, returning empty")
            logger.warning("YouTube service not available")
            return []
        
        try:
            # Build search query for DIY/installation content
            search_query = self._build_search_query(product_name, category)
            print(f"[YOUTUBE SERVICE] Searching with query: {search_query}")
            logger.info("Searching YouTube for DIY videos", query=search_query)
            
            # Run synchronous YouTube API call in thread pool
            loop = asyncio.get_event_loop()
            videos = await loop.run_in_executor(
                _executor,
                self._search_videos_sync,
                search_query,
                max_results
            )
            
            print(f"[YOUTUBE SERVICE] Found {len(videos)} videos")
            return videos
            
        except Exception as e:
            print(f"[YOUTUBE SERVICE] Error: {e}")
            logger.error("YouTube search failed", error=str(e))
            return []
    
    def _search_videos_sync(self, search_query: str, max_results: int) -> List[Dict[str, Any]]:
        """Synchronous method to search YouTube - runs in thread pool."""
        try:
            # Calculate date 3 years ago for filtering recent content
            three_years_ago = (datetime.utcnow() - timedelta(days=3*365)).isoformat() + "Z"
            
            print(f"[YOUTUBE SERVICE SYNC] Executing search API call...")
            # Search for videos
            search_response = self.youtube.search().list(
                q=search_query,
                part='snippet',
                type='video',
                order='viewCount',  # Sort by view count for popular videos
                publishedAfter=three_years_ago,  # Only videos from last 3 years
                maxResults=max_results * 2,  # Fetch extra to filter
                relevanceLanguage='en',
                videoDuration='any',  # Allow any duration
                safeSearch='strict'
            ).execute()
            
            video_ids = [item['id']['videoId'] for item in search_response.get('items', [])]
            print(f"[YOUTUBE SERVICE SYNC] Found {len(video_ids)} video IDs")
            
            if not video_ids:
                return []
            
            # Get video statistics (view counts)
            print(f"[YOUTUBE SERVICE SYNC] Getting video stats...")
            videos_response = self.youtube.videos().list(
                part='statistics,snippet',
                id=','.join(video_ids)
            ).execute()
            
            # Process and filter videos
            videos = []
            for item in videos_response.get('items', []):
                view_count = int(item['statistics'].get('viewCount', 0))
                
                # Filter for videos with at least 10K views
                if view_count < 10000:
                    continue
                
                video_data = {
                    'video_id': item['id'],
                    'title': item['snippet']['title'],
                    'url': f"https://www.youtube.com/watch?v={item['id']}",
                    'thumbnail_url': item['snippet']['thumbnails'].get('medium', {}).get('url', 
                                     item['snippet']['thumbnails'].get('default', {}).get('url', '')),
                    'view_count': view_count,
                    'view_count_formatted': self._format_view_count(view_count),
                    'channel_name': item['snippet']['channelTitle'],
                    'published_date': item['snippet']['publishedAt'][:10]  # YYYY-MM-DD
                }
                videos.append(video_data)
            
            # Sort by view count and return top results
            videos.sort(key=lambda x: x['view_count'], reverse=True)
            result = videos[:max_results]
            
            print(f"[YOUTUBE SERVICE SYNC] Returning {len(result)} videos after filtering")
            return result
            
        except HttpError as e:
            print(f"[YOUTUBE SERVICE SYNC] HTTP Error: {e}")
            logger.error("YouTube API error", error=str(e))
            return []
        except Exception as e:
            print(f"[YOUTUBE SERVICE SYNC] Error: {e}")
            logger.error("YouTube search sync failed", error=str(e))
            return []
    
    def _build_search_query(self, product_name: str, category: Optional[str] = None) -> str:
        """Build an optimized search query for DIY tutorials."""
        # Clean up product name
        clean_name = product_name.lower().strip()
        
        # Category-specific query patterns
        category_patterns = {
            'hvac': 'how to install replace {} DIY tutorial',
            'plumbing': 'how to install {} DIY plumbing tutorial',
            'flooring': 'how to install {} DIY flooring tutorial',
            'electrical': 'how to install {} DIY electrical tutorial',
            'paint': 'how to use {} painting tutorial DIY',
            'outdoor_garden': 'how to install {} DIY outdoor tutorial',
            'kitchen_bath': 'how to install {} DIY tutorial',
            'lighting': 'how to install {} DIY lighting tutorial',
            'appliances': 'how to install {} DIY appliance tutorial',
        }
        
        # Use category-specific pattern if available
        if category and category.lower() in category_patterns:
            pattern = category_patterns[category.lower()]
        else:
            # Default pattern
            pattern = 'how to install {} DIY tutorial'
        
        return pattern.format(clean_name)
    
    def _format_view_count(self, count: int) -> str:
        """Format view count for display (e.g., 1.2M, 500K)."""
        if count >= 1_000_000:
            return f"{count / 1_000_000:.1f}M views"
        elif count >= 1_000:
            return f"{count / 1_000:.0f}K views"
        else:
            return f"{count} views"


# Singleton instance
_youtube_service: Optional[YouTubeService] = None


def get_youtube_service() -> YouTubeService:
    """Get or create YouTube service instance."""
    global _youtube_service
    if _youtube_service is None:
        _youtube_service = YouTubeService()
    return _youtube_service
