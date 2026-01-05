"""
Synonyms API Endpoints
=======================

CRUD operations for synonym management and Azure AI Search sync.
"""

import logging
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query
from datetime import datetime

from models.synonym import (
    SynonymGroup,
    SynonymCreate,
    SynonymUpdate,
    SynonymListResponse,
    SynonymTestRequest,
    SynonymTestResponse,
    BulkSynonymImport
)
from services.cosmos_db_service import CosmosDBService
from services.synonym_manager import SynonymManager

logger = logging.getLogger(__name__)
router = APIRouter()

# Initialize services
cosmos_service = CosmosDBService()
synonym_manager = SynonymManager()


@router.get("/synonyms", response_model=SynonymListResponse)
async def list_synonyms(
    enabled_only: bool = Query(False, description="Only return enabled synonyms"),
    limit: int = Query(100, ge=1, le=500)
):
    """List all synonym groups."""
    try:
        synonyms = await cosmos_service.list_synonyms(
            enabled_only=enabled_only,
            limit=limit
        )
        return SynonymListResponse(synonyms=synonyms, total=len(synonyms))
    except Exception as e:
        logger.error(f"Failed to list synonyms: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/synonyms", response_model=SynonymGroup, status_code=201)
async def create_synonym(synonym_data: SynonymCreate):
    """Create a new synonym group and sync to Azure AI Search."""
    try:
        synonym = SynonymGroup(
            **synonym_data.model_dump(),
            createdAt=datetime.utcnow()
        )
        created_synonym = await cosmos_service.create_synonym(synonym)
        
        # Sync all synonyms to Azure AI Search
        all_synonyms = await cosmos_service.list_synonyms(enabled_only=False)
        sync_success = await synonym_manager.sync_to_azure_search(all_synonyms)
        
        if not sync_success:
            logger.warning("Synonym created but failed to sync to Azure Search")
        
        return created_synonym
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to create synonym: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/synonyms/{synonym_id}", response_model=SynonymGroup)
async def get_synonym(synonym_id: str):
    """Get a specific synonym group by ID."""
    try:
        synonym = await cosmos_service.get_synonym(synonym_id)
        if not synonym:
            raise HTTPException(status_code=404, detail="Synonym not found")
        return synonym
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get synonym: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.patch("/synonyms/{synonym_id}", response_model=SynonymGroup)
async def update_synonym(synonym_id: str, updates: SynonymUpdate):
    """Update an existing synonym group and sync to Azure AI Search."""
    try:
        # Only include non-None fields
        update_dict = {k: v for k, v in updates.model_dump().items() if v is not None}
        
        if not update_dict:
            raise HTTPException(status_code=400, detail="No updates provided")
        
        update_dict["updatedAt"] = datetime.utcnow()
        updated_synonym = await cosmos_service.update_synonym(synonym_id, update_dict)
        
        if not updated_synonym:
            raise HTTPException(status_code=404, detail="Synonym not found")
        
        # Sync all synonyms to Azure AI Search
        all_synonyms = await cosmos_service.list_synonyms(enabled_only=False)
        await synonym_manager.sync_to_azure_search(all_synonyms)
        
        return updated_synonym
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update synonym: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/synonyms/{synonym_id}", status_code=204)
async def delete_synonym(synonym_id: str):
    """Delete a synonym group and sync to Azure AI Search."""
    try:
        deleted = await cosmos_service.delete_synonym(synonym_id)
        if not deleted:
            raise HTTPException(status_code=404, detail="Synonym not found")
        
        # Sync remaining synonyms to Azure AI Search
        all_synonyms = await cosmos_service.list_synonyms(enabled_only=False)
        await synonym_manager.sync_to_azure_search(all_synonyms)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete synonym: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/synonyms/{synonym_id}/toggle", response_model=SynonymGroup)
async def toggle_synonym(synonym_id: str):
    """Toggle synonym enabled/disabled status and sync to Azure AI Search."""
    try:
        synonym = await cosmos_service.get_synonym(synonym_id)
        if not synonym:
            raise HTTPException(status_code=404, detail="Synonym not found")
        
        updated_synonym = await cosmos_service.update_synonym(
            synonym_id,
            {"enabled": not synonym.enabled, "updatedAt": datetime.utcnow()}
        )
        
        # Sync all synonyms to Azure AI Search
        all_synonyms = await cosmos_service.list_synonyms(enabled_only=False)
        await synonym_manager.sync_to_azure_search(all_synonyms)
        
        return updated_synonym
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to toggle synonym: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/synonyms/sync", status_code=200)
async def sync_synonyms():
    """Manually trigger sync of all synonyms to Azure AI Search."""
    try:
        all_synonyms = await cosmos_service.list_synonyms(enabled_only=False)
        sync_success = await synonym_manager.sync_to_azure_search(all_synonyms)
        
        if sync_success:
            return {
                "success": True,
                "message": f"Successfully synced {len(all_synonyms)} synonym groups to Azure AI Search"
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to sync synonyms")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to sync synonyms: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/synonyms/azure/current")
async def get_current_azure_synonyms():
    """Get the current synonym map from Azure AI Search."""
    try:
        current_map = await synonym_manager.get_current_synonym_map()
        
        if current_map:
            parsed = synonym_manager.parse_solr_format(current_map)
            return {
                "raw": current_map,
                "parsed": parsed
            }
        else:
            return {
                "raw": None,
                "parsed": [],
                "message": "No synonym map found in Azure AI Search"
            }
            
    except Exception as e:
        logger.error(f"Failed to get current Azure synonyms: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/synonyms/test", response_model=SynonymTestResponse)
async def test_synonym(test_request: SynonymTestRequest):
    """Test how a search query would be expanded with current synonyms."""
    try:
        # This would ideally call the main backend's search endpoint
        # For now, return a mock response showing concept
        return SynonymTestResponse(
            query=test_request.query,
            expanded_terms=[test_request.query],  # Would be expanded with synonyms
            sample_results=[]
        )
    except Exception as e:
        logger.error(f"Failed to test synonym: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/synonyms/bulk-import", status_code=201)
async def bulk_import_synonyms(import_data: BulkSynonymImport):
    """Bulk import synonyms from CSV format."""
    try:
        created_count = 0
        errors = []
        
        for synonym_data in import_data.synonyms:
            try:
                synonym = SynonymGroup(
                    **synonym_data.model_dump(),
                    createdAt=datetime.utcnow()
                )
                await cosmos_service.create_synonym(synonym)
                created_count += 1
            except Exception as e:
                errors.append(f"Failed to create synonym '{synonym_data.name}': {str(e)}")
        
        # Sync all synonyms to Azure AI Search
        all_synonyms = await cosmos_service.list_synonyms(enabled_only=False)
        await synonym_manager.sync_to_azure_search(all_synonyms)
        
        return {
            "success": True,
            "created": created_count,
            "errors": errors
        }
        
    except Exception as e:
        logger.error(f"Failed to bulk import synonyms: {e}")
        raise HTTPException(status_code=500, detail=str(e))
