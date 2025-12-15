"""
Returns Agent
==============

Handles return initiation, status, and refund processing.
"""

from typing import Optional, Dict, Any
from datetime import datetime
import uuid
import structlog

logger = structlog.get_logger(__name__)


# Return policy information
RETURN_POLICY = {
    "window_days": 90,
    "refund_processing_days": "3-5 business days",
    "return_shipping": "Free return shipping with prepaid label",
    "exceptions": [
        "Custom/special order items",
        "Hazardous materials",
        "Items marked final sale"
    ],
    "conditions": [
        "Item must be unused and in original packaging",
        "Include original receipt or order confirmation",
        "All parts and accessories must be included"
    ]
}

# Return reasons
RETURN_REASONS = {
    "defective": "The item is defective or damaged",
    "wrong_item": "Received the wrong item",
    "not_as_described": "Item doesn't match description",
    "changed_mind": "Changed my mind / No longer needed",
    "other": "Other reason"
}


class ReturnsAgent:
    """Agent for handling returns and refunds."""
    
    def __init__(self, app_state):
        """Initialize the returns agent."""
        self.cosmos = app_state.cosmos
        logger.info("ReturnsAgent initialized")
    
    async def initiate_return(
        self,
        order_id: str,
        product_id: str,
        reason: str,
        quantity: int = 1,
        description: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Initiate a return for a product from an order.
        """
        logger.info("Initiating return", order_id=order_id, product_id=product_id, reason=reason)
        
        try:
            # Get the order
            order = await self.cosmos.get_order(order_id)
            
            if not order:
                return {
                    "success": False,
                    "summary": f"I couldn't find order #{order_id}. Please check the order number."
                }
            
            # Check order status
            if order["status"] not in ["confirmed", "processing", "shipped", "delivered"]:
                return {
                    "success": False,
                    "summary": f"Order #{order_id} is {order['status']} and is not eligible for returns."
                }
            
            # Find the product in the order
            order_item = None
            for item in order.get("items", []):
                if item["product_id"] == product_id:
                    order_item = item
                    break
            
            if not order_item:
                return {
                    "success": False,
                    "summary": f"I couldn't find that product in order #{order_id}. Would you like me to look up the items in this order?"
                }
            
            # Check quantity
            if quantity > order_item["quantity"]:
                return {
                    "success": False,
                    "summary": f"You only ordered {order_item['quantity']} of this item. Please specify a valid quantity to return."
                }
            
            # Calculate refund amount
            refund_amount = order_item["unit_price"] * quantity
            
            # Create return record
            return_id = str(uuid.uuid4())[:8].upper()
            return_label = f"RET-{uuid.uuid4().hex[:8].upper()}"
            
            return_record = {
                "id": return_id,
                "order_id": order_id,
                "product_id": product_id,
                "product_name": order_item["product_name"],
                "quantity": quantity,
                "unit_price": order_item["unit_price"],
                "refund_amount": refund_amount,
                "reason": reason,
                "reason_description": RETURN_REASONS.get(reason, reason),
                "additional_description": description,
                "status": "initiated",
                "return_label": return_label,
                "created_at": datetime.utcnow()
            }
            
            await self.cosmos.create_return(return_record)
            
            # Create summary
            reason_text = RETURN_REASONS.get(reason, reason)
            summary = f"I've started a return for {order_item['product_name']} from order #{order_id}. "
            summary += f"Return ID: {return_id}. "
            summary += f"Your return label is: {return_label}. "
            summary += f"Once we receive the item, your refund of ${refund_amount:.2f} will be processed within {RETURN_POLICY['refund_processing_days']}. "
            summary += RETURN_POLICY['return_shipping'] + "."
            
            return {
                "success": True,
                "return_id": return_id,
                "return_label": return_label,
                "order_id": order_id,
                "product_name": order_item["product_name"],
                "quantity": quantity,
                "refund_amount": refund_amount,
                "status": "initiated",
                "instructions": [
                    "Print the return label",
                    "Pack the item securely in original packaging if possible",
                    "Attach the return label to the package",
                    "Drop off at any UPS or USPS location",
                    f"Refund will be processed within {RETURN_POLICY['refund_processing_days']} of receipt"
                ],
                "summary": summary
            }
            
        except Exception as e:
            logger.error("Initiate return failed", error=str(e))
            return {
                "success": False,
                "error": str(e),
                "summary": "I had trouble initiating the return. Please try again or contact customer support."
            }
    
    async def get_return_status(self, return_id: str) -> Dict[str, Any]:
        """
        Get the status of a return.
        """
        logger.info("Getting return status", return_id=return_id)
        
        try:
            return_record = await self.cosmos.get_return(return_id)
            
            if not return_record:
                return {
                    "found": False,
                    "summary": f"I couldn't find return #{return_id}. Please check the return ID."
                }
            
            status_messages = {
                "initiated": "has been initiated - please ship the item using the provided label",
                "in_transit": "is in transit back to our warehouse",
                "received": "has been received and is being inspected",
                "approved": "has been approved - your refund is being processed",
                "refunded": "has been completed and your refund has been issued",
                "rejected": "has been rejected - please contact customer support for details"
            }
            
            status = return_record["status"]
            status_text = status_messages.get(status, f"has status: {status}")
            
            summary = f"Return #{return_id} for {return_record['product_name']} {status_text}. "
            
            if status in ["initiated", "in_transit"]:
                summary += f"Return label: {return_record['return_label']}. "
            
            if status in ["approved", "refunded"]:
                summary += f"Refund amount: ${return_record['refund_amount']:.2f}."
            
            return {
                "found": True,
                "return_id": return_id,
                "order_id": return_record["order_id"],
                "product_name": return_record["product_name"],
                "status": status,
                "refund_amount": return_record["refund_amount"],
                "return_label": return_record.get("return_label"),
                "created_at": return_record.get("created_at"),
                "summary": summary
            }
            
        except Exception as e:
            logger.error("Get return status failed", error=str(e))
            return {
                "found": False,
                "error": str(e),
                "summary": "I had trouble looking up that return. Please try again."
            }
    
    async def get_return_policy(self) -> Dict[str, Any]:
        """
        Get the store's return policy information.
        """
        logger.info("Getting return policy")
        
        summary = f"Our return policy allows returns within {RETURN_POLICY['window_days']} days of purchase. "
        summary += f"{RETURN_POLICY['return_shipping']}. "
        summary += f"Refunds are processed within {RETURN_POLICY['refund_processing_days']}. "
        summary += "Items must be unused and in original packaging. "
        summary += "Some exceptions apply for custom orders and hazardous materials."
        
        return {
            "policy": RETURN_POLICY,
            "summary": summary
        }
    
    async def check_return_eligibility(
        self,
        order_id: str,
        product_id: str
    ) -> Dict[str, Any]:
        """
        Check if a product from an order is eligible for return.
        """
        logger.info("Checking return eligibility", order_id=order_id, product_id=product_id)
        
        try:
            order = await self.cosmos.get_order(order_id)
            
            if not order:
                return {
                    "eligible": False,
                    "reason": "Order not found",
                    "summary": f"I couldn't find order #{order_id}."
                }
            
            # Check if order is within return window
            order_date = order.get("created_at")
            if order_date:
                days_since_order = (datetime.utcnow() - order_date).days
                if days_since_order > RETURN_POLICY["window_days"]:
                    return {
                        "eligible": False,
                        "reason": "Return window expired",
                        "days_since_order": days_since_order,
                        "summary": f"Order #{order_id} was placed {days_since_order} days ago, which is outside our {RETURN_POLICY['window_days']}-day return window."
                    }
            
            # Find product in order
            product_found = False
            product_name = ""
            for item in order.get("items", []):
                if item["product_id"] == product_id:
                    product_found = True
                    product_name = item["product_name"]
                    break
            
            if not product_found:
                return {
                    "eligible": False,
                    "reason": "Product not in order",
                    "summary": f"I couldn't find that product in order #{order_id}."
                }
            
            # Product is eligible
            return {
                "eligible": True,
                "order_id": order_id,
                "product_id": product_id,
                "product_name": product_name,
                "return_window_days": RETURN_POLICY["window_days"],
                "free_returns": True,
                "summary": f"Good news! {product_name} from order #{order_id} is eligible for return. Would you like me to start the return process?"
            }
            
        except Exception as e:
            logger.error("Check eligibility failed", error=str(e))
            return {
                "eligible": False,
                "error": str(e),
                "summary": "I had trouble checking return eligibility. Please try again."
            }
