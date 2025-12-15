# =============================================================================
# KetzAgenticEcomm - Agent Tools
# =============================================================================
"""
Agent tools for the KetzAgenticEcomm voice assistant.
These tools are called by the GPT-4o Realtime API function calling.
"""

from .product_tools import search_products, get_product_details, get_recommendations
from .order_tools import create_order, get_order_status, cancel_order
from .return_tools import initiate_return, get_return_status, check_return_eligibility
from .image_tools import search_by_image

__all__ = [
    # Product tools
    "search_products",
    "get_product_details",
    "get_recommendations",
    # Order tools
    "create_order",
    "get_order_status",
    "cancel_order",
    # Return tools
    "initiate_return",
    "get_return_status",
    "check_return_eligibility",
    # Image tools
    "search_by_image",
]
