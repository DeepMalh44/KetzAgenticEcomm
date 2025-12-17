"""
Search Analytics Service
========================

Sends search telemetry to Azure Application Insights for traffic analytics.
This enables tracking of:
- Search queries and result counts
- Click-through events (which products users click on)
- Session correlation for search-to-click analysis

Based on: https://github.com/Azure-Samples/azure-search-traffic-analytics
"""

import uuid
from typing import Optional, Dict, Any, List
from datetime import datetime
import structlog
from opencensus.ext.azure.log_exporter import AzureLogHandler
from opencensus.ext.azure import metrics_exporter
from applicationinsights import TelemetryClient

logger = structlog.get_logger(__name__)


class SearchAnalyticsService:
    """
    Service for tracking search analytics to Application Insights.
    
    Tracks custom events:
    - "Search": When a user performs a search
    - "Click": When a user clicks on a search result
    """
    
    def __init__(self, connection_string: Optional[str] = None):
        """
        Initialize the search analytics service.
        
        Args:
            connection_string: Application Insights connection string.
                             If None, telemetry is disabled.
        """
        self.enabled = bool(connection_string)
        self.telemetry_client = None
        
        if self.enabled:
            try:
                self.telemetry_client = TelemetryClient(connection_string=connection_string)
                # Set cloud role for better identification in App Insights
                self.telemetry_client.context.cloud.role = "KetzAgenticEcomm-Backend"
                self.telemetry_client.context.cloud.role_instance = "search-api"
                logger.info("Search analytics enabled", 
                          endpoint=connection_string.split(";")[1] if ";" in connection_string else "unknown")
            except Exception as e:
                logger.warning("Failed to initialize telemetry client", error=str(e))
                self.enabled = False
        else:
            logger.info("Search analytics disabled - no connection string provided")
    
    def generate_search_id(self) -> str:
        """Generate a unique search ID for correlating searches with clicks."""
        return str(uuid.uuid4())
    
    def track_search(
        self,
        search_id: str,
        query: str,
        results_count: int,
        index_name: str = "products",
        category: Optional[str] = None,
        min_price: Optional[float] = None,
        max_price: Optional[float] = None,
        sort_by: Optional[str] = None,
        duration_ms: Optional[float] = None,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None
    ):
        """
        Track a search event in Application Insights.
        
        Args:
            search_id: Unique ID for this search (used to correlate with clicks)
            query: The search query text
            results_count: Number of results returned
            index_name: Name of the search index
            category: Category filter if applied
            min_price: Min price filter if applied
            max_price: Max price filter if applied
            sort_by: Sort field if applied
            duration_ms: Search duration in milliseconds
            user_id: User ID if available
            session_id: Session ID if available
        """
        if not self.enabled:
            return
        
        try:
            properties = {
                "SearchId": search_id,
                "SearchServiceName": "search-ketzagentic-kh7xm2",
                "IndexName": index_name,
                "QueryTerms": query,
                "ResultCount": str(results_count),
                "ScoringProfile": "",  # Not using scoring profiles
            }
            
            # Add optional filters
            if category:
                properties["CategoryFilter"] = category
            if min_price is not None:
                properties["MinPriceFilter"] = str(min_price)
            if max_price is not None:
                properties["MaxPriceFilter"] = str(max_price)
            if sort_by:
                properties["SortBy"] = sort_by
            if user_id:
                properties["UserId"] = user_id
            if session_id:
                properties["SessionId"] = session_id
            
            # Add metrics
            measurements = {}
            if duration_ms is not None:
                measurements["SearchDurationMs"] = duration_ms
            measurements["ResultCount"] = float(results_count)
            
            # Track the search event
            self.telemetry_client.track_event("Search", properties, measurements)
            
            logger.debug("Tracked search event", 
                        search_id=search_id, 
                        query=query, 
                        results=results_count)
            
        except Exception as e:
            logger.error("Failed to track search event", error=str(e), query=query)
    
    def track_click(
        self,
        search_id: str,
        clicked_doc_id: str,
        rank: int,
        query: Optional[str] = None,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None
    ):
        """
        Track a click event when user clicks on a search result.
        
        Args:
            search_id: The search ID from the original search (for correlation)
            clicked_doc_id: The document/product ID that was clicked
            rank: The position of the clicked result (1-based)
            query: The original search query (optional, for context)
            user_id: User ID if available
            session_id: Session ID if available
        """
        if not self.enabled:
            return
        
        try:
            properties = {
                "SearchId": search_id,
                "ClickedDocId": clicked_doc_id,
                "Rank": str(rank),
                "SearchServiceName": "search-ketzagentic-kh7xm2",
                "IndexName": "products",
            }
            
            if query:
                properties["QueryTerms"] = query
            if user_id:
                properties["UserId"] = user_id
            if session_id:
                properties["SessionId"] = session_id
            
            measurements = {
                "Rank": float(rank)
            }
            
            # Track the click event
            self.telemetry_client.track_event("Click", properties, measurements)
            
            logger.debug("Tracked click event", 
                        search_id=search_id, 
                        product_id=clicked_doc_id, 
                        rank=rank)
            
        except Exception as e:
            logger.error("Failed to track click event", error=str(e), doc_id=clicked_doc_id)
    
    def track_add_to_cart(
        self,
        search_id: Optional[str],
        product_id: str,
        product_name: str,
        quantity: int = 1,
        price: Optional[float] = None,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None
    ):
        """
        Track an add-to-cart event.
        
        Args:
            search_id: The search ID if this came from a search result
            product_id: The product ID added to cart
            product_name: The product name
            quantity: Quantity added
            price: Product price
            user_id: User ID if available
            session_id: Session ID if available
        """
        if not self.enabled:
            return
        
        try:
            properties = {
                "ProductId": product_id,
                "ProductName": product_name,
                "Quantity": str(quantity),
            }
            
            if search_id:
                properties["SearchId"] = search_id
            if user_id:
                properties["UserId"] = user_id
            if session_id:
                properties["SessionId"] = session_id
            
            measurements = {
                "Quantity": float(quantity)
            }
            if price is not None:
                measurements["Price"] = price
                measurements["TotalValue"] = price * quantity
            
            self.telemetry_client.track_event("AddToCart", properties, measurements)
            
            logger.debug("Tracked add-to-cart event", 
                        product_id=product_id, 
                        quantity=quantity)
            
        except Exception as e:
            logger.error("Failed to track add-to-cart event", error=str(e))
    
    def flush(self):
        """Flush any pending telemetry to Application Insights."""
        if self.enabled and self.telemetry_client:
            try:
                self.telemetry_client.flush()
            except Exception as e:
                logger.error("Failed to flush telemetry", error=str(e))
    
    def close(self):
        """Close the telemetry client and flush remaining data."""
        self.flush()


# Singleton instance for convenience
_analytics_service: Optional[SearchAnalyticsService] = None


def get_analytics_service() -> Optional[SearchAnalyticsService]:
    """Get the global analytics service instance."""
    return _analytics_service


def init_analytics_service(connection_string: Optional[str] = None) -> SearchAnalyticsService:
    """Initialize the global analytics service."""
    global _analytics_service
    _analytics_service = SearchAnalyticsService(connection_string)
    return _analytics_service
