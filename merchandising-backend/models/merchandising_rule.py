"""
Merchandising Rule Models
==========================

Pydantic models for merchandising rules that pin/boost products.
"""

from datetime import datetime
from typing import List, Optional, Literal
from pydantic import BaseModel, Field
from uuid import uuid4


class RuleConditions(BaseModel):
    """Conditions that determine when a rule applies."""
    query_contains: Optional[List[str]] = Field(default=None, description="Apply if search query contains any of these terms")
    category: Optional[str] = Field(default=None, description="Apply to specific category")
    date_range: Optional[dict] = Field(default=None, description="Apply within date range {start, end}")


class RuleAction(BaseModel):
    """Action to apply to a product."""
    type: Literal["pin", "boost", "bury"] = Field(..., description="Type of action")
    productId: str = Field(..., description="Product ID to affect")
    position: Optional[int] = Field(default=None, description="Position for pin/bury actions")
    multiplier: Optional[float] = Field(default=None, description="Boost multiplier (e.g., 2.0)")


class MerchandisingRule(BaseModel):
    """Complete merchandising rule."""
    id: str = Field(default_factory=lambda: str(uuid4()), description="Unique rule ID")
    name: str = Field(..., description="Human-readable rule name")
    description: Optional[str] = Field(default=None, description="Rule description")
    conditions: RuleConditions = Field(..., description="When to apply this rule")
    actions: dict = Field(..., description="Actions to perform")
    enabled: bool = Field(default=True, description="Whether rule is active")
    priority: int = Field(default=10, description="Rule priority (higher = first)")
    createdBy: str = Field(default="system", description="User who created the rule")
    createdAt: datetime = Field(default_factory=datetime.utcnow)
    updatedAt: Optional[datetime] = Field(default=None)


class RuleCreate(BaseModel):
    """Create new rule request."""
    name: str
    description: Optional[str] = None
    conditions: RuleConditions
    actions: dict  # Flexible format from frontend
    enabled: bool = True
    priority: int = 10
    createdBy: str = "system"


class RuleUpdate(BaseModel):
    """Update existing rule request."""
    name: Optional[str] = None
    description: Optional[str] = None
    conditions: Optional[RuleConditions] = None
    actions: Optional[List[RuleAction]] = None
    enabled: Optional[bool] = None
    priority: Optional[int] = None


class RuleListResponse(BaseModel):
    """List of rules response."""
    rules: List[MerchandisingRule]
    total: int
