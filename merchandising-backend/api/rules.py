"""
Rules API Endpoints
===================

CRUD operations for merchandising rules.
"""

import logging
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query
from datetime import datetime

from models.merchandising_rule import (
    MerchandisingRule,
    RuleCreate,
    RuleUpdate,
    RuleListResponse
)
from services.cosmos_db_service import CosmosDBService
from services.rules_engine import RulesEngine

logger = logging.getLogger(__name__)
router = APIRouter()

# Initialize services
cosmos_service = CosmosDBService()


@router.get("/rules", response_model=RuleListResponse)
async def list_rules(
    enabled_only: bool = Query(False, description="Only return enabled rules"),
    category: Optional[str] = Query(None, description="Filter by category"),
    limit: int = Query(100, ge=1, le=500)
):
    """List all merchandising rules."""
    try:
        rules = await cosmos_service.list_rules(
            enabled_only=enabled_only,
            category=category,
            limit=limit
        )
        return RuleListResponse(rules=rules, total=len(rules))
    except Exception as e:
        logger.error(f"Failed to list rules: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/rules", response_model=MerchandisingRule, status_code=201)
async def create_rule(rule_data: RuleCreate):
    """Create a new merchandising rule."""
    try:
        rule = MerchandisingRule(
            **rule_data.model_dump(),
            createdAt=datetime.utcnow()
        )
        created_rule = await cosmos_service.create_rule(rule)
        return created_rule
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to create rule: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/rules/{rule_id}", response_model=MerchandisingRule)
async def get_rule(rule_id: str):
    """Get a specific rule by ID."""
    try:
        rule = await cosmos_service.get_rule(rule_id)
        if not rule:
            raise HTTPException(status_code=404, detail="Rule not found")
        return rule
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get rule: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.patch("/rules/{rule_id}", response_model=MerchandisingRule)
async def update_rule(rule_id: str, updates: RuleUpdate):
    """Update an existing rule."""
    try:
        # Only include non-None fields
        update_dict = {k: v for k, v in updates.model_dump().items() if v is not None}
        
        if not update_dict:
            raise HTTPException(status_code=400, detail="No updates provided")
        
        updated_rule = await cosmos_service.update_rule(rule_id, update_dict)
        if not updated_rule:
            raise HTTPException(status_code=404, detail="Rule not found")
        
        return updated_rule
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update rule: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/rules/{rule_id}", status_code=204)
async def delete_rule(rule_id: str):
    """Delete a rule."""
    try:
        deleted = await cosmos_service.delete_rule(rule_id)
        if not deleted:
            raise HTTPException(status_code=404, detail="Rule not found")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete rule: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/rules/{rule_id}/toggle", response_model=MerchandisingRule)
async def toggle_rule(rule_id: str):
    """Toggle rule enabled/disabled status."""
    try:
        rule = await cosmos_service.get_rule(rule_id)
        if not rule:
            raise HTTPException(status_code=404, detail="Rule not found")
        
        updated_rule = await cosmos_service.update_rule(
            rule_id,
            {"enabled": not rule.enabled}
        )
        return updated_rule
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to toggle rule: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/rules/preview")
async def preview_rules(
    query: str = Query(..., description="Search query"),
    category: Optional[str] = Query(None, description="Category"),
    rule_ids: Optional[List[str]] = None
):
    """
    Preview the effect of rules on search results.
    Fetches real search results and shows before/after applying rules.
    """
    try:
        # Get applicable rules
        if rule_ids:
            rules = []
            for rule_id in rule_ids:
                rule = await cosmos_service.get_rule(rule_id)
                if rule and rule.enabled:
                    rules.append(rule)
        else:
            rules = await cosmos_service.get_active_rules_for_query(query, category)
        
        # For preview, we'll use mock results
        # In production, this would call the main backend's search API
        mock_results = [
            {"id": f"PROD-{i}", "name": f"Product {i}", "@search.score": 1.0 - (i * 0.1)}
            for i in range(1, 11)
        ]
        
        preview = RulesEngine.preview_rules(mock_results, rules)
        return preview
    except Exception as e:
        logger.error(f"Failed to preview rules: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/active/{query}")
async def get_active_rules(
    query: str,
    category: Optional[str] = Query(None, description="Category filter")
):
    """Get all active rules that would apply to a given query."""
    try:
        rules = await cosmos_service.get_active_rules_for_query(query, category)
        return {
            "query": query,
            "category": category,
            "rules": rules,
            "count": len(rules)
        }
    except Exception as e:
        logger.error(f"Failed to get active rules: {e}")
        raise HTTPException(status_code=500, detail=str(e))
