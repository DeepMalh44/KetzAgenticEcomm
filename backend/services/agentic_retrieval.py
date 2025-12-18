"""
Agentic Retrieval Service for Azure AI Search.

This service uses Azure AI Search's Agentic Retrieval feature to provide
intelligent, LLM-powered search that can handle complex multi-part queries.

This is a SEPARATE service from ai_search.py and does NOT modify existing search functionality.
"""

import os
import logging
import httpx
from typing import Optional, List, Dict, Any
from config.settings import settings

logger = logging.getLogger(__name__)


class AgenticRetrievalService:
    """
    Service for interacting with Azure AI Search's Agentic Retrieval feature.
    
    Agentic Retrieval uses a Knowledge Base that:
    1. Decomposes complex queries into subqueries
    2. Runs subqueries in parallel against the search index
    3. Reranks results for relevance
    4. Returns structured data for product display
    """
    
    def __init__(self):
        """Initialize the Agentic Retrieval Service."""
        self.search_endpoint = settings.azure_search_endpoint
        self.search_key = settings.azure_search_key
        self.knowledge_base_name = getattr(settings, 'knowledge_base_name', 'products-kb')
        self.knowledge_source_name = getattr(settings, 'knowledge_source_name', 'products-ks')
        self.api_version = "2025-11-01-preview"
        
        # HTTP client for API calls
        self.http_client = httpx.AsyncClient(timeout=30.0)
        
        logger.info(f"AgenticRetrievalService initialized with KB: {self.knowledge_base_name}")
    
    def _get_headers(self) -> Dict[str, str]:
        """Get headers for Azure AI Search API calls."""
        return {
            "Content-Type": "application/json",
            "api-key": self.search_key
        }
    
    async def search(
        self,
        query: str,
        chat_history: Optional[List[Dict[str, str]]] = None,
        top: int = 20,
        include_activity: bool = False
    ) -> Dict[str, Any]:
        """
        Perform an agentic retrieval search.
        
        Args:
            query: The user's search query (can be complex/conversational)
            chat_history: Optional chat history for context
            top: Maximum number of results to return
            include_activity: Whether to include query plan details
            
        Returns:
            Dictionary containing products and optional activity information
        """
        try:
            url = f"{self.search_endpoint}/knowledgebases/{self.knowledge_base_name}/retrieve?api-version={self.api_version}"
            
            # Build messages array
            messages = []
            
            # Add chat history if provided (for conversational context)
            if chat_history:
                for msg in chat_history[-5:]:  # Last 5 messages for context
                    messages.append({
                        "role": msg.get("role", "user"),
                        "content": [{"type": "text", "text": msg.get("content", "")}]
                    })
            
            # Add the current query
            messages.append({
                "role": "user",
                "content": [{"type": "text", "text": query}]
            })
            
            # Build the retrieve request
            # Note: API 2025-11-01-preview requires 'kind' parameter and doesn't support 'maxResults'
            request_body = {
                "messages": messages,
                "knowledgeSourceParams": [
                    {
                        "kind": "searchIndex",
                        "knowledgeSourceName": self.knowledge_source_name,
                        "includeReferences": True,
                        "includeReferenceSourceData": True
                    }
                ],
                "includeActivity": include_activity
            }
            
            logger.info(f"Agentic retrieval query: {query[:100]}...")
            
            response = await self.http_client.post(
                url,
                headers=self._get_headers(),
                json=request_body
            )
            
            # 200 = full success, 206 = partial content (some knowledge sources failed)
            if response.status_code not in [200, 206]:
                logger.error(f"Agentic retrieval failed: {response.status_code} - {response.text}")
                return {
                    "products": [],
                    "error": f"Search failed with status {response.status_code}",
                    "total": 0
                }
            
            if response.status_code == 206:
                logger.warning("Agentic retrieval returned partial content (some knowledge sources may have failed)")
            
            result = response.json()
            
            # Parse the response and extract products
            products = self._parse_response(result)
            
            response_data = {
                "products": products,
                "total": len(products),
                "query": query
            }
            
            # Include activity/query plan if requested
            if include_activity and "activity" in result:
                response_data["activity"] = result["activity"]
            
            # Include the LLM-generated response if available
            if "response" in result and result["response"]:
                for resp in result["response"]:
                    if "content" in resp:
                        for content in resp["content"]:
                            if content.get("type") == "text":
                                response_data["llm_response"] = content.get("text", "")
                                break
            
            logger.info(f"Agentic retrieval returned {len(products)} products")
            return response_data
            
        except Exception as e:
            logger.error(f"Agentic retrieval error: {str(e)}")
            return {
                "products": [],
                "error": str(e),
                "total": 0
            }
    
    def _parse_response(self, result: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Parse the agentic retrieval response and extract product data.
        
        The response contains references with source data that maps to our product schema.
        """
        products = []
        seen_ids = set()  # Deduplicate by product ID
        
        try:
            references = result.get("references", [])
            
            for ref in references:
                source_data = ref.get("sourceData", {})
                
                # Extract the product ID
                product_id = source_data.get("id")
                if not product_id or product_id in seen_ids:
                    continue
                
                seen_ids.add(product_id)
                
                # Map to our product schema
                product = {
                    "id": product_id,
                    "name": source_data.get("name", ""),
                    "description": source_data.get("description", ""),
                    "category": source_data.get("category", ""),
                    "subcategory": source_data.get("subcategory", ""),
                    "brand": source_data.get("brand", ""),
                    "sku": source_data.get("sku", ""),
                    "price": source_data.get("price", 0),
                    "sale_price": source_data.get("sale_price"),
                    "rating": source_data.get("rating", 0),
                    "review_count": source_data.get("review_count", 0),
                    "in_stock": source_data.get("in_stock", True),
                    "featured": source_data.get("featured", False),
                    "image_url": source_data.get("image_url", ""),
                    # Include relevance score if available
                    "relevance_score": ref.get("score", 0)
                }
                
                products.append(product)
            
            # Sort by relevance score (descending)
            products.sort(key=lambda x: x.get("relevance_score", 0), reverse=True)
            
        except Exception as e:
            logger.error(f"Error parsing agentic response: {str(e)}")
        
        return products
    
    async def get_answer(
        self,
        query: str,
        chat_history: Optional[List[Dict[str, str]]] = None
    ) -> Dict[str, Any]:
        """
        Get a natural language answer using answer synthesis mode.
        
        This is useful for chat interfaces where you want the LLM to
        formulate a complete answer rather than just returning products.
        
        Args:
            query: The user's question
            chat_history: Optional chat history for context
            
        Returns:
            Dictionary with answer text and supporting products
        """
        # For answer synthesis, we include activity to get the full response
        result = await self.search(
            query=query,
            chat_history=chat_history,
            top=10,
            include_activity=True
        )
        
        return {
            "answer": result.get("llm_response", "I couldn't find relevant information for your query."),
            "products": result.get("products", []),
            "activity": result.get("activity"),
            "query": query
        }
    
    async def health_check(self) -> bool:
        """Check if the agentic retrieval service is available."""
        try:
            url = f"{self.search_endpoint}/knowledgebases/{self.knowledge_base_name}?api-version={self.api_version}"
            response = await self.http_client.get(url, headers=self._get_headers())
            return response.status_code == 200
        except Exception as e:
            logger.error(f"Agentic retrieval health check failed: {str(e)}")
            return False
    
    async def close(self):
        """Close the HTTP client."""
        await self.http_client.aclose()


# Singleton instance
_agentic_service: Optional[AgenticRetrievalService] = None


def get_agentic_service() -> AgenticRetrievalService:
    """Get or create the singleton AgenticRetrievalService instance."""
    global _agentic_service
    if _agentic_service is None:
        _agentic_service = AgenticRetrievalService()
    return _agentic_service
