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
from models.synonym import SynonymGroup

logger = logging.getLogger(__name__)


class CosmosDBService:
    """Cosmos DB service for merchandising data."""
    
    def __init__(self):
        """Initialize Cosmos DB client."""
        self.client: Optional[AsyncIOMotorClient] = None
        self.database = None
        self.rules_collection = None
        self.synonyms_collection = None
        self._connect()
    
    def _connect(self):
        """Connect to Cosmos DB."""
        try:
            # Ensure retryWrites=false for Cosmos DB MongoDB API
            connection_string = settings.azure_cosmos_connection_string
            if "retryWrites" not in connection_string:
                separator = "&" if "?" in connection_string else "?"
                connection_string = f"{connection_string}{separator}retryWrites=false"
            
            self.client = AsyncIOMotorClient(connection_string)
            self.database = self.client[settings.azure_cosmos_database]
            self.rules_collection = self.database["merchandising_rules"]
            self.synonyms_collection = self.database["synonyms"]
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
            await self.synonyms_collection.find_one()
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
            
            # Note: Removed .sort() as Cosmos DB requires indexes for sorting
            # Rules will be sorted by priority in the application layer
            cursor = self.rules_collection.find(query).limit(limit)
            docs = await cursor.to_list(length=limit)
            
            rules = []
            for doc in docs:
                doc["id"] = doc["_id"]
                rules.append(MerchandisingRule(**doc))
            
            # Sort by priority in Python
            rules.sort(key=lambda r: r.priority, reverse=True)
            
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
    
    # Synonyms CRUD Operations
    
    async def create_synonym(self, synonym: SynonymGroup) -> SynonymGroup:
        """Create a new synonym group."""
        try:
            synonym_dict = synonym.model_dump()
            synonym_dict["_id"] = synonym_dict["id"]  # Use id as _id for MongoDB
            await self.synonyms_collection.insert_one(synonym_dict)
            logger.info(f"✅ Created synonym: {synonym.id}")
            return synonym
        except DuplicateKeyError:
            logger.error(f"❌ Synonym already exists: {synonym.id}")
            raise ValueError("Synonym with this ID already exists")
        except Exception as e:
            logger.error(f"❌ Failed to create synonym: {e}")
            raise
    
    async def get_synonym(self, synonym_id: str) -> Optional[SynonymGroup]:
        """Get a synonym by ID."""
        try:
            doc = await self.synonyms_collection.find_one({"_id": synonym_id})
            if doc:
                doc["id"] = doc["_id"]  # Map _id back to id
                return SynonymGroup(**doc)
            return None
        except Exception as e:
            logger.error(f"❌ Failed to get synonym {synonym_id}: {e}")
            raise
    
    async def list_synonyms(
        self,
        enabled_only: bool = False,
        limit: int = 100
    ) -> List[SynonymGroup]:
        """List all synonym groups with optional filters."""
        try:
            query = {}
            if enabled_only:
                query["enabled"] = True
            
            cursor = self.synonyms_collection.find(query).limit(limit)
            docs = await cursor.to_list(length=limit)
            
            synonyms = []
            for doc in docs:
                doc["id"] = doc["_id"]
                synonyms.append(SynonymGroup(**doc))
            
            return synonyms
        except Exception as e:
            logger.error(f"❌ Failed to list synonyms: {e}")
            raise
    
    async def update_synonym(self, synonym_id: str, updates: dict) -> Optional[SynonymGroup]:
        """Update a synonym."""
        try:
            result = await self.synonyms_collection.find_one_and_update(
                {"_id": synonym_id},
                {"$set": updates},
                return_document=True
            )
            
            if result:
                result["id"] = result["_id"]
                logger.info(f"✅ Updated synonym: {synonym_id}")
                return SynonymGroup(**result)
            return None
        except Exception as e:
            logger.error(f"❌ Failed to update synonym {synonym_id}: {e}")
            raise
    
    async def delete_synonym(self, synonym_id: str) -> bool:
        """Delete a synonym."""
        try:
            result = await self.synonyms_collection.delete_one({"_id": synonym_id})
            if result.deleted_count > 0:
                logger.info(f"✅ Deleted synonym: {synonym_id}")
                return True
            return False
        except Exception as e:
            logger.error(f"❌ Failed to delete synonym {synonym_id}: {e}")
            raise
