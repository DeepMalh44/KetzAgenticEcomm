"""
Cosmos DB Service for Merchandising Portal
===========================================

Manages Cosmos DB operations for merchandising rules.
Reuses existing Cosmos DB from main backend.
"""

import logging
from typing import List, Optional
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo.errors import DuplicateKeyError

from config import settings
from models.merchandising_rule import MerchandisingRule

logger = logging.getLogger(__name__)


class CosmosDBService:
    """Cosmos DB service for merchandising data."""
    
    def __init__(self):
        """Initialize Cosmos DB client."""
        self.client: Optional[AsyncIOMotorClient] = None
        self.database = None
        self.rules_collection = None
        self._connect()
    
    def _connect(self):
        """Connect to Cosmos DB."""
        try:
            self.client = AsyncIOMotorClient(settings.azure_cosmos_connection_string)
            self.database = self.client[settings.azure_cosmos_database]
            self.rules_collection = self.database["merchandising_rules"]
            logger.info("✅ Connected to Cosmos DB")
        except Exception as e:
            logger.error(f"❌ Failed to connect to Cosmos DB: {e}")
            raise
    
    async def ensure_containers(self):
        """Ensure required collections exist."""
        try:
            # Collections are auto-created in MongoDB API
            # Just verify connection
            await self.rules_collection.find_one()
            logger.info("✅ Cosmos DB containers ready")
        except Exception as e:
            logger.warning(f"Container check: {e}")
    
    # Rules CRUD Operations
    
    async def create_rule(self, rule: MerchandisingRule) -> MerchandisingRule:
        """Create a new merchandising rule."""
        try:
            rule_dict = rule.model_dump()
            rule_dict["_id"] = rule_dict["id"]  # Use id as _id for MongoDB
            await self.rules_collection.insert_one(rule_dict)
            logger.info(f"✅ Created rule: {rule.id}")
            return rule
        except DuplicateKeyError:
            logger.error(f"❌ Rule already exists: {rule.id}")
            raise ValueError("Rule with this ID already exists")
        except Exception as e:
            logger.error(f"❌ Failed to create rule: {e}")
            raise
    
    async def get_rule(self, rule_id: str) -> Optional[MerchandisingRule]:
        """Get a rule by ID."""
        try:
            doc = await self.rules_collection.find_one({"_id": rule_id})
            if doc:
                doc["id"] = doc["_id"]  # Map _id back to id
                return MerchandisingRule(**doc)
            return None
        except Exception as e:
            logger.error(f"❌ Failed to get rule {rule_id}: {e}")
            raise
    
    async def list_rules(
        self,
        enabled_only: bool = False,
        category: Optional[str] = None,
        limit: int = 100
    ) -> List[MerchandisingRule]:
        """List all rules with optional filters."""
        try:
            query = {}
            if enabled_only:
                query["enabled"] = True
            if category:
                query["conditions.category"] = category
            
            cursor = self.rules_collection.find(query).limit(limit).sort("priority", -1)
            docs = await cursor.to_list(length=limit)
            
            rules = []
            for doc in docs:
                doc["id"] = doc["_id"]
                rules.append(MerchandisingRule(**doc))
            
            return rules
        except Exception as e:
            logger.error(f"❌ Failed to list rules: {e}")
            raise
    
    async def update_rule(self, rule_id: str, updates: dict) -> Optional[MerchandisingRule]:
        """Update a rule."""
        try:
            from datetime import datetime
            updates["updatedAt"] = datetime.utcnow()
            
            result = await self.rules_collection.find_one_and_update(
                {"_id": rule_id},
                {"$set": updates},
                return_document=True
            )
            
            if result:
                result["id"] = result["_id"]
                logger.info(f"✅ Updated rule: {rule_id}")
                return MerchandisingRule(**result)
            return None
        except Exception as e:
            logger.error(f"❌ Failed to update rule {rule_id}: {e}")
            raise
    
    async def delete_rule(self, rule_id: str) -> bool:
        """Delete a rule."""
        try:
            result = await self.rules_collection.delete_one({"_id": rule_id})
            if result.deleted_count > 0:
                logger.info(f"✅ Deleted rule: {rule_id}")
                return True
            return False
        except Exception as e:
            logger.error(f"❌ Failed to delete rule {rule_id}: {e}")
            raise
    
    async def get_active_rules_for_query(self, query: str, category: Optional[str] = None) -> List[MerchandisingRule]:
        """Get active rules that apply to a search query."""
        try:
            from datetime import datetime
            now = datetime.utcnow().isoformat()
            
            # Get all enabled rules
            pipeline = [
                {"$match": {"enabled": True}},
                {"$sort": {"priority": -1}}
            ]
            
            cursor = self.rules_collection.aggregate(pipeline)
            docs = await cursor.to_list(length=100)
            
            # Filter rules based on conditions
            applicable_rules = []
            for doc in docs:
                doc["id"] = doc["_id"]
                rule = MerchandisingRule(**doc)
                
                # Check query conditions
                if rule.conditions.query_contains:
                    query_lower = query.lower()
                    if not any(term.lower() in query_lower for term in rule.conditions.query_contains):
                        continue
                
                # Check category
                if rule.conditions.category and category != rule.conditions.category:
                    continue
                
                # Check date range
                if rule.conditions.date_range:
                    start = rule.conditions.date_range.get("start")
                    end = rule.conditions.date_range.get("end")
                    if start and now < start:
                        continue
                    if end and now > end:
                        continue
                
                applicable_rules.append(rule)
            
            return applicable_rules
        except Exception as e:
            logger.error(f"❌ Failed to get active rules: {e}")
            raise
