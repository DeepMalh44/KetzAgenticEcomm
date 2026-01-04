from fastapi import APIRouter, Query
from typing import List, Optional
from azure.search.documents import SearchClient
from azure.core.credentials import AzureKeyCredential
from config import settings

router = APIRouter()

def get_search_client():
    return SearchClient(
        endpoint=settings.azure_search_endpoint,
        index_name=settings.azure_search_index,
        credential=AzureKeyCredential(settings.azure_search_key)
    )

@router.get("/products/search")
async def search_products(
    q: str = Query(..., description="Search query"),
    top: int = Query(20, description="Number of results to return")
):
    """
    Search for products in Azure AI Search.
    Returns products for the ProductPicker component.
    """
    try:
        search_client = get_search_client()
        
        results = search_client.search(
            search_text=q,
            top=top,
            select=["id", "name", "category", "price"]
        )
        
        products = []
        for result in results:
            products.append({
                "id": result.get("id"),
                "name": result.get("name"),
                "category": result.get("category", ""),
                "price": float(result.get("price", 0))
            })
        
        return {
            "results": products,
            "total": len(products)
        }
    except Exception as e:
        return {
            "results": [],
            "total": 0,
            "error": str(e)
        }
