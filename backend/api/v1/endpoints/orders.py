"""
Orders API Endpoints
=====================

REST API for order management.
"""

from typing import Optional, List
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel, Field
import structlog
import random

logger = structlog.get_logger(__name__)

router = APIRouter()


class OrderItem(BaseModel):
    """Order item model."""
    product_id: str
    product_name: str
    quantity: int = Field(..., ge=1)
    unit_price: float
    total_price: float


class CreateOrderRequest(BaseModel):
    """Create order request."""
    items: List[dict] = Field(..., description="List of items with product_id and quantity")
    delivery_address: Optional[str] = None
    customer_id: Optional[str] = None


class OrderResponse(BaseModel):
    """Order response model."""
    id: str
    customer_id: Optional[str]
    items: List[OrderItem]
    subtotal: float
    tax: float
    total: float
    status: str
    delivery_address: Optional[str]
    estimated_delivery: Optional[str]
    created_at: datetime
    updated_at: datetime


@router.post("/", response_model=OrderResponse)
async def create_order(request: Request, order_request: CreateOrderRequest):
    """Create a new order."""
    try:
        cosmos_service = request.app.state.cosmos
        
        # Validate products and build order items
        order_items = []
        subtotal = 0.0
        
        for item in order_request.items:
            product = await cosmos_service.get_product(item["product_id"])
            if not product:
                raise HTTPException(
                    status_code=400, 
                    detail=f"Product not found: {item['product_id']}"
                )
            
            quantity = item.get("quantity", 1)
            unit_price = product.get("sale_price") or product["price"]
            total_price = unit_price * quantity
            
            order_items.append(OrderItem(
                product_id=item["product_id"],
                product_name=product["name"],
                quantity=quantity,
                unit_price=unit_price,
                total_price=total_price
            ))
            subtotal += total_price
        
        # Calculate tax (8.25% example)
        tax = round(subtotal * 0.0825, 2)
        total = round(subtotal + tax, 2)
        
        # Generate 4-digit order ID
        order_id = await cosmos_service.generate_order_id()
        
        # Create order
        order = {
            "id": order_id,
            "customer_id": order_request.customer_id,
            "items": [item.model_dump() for item in order_items],
            "subtotal": subtotal,
            "tax": tax,
            "total": total,
            "status": "confirmed",
            "delivery_address": order_request.delivery_address,
            "estimated_delivery": "3-5 business days",
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        
        await cosmos_service.create_order(order)
        
        logger.info("Order created", order_id=order["id"], total=total)
        
        return OrderResponse(**order)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Create order failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{order_id}", response_model=OrderResponse)
async def get_order(request: Request, order_id: str):
    """Get order by ID."""
    try:
        cosmos_service = request.app.state.cosmos
        order = await cosmos_service.get_order(order_id)
        
        if not order:
            raise HTTPException(status_code=404, detail="Order not found")
        
        return OrderResponse(**order)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Get order failed", error=str(e), order_id=order_id)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/customer/{customer_id}")
async def get_customer_orders(
    request: Request,
    customer_id: str,
    limit: int = Query(20, ge=1, le=100)
):
    """Get all orders for a specific customer."""
    try:
        cosmos_service = request.app.state.cosmos
        orders = await cosmos_service.get_orders_by_customer(customer_id, limit)
        
        return {
            "customer_id": customer_id,
            "orders": orders,
            "total": len(orders)
        }
        
    except Exception as e:
        logger.error("Get customer orders failed", error=str(e), customer_id=customer_id)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/")
async def list_orders(
    request: Request,
    customer_id: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    limit: int = Query(20, ge=1, le=100)
):
    """List orders with optional filters."""
    try:
        cosmos_service = request.app.state.cosmos
        orders = await cosmos_service.list_orders(
            customer_id=customer_id,
            status=status,
            limit=limit
        )
        
        return {
            "orders": orders,
            "total": len(orders)
        }
        
    except Exception as e:
        logger.error("List orders failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{order_id}/status")
async def update_order_status(
    request: Request,
    order_id: str,
    status: str = Query(..., description="New order status")
):
    """Update order status."""
    valid_statuses = ["confirmed", "processing", "shipped", "delivered", "cancelled", "return_requested", "returned"]
    if status not in valid_statuses:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid status. Must be one of: {valid_statuses}"
        )
    
    try:
        cosmos_service = request.app.state.cosmos
        updated = await cosmos_service.update_order_status(order_id, status)
        
        if not updated:
            raise HTTPException(status_code=404, detail="Order not found")
        
        return {"order_id": order_id, "status": status, "updated": True}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Update status failed", error=str(e), order_id=order_id)
        raise HTTPException(status_code=500, detail=str(e))


class UpdateOrderRequest(BaseModel):
    """Update order request."""
    status: Optional[str] = None
    delivery_address: Optional[str] = None


@router.patch("/{order_id}")
async def patch_order(
    request: Request,
    order_id: str,
    update_request: UpdateOrderRequest
):
    """Update order fields (PATCH)."""
    valid_statuses = ["confirmed", "processing", "shipped", "delivered", "cancelled", "return_requested", "returned"]
    
    if update_request.status and update_request.status not in valid_statuses:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid status. Must be one of: {valid_statuses}"
        )
    
    try:
        cosmos_service = request.app.state.cosmos
        
        updates = {}
        if update_request.status:
            updates["status"] = update_request.status
        if update_request.delivery_address:
            updates["delivery_address"] = update_request.delivery_address
        
        if not updates:
            raise HTTPException(status_code=400, detail="No valid fields to update")
        
        updated = await cosmos_service.update_order(order_id, updates)
        
        if not updated:
            raise HTTPException(status_code=404, detail="Order not found")
        
        return {"order_id": order_id, "updated": True, **updates}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Patch order failed", error=str(e), order_id=order_id)
        raise HTTPException(status_code=500, detail=str(e))


class ReturnRequest(BaseModel):
    """Return request model."""
    product_id: str
    reason: str = Field(..., description="Reason for return")
    quantity: int = Field(1, ge=1)


@router.post("/{order_id}/return")
async def initiate_return(
    request: Request,
    order_id: str,
    return_request: ReturnRequest
):
    """Initiate a return for an order item."""
    try:
        cosmos_service = request.app.state.cosmos
        
        # Get order
        order = await cosmos_service.get_order(order_id)
        if not order:
            raise HTTPException(status_code=404, detail="Order not found")
        
        # Verify product is in order
        product_in_order = any(
            item["product_id"] == return_request.product_id 
            for item in order.get("items", [])
        )
        if not product_in_order:
            raise HTTPException(
                status_code=400,
                detail="Product not found in this order"
            )
        
        # Create return record
        return_record = {
            "id": str(uuid.uuid4()),
            "order_id": order_id,
            "product_id": return_request.product_id,
            "reason": return_request.reason,
            "quantity": return_request.quantity,
            "status": "initiated",
            "return_label": f"RET-{uuid.uuid4().hex[:8].upper()}",
            "created_at": datetime.utcnow()
        }
        
        await cosmos_service.create_return(return_record)
        
        logger.info("Return initiated", return_id=return_record["id"], order_id=order_id)
        
        return {
            "return_id": return_record["id"],
            "return_label": return_record["return_label"],
            "status": "initiated",
            "instructions": "Please ship the item within 14 days using the provided return label."
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Initiate return failed", error=str(e), order_id=order_id)
        raise HTTPException(status_code=500, detail=str(e))
