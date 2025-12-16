"""
Orders Agent
=============

Handles order creation, tracking, and status updates.
"""

from typing import Optional, List, Dict, Any
from datetime import datetime
import uuid
import structlog

logger = structlog.get_logger(__name__)


class OrdersAgent:
    """Agent for order management operations."""
    
    def __init__(self, app_state):
        """Initialize the orders agent."""
        self.cosmos = app_state.cosmos
        logger.info("OrdersAgent initialized")
    
    async def create_order(
        self,
        items: List[Dict[str, Any]],
        delivery_address: Optional[str] = None,
        customer_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create a new order.
        
        Args:
            items: List of {product_id, quantity} dictionaries
            delivery_address: Optional delivery address
            customer_id: Optional customer ID
        """
        logger.info("Creating order", item_count=len(items))
        
        try:
            # Validate and enrich items
            order_items = []
            subtotal = 0.0
            unavailable_items = []
            
            for item in items:
                product = await self.cosmos.get_product(item["product_id"])
                
                if not product:
                    unavailable_items.append(item["product_id"])
                    continue
                
                if not product.get("in_stock", True):
                    unavailable_items.append(product["name"])
                    continue
                
                quantity = item.get("quantity", 1)
                unit_price = product.get("sale_price") or product["price"]
                total_price = unit_price * quantity
                
                order_items.append({
                    "product_id": item["product_id"],
                    "product_name": product["name"],
                    "brand": product.get("brand", ""),
                    "quantity": quantity,
                    "unit_price": unit_price,
                    "total_price": total_price
                })
                subtotal += total_price
            
            if not order_items:
                return {
                    "success": False,
                    "error": "No valid items in order",
                    "unavailable": unavailable_items,
                    "summary": f"Sorry, I couldn't create the order. The items you selected are unavailable: {', '.join(unavailable_items)}."
                }
            
            # Calculate totals
            tax_rate = 0.0825  # 8.25% tax
            tax = round(subtotal * tax_rate, 2)
            total = round(subtotal + tax, 2)
            
            # Generate 4-digit order ID
            order_id = await self.cosmos.generate_order_id()
            
            # Create order
            order = {
                "id": order_id,
                "customer_id": customer_id,
                "items": order_items,
                "subtotal": subtotal,
                "tax": tax,
                "total": total,
                "status": "confirmed",
                "delivery_address": delivery_address,
                "estimated_delivery": "3-5 business days",
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            }
            
            await self.cosmos.create_order(order)
            
            # Create summary
            item_names = [item["product_name"] for item in order_items[:3]]
            summary = f"Great! I've created your order #{order_id} for {', '.join(item_names)}"
            if len(order_items) > 3:
                summary += f" and {len(order_items) - 3} more item(s)"
            summary += f". Your total is ${total:.2f} including tax."
            summary += f" Estimated delivery: {order['estimated_delivery']}."
            
            if unavailable_items:
                summary += f" Note: Some items were unavailable and removed from the order."
            
            return {
                "success": True,
                "order_id": order_id,
                "items": order_items,
                "subtotal": subtotal,
                "tax": tax,
                "total": total,
                "status": "confirmed",
                "estimated_delivery": order["estimated_delivery"],
                "summary": summary
            }
            
        except Exception as e:
            logger.error("Create order failed", error=str(e))
            return {
                "success": False,
                "error": str(e),
                "summary": "I had trouble creating your order. Please try again."
            }
    
    async def get_order_status(self, order_id: str) -> Dict[str, Any]:
        """
        Get the status of an existing order.
        """
        logger.info("Getting order status", order_id=order_id)
        
        try:
            order = await self.cosmos.get_order(order_id)
            
            if not order:
                return {
                    "found": False,
                    "summary": f"I couldn't find an order with ID {order_id}. Please check the order number and try again."
                }
            
            # Create status summary
            status = order["status"]
            status_messages = {
                "confirmed": "has been confirmed and is being processed",
                "processing": "is being prepared for shipment",
                "shipped": "has been shipped and is on its way",
                "delivered": "has been delivered",
                "cancelled": "has been cancelled"
            }
            
            status_text = status_messages.get(status, f"has status: {status}")
            
            item_count = len(order.get("items", []))
            item_text = "item" if item_count == 1 else "items"
            
            summary = f"Order #{order_id} {status_text}. "
            summary += f"It contains {item_count} {item_text} "
            summary += f"totaling ${order['total']:.2f}. "
            
            if status in ["confirmed", "processing"]:
                summary += f"Expected delivery: {order.get('estimated_delivery', '3-5 business days')}."
            elif status == "shipped":
                summary += "You should receive it soon!"
            
            return {
                "found": True,
                "order_id": order_id,
                "status": status,
                "items": order.get("items", []),
                "total": order["total"],
                "created_at": order.get("created_at"),
                "estimated_delivery": order.get("estimated_delivery"),
                "summary": summary
            }
            
        except Exception as e:
            logger.error("Get order status failed", error=str(e))
            return {
                "found": False,
                "error": str(e),
                "summary": "I had trouble looking up that order. Please try again."
            }
    
    async def list_customer_orders(
        self,
        customer_id: str,
        status: Optional[str] = None,
        limit: int = 10
    ) -> Dict[str, Any]:
        """
        List orders for a customer.
        """
        logger.info("Listing customer orders", customer_id=customer_id)
        
        try:
            orders = await self.cosmos.list_orders(
                customer_id=customer_id,
                status=status,
                limit=limit
            )
            
            if not orders:
                return {
                    "count": 0,
                    "orders": [],
                    "summary": "I don't see any orders for your account. Would you like to place a new order?"
                }
            
            # Create summary
            if len(orders) == 1:
                o = orders[0]
                summary = f"You have one order: #{o['id']} ({o['status']}) for ${o['total']:.2f}."
            else:
                recent = orders[0]
                summary = f"You have {len(orders)} orders. Most recent: #{recent['id']} ({recent['status']}) for ${recent['total']:.2f}."
            
            return {
                "count": len(orders),
                "orders": [
                    {
                        "order_id": o["id"],
                        "status": o["status"],
                        "total": o["total"],
                        "item_count": len(o.get("items", [])),
                        "created_at": o.get("created_at")
                    }
                    for o in orders
                ],
                "summary": summary
            }
            
        except Exception as e:
            logger.error("List orders failed", error=str(e))
            return {
                "error": str(e),
                "summary": "I had trouble retrieving your orders. Please try again."
            }
    
    async def cancel_order(self, order_id: str) -> Dict[str, Any]:
        """
        Cancel an existing order if eligible.
        """
        logger.info("Cancelling order", order_id=order_id)
        
        try:
            order = await self.cosmos.get_order(order_id)
            
            if not order:
                return {
                    "success": False,
                    "summary": f"I couldn't find order #{order_id}."
                }
            
            # Check if cancellable
            if order["status"] in ["shipped", "delivered"]:
                return {
                    "success": False,
                    "summary": f"Order #{order_id} has already been {order['status']} and cannot be cancelled. Would you like to initiate a return instead?"
                }
            
            if order["status"] == "cancelled":
                return {
                    "success": False,
                    "summary": f"Order #{order_id} has already been cancelled."
                }
            
            # Cancel the order
            await self.cosmos.update_order_status(order_id, "cancelled")
            
            return {
                "success": True,
                "order_id": order_id,
                "previous_status": order["status"],
                "summary": f"Order #{order_id} has been cancelled. A refund of ${order['total']:.2f} will be processed within 3-5 business days."
            }
            
        except Exception as e:
            logger.error("Cancel order failed", error=str(e))
            return {
                "success": False,
                "error": str(e),
                "summary": "I had trouble cancelling that order. Please try again or contact customer support."
            }
