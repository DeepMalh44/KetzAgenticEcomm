# =============================================================================
# KetzAgenticEcomm - Return Tools
# =============================================================================
"""
Return and refund related tools for the voice assistant.
"""

import logging
import uuid
from datetime import datetime, timedelta
from typing import Any, Dict, Optional

from services.cosmos_db import CosmosDBService

logger = logging.getLogger(__name__)


async def check_return_eligibility(
    order_id: str,
    product_id: Optional[str] = None,
    customer_id: Optional[str] = None,
    cosmos_db: Optional[CosmosDBService] = None,
) -> Dict[str, Any]:
    """
    Check if an order/item is eligible for return.
    
    Args:
        order_id: The order ID
        product_id: Optional specific product to check
        customer_id: Customer ID for verification
        cosmos_db: CosmosDBService instance
        
    Returns:
        Dictionary with eligibility status
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
        
        # Check order status
        if order.get("status") != "delivered":
            return {
                "success": True,
                "eligible": False,
                "reason": f"Order must be delivered before initiating a return. "
                         f"Current status: {order.get('status')}"
            }
        
        # Check return window (30 days)
        delivered_at = order.get("delivered_at") or order.get("created_at")
        if delivered_at:
            delivered_date = datetime.fromisoformat(delivered_at.replace("Z", "+00:00"))
            days_since_delivery = (datetime.utcnow().replace(tzinfo=delivered_date.tzinfo) - delivered_date).days
            
            if days_since_delivery > 30:
                return {
                    "success": True,
                    "eligible": False,
                    "reason": f"Return window has expired. Items must be returned within 30 days of delivery. "
                             f"It has been {days_since_delivery} days since delivery."
                }
        
        # Check specific product eligibility
        eligible_items = []
        non_returnable = ["paint", "custom", "clearance", "hazmat"]
        
        for item in order.get("items", []):
            if product_id and item.get("product_id") != product_id:
                continue
            
            # Check if product category is returnable
            product = await cosmos_db.get_product(item.get("product_id"))
            is_returnable = True
            reason = "Eligible for return"
            
            if product:
                category = product.get("category", "").lower()
                if any(nr in category for nr in non_returnable):
                    is_returnable = False
                    reason = f"This item category ({category}) is not eligible for return"
            
            eligible_items.append({
                "product_id": item.get("product_id"),
                "name": item.get("name"),
                "quantity": item.get("quantity"),
                "eligible": is_returnable,
                "reason": reason,
                "refund_amount": item.get("total") if is_returnable else 0
            })
        
        all_eligible = all(item["eligible"] for item in eligible_items)
        total_refund = sum(item["refund_amount"] for item in eligible_items)
        
        return {
            "success": True,
            "eligible": all_eligible or any(item["eligible"] for item in eligible_items),
            "order_id": order_id,
            "items": eligible_items,
            "potential_refund": total_refund,
            "return_policy": "Items must be unused, in original packaging, and returned within 30 days.",
            "message": "Your order is eligible for return." if all_eligible else 
                      "Some items may not be eligible for return. See details."
        }
        
    except Exception as e:
        logger.error(f"Check return eligibility error: {e}")
        return {
            "success": False,
            "error": str(e)
        }


async def initiate_return(
    order_id: str,
    customer_id: str,
    items: list,  # List of {product_id, quantity, reason}
    return_method: str = "mail",  # "mail" or "store"
    cosmos_db: Optional[CosmosDBService] = None,
) -> Dict[str, Any]:
    """
    Initiate a return for order items.
    
    Args:
        order_id: The order ID
        customer_id: Customer ID
        items: Items to return with quantities and reasons
        return_method: "mail" for shipping or "store" for in-store
        cosmos_db: CosmosDBService instance
        
    Returns:
        Dictionary with return details
    """
    try:
        if not cosmos_db:
            return {
                "success": False,
                "error": "Database service not available"
            }
        
        # First check eligibility
        eligibility = await check_return_eligibility(
            order_id=order_id,
            customer_id=customer_id,
            cosmos_db=cosmos_db
        )
        
        if not eligibility.get("success") or not eligibility.get("eligible"):
            return {
                "success": False,
                "error": eligibility.get("reason") or eligibility.get("error") or "Not eligible for return"
            }
        
        order = await cosmos_db.get_order(order_id)
        
        # Create return items list
        return_items = []
        total_refund = 0.0
        
        for return_item in items:
            # Find the item in the order
            order_item = next(
                (oi for oi in order.get("items", []) 
                 if oi.get("product_id") == return_item.get("product_id")),
                None
            )
            
            if not order_item:
                continue
            
            quantity = min(return_item.get("quantity", 1), order_item.get("quantity", 1))
            refund = (order_item.get("unit_price", 0) * quantity)
            total_refund += refund
            
            return_items.append({
                "product_id": return_item.get("product_id"),
                "name": order_item.get("name"),
                "quantity": quantity,
                "reason": return_item.get("reason", "Changed my mind"),
                "refund_amount": refund,
            })
        
        if not return_items:
            return {
                "success": False,
                "error": "No valid items to return"
            }
        
        # Create return record
        return_id = f"RET-{uuid.uuid4().hex[:8].upper()}"
        return_record = {
            "id": return_id,
            "order_id": order_id,
            "customer_id": customer_id,
            "items": return_items,
            "total_refund": total_refund,
            "return_method": return_method,
            "status": "initiated",
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
            "shipping_label": None,
            "tracking_number": None,
        }
        
        # Generate shipping label for mail returns
        if return_method == "mail":
            return_record["shipping_label"] = f"https://shipping.ketzagenticecomm.com/labels/{return_id}"
            return_record["instructions"] = [
                "Print the prepaid shipping label",
                "Pack items securely in original packaging if possible",
                "Drop off at any UPS location",
                "Keep your tracking number for reference"
            ]
        else:
            return_record["instructions"] = [
                "Bring items to any Ketz Home Improvement store",
                "Show this return ID to customer service",
                "Receive your refund immediately"
            ]
        
        # Save return to database
        await cosmos_db.create_return(return_record)
        
        return {
            "success": True,
            "return_id": return_id,
            "order_id": order_id,
            "items": return_items,
            "total_refund": total_refund,
            "return_method": return_method,
            "status": "initiated",
            "shipping_label": return_record.get("shipping_label"),
            "instructions": return_record.get("instructions"),
            "message": f"Return {return_id} initiated successfully! "
                      f"Refund of ${total_refund:.2f} will be processed after items are received. "
                      f"{'A prepaid shipping label has been generated.' if return_method == 'mail' else 'Please bring items to your nearest store.'}"
        }
        
    except Exception as e:
        logger.error(f"Initiate return error: {e}")
        return {
            "success": False,
            "error": str(e)
        }


async def get_return_status(
    return_id: str,
    customer_id: Optional[str] = None,
    cosmos_db: Optional[CosmosDBService] = None,
) -> Dict[str, Any]:
    """
    Get the status of a return.
    
    Args:
        return_id: The return ID
        customer_id: Optional customer ID for verification
        cosmos_db: CosmosDBService instance
        
    Returns:
        Dictionary with return status
    """
    try:
        if not cosmos_db:
            return {
                "success": False,
                "error": "Database service not available"
            }
        
        return_record = await cosmos_db.get_return(return_id)
        
        if not return_record:
            return {
                "success": False,
                "error": f"Return {return_id} not found"
            }
        
        # Verify customer if provided
        if customer_id and return_record.get("customer_id") != customer_id:
            return {
                "success": False,
                "error": "Return not found for this customer"
            }
        
        status_map = {
            "initiated": "Return Initiated",
            "label_printed": "Shipping Label Printed",
            "in_transit": "Package In Transit",
            "received": "Items Received",
            "inspecting": "Items Being Inspected",
            "approved": "Return Approved",
            "refund_processing": "Refund Processing",
            "completed": "Refund Completed",
            "rejected": "Return Rejected",
        }
        
        current_status = return_record.get("status", "initiated")
        
        return {
            "success": True,
            "return_id": return_id,
            "order_id": return_record.get("order_id"),
            "status": current_status,
            "status_display": status_map.get(current_status, current_status),
            "items": return_record.get("items"),
            "total_refund": return_record.get("total_refund"),
            "return_method": return_record.get("return_method"),
            "tracking_number": return_record.get("tracking_number"),
            "created_at": return_record.get("created_at"),
            "shipping_label": return_record.get("shipping_label"),
            "message": f"Return {return_id}: {status_map.get(current_status, current_status)}. "
                      f"Expected refund: ${return_record.get('total_refund', 0):.2f}"
        }
        
    except Exception as e:
        logger.error(f"Get return status error: {e}")
        return {
            "success": False,
            "error": str(e)
        }
