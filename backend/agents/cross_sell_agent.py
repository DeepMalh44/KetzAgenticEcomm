"""
Cross-Sell Agent
================

Generates intelligent cross-sell recommendations using GPT-4o.
Suggests complementary products based on:
- Search context (what customer is browsing)
- Cart contents (what customer is buying)
- Category relationships

Trigger strategies:
- On search: Light suggestions (shown in "You may like" section)
- On cart add: Stronger recommendations - updates (not appends) on each add
"""

from typing import Optional, List, Dict, Any
import structlog
from openai import AsyncAzureOpenAI
from azure.identity import DefaultAzureCredential, get_bearer_token_provider

from config import settings

logger = structlog.get_logger(__name__)


# Category relevance mapping for cross-sell filtering
# Maps a source category to acceptable recommendation categories
# NOTE: For categories where we lack specific accessories in the catalog,
# we set empty list to disable cross-sell (better than showing irrelevant products)
RELEVANT_CATEGORIES = {
    "flooring": [],  # Disabled - catalog lacks flooring accessories (underlayment, nailers, etc.)
    "paint": ["hand_tools", "building_materials", "safety", "cleaning"],
    "plumbing": ["hand_tools", "power_tools", "building_materials", "safety"],
    "electrical": ["hand_tools", "power_tools", "safety", "lighting"],
    "appliances": ["plumbing", "electrical", "cleaning", "storage", "appliance_parts"],
    "appliance_parts": ["appliances", "plumbing", "cleaning", "storage"],  # Water filters, etc.
    "power_tools": ["hand_tools", "safety", "storage", "building_materials"],
    "hand_tools": ["power_tools", "safety", "storage", "building_materials"],
    "hvac": ["electrical", "hand_tools", "safety"],
    "building_materials": ["hand_tools", "power_tools", "safety", "paint"],
    "outdoor_garden": ["power_tools", "hand_tools", "building_materials", "storage"],
    "outdoor_living": ["outdoor_garden", "hand_tools", "building_materials", "storage"],
    "kitchen_bath": ["plumbing", "appliances", "storage", "lighting"],
    "lighting": ["electrical", "hand_tools", "smart_home"],
    "storage": ["hand_tools", "building_materials"],
    "safety": ["hand_tools", "power_tools"],
    "hardware": ["hand_tools", "building_materials", "safety"],
    "smart_home": ["electrical", "lighting", "hardware"],
}


# Fallback category-based cross-sell rules
# Used when GPT is unavailable or for instant recommendations
CROSS_SELL_RULES = {
    # Appliances -> Accessories & Installation items
    "appliances": {
        "refrigerator": ["water filter", "refrigerator water filter", "ice maker", "appliance cleaner"],
        "washer": ["dryer", "washer hose", "drain pan", "pedestal"],
        "dryer": ["washer", "dryer vent kit", "lint trap"],
        "dishwasher": ["rinse aid", "installation kit"],
        "range": ["range hood", "cookware", "oven cleaner"],
        "default": ["appliance installation", "power strip", "appliance cleaner"]
    },
    
    # Flooring -> Installation & Finishing
    "flooring": {
        "hardwood": ["underlayment", "floor finish", "wood filler", "flooring nailer", "transition strips", "knee pads"],
        "laminate": ["underlayment", "transition strips", "tapping block", "pull bar", "spacers"],
        "vinyl": ["floor adhesive", "transition strips", "seam sealer", "utility knife"],
        "tile": ["thinset mortar", "grout", "tile spacers", "tile saw", "knee pads", "grout float"],
        "default": ["underlayment", "transition strips", "flooring tools", "knee pads"]
    },
    
    # Paint -> Supplies & Prep
    "paint": {
        "interior": ["paint brushes", "rollers", "painters tape", "drop cloth", "paint tray", "primer"],
        "exterior": ["paint brushes", "paint sprayer", "caulk", "sandpaper", "ladder"],
        "primer": ["paint", "sandpaper", "tack cloth"],
        "default": ["paint brushes", "rollers", "painters tape", "drop cloth"]
    },
    
    # Plumbing -> Tools & Parts
    "plumbing": {
        "faucet": ["supply lines", "plumbers putty", "pipe wrench", "teflon tape", "drain assembly"],
        "toilet": ["wax ring", "toilet supply line", "toilet seat", "plunger", "toilet auger"],
        "water_heater": ["expansion tank", "water heater pan", "flex connectors"],
        "water_filter": ["filter replacement", "water test kit", "tubing"],
        "default": ["teflon tape", "pipe wrench", "plumbers putty", "supply lines"]
    },
    
    # Power Tools -> Accessories
    "power_tools": {
        "drill": ["drill bits", "screwdriver bits", "battery", "charger", "tool bag"],
        "saw": ["saw blades", "safety glasses", "hearing protection", "clamps", "workbench"],
        "sander": ["sandpaper", "dust mask", "shop vacuum", "wood filler"],
        "default": ["safety glasses", "hearing protection", "tool bag", "battery"]
    },
    
    # Hand Tools -> Complementary
    "hand_tools": {
        "hammer": ["nails", "nail set", "pry bar", "tool belt"],
        "screwdriver": ["screws", "drill bits", "magnetic holder"],
        "wrench": ["socket set", "extension bar", "breaker bar"],
        "default": ["tool bag", "gloves", "flashlight"]
    },
    
    # Electrical -> Safety & Accessories
    "electrical": {
        "outlet": ["outlet cover", "wire nuts", "electrical tape", "voltage tester"],
        "switch": ["switch plate", "wire stripper", "screwdriver"],
        "lighting": ["light bulbs", "dimmer switch", "wire nuts", "electrical box"],
        "default": ["voltage tester", "wire nuts", "electrical tape"]
    },
    
    # HVAC/Filters -> Maintenance
    "hvac": {
        "air_filter": ["vent covers", "hvac tape", "thermostat"],
        "thermostat": ["batteries", "wire labels", "level"],
        "default": ["air filter", "vent covers", "hvac tape"]
    },
    
    # Building Materials -> Fasteners & Tools
    "building_materials": {
        "lumber": ["screws", "nails", "wood glue", "saw", "level", "tape measure"],
        "drywall": ["drywall screws", "joint compound", "tape", "drywall saw", "sanding sponge"],
        "default": ["screws", "level", "tape measure", "safety glasses"]
    },
    
    # Outdoor/Garden -> Accessories
    "outdoor_garden": {
        "grill": ["grill cover", "grilling tools", "propane tank", "grill brush"],
        "patio": ["outdoor cushions", "umbrella", "outdoor rug"],
        "default": ["outdoor lighting", "garden hose", "storage"]
    }
}


class CrossSellAgent:
    """Agent for GPT-powered cross-sell recommendations."""
    
    def __init__(self, app_state):
        """Initialize the cross-sell agent with services."""
        self.cosmos = app_state.cosmos
        self.search = app_state.search
        
        # Initialize Azure OpenAI client with managed identity (Azure AD token)
        credential = DefaultAzureCredential()
        token_provider = get_bearer_token_provider(
            credential,
            "https://cognitiveservices.azure.com/.default"
        )
        
        self.openai_client = AsyncAzureOpenAI(
            azure_ad_token_provider=token_provider,
            api_version="2024-02-15-preview",
            azure_endpoint=settings.azure_openai_endpoint
        )
        
        logger.info("CrossSellAgent initialized with managed identity")
    
    async def get_cross_sell_for_search(
        self,
        search_query: str,
        search_results: List[Dict],
        limit: int = 4
    ) -> Dict[str, Any]:
        """
        Get cross-sell recommendations based on a search query.
        Lighter suggestions - shown in "You may like" section.
        
        Args:
            search_query: The user's search query
            search_results: Products found in the search
            limit: Maximum recommendations to return
        """
        logger.info("Getting cross-sell for search", query=search_query, result_count=len(search_results))
        
        try:
            if not search_results:
                return {
                    "success": False,
                    "recommendations": [],
                    "context": "search",
                    "based_on": search_query
                }
            
            # Get the primary category from search results
            categories = [p.get("category", "") for p in search_results if p.get("category")]
            primary_category = categories[0] if categories else None
            original_category = primary_category.lower() if primary_category else ""
            
            # DEBUG: Log the category being checked
            print(f"[CROSS-SELL DEBUG] original_category='{original_category}', in_dict={original_category in RELEVANT_CATEGORIES}, value={RELEVANT_CATEGORIES.get(original_category, 'NOT_IN_DICT')}")
            
            # EARLY EXIT: If category is explicitly disabled (in dict with empty list), skip cross-sell entirely
            if original_category in RELEVANT_CATEGORIES and not RELEVANT_CATEGORIES[original_category]:
                logger.info(
                    "[CROSS-SELL FILTER] DISABLED - category has no acceptable cross-sell",
                    original_category=original_category
                )
                return {
                    "success": True,
                    "recommendations": [],
                    "context": "search",
                    "based_on": search_query,
                    "query_used": None,
                    "summary": None
                }
            
            # Use GPT to generate smart recommendation query
            recommendation_query = await self._generate_recommendation_query_gpt(
                context="search",
                products=search_results[:3],  # Use top 3 products for context
                search_query=search_query
            )
            
            # If GPT fails, fall back to rules
            if not recommendation_query:
                recommendation_query = self._get_fallback_recommendations(
                    category=primary_category,
                    products=search_results[:3]
                )
            
            # Search for recommended products
            print(f"[CROSS-SELL SEARCH] Querying with: {recommendation_query}")
            recommendations = await self.search.search_products(
                query=recommendation_query,
                limit=limit + 10  # Get extra to filter out original products and irrelevant categories
            )
            
            print(f"[CROSS-SELL SEARCH] Got {len(recommendations) if recommendations else 0} results")
            if recommendations:
                print(f"[CROSS-SELL SEARCH] First 3: {[r.get('name') for r in recommendations[:3]]}")
                print(f"[CROSS-SELL SEARCH] Categories: {[r.get('category') for r in recommendations[:5]]}")
            
            # Filter out products from the original search
            original_ids = {p.get("id") for p in search_results}
            original_names = {p.get("name", "").lower() for p in search_results}
            
            # Get acceptable categories for cross-sell (already validated above)
            acceptable_categories = RELEVANT_CATEGORIES.get(original_category, None)
            
            filtered_recommendations = []
            print(f"[CROSS-SELL FILTER] Starting filter: acceptable_categories={acceptable_categories}, num_recs={len(recommendations) if recommendations else 0}")
            for rec in recommendations:
                if rec.get("id") not in original_ids:
                    rec_name = rec.get("name", "").lower()
                    rec_category = (rec.get("category", "") or "").lower()
                    
                    print(f"[CROSS-SELL FILTER] Checking: {rec.get('name')[:40]} | category={rec_category} | acceptable={acceptable_categories}")
                    
                    # Check if it's the same category as original (skip same category products)
                    if rec_category == original_category:
                        print(f"[CROSS-SELL FILTER] SKIPPED - same category as original ({original_category})")
                        continue
                    
                    # Check if it's a similar product name (skip duplicates)
                    is_similar = any(
                        name in rec_name or rec_name in name 
                        for name in original_names
                    )
                    if is_similar:
                        print("[CROSS-SELL FILTER] SKIPPED - similar product name")
                        continue
                    
                    # Check if the category is relevant for cross-sell
                    # IMPORTANT: If category is NOT in dict, we should also filter (default to empty = no cross-sell)
                    # This prevents showing random products for unknown categories
                    if acceptable_categories is None:
                        # Category not in our mapping - treat as "allow cross-sell from same category" (filtered above)
                        # OR treat as "no cross-sell" - let's log and skip for safety
                        print(f"[CROSS-SELL FILTER] SKIPPED - original category '{original_category}' not in RELEVANT_CATEGORIES mapping")
                        continue
                    
                    if rec_category not in acceptable_categories:
                        print(f"[CROSS-SELL FILTER] SKIPPED - category '{rec_category}' not in acceptable: {acceptable_categories}")
                        continue
                    
                    print(f"[CROSS-SELL FILTER] PASSED - adding {rec.get('name')[:30]}")
                    filtered_recommendations.append(rec)
            
            final_recs = filtered_recommendations[:limit]
            
            # Log what we filtered
            print(f"[CROSS-SELL] Filtering complete: before={len(recommendations) if recommendations else 0}, after={len(final_recs)}")
            
            # If we got no results from specific queries, DON'T fall back to generic category searches
            # It's better to show no cross-sell than irrelevant products
            # The category-based fallback was returning generic tools not related to the actual product
            
            return {
                "success": True,
                "recommendations": final_recs,
                "context": "search",
                "based_on": search_query,
                "query_used": recommendation_query,
                "summary": self._create_summary(final_recs, "search", search_query)
            }
            
        except Exception as e:
            logger.error("Cross-sell for search failed", error=str(e))
            return {
                "success": False,
                "recommendations": [],
                "error": str(e)
            }
    
    async def get_cross_sell_for_cart(
        self,
        cart_items: List[Dict],
        limit: int = 6
    ) -> Dict[str, Any]:
        """
        Get cross-sell recommendations based on cart contents.
        Stronger recommendations - what customer will need for their purchase.
        Updates (replaces) on each cart add rather than appending.
        
        Args:
            cart_items: Products currently in the cart
            limit: Maximum recommendations to return
        """
        logger.info("Getting cross-sell for cart", item_count=len(cart_items))
        
        try:
            if not cart_items:
                return {
                    "success": False,
                    "recommendations": [],
                    "context": "cart",
                    "based_on": []
                }
            
            # Use GPT to analyze cart and suggest what else is needed
            recommendation_query = await self._generate_recommendation_query_gpt(
                context="cart",
                products=cart_items,
                search_query=None
            )
            
            # If GPT fails, fall back to rules
            if not recommendation_query:
                recommendation_query = self._get_fallback_recommendations(
                    category=cart_items[0].get("category") if cart_items else None,
                    products=cart_items
                )
            
            # Search for recommended products
            recommendations = await self.search.search_products(
                query=recommendation_query,
                limit=limit + len(cart_items)
            )
            
            # Filter out products already in cart
            cart_ids = {item.get("id") or item.get("product_id") for item in cart_items}
            cart_names = {item.get("name", "").lower() for item in cart_items}
            
            filtered_recommendations = []
            for rec in recommendations:
                if rec.get("id") not in cart_ids:
                    rec_name = rec.get("name", "").lower()
                    is_similar = any(
                        name in rec_name or rec_name in name 
                        for name in cart_names
                    )
                    if not is_similar:
                        filtered_recommendations.append(rec)
            
            final_recs = filtered_recommendations[:limit]
            product_names = [item.get("name", "product") for item in cart_items[:3]]
            
            return {
                "success": True,
                "recommendations": final_recs,
                "context": "cart",
                "based_on": product_names,
                "query_used": recommendation_query,
                "summary": self._create_summary(final_recs, "cart", product_names)
            }
            
        except Exception as e:
            logger.error("Cross-sell for cart failed", error=str(e))
            return {
                "success": False,
                "recommendations": [],
                "error": str(e)
            }
    
    async def _generate_recommendation_query_gpt(
        self,
        context: str,
        products: List[Dict],
        search_query: Optional[str] = None
    ) -> Optional[str]:
        """
        Use GPT to generate a smart search query for cross-sell products.
        
        Args:
            context: 'search' or 'cart'
            products: Products to base recommendations on
            search_query: Original search query (for search context)
        """
        try:
            # Build product context
            product_info = []
            for p in products[:5]:  # Limit to 5 products for context
                info = f"- {p.get('name', 'Unknown')} (category: {p.get('category', 'unknown')})"
                product_info.append(info)
            
            products_text = "\n".join(product_info)
            
            if context == "search":
                prompt = f"""You are a home improvement store expert. A customer searched for: "{search_query}"

They found these products:
{products_text}

Generate a search query to find complementary products they might also need. Think about:
- Tools or supplies needed to install/use these products
- Related accessories or parts
- Safety equipment if needed
- Products that are commonly bought together

Respond with ONLY a search query (no explanation, just the search terms). Keep it concise (3-6 words).
Example: "underlayment transition strips flooring tools" or "paint brushes rollers tape" """

            else:  # cart context
                prompt = f"""You are a home improvement store expert. A customer has these items in their cart:
{products_text}

Generate a search query to find products they'll likely need to complete their project. Think about:
- Installation supplies and tools
- Related accessories or parts  
- Safety equipment
- Commonly forgotten items for this type of project

Respond with ONLY a search query (no explanation, just the search terms). Keep it concise (3-6 words).
Example: "underlayment transition strips flooring tools" or "wax ring supply line toilet seat" """

            response = await self.openai_client.chat.completions.create(
                model=settings.azure_openai_deployment,
                messages=[
                    {"role": "system", "content": "You are a helpful home improvement expert. Respond only with search terms, no explanations."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=50
            )
            
            query = response.choices[0].message.content.strip()
            # Remove quotes if GPT wrapped the query
            query = query.strip('"\'')
            logger.info("GPT generated cross-sell query", query=query)
            return query
            
        except Exception as e:
            logger.error("GPT recommendation query failed", error=str(e))
            return None
    
    def _get_fallback_recommendations(
        self,
        category: Optional[str],
        products: List[Dict]
    ) -> str:
        """
        Generate fallback search query using rule-based approach.
        Used when GPT is unavailable.
        """
        if not category:
            return "home improvement essentials tools"
        
        category_lower = category.lower().replace("_", " ")
        
        # Find matching category rules
        for cat_key, rules in CROSS_SELL_RULES.items():
            if cat_key in category_lower or category_lower in cat_key:
                # Try to match specific subcategory
                for product in products:
                    name_lower = product.get("name", "").lower()
                    for subcat, items in rules.items():
                        if subcat != "default" and subcat in name_lower:
                            return " ".join(items[:4])
                
                # Fall back to default for category
                default_items = rules.get("default", [])
                return " ".join(default_items[:4])
        
        # Generic fallback
        return f"{category} accessories supplies tools"
    
    def _create_summary(
        self,
        recommendations: List[Dict],
        context: str,
        based_on: Any
    ) -> str:
        """Create a voice-friendly summary of recommendations."""
        if not recommendations:
            return "I don't have additional recommendations right now."
        
        rec_names = [r.get("name", "product") for r in recommendations[:3]]
        
        if context == "search":
            return f"Based on your search for {based_on}, you might also need: {', '.join(rec_names)}."
        else:
            products_text = ", ".join(based_on[:2]) if isinstance(based_on, list) else based_on
            return f"To complete your project with {products_text}, you might also need: {', '.join(rec_names)}."
