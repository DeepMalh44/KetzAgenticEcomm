"""
Shopping Concierge Agent
=========================

Handles product discovery, search, recommendations, and project guidance.
"""

from typing import Optional, List, Dict, Any
import structlog

logger = structlog.get_logger(__name__)


# Project recommendations database
PROJECT_RECOMMENDATIONS = {
    "bathroom_renovation": {
        "description": "Complete bathroom renovation project",
        "budget": {
            "estimate": "$5,000 - $15,000",
            "items": [
                {"category": "plumbing", "items": ["toilet", "vanity", "faucet", "shower head"]},
                {"category": "flooring", "items": ["tile", "grout", "underlayment"]},
                {"category": "paint", "items": ["bathroom paint", "primer", "caulk"]},
                {"category": "electrical", "items": ["exhaust fan", "lighting", "GFCI outlets"]},
                {"category": "hardware", "items": ["towel bars", "toilet paper holder", "mirror"]}
            ]
        },
        "mid_range": {
            "estimate": "$10,000 - $25,000",
            "items": [
                {"category": "plumbing", "items": ["designer toilet", "double vanity", "rain shower system"]},
                {"category": "flooring", "items": ["porcelain tile", "heated floor mat"]},
                {"category": "kitchen_bath", "items": ["quartz countertop", "undermount sink"]}
            ]
        },
        "premium": {
            "estimate": "$25,000 - $50,000+",
            "items": [
                {"category": "plumbing", "items": ["smart toilet", "freestanding tub", "custom shower"]},
                {"category": "flooring", "items": ["marble tile", "radiant floor heating"]},
                {"category": "kitchen_bath", "items": ["custom cabinetry", "marble countertop"]}
            ]
        }
    },
    "kitchen_remodel": {
        "description": "Kitchen remodeling project",
        "budget": {
            "estimate": "$10,000 - $25,000",
            "items": [
                {"category": "kitchen_bath", "items": ["cabinet refacing", "laminate countertop", "sink"]},
                {"category": "appliances", "items": ["refrigerator", "range", "dishwasher"]},
                {"category": "flooring", "items": ["vinyl plank", "underlayment"]}
            ]
        },
        "mid_range": {
            "estimate": "$25,000 - $50,000",
            "items": [
                {"category": "kitchen_bath", "items": ["new cabinets", "quartz countertop", "farmhouse sink"]},
                {"category": "appliances", "items": ["stainless appliance package"]},
                {"category": "flooring", "items": ["hardwood", "tile backsplash"]}
            ]
        },
        "premium": {
            "estimate": "$50,000 - $100,000+",
            "items": [
                {"category": "kitchen_bath", "items": ["custom cabinets", "granite countertop", "pot filler"]},
                {"category": "appliances", "items": ["professional range", "built-in refrigerator"]},
                {"category": "flooring", "items": ["natural stone", "custom backsplash"]}
            ]
        }
    },
    "deck_building": {
        "description": "Build a new deck",
        "budget": {
            "estimate": "$2,000 - $8,000",
            "items": [
                {"category": "building_materials", "items": ["pressure treated lumber", "deck screws", "joist hangers"]},
                {"category": "hand_tools", "items": ["hammer", "level", "tape measure"]},
                {"category": "power_tools", "items": ["circular saw", "drill"]}
            ]
        },
        "mid_range": {
            "estimate": "$8,000 - $20,000",
            "items": [
                {"category": "building_materials", "items": ["composite decking", "aluminum railings"]},
                {"category": "power_tools", "items": ["miter saw", "impact driver"]},
                {"category": "outdoor_garden", "items": ["deck lighting", "post caps"]}
            ]
        },
        "premium": {
            "estimate": "$20,000 - $50,000+",
            "items": [
                {"category": "building_materials", "items": ["premium composite", "cable railings"]},
                {"category": "outdoor_garden", "items": ["built-in seating", "pergola kit", "outdoor kitchen"]}
            ]
        }
    },
    "painting": {
        "description": "Interior or exterior painting project",
        "budget": {
            "estimate": "$200 - $500 per room",
            "items": [
                {"category": "paint", "items": ["interior paint", "primer", "painters tape"]},
                {"category": "hand_tools", "items": ["paint brushes", "rollers", "trays", "drop cloths"]}
            ]
        },
        "mid_range": {
            "estimate": "$500 - $1,000 per room",
            "items": [
                {"category": "paint", "items": ["premium paint", "quality primer", "specialty finishes"]},
                {"category": "power_tools", "items": ["paint sprayer"]}
            ]
        },
        "premium": {
            "estimate": "$1,000+ per room",
            "items": [
                {"category": "paint", "items": ["designer paint", "specialty primers", "decorative finishes"]},
                {"category": "hand_tools", "items": ["professional brush set", "texturing tools"]}
            ]
        }
    },
    "flooring_installation": {
        "description": "New flooring installation",
        "budget": {
            "estimate": "$3 - $5 per sqft",
            "items": [
                {"category": "flooring", "items": ["laminate flooring", "underlayment", "transition strips"]},
                {"category": "hand_tools", "items": ["pry bar", "tapping block", "spacers"]}
            ]
        },
        "mid_range": {
            "estimate": "$6 - $10 per sqft",
            "items": [
                {"category": "flooring", "items": ["engineered hardwood", "premium underlayment"]},
                {"category": "power_tools", "items": ["flooring nailer", "miter saw"]}
            ]
        },
        "premium": {
            "estimate": "$10 - $20+ per sqft",
            "items": [
                {"category": "flooring", "items": ["solid hardwood", "exotic wood", "natural stone"]},
                {"category": "hand_tools", "items": ["professional installation kit"]}
            ]
        }
    },
    "plumbing_repair": {
        "description": "Plumbing repairs and upgrades",
        "budget": {
            "estimate": "$50 - $200",
            "items": [
                {"category": "plumbing", "items": ["faucet repair kit", "washers", "plumbers tape"]},
                {"category": "hand_tools", "items": ["pipe wrench", "basin wrench", "plunger"]}
            ]
        },
        "mid_range": {
            "estimate": "$200 - $1,000",
            "items": [
                {"category": "plumbing", "items": ["new faucet", "garbage disposal", "water filter"]},
                {"category": "power_tools", "items": ["pipe cutter", "drain snake"]}
            ]
        },
        "premium": {
            "estimate": "$1,000 - $5,000+",
            "items": [
                {"category": "plumbing", "items": ["tankless water heater", "whole house filter", "sump pump"]},
                {"category": "hand_tools", "items": ["professional plumbing kit"]}
            ]
        }
    },
    "electrical_work": {
        "description": "Electrical repairs and upgrades",
        "budget": {
            "estimate": "$50 - $200",
            "items": [
                {"category": "electrical", "items": ["outlets", "switches", "wire nuts", "electrical tape"]},
                {"category": "hand_tools", "items": ["wire strippers", "voltage tester", "screwdrivers"]}
            ]
        },
        "mid_range": {
            "estimate": "$200 - $1,000",
            "items": [
                {"category": "electrical", "items": ["dimmer switches", "ceiling fan", "under cabinet lighting"]},
                {"category": "power_tools", "items": ["drill", "fish tape"]}
            ]
        },
        "premium": {
            "estimate": "$1,000 - $5,000+",
            "items": [
                {"category": "electrical", "items": ["subpanel", "smart switches", "recessed lighting kit"]},
                {"category": "hand_tools", "items": ["professional electrician kit"]}
            ]
        }
    },
    "landscaping": {
        "description": "Landscaping and outdoor projects",
        "budget": {
            "estimate": "$500 - $2,000",
            "items": [
                {"category": "outdoor_garden", "items": ["plants", "mulch", "garden soil", "edging"]},
                {"category": "hand_tools", "items": ["shovel", "rake", "garden hose"]}
            ]
        },
        "mid_range": {
            "estimate": "$2,000 - $10,000",
            "items": [
                {"category": "outdoor_garden", "items": ["trees", "shrubs", "irrigation system", "landscape lighting"]},
                {"category": "building_materials", "items": ["pavers", "retaining wall blocks"]}
            ]
        },
        "premium": {
            "estimate": "$10,000 - $50,000+",
            "items": [
                {"category": "outdoor_garden", "items": ["outdoor kitchen", "water feature", "fire pit"]},
                {"category": "building_materials", "items": ["natural stone", "pergola"]}
            ]
        }
    },
    "garage_organization": {
        "description": "Garage organization and storage",
        "budget": {
            "estimate": "$200 - $500",
            "items": [
                {"category": "storage", "items": ["shelving units", "pegboard", "storage bins"]},
                {"category": "hand_tools", "items": ["drill", "level", "stud finder"]}
            ]
        },
        "mid_range": {
            "estimate": "$500 - $2,000",
            "items": [
                {"category": "storage", "items": ["wall systems", "workbench", "tool chest"]},
                {"category": "flooring", "items": ["garage floor coating"]}
            ]
        },
        "premium": {
            "estimate": "$2,000 - $10,000+",
            "items": [
                {"category": "storage", "items": ["custom cabinets", "ceiling storage", "slatwall system"]},
                {"category": "appliances", "items": ["garage heater", "air compressor"]}
            ]
        }
    },
    "fence_building": {
        "description": "Build a new fence",
        "budget": {
            "estimate": "$1,000 - $3,000",
            "items": [
                {"category": "building_materials", "items": ["fence pickets", "posts", "concrete", "brackets"]},
                {"category": "hand_tools", "items": ["post hole digger", "level", "hammer"]}
            ]
        },
        "mid_range": {
            "estimate": "$3,000 - $8,000",
            "items": [
                {"category": "building_materials", "items": ["cedar fence panels", "metal posts", "gate hardware"]},
                {"category": "power_tools", "items": ["post driver", "circular saw"]}
            ]
        },
        "premium": {
            "estimate": "$8,000 - $20,000+",
            "items": [
                {"category": "building_materials", "items": ["composite fence", "aluminum fence", "automatic gate"]},
                {"category": "electrical", "items": ["gate opener", "security lighting"]}
            ]
        }
    }
}


class ShoppingConciergeAgent:
    """Agent for product discovery, search, and recommendations."""
    
    def __init__(self, app_state):
        """Initialize the shopping concierge agent."""
        self.cosmos = app_state.cosmos
        self.search = app_state.search
        logger.info("ShoppingConciergeAgent initialized")
    
    async def search_products(
        self,
        query: str,
        category: Optional[str] = None,
        min_price: Optional[float] = None,
        max_price: Optional[float] = None,
        min_review_score: Optional[float] = None,
        min_return_count: Optional[int] = None,
        sort_by: Optional[str] = None,
        sort_order: str = "desc",
        limit: int = 5
    ) -> Dict[str, Any]:
        """
        Search for products using AI Search.
        
        Returns products matching the query with optional filters.
        Supports filtering by review_score and return_count.
        Can sort by review_score, return_count, price, or rating.
        """
        logger.info("Searching products", query=query, category=category, 
                   min_review_score=min_review_score, min_return_count=min_return_count,
                   sort_by=sort_by)
        
        try:
            # Use AI Search for full-featured search
            products = await self.search.search_products(
                query=query,
                category=category,
                min_price=min_price,
                max_price=max_price,
                min_review_score=min_review_score,
                min_return_count=min_return_count,
                sort_by=sort_by,
                sort_order=sort_order,
                limit=limit
            )
            
            if not products and category:
                # Retry without category filter - the model may have picked wrong category
                logger.info("No results with category filter, retrying without", query=query, category=category)
                products = await self.search.search_products(
                    query=query,
                    category=None,  # Remove category filter
                    min_price=min_price,
                    max_price=max_price,
                    min_review_score=min_review_score,
                    min_return_count=min_return_count,
                    sort_by=sort_by,
                    sort_order=sort_order,
                    limit=limit
                )
            
            if not products:
                # Fallback to Cosmos DB text search
                products = await self.cosmos.search_products_text(
                    query=query,
                    category=None,  # Don't filter by category in fallback
                    min_price=min_price,
                    max_price=max_price,
                    limit=limit
                )
            
            # Format results for voice response
            if products:
                result = {
                    "found": len(products),
                    "products": [
                        {
                            "id": p["id"],
                            "name": p["name"],
                            "price": p.get("sale_price") or p["price"],
                            "original_price": p["price"] if p.get("sale_price") else None,
                            "brand": p.get("brand", ""),
                            "rating": p.get("rating"),
                            "review_score": p.get("review_score"),
                            "return_count": p.get("return_count", 0),
                            "in_stock": p.get("in_stock", True)
                        }
                        for p in products
                    ],
                    "summary": self._create_search_summary(products, query)
                }
            else:
                result = {
                    "found": 0,
                    "products": [],
                    "summary": f"I couldn't find any products matching '{query}'. Would you like to try a different search or browse categories?"
                }
            
            return result
            
        except Exception as e:
            logger.error("Product search failed", error=str(e))
            return {
                "error": str(e),
                "summary": "I had trouble searching for products. Please try again."
            }
    
    def _create_search_summary(self, products: List[Dict], query: str) -> str:
        """Create a voice-friendly summary of search results."""
        if len(products) == 1:
            p = products[0]
            price = p.get("sale_price") or p["price"]
            return f"I found one product: {p['name']} by {p.get('brand', 'unknown brand')} for ${price:.2f}."
        
        price_range = [p.get("sale_price") or p["price"] for p in products]
        min_p, max_p = min(price_range), max(price_range)
        
        if min_p == max_p:
            price_info = f"priced at ${min_p:.2f}"
        else:
            price_info = f"ranging from ${min_p:.2f} to ${max_p:.2f}"
        
        return f"I found {len(products)} products matching '{query}', {price_info}. Would you like details on any of these?"
    
    async def get_product_details(self, product_id: str) -> Dict[str, Any]:
        """
        Get detailed information about a specific product.
        """
        logger.info("Getting product details", product_id=product_id)
        
        try:
            product = await self.cosmos.get_product(product_id)
            
            if not product:
                return {
                    "error": "Product not found",
                    "summary": "I couldn't find that product. It may no longer be available."
                }
            
            # Format for voice response
            price = product.get("sale_price") or product["price"]
            original = product["price"] if product.get("sale_price") else None
            
            summary_parts = [
                f"The {product['name']} by {product.get('brand', 'unknown brand')}",
                f"is priced at ${price:.2f}"
            ]
            
            if original and original > price:
                savings = original - price
                summary_parts.append(f"(save ${savings:.2f} from the original ${original:.2f})")
            
            if product.get("rating"):
                summary_parts.append(f"It has a {product['rating']:.1f} star rating")
                if product.get("review_count"):
                    summary_parts.append(f"from {product['review_count']} reviews")
            
            if not product.get("in_stock", True):
                summary_parts.append("Note: This item is currently out of stock")
            
            return {
                "product": product,
                "summary": ". ".join(summary_parts) + "."
            }
            
        except Exception as e:
            logger.error("Get product details failed", error=str(e))
            return {
                "error": str(e),
                "summary": "I had trouble getting the product details. Please try again."
            }
    
    async def check_inventory(
        self, 
        product_id: str, 
        zip_code: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Check product inventory and availability.
        """
        logger.info("Checking inventory", product_id=product_id, zip_code=zip_code)
        
        try:
            inventory = await self.cosmos.check_inventory(product_id, zip_code)
            
            if inventory.get("error"):
                return {
                    "error": inventory["error"],
                    "summary": "I couldn't find that product to check availability."
                }
            
            # Format for voice response
            if inventory["available"]:
                summary = f"Good news! This item is in stock with {inventory['quantity']} units available."
                if inventory.get("delivery_available"):
                    summary += f" Delivery is available, estimated {inventory['estimated_delivery']}."
                if inventory.get("store_pickup"):
                    summary += " Store pickup is also available."
            else:
                summary = "Unfortunately, this item is currently out of stock."
            
            return {
                "inventory": inventory,
                "summary": summary
            }
            
        except Exception as e:
            logger.error("Check inventory failed", error=str(e))
            return {
                "error": str(e),
                "summary": "I had trouble checking inventory. Please try again."
            }
    
    async def get_project_recommendations(
        self,
        project_type: str,
        budget: str = "mid_range"
    ) -> Dict[str, Any]:
        """
        Get product recommendations for a DIY project.
        """
        logger.info("Getting project recommendations", project=project_type, budget=budget)
        
        project = PROJECT_RECOMMENDATIONS.get(project_type)
        
        if not project:
            return {
                "error": f"Unknown project type: {project_type}",
                "summary": f"I don't have recommendations for that project type. Available projects include: bathroom renovation, kitchen remodel, deck building, painting, flooring installation, and more."
            }
        
        budget_data = project.get(budget, project.get("mid_range"))
        
        # Search for actual products in each category
        recommendations = []
        for category_info in budget_data["items"]:
            category = category_info["category"]
            for item_name in category_info["items"][:2]:  # Limit to 2 per category
                products = await self.cosmos.search_products_text(
                    query=item_name,
                    category=category,
                    limit=1
                )
                if products:
                    recommendations.append(products[0])
        
        # Create summary
        summary_parts = [
            f"For a {project['description'].lower()}, here's what you'll need.",
            f"Budget estimate: {budget_data['estimate']}."
        ]
        
        if recommendations:
            top_items = [r["name"] for r in recommendations[:3]]
            summary_parts.append(f"Key items include: {', '.join(top_items)}, and more.")
        
        return {
            "project": project_type,
            "budget_level": budget,
            "estimate": budget_data["estimate"],
            "categories": budget_data["items"],
            "sample_products": recommendations[:5],
            "summary": " ".join(summary_parts)
        }
    
    async def get_category_overview(self, category: str) -> Dict[str, Any]:
        """Get an overview of a product category."""
        logger.info("Getting category overview", category=category)
        
        try:
            products = await self.cosmos.get_products_by_category(category, limit=10)
            
            if not products:
                return {
                    "category": category,
                    "count": 0,
                    "summary": f"I don't have any products in the {category.replace('_', ' ')} category right now."
                }
            
            # Calculate stats
            prices = [p.get("sale_price") or p["price"] for p in products]
            avg_price = sum(prices) / len(prices)
            
            top_rated = sorted(
                [p for p in products if p.get("rating")],
                key=lambda x: x["rating"],
                reverse=True
            )[:3]
            
            summary = f"In {category.replace('_', ' ')}, I have {len(products)} products "
            summary += f"with prices averaging ${avg_price:.2f}. "
            
            if top_rated:
                summary += f"Top rated: {top_rated[0]['name']} with {top_rated[0]['rating']:.1f} stars."
            
            return {
                "category": category,
                "count": len(products),
                "price_range": {"min": min(prices), "max": max(prices), "avg": avg_price},
                "top_rated": top_rated,
                "sample_products": products[:5],
                "summary": summary
            }
            
        except Exception as e:
            logger.error("Category overview failed", error=str(e))
            return {
                "error": str(e),
                "summary": f"I had trouble getting the {category} category overview."
            }
