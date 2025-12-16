"""
Cosmos DB Service (MongoDB API)
================================

Data access layer for products, orders, and sessions.
Uses Azure Cosmos DB with MongoDB API (serverless).
"""

from typing import Optional, List, Dict, Any
from datetime import datetime
from motor.motor_asyncio import AsyncIOMotorClient
import structlog

logger = structlog.get_logger(__name__)


class CosmosDBService:
    """Service for Cosmos DB MongoDB API operations."""
    
    def __init__(self, connection_string: str, database_name: str):
        """Initialize the Cosmos DB service."""
        # Disable retryable writes for Azure Cosmos DB MongoDB API
        if "retrywrites" not in connection_string.lower():
            if "?" in connection_string:
                connection_string += "&retrywrites=false"
            else:
                connection_string += "?retrywrites=false"
        
        self.client = AsyncIOMotorClient(connection_string)
        self.db = self.client[database_name]
        
        # Collections
        self.products = self.db["products"]
        self.orders = self.db["orders"]
        self.sessions = self.db["sessions"]
        self.returns = self.db["returns"]
        
        logger.info("CosmosDB service initialized", database=database_name)
    
    # ===================
    # Product Operations
    # ===================
    
    async def get_product(self, product_id: str) -> Optional[Dict[str, Any]]:
        """Get a product by ID."""
        product = await self.products.find_one({"id": product_id})
        if product:
            product["_id"] = str(product["_id"])
        return product
    
    async def get_products_by_category(
        self, 
        category: str, 
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """Get products by category."""
        cursor = self.products.find({"category": category}).limit(limit)
        products = await cursor.to_list(length=limit)
        for p in products:
            p["_id"] = str(p["_id"])
        return products
    
    async def list_products(
        self, 
        limit: int = 20, 
        skip: int = 0
    ) -> List[Dict[str, Any]]:
        """List products with pagination."""
        cursor = self.products.find().skip(skip).limit(limit)
        products = await cursor.to_list(length=limit)
        for p in products:
            p["_id"] = str(p["_id"])
        return products
    
    async def get_featured_products(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get featured/popular products."""
        cursor = self.products.find(
            {"$or": [{"featured": True}, {"rating": {"$gte": 4.5}}]}
        ).sort("rating", -1).limit(limit)
        products = await cursor.to_list(length=limit)
        for p in products:
            p["_id"] = str(p["_id"])
        return products
    
    async def search_products_text(
        self,
        query: str,
        category: Optional[str] = None,
        min_price: Optional[float] = None,
        max_price: Optional[float] = None,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Search products using regex (for fallback when AI Search is not available).
        Note: Use AISearchService.search_products() for full-featured search.
        """
        # Build filter
        filter_query = {}
        
        # Text search using regex on name and description
        if query:
            terms = query.strip().split()
            if terms:
                regex_conditions = []
                for term in terms:
                    regex_conditions.append({
                        "$or": [
                            {"name": {"$regex": term, "$options": "i"}},
                            {"description": {"$regex": term, "$options": "i"}},
                            {"brand": {"$regex": term, "$options": "i"}}
                        ]
                    })
                filter_query["$and"] = regex_conditions
        
        # Category filter
        if category:
            filter_query["category"] = category
        
        # Price filters
        if min_price is not None or max_price is not None:
            price_filter = {}
            if min_price is not None:
                price_filter["$gte"] = min_price
            if max_price is not None:
                price_filter["$lte"] = max_price
            filter_query["price"] = price_filter
        
        cursor = self.products.find(filter_query).limit(limit)
        products = await cursor.to_list(length=limit)
        
        for p in products:
            p["_id"] = str(p["_id"])
        
        return products
    
    async def create_product(self, product: Dict[str, Any]) -> str:
        """Create a new product."""
        result = await self.products.insert_one(product)
        logger.info("Product created", product_id=product.get("id"))
        return str(result.inserted_id)
    
    async def update_product(
        self, 
        product_id: str, 
        updates: Dict[str, Any]
    ) -> bool:
        """Update a product."""
        updates["updated_at"] = datetime.utcnow()
        result = await self.products.update_one(
            {"id": product_id},
            {"$set": updates}
        )
        return result.modified_count > 0
    
    async def bulk_insert_products(
        self, 
        products: List[Dict[str, Any]]
    ) -> int:
        """Bulk insert products."""
        if not products:
            return 0
        result = await self.products.insert_many(products)
        count = len(result.inserted_ids)
        logger.info("Bulk insert completed", count=count)
        return count
    
    async def count_products(self) -> int:
        """Count total products."""
        return await self.products.count_documents({})
    
    async def get_categories(self) -> List[str]:
        """Get all unique categories."""
        return await self.products.distinct("category")
    
    # ===================
    # Order Operations
    # ===================
    
    async def create_order(self, order: Dict[str, Any]) -> str:
        """Create a new order."""
        order["created_at"] = datetime.utcnow()
        order["updated_at"] = datetime.utcnow()
        result = await self.orders.insert_one(order)
        logger.info("Order created", order_id=order.get("id"))
        return str(result.inserted_id)
    
    async def get_order(self, order_id: str) -> Optional[Dict[str, Any]]:
        """Get an order by ID."""
        order = await self.orders.find_one({"id": order_id})
        if order:
            order["_id"] = str(order["_id"])
        return order
    
    async def list_orders(
        self,
        customer_id: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """List orders with optional filters."""
        filter_query = {}
        if customer_id:
            filter_query["customer_id"] = customer_id
        if status:
            filter_query["status"] = status
        
        # Note: Cosmos DB MongoDB API may not support sorting without index
        # Using simple find without sort for compatibility
        cursor = self.orders.find(filter_query).limit(limit)
        
        orders = await cursor.to_list(length=limit)
        for o in orders:
            o["_id"] = str(o["_id"])
        # Sort in memory by created_at descending
        orders.sort(key=lambda x: x.get("created_at", ""), reverse=True)
        return orders
    
    async def update_order_status(self, order_id: str, status: str) -> bool:
        """Update order status."""
        result = await self.orders.update_one(
            {"id": order_id},
            {"$set": {"status": status, "updated_at": datetime.utcnow()}}
        )
        return result.modified_count > 0
    
    async def update_order(self, order_id: str, updates: Dict[str, Any]) -> bool:
        """Update an order with arbitrary fields."""
        updates["updated_at"] = datetime.utcnow()
        result = await self.orders.update_one(
            {"id": order_id},
            {"$set": updates}
        )
        return result.modified_count > 0
    
    async def update_stock(self, product_id: str, quantity_change: int) -> bool:
        """Update product stock quantity (positive to add, negative to subtract)."""
        result = await self.products.update_one(
            {"id": product_id},
            {
                "$inc": {"stock_quantity": quantity_change},
                "$set": {"updated_at": datetime.utcnow()}
            }
        )
        return result.modified_count > 0
    
    # ===================
    # Return Operations
    # ===================
    
    async def create_return(self, return_record: Dict[str, Any]) -> str:
        """Create a return record."""
        return_record["created_at"] = datetime.utcnow()
        result = await self.returns.insert_one(return_record)
        logger.info("Return created", return_id=return_record.get("id"))
        return str(result.inserted_id)
    
    async def get_return(self, return_id: str) -> Optional[Dict[str, Any]]:
        """Get a return by ID."""
        ret = await self.returns.find_one({"id": return_id})
        if ret:
            ret["_id"] = str(ret["_id"])
        return ret
    
    # ===================
    # Session Operations
    # ===================
    
    async def create_session(self, session: Dict[str, Any]) -> str:
        """Create a new session."""
        session["created_at"] = datetime.utcnow()
        session["updated_at"] = datetime.utcnow()
        result = await self.sessions.insert_one(session)
        return str(result.inserted_id)
    
    async def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get a session by ID."""
        session = await self.sessions.find_one({"id": session_id})
        if session:
            session["_id"] = str(session["_id"])
        return session
    
    async def update_session(
        self, 
        session_id: str, 
        updates: Dict[str, Any]
    ) -> bool:
        """Update a session."""
        updates["updated_at"] = datetime.utcnow()
        result = await self.sessions.update_one(
            {"id": session_id},
            {"$set": updates}
        )
        return result.modified_count > 0
    
    # ===================
    # Inventory Operations
    # ===================
    
    async def check_inventory(
        self, 
        product_id: str, 
        zip_code: Optional[str] = None
    ) -> Dict[str, Any]:
        """Check product inventory/availability."""
        product = await self.get_product(product_id)
        if not product:
            return {"available": False, "error": "Product not found"}
        
        # Mock inventory data (in real app, integrate with inventory system)
        return {
            "product_id": product_id,
            "available": product.get("in_stock", True),
            "quantity": product.get("stock_quantity", 100),
            "delivery_available": True,
            "store_pickup": True,
            "estimated_delivery": "2-3 business days"
        }
    
    async def close(self):
        """Close the database connection."""
        self.client.close()
        logger.info("CosmosDB connection closed")
