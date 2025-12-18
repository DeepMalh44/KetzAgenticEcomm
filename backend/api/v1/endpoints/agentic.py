"""
Agentic Retrieval API Endpoints
================================

This module provides API endpoints for Azure AI Search Agentic Retrieval.
These are SEPARATE endpoints from the existing semantic search in products.py.

Endpoints:
- POST /api/v1/agentic/search - Agentic retrieval search
- GET /api/v1/agentic/health - Health check for agentic retrieval
"""

import logging
from typing import Optional, List
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from services.agentic_retrieval import AgenticRetrievalService

logger = logging.getLogger(__name__)

router = APIRouter(tags=["agentic"])

# Initialize the agentic retrieval service
agentic_service = AgenticRetrievalService()


class ChatMessage(BaseModel):
    """Chat message for conversational context."""
    role: str = Field(..., description="Message role: 'user' or 'assistant'")
    content: str = Field(..., description="Message content")


class AgenticSearchRequest(BaseModel):
    """Request model for agentic retrieval search."""
    query: str = Field(..., description="The search query (can be complex/conversational)")
    chat_history: Optional[List[ChatMessage]] = Field(
        default=None, 
        description="Previous chat messages for conversational context"
    )
    top: int = Field(default=20, ge=1, le=50, description="Maximum results to return")
    include_activity: bool = Field(
        default=False, 
        description="Include query plan/activity details in response"
    )


class ProductResult(BaseModel):
    """Product result from agentic retrieval."""
    id: str
    name: str
    description: Optional[str] = None
    category: Optional[str] = None
    subcategory: Optional[str] = None
    brand: Optional[str] = None
    price: Optional[float] = None
    sale_price: Optional[float] = None
    rating: Optional[float] = None
    review_count: Optional[int] = None
    in_stock: Optional[bool] = None
    image_url: Optional[str] = None
    sku: Optional[str] = None


class AgenticSearchResponse(BaseModel):
    """Response model for agentic retrieval search."""
    products: List[dict] = Field(default_factory=list)
    total: int = Field(default=0)
    query: str = Field(default="")
    llm_response: Optional[str] = Field(
        default=None,
        description="LLM-generated response about the products"
    )
    activity: Optional[List[dict]] = Field(
        default=None,
        description="Query plan and execution details"
    )
    error: Optional[str] = None


@router.post("/search", response_model=AgenticSearchResponse)
async def agentic_search(request: AgenticSearchRequest):
    """
    Perform an agentic retrieval search.
    
    This endpoint uses Azure AI Search's Agentic Retrieval feature which:
    1. Decomposes complex queries into subqueries
    2. Runs subqueries in parallel
    3. Reranks results for relevance
    4. Can provide LLM-generated summaries
    
    Unlike the standard search endpoint, this can handle:
    - Complex multi-part queries ("I need tools for a bathroom renovation under $200")
    - Conversational queries with chat history context
    - Questions that require reasoning about multiple product types
    
    Args:
        request: AgenticSearchRequest with query and optional parameters
        
    Returns:
        AgenticSearchResponse with products and optional LLM response
    """
    try:
        logger.info(f"Agentic search request: {request.query[:100]}...")
        
        # Convert chat history to dict format
        chat_history = None
        if request.chat_history:
            chat_history = [
                {"role": msg.role, "content": msg.content} 
                for msg in request.chat_history
            ]
        
        # Perform the agentic retrieval
        result = await agentic_service.search(
            query=request.query,
            chat_history=chat_history,
            top=request.top,
            include_activity=request.include_activity
        )
        
        return AgenticSearchResponse(**result)
        
    except Exception as e:
        logger.error(f"Agentic search error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
async def agentic_health():
    """
    Health check for agentic retrieval service.
    
    Verifies that the Knowledge Base is accessible.
    """
    try:
        # Try a simple query to verify the service is working
        result = await agentic_service.search(
            query="test",
            top=1,
            include_activity=False
        )
        
        if "error" in result and result["error"]:
            return {
                "status": "unhealthy",
                "error": result["error"],
                "knowledge_base": agentic_service.knowledge_base_name
            }
        
        return {
            "status": "healthy",
            "knowledge_base": agentic_service.knowledge_base_name,
            "knowledge_source": agentic_service.knowledge_source_name
        }
        
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
            "knowledge_base": agentic_service.knowledge_base_name
        }


@router.get("/search")
async def agentic_search_get(
    q: str = Query(..., description="Search query"),
    top: int = Query(default=20, ge=1, le=50, description="Maximum results")
):
    """
    GET version of agentic search for simple queries.
    
    For complex queries with chat history, use POST /search instead.
    """
    request = AgenticSearchRequest(query=q, top=top)
    return await agentic_search(request)
