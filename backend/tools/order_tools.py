# =============================================================================
# KetzAgenticEcomm - Order Tools
# =============================================================================
"""
Order-related tools for the voice assistant.
"""

import logging
import uuid
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from services.cosmos_db import CosmosDBService

logger = logging.getLogger(__name__)


async def create_order(
    customer_id: str,
    items: List[Dict[str, Any]],
    shipping_address: Dict[str, str],
    payment_method: str = "card_on_file",
    cosmos_db: Optional[CosmosDBService] = None,
) -> Dict[str, Any]:
    """
    Create a new order.
    
    Args:
        customer_id: Customer identifier
        items: List of items with product_id and quantity
        shipping_address: Shipping address details
        payment_method: Payment method identifier
        cosmos_db: CosmosDBService instance
        
    Returns:
        Dictionary with order confirmation
    """
    try:
        if not cosmos_db:
            return {
                "success": False,
                "error": "Database service not available"
            }
        
        # Validate items and calculate totals
        order_items = []
        subtotal = 0.0
        
        for item in items:
            product = await cosmos_db.get_product(item.get("product_id"))
            if not product:
                return {
                    "success": False,
                    "error": f"Product {item.get('product_id')} not found"
                }
            
            quantity = item.get("quantity", 1)
            if product.get("stock_quantity", 0) < quantity:
                return {
                    "success": False,
                    "error": f"Insufficient stock for {product.get('name')}"
                }
            
            item_total = product.get("price", 0) * quantity
            subtotal += item_total
            
            order_items.append({
                "product_id": product.get("id"),
                "name": product.get("name"),
                "sku": product.get("sku"),
                "quantity": quantity,
                "unit_price": product.get("price"),
                "total": item_total,
                "image_url": product.get("image_url"),
            })
        
        # Calculate order totals
        tax_rate = 0.08  # 8% tax
        tax = round(subtotal * tax_rate, 2)
        shipping = 0.0 if subtotal >= 50 else 9.99  # Free shipping over $50
        total = round(subtotal + tax + shipping, 2)
        
        # Estimate delivery date (3-5 business days)
        estimated_delivery = datetime.utcnow() + timedelta(days=5)
        
        # Create order document
        order_id = f"ORD-{uuid.uuid4().hex[:8].upper()}"
        order = {
            "id": order_id,
            "customer_id": customer_id,
            "items": order_items,
            "subtotal": subtotal,
            "tax": tax,
            "shipping_cost": shipping,
            "total": total,
            "shipping_address": shipping_address,
            "payment_method": payment_method,
            "status": "confirmed",
            "estimated_delivery": estimated_delivery.isoformat(),
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
            "tracking_number": None,
            "carrier": None,
        }
        
        # Save order to database
        await cosmos_db.create_order(order)
        
        # Update stock quantities
        for item in order_items:
            await cosmos_db.update_stock(
                item["product_id"],
                -item["quantity"]
            )
        
        return {
            "success": True,
            "order_id": order_id,
            "total": total,
            "item_count": len(order_items),
            "estimated_delivery": estimated_delivery.strftime("%B %d, %Y"),
            "message": f"Order {order_id} confirmed! Your total is ${total:.2f}. "
                      f"Expected delivery by {estimated_delivery.strftime('%B %d, %Y')}.",
            "details": {
                "subtotal": subtotal,
                "tax": tax,
                "shipping": shipping,
                "items": [{"name": i["name"], "quantity": i["quantity"]} for i in order_items]
            }
        }
        
    except Exception as e:
        logger.error(f"Create order error: {e}")
        return {
            "success": False,
            "error": str(e)
        }


async def get_order_status(
    order_id: str,
    customer_id: Optional[str] = None,
    cosmos_db: Optional[CosmosDBService] = None,
) -> Dict[str, Any]:
    """
    Get the status of an order.
    
    Args:
        order_id: The order ID
        customer_id: Optional customer ID for verification
        cosmos_db: CosmosDBService instance
        
    Returns:
        Dictionary with order status
    """
    try:
        if not cosmos_db:
            return {
                "success": False,
                "error": "Database service not available"
            }
        
        order = await cosmos_db.get_order(order_id)
        
        if not order:
            return {
                "success": False,
                "error": f"Order {order_id} not found"
            }
        
        # Verify customer if provided
        if customer_id and order.get("customer_id") != customer_id:
            return {
                "success": False,
                "error": "Order not found for this customer"
            }
        
        # Build status timeline
        status_map = {
            "confirmed": "Order Confirmed",
            "processing": "Processing",
            "shipped": "Shipped",
            "out_for_delivery": "Out for Delivery",
            "delivered": "Delivered",
            "cancelled": "Cancelled",
        }
        
        current_status = order.get("status", "confirmed")
        
        return {
            "success": True,
            "order_id": order_id,
            "status": current_status,
            "status_display": status_map.get(current_status, current_status),
            "total": order.get("total"),
            "item_count": len(order.get("items", [])),
            "created_at": order.get("created_at"),
            "estimated_delivery": order.get("estimated_delivery"),
            "tracking_number": order.get("tracking_number"),
            "carrier": order.get("carrier"),
            "shipping_address": order.get("shipping_address"),
            "items": [
                {
                    "name": item.get("name"),
                    "quantity": item.get("quantity"),
                    "unit_price": item.get("unit_price")
                }
                for item in order.get("items", [])
            ],
            "message": f"Order {order_id} is currently {status_map.get(current_status, current_status).lower()}."
        }
        
    except Exception as e:
        logger.error(f"Get order status error: {e}")
        return {
            "success": False,
            "error": str(e)
        }


async def cancel_order(
    order_id: str,
    customer_id: str,
    reason: Optional[str] = None,
    cosmos_db: Optional[CosmosDBService] = None,
) -> Dict[str, Any]:
    """
    Cancel an order if eligible.
    
    Args:
        order_id: The order ID
        customer_id: Customer ID for verification
        reason: Cancellation reason
        cosmos_db: CosmosDBService instance
        
    Returns:
        Dictionary with cancellation result
    """
    try:
        if not cosmos_db:
            return {
                "success": False,
                "error": "Database service not available"
            }
        
        order = await cosmos_db.get_order(order_id)
        
        if not order:
            return {
                "success": False,
                "error": f"Order {order_id} not found"
            }
        
        # Verify customer
        if order.get("customer_id") != customer_id:
            return {
                "success": False,
                "error": "Order not found for this customer"
            }
        
        # Check if cancellable
        non_cancellable = ["shipped", "out_for_delivery", "delivered", "cancelled"]
        if order.get("status") in non_cancellable:
            return {
                "success": False,
                "error": f"Order cannot be cancelled. Current status: {order.get('status')}. "
                        f"Please initiate a return instead.",
                "suggest_return": order.get("status") in ["delivered"]
            }
        
        # Cancel the order
        await cosmos_db.update_order(order_id, {
            "status": "cancelled",
            "cancellation_reason": reason,
            "cancelled_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
        })
        
        # Restore stock quantities
        for item in order.get("items", []):
            await cosmos_db.update_stock(
                item["product_id"],
                item["quantity"]
            )
        
        return {
            "success": True,
            "order_id": order_id,
            "status": "cancelled",
            "refund_amount": order.get("total"),
            "message": f"Order {order_id} has been cancelled. "
                      f"A refund of ${order.get('total'):.2f} will be processed within 3-5 business days."
        }
        
    except Exception as e:
        logger.error(f"Cancel order error: {e}")
        return {
            "success": False,
            "error": str(e)
        }
