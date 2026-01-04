"""
GPT-4o Realtime WebSocket Endpoint
===================================

Native voice-to-voice communication using GPT-4o Realtime API.
Supports barge-in (user interruption) natively.
"""

import asyncio
import base64
import json
import logging
from typing import Optional, Any
from datetime import datetime
import uuid

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from openai import AsyncAzureOpenAI
import structlog

from config import settings
from agents.shopping_concierge import ShoppingConciergeAgent
from agents.orders_agent import OrdersAgent
from agents.returns_agent import ReturnsAgent
from agents.image_search_agent import ImageSearchAgent
from agents.cross_sell_agent import CrossSellAgent
from tools.youtube_tools import get_diy_videos

logger = structlog.get_logger(__name__)

router = APIRouter()


def serialize_for_json(obj: Any) -> Any:
    """Recursively convert datetime objects to ISO strings for JSON serialization."""
    if isinstance(obj, datetime):
        return obj.isoformat()
    elif isinstance(obj, dict):
        return {k: serialize_for_json(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [serialize_for_json(item) for item in obj]
    return obj


# System prompt for the home improvement assistant
SYSTEM_PROMPT = """You are Ketz, an expert AI assistant for a home improvement store similar to Lowe's or Home Depot.

You help customers with:
1. **Product Discovery**: Finding tools, building materials, paint, flooring, plumbing, electrical supplies, outdoor/garden equipment, kitchen & bath fixtures, and more.
2. **Project Guidance**: Offering step-by-step advice for DIY projects like bathroom renovations, deck building, painting rooms, installing flooring, etc.
3. **Product Comparisons**: Comparing brands, features, and prices to help customers make informed decisions.
4. **Order Management**: Checking order status, tracking deliveries, and managing purchases.
5. **Returns & Support**: Assisting with returns, exchanges, and product issues.
6. **Image Search**: When customers describe or upload images, help find visually similar products.
7. **DIY Tutorial Videos**: When customers are looking at products that require installation (HVAC filters, flooring, plumbing fixtures, light fixtures, appliances), proactively offer to show YouTube DIY tutorial videos.

## Communication Style:
- Be warm, helpful, and knowledgeable like a friendly store expert
- Use conversational language appropriate for voice interaction
- Keep responses concise but informative (voice interactions should be brief)
- Ask clarifying questions when the request is ambiguous
- Proactively suggest related products or helpful tips

## Product Categories Available:
- Power Tools (drills, saws, sanders)
- Hand Tools (hammers, screwdrivers, wrenches)
- Building Materials (lumber, drywall, concrete)
- Paint & Stains (interior, exterior, primers)
- Flooring (hardwood, tile, laminate, vinyl)
- Plumbing (faucets, pipes, water heaters)
- Electrical (outlets, switches, lighting)
- Kitchen & Bath (countertops, cabinets, fixtures)
- Outdoor & Garden (grills, patio furniture, plants)
- Storage & Organization (shelving, bins, garage)
- Hardware (fasteners, hinges, locks)
- Appliances (refrigerators, washers, HVAC)

## Available Functions:
- search_products: Search for products by name, category, or description
- search_products_by_image: Find visually similar products using image embeddings
- get_product_details: Get detailed information about a specific product
- check_inventory: Check product availability and stock levels
- add_to_cart: Add a product to the shopping cart (requires product_id - search first if needed)
- view_cart: Show the customer's shopping cart
- remove_from_cart: Remove a product from the cart
- clear_cart: Clear all items from the cart
- create_order: Place an order for products
- get_order_status: Check the status of an existing order
- initiate_return: Start a return process for a product
- get_project_recommendations: Get recommended products for a DIY project
- get_diy_videos: Search for YouTube DIY tutorial videos for product installation

## DIY Video Guidelines:
When customers are searching for or discussing products that typically need installation or replacement, ALWAYS use get_diy_videos to find helpful tutorials. This is a key feature - customers love seeing how-to videos! Call get_diy_videos for:
- HVAC filters, air filters, furnace filters
- Flooring (hardwood, laminate, vinyl, tile)
- Plumbing fixtures (faucets, toilets, garbage disposals)
- Light fixtures, ceiling fans
- Appliances that need installation
- Paint and painting supplies
- Any product where customer asks "how to install" or "how to replace"
After showing products, proactively offer: "Would you like me to find some DIY tutorial videos for installing this?"

## Cart Workflow:
When a customer asks to add something to their cart:
1. First, use search_products to find the product and get its ID
2. Then, use add_to_cart with the product_id from the search results
3. Confirm to the customer that the item was added

Always be helpful and guide customers toward finding exactly what they need for their home improvement projects!
"""


# Tools definition for GPT-4o Realtime
TOOLS = [
    {
        "type": "function",
        "name": "search_products",
        "description": "Search for products by name, category, keywords, or description. Use this when a customer is looking for a product or browsing a category.",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Search query - product name, category, or keywords"
                },
                "category": {
                    "type": "string",
                    "description": "Optional category filter (e.g., 'power_tools', 'flooring', 'plumbing')",
                    "enum": ["power_tools", "hand_tools", "building_materials", "paint", "flooring", "plumbing", "electrical", "kitchen_bath", "outdoor_garden", "storage", "hardware", "appliances"]
                },
                "min_price": {
                    "type": "number",
                    "description": "Minimum price filter"
                },
                "max_price": {
                    "type": "number",
                    "description": "Maximum price filter"
                },
                "limit": {
                    "type": "integer",
                    "description": "Maximum number of results (default 5)",
                    "default": 5
                }
            },
            "required": ["query"]
        }
    },
    {
        "type": "function",
        "name": "get_product_details",
        "description": "Get detailed information about a specific product including specifications, reviews, and availability.",
        "parameters": {
            "type": "object",
            "properties": {
                "product_id": {
                    "type": "string",
                    "description": "The unique product ID"
                }
            },
            "required": ["product_id"]
        }
    },
    {
        "type": "function",
        "name": "check_inventory",
        "description": "Check product availability and stock levels at nearby stores or for delivery.",
        "parameters": {
            "type": "object",
            "properties": {
                "product_id": {
                    "type": "string",
                    "description": "The product ID to check"
                },
                "zip_code": {
                    "type": "string",
                    "description": "Customer's zip code for local store availability"
                }
            },
            "required": ["product_id"]
        }
    },
    {
        "type": "function",
        "name": "create_order",
        "description": "Place an order for one or more products. Use this when the customer confirms they want to purchase.",
        "parameters": {
            "type": "object",
            "properties": {
                "items": {
                    "type": "array",
                    "description": "List of items to order",
                    "items": {
                        "type": "object",
                        "properties": {
                            "product_id": {"type": "string"},
                            "quantity": {"type": "integer"}
                        },
                        "required": ["product_id", "quantity"]
                    }
                },
                "delivery_address": {
                    "type": "string",
                    "description": "Delivery address for the order"
                }
            },
            "required": ["items"]
        }
    },
    {
        "type": "function",
        "name": "get_order_status",
        "description": "Get detailed status information about a specific order (backend query only). Use 'view_orders' or 'get_order_by_number' instead if customer wants to SEE their orders in the UI.",
        "parameters": {
            "type": "object",
            "properties": {
                "order_id": {
                    "type": "string",
                    "description": "The order ID to check"
                }
            },
            "required": ["order_id"]
        }
    },
    {
        "type": "function",
        "name": "initiate_return",
        "description": "Start a return process for a product from an existing order.",
        "parameters": {
            "type": "object",
            "properties": {
                "order_id": {
                    "type": "string",
                    "description": "The original order ID"
                },
                "product_id": {
                    "type": "string",
                    "description": "The product ID to return"
                },
                "reason": {
                    "type": "string",
                    "description": "Reason for the return",
                    "enum": ["defective", "wrong_item", "not_as_described", "changed_mind", "other"]
                }
            },
            "required": ["order_id", "product_id", "reason"]
        }
    },
    {
        "type": "function",
        "name": "search_similar_products",
        "description": "Find products that look similar to an uploaded image. Use when customer wants to find products matching a photo.",
        "parameters": {
            "type": "object",
            "properties": {
                "image_id": {
                    "type": "string",
                    "description": "The ID of the uploaded image to search with"
                },
                "limit": {
                    "type": "integer",
                    "description": "Maximum number of results",
                    "default": 5
                }
            },
            "required": ["image_id"]
        }
    },
    {
        "type": "function",
        "name": "get_project_recommendations",
        "description": "Get recommended products for a specific DIY project type.",
        "parameters": {
            "type": "object",
            "properties": {
                "project_type": {
                    "type": "string",
                    "description": "Type of home improvement project",
                    "enum": ["bathroom_renovation", "kitchen_remodel", "deck_building", "painting", "flooring_installation", "plumbing_repair", "electrical_work", "landscaping", "garage_organization", "fence_building"]
                },
                "budget": {
                    "type": "string",
                    "description": "Budget range for the project",
                    "enum": ["budget", "mid_range", "premium"]
                }
            },
            "required": ["project_type"]
        }
    },
    {
        "type": "function",
        "name": "add_to_cart",
        "description": "Add a product to the customer's shopping cart by searching for it by name. Use this when a customer wants to add an item to their cart.",
        "parameters": {
            "type": "object",
            "properties": {
                "product_name": {
                    "type": "string", 
                    "description": "The name or description of the product to search for and add to cart (e.g., 'DeWalt drill', 'hardwood flooring', 'hammer')"
                },
                "quantity": {
                    "type": "integer",
                    "description": "Number of items to add (default 1)",
                    "default": 1
                }
            },
            "required": ["product_name"]
        }
    },
    {
        "type": "function",
        "name": "view_cart",
        "description": "Show the customer their current shopping cart contents.",
        "parameters": {
            "type": "object",
            "properties": {},
            "required": []
        }
    },
    {
        "type": "function",
        "name": "remove_from_cart",
        "description": "Remove a product from the customer's shopping cart.",
        "parameters": {
            "type": "object",
            "properties": {
                "product_id": {
                    "type": "string",
                    "description": "The product ID to remove from cart"
                }
            },
            "required": ["product_id"]
        }
    },
    {
        "type": "function",
        "name": "clear_cart",
        "description": "Clear all items from the customer's shopping cart.",
        "parameters": {
            "type": "object",
            "properties": {},
            "required": []
        }
    },
    {
        "type": "function",
        "name": "get_diy_videos",
        "description": """Search for DIY tutorial videos on YouTube related to a product. 
IMPORTANT: Call this tool whenever a customer searches for products that require installation like HVAC filters, flooring, plumbing fixtures, light fixtures, appliances, or paint.
Also call when user asks 'how to install', 'how to replace', or mentions 'DIY'.
This helps customers see helpful installation tutorials alongside product results.
Returns popular, highly-viewed tutorial videos from YouTube.""",
        "parameters": {
            "type": "object",
            "properties": {
                "product_name": {
                    "type": "string",
                    "description": "The name of the product to find DIY tutorials for (e.g., 'HVAC air filter', 'vinyl plank flooring', 'bathroom faucet')"
                },
                "category": {
                    "type": "string",
                    "description": "Optional product category for better search results (e.g., 'hvac', 'flooring', 'plumbing', 'electrical', 'paint')"
                }
            },
            "required": ["product_name"]
        }
    },
    {
        "type": "function",
        "name": "view_orders",
        "description": "OPEN the orders popup UI to show the customer ALL their order history. Use when customer says 'show my orders', 'view my orders', 'check my orders', 'open my orders', or wants to SEE their order list.",
        "parameters": {
            "type": "object",
            "properties": {},
            "required": []
        }
    },
    {
        "type": "function",
        "name": "get_order_by_number",
        "description": "OPEN the orders popup UI filtered to a SPECIFIC order number. Use when customer says 'where is order X', 'show me order X', 'check order X status' where X is an order number.",
        "parameters": {
            "type": "object",
            "properties": {
                "order_number": {
                    "type": "string",
                    "description": "The order number or order ID to look up and display"
                }
            },
            "required": ["order_number"]
        }
    }
]


class RealtimeSession:
    """Manages a GPT-4o Realtime session with barge-in support."""
    
    def __init__(self, session_id: str, websocket: WebSocket, app_state):
        self.session_id = session_id
        self.websocket = websocket
        self.app_state = app_state
        self.openai_ws = None
        self.is_active = True
        self.websocket_closed = False
        self.conversation_items = []
        
        # Initialize agents
        self.shopping_agent = ShoppingConciergeAgent(app_state)
        self.orders_agent = OrdersAgent(app_state)
        self.returns_agent = ReturnsAgent(app_state)
        self.image_agent = ImageSearchAgent(app_state)
        self.cross_sell_agent = CrossSellAgent(app_state)
        
        logger.info("Realtime session created", session_id=session_id)
    
    async def connect_to_openai(self):
        """Establish WebSocket connection to GPT-4o Realtime API."""
        import websockets
        from azure.identity.aio import DefaultAzureCredential
        
        # Convert https:// endpoint to wss:// for WebSocket connection
        ws_endpoint = settings.azure_openai_endpoint.replace("https://", "wss://").rstrip("/")
        url = f"{ws_endpoint}/openai/realtime?api-version=2024-10-01-preview&deployment={settings.azure_openai_realtime_deployment}"
        
        print(f"[REALTIME] Connecting to: {url}")
        print(f"[REALTIME] Deployment: {settings.azure_openai_realtime_deployment}")
        print(f"[REALTIME] Has API key: {bool(settings.azure_openai_api_key)}")
        
        # Try API key first, fall back to Azure AD auth
        if settings.azure_openai_api_key:
            print("[REALTIME] Using API key authentication")
            headers = {
                "api-key": settings.azure_openai_api_key
            }
        else:
            # Use Azure AD authentication
            print("[REALTIME] Using Azure AD authentication (no API key)")
            try:
                credential = DefaultAzureCredential()
                print("[REALTIME] Getting token...")
                token = await credential.get_token("https://cognitiveservices.azure.com/.default")
                print(f"[REALTIME] Got Azure AD token (length: {len(token.token)})")
                headers = {
                    "Authorization": f"Bearer {token.token}"
                }
                await credential.close()
            except Exception as e:
                print(f"[REALTIME] Failed to get Azure AD token: {type(e).__name__}: {e}")
                logger.error("Failed to get Azure AD token", error=str(e), error_type=type(e).__name__, session_id=self.session_id)
                raise
        
        try:
            print("[REALTIME] Connecting WebSocket with 30s timeout...")
            self.openai_ws = await websockets.connect(
                url, 
                extra_headers=headers,
                open_timeout=30,
                close_timeout=10
            )
            print("[REALTIME] Connected to GPT-4o Realtime successfully!")
            logger.info("Connected to GPT-4o Realtime successfully", session_id=self.session_id)
        except Exception as e:
            print(f"[REALTIME] Failed to connect: {type(e).__name__}: {e}")
            logger.error("Failed to connect to OpenAI Realtime WebSocket", 
                        error=str(e), 
                        error_type=type(e).__name__,
                        url=url,
                        session_id=self.session_id)
            raise
        
        # Configure the session
        await self.configure_session()
    
    async def configure_session(self):
        """Send session configuration to GPT-4o Realtime."""
        print(f"[CONFIG] Configuring session with {len(TOOLS)} tools")
        print(f"[CONFIG] Tools: {[t['name'] for t in TOOLS]}")
        config = {
            "type": "session.update",
            "session": {
                "modalities": ["text", "audio"],
                "instructions": SYSTEM_PROMPT,
                "voice": "alloy",  # Options: alloy, echo, shimmer
                "input_audio_format": "pcm16",
                "output_audio_format": "pcm16",
                "input_audio_transcription": {
                    "model": "whisper-1"
                },
                "turn_detection": {
                    "type": "server_vad",  # Server-side VAD for barge-in
                    "threshold": 0.5,
                    "prefix_padding_ms": 300,
                    "silence_duration_ms": 500
                },
                "tools": TOOLS,
                "tool_choice": "auto",
                "temperature": 0.7
            }
        }
        
        await self.openai_ws.send(json.dumps(config))
        logger.info("Session configured", session_id=self.session_id)
    
    async def handle_tool_call(self, tool_name: str, arguments: dict) -> str:
        """Execute a tool call and return the result."""
        logger.info("Handling tool call", tool=tool_name, args=arguments, session_id=self.session_id)
        print(f"[TOOL CALL] {tool_name} with args: {arguments}")  # Debug print
        
        try:
            if tool_name == "search_products":
                result = await self.shopping_agent.search_products(**arguments)
                
                # Trigger cross-sell recommendations based on search results
                print(f"[CROSS-SELL DEBUG] search_products result has products: {bool(result.get('products'))}, count: {len(result.get('products', []))}")
                if result.get("products"):
                    try:
                        print(f"[CROSS-SELL DEBUG] Calling get_cross_sell_for_search with query: {arguments.get('query', '')}")
                        cross_sell_result = await self.cross_sell_agent.get_cross_sell_for_search(
                            search_query=arguments.get("query", ""),
                            search_results=result["products"],
                            limit=4
                        )
                        print(f"[CROSS-SELL DEBUG] Result: success={cross_sell_result.get('success')}, recs={len(cross_sell_result.get('recommendations', []))}")
                        if cross_sell_result.get("success") and cross_sell_result.get("recommendations"):
                            print(f"[CROSS-SELL] Found {len(cross_sell_result['recommendations'])} recommendations for search")
                            print(f"[CROSS-SELL DEBUG] websocket_closed={self.websocket_closed}")
                            if not self.websocket_closed:
                                await self.websocket.send_json({
                                    "type": "cross_sell",
                                    "context": "search",
                                    "data": cross_sell_result
                                })
                                print(f"[CROSS-SELL DEBUG] Sent cross_sell message to frontend!")
                        else:
                            print(f"[CROSS-SELL DEBUG] No recommendations or not successful: {cross_sell_result}")
                    except Exception as cs_error:
                        print(f"[CROSS-SELL ERROR] Failed to get cross-sell: {cs_error}")
                        import traceback
                        traceback.print_exc()
                
                # Automatically fetch DIY videos for installation-related product categories
                query = arguments.get("query", "").lower()
                category = arguments.get("category", "").lower() if arguments.get("category") else ""
                
                # Categories and keywords that typically need installation tutorials
                diy_categories = ["hvac", "flooring", "plumbing", "electrical", "appliances", "paint", "kitchen_bath", "outdoor_garden"]
                diy_keywords = ["filter", "install", "replace", "faucet", "toilet", "flooring", "tile", "light", "fan", "heater", "thermostat", "disposal", "sink"]
                
                should_show_diy = (
                    category in diy_categories or 
                    any(kw in query for kw in diy_keywords)
                )
                
                if should_show_diy and result.get("products"):
                    print(f"[DIY VIDEOS] Auto-triggering for query: {query}, category: {category}")
                    # Get the first product name for video search
                    first_product = result["products"][0].get("name", query)
                    diy_result = await get_diy_videos(product_name=first_product, category=category or None)
                    
                    if diy_result.get("videos"):
                        print(f"[DIY VIDEOS] Auto-fetched {len(diy_result['videos'])} videos")
                        # Send DIY videos to frontend
                        if not self.websocket_closed:
                            await self.websocket.send_json({
                                "type": "diy_videos",
                                "data": diy_result
                            })
                            
            elif tool_name == "get_product_details":
                result = await self.shopping_agent.get_product_details(**arguments)
            elif tool_name == "check_inventory":
                result = await self.shopping_agent.check_inventory(**arguments)
            elif tool_name == "create_order":
                result = await self.orders_agent.create_order(**arguments)
            elif tool_name == "get_order_status":
                result = await self.orders_agent.get_order_status(**arguments)
            elif tool_name == "initiate_return":
                result = await self.returns_agent.initiate_return(**arguments)
            elif tool_name == "search_similar_products":
                result = await self.image_agent.search_similar(**arguments)
            elif tool_name == "get_project_recommendations":
                result = await self.shopping_agent.get_project_recommendations(**arguments)
            elif tool_name == "add_to_cart":
                # Search by product name and add to cart
                product_name = arguments.get("product_name", "")
                quantity = arguments.get("quantity", 1)
                print(f"[ADD TO CART] Searching for: '{product_name}', quantity={quantity}")
                
                product = None
                
                # Search for the product by name
                if product_name:
                    print(f"[ADD TO CART] Searching products with query: {product_name}")
                    search_results = await self.shopping_agent.search_products(query=product_name, limit=1)
                    print(f"[ADD TO CART] Search results: {search_results}")
                    
                    if search_results.get("products") and len(search_results["products"]) > 0:
                        found_product = search_results["products"][0]
                        found_product_id = found_product["id"]
                        print(f"[ADD TO CART] Found product: {found_product['name']} (ID: {found_product_id})")
                        
                        # Get full product details from Cosmos DB
                        product = await self.app_state.cosmos.get_product(found_product_id)
                        print(f"[ADD TO CART] Cosmos lookup result: {product is not None}")
                        
                        # If Cosmos lookup fails, use the search result directly
                        if not product:
                            print(f"[ADD TO CART] Using search result directly (Cosmos lookup failed)")
                            product = found_product
                
                if product:
                    result = {
                        "success": True,
                        "action": "add_to_cart",
                        "product": product,
                        "quantity": quantity,
                        "message": f"Added {quantity} x {product['name']} to your cart."
                    }
                    print(f"[ADD TO CART] Success: {result['message']}")
                    
                    # Trigger cross-sell recommendations for cart add
                    # Send updated cross-sell (replaces previous recommendations)
                    cross_sell_result = await self.cross_sell_agent.get_cross_sell_for_cart(
                        cart_items=[product],  # The newly added item
                        limit=6
                    )
                    if cross_sell_result.get("success") and cross_sell_result.get("recommendations"):
                        print(f"[CROSS-SELL] Found {len(cross_sell_result['recommendations'])} cart recommendations")
                        if not self.websocket_closed:
                            await self.websocket.send_json({
                                "type": "cross_sell",
                                "context": "cart",
                                "data": cross_sell_result
                            })
                else:
                    result = {"success": False, "error": f"Could not find product matching: {product_name}"}
                    print(f"[ADD TO CART] Failed: No products found")
            elif tool_name == "view_cart":
                result = {
                    "success": True,
                    "action": "view_cart",
                    "message": "Opening your shopping cart..."
                }
            elif tool_name == "remove_from_cart":
                product_id = arguments.get("product_id")
                result = {
                    "success": True,
                    "action": "remove_from_cart",
                    "product_id": product_id,
                    "message": f"Removed item from your cart."
                }
            elif tool_name == "clear_cart":
                result = {
                    "success": True,
                    "action": "clear_cart",
                    "message": "Your cart has been cleared."
                }
            elif tool_name == "get_diy_videos":
                # Get DIY tutorial videos from YouTube
                print(f"[DIY VIDEOS] Tool called with arguments: {arguments}")
                result = await get_diy_videos(**arguments)
                print(f"[DIY VIDEOS] Result: found={result.get('found', 0)}, videos={len(result.get('videos', []))}")
            elif tool_name == "view_orders":
                result = {
                    "success": True,
                    "action": "view_orders",
                    "message": "Opening your order history..."
                }
            elif tool_name == "get_order_by_number":
                order_number = arguments.get("order_number", "")
                result = {
                    "success": True,
                    "action": "view_orders",
                    "order_number": order_number,
                    "message": f"Looking up order {order_number}..."
                }
            else:
                result = {"error": f"Unknown tool: {tool_name}"}
            
            # Serialize result to handle datetime objects
            serialized_result = serialize_for_json(result)
            return json.dumps(serialized_result)
            
        except Exception as e:
            logger.error("Tool call failed", tool=tool_name, error=str(e))
            return json.dumps({"error": str(e)})
    
    async def process_openai_messages(self):
        """Process messages from GPT-4o Realtime API."""
        try:
            async for message in self.openai_ws:
                if not self.is_active:
                    break
                
                data = json.loads(message)
                event_type = data.get("type", "")
                
                # Log events for debugging
                if event_type not in ["response.audio.delta"]:  # Don't log audio deltas
                    logger.debug("OpenAI event", event_type=event_type, session_id=self.session_id)
                
                # Handle different event types
                if event_type == "session.created":
                    if not self.websocket_closed:
                        await self.websocket.send_json({
                            "type": "session.ready",
                            "session_id": self.session_id
                        })
                
                elif event_type == "response.audio.delta":
                    # Forward audio to client
                    if not self.websocket_closed:
                        await self.websocket.send_json({
                            "type": "audio",
                            "audio": data.get("delta", "")
                        })
                
                elif event_type == "response.audio_transcript.delta":
                    # Forward transcript to client
                    if not self.websocket_closed:
                        await self.websocket.send_json({
                            "type": "transcript",
                            "role": "assistant",
                            "delta": data.get("delta", "")
                        })
                
                elif event_type == "input_audio_buffer.speech_started":
                    # User started speaking (barge-in detected)
                    if not self.websocket_closed:
                        await self.websocket.send_json({
                            "type": "user_speech_started"
                        })
                
                elif event_type == "input_audio_buffer.speech_stopped":
                    # User stopped speaking
                    if not self.websocket_closed:
                        await self.websocket.send_json({
                            "type": "user_speech_stopped"
                        })
                
                elif event_type == "conversation.item.input_audio_transcription.completed":
                    # User's speech transcribed
                    transcript = data.get("transcript", "")
                    if not self.websocket_closed:
                        await self.websocket.send_json({
                            "type": "transcript",
                            "role": "user",
                            "text": transcript
                        })
                
                elif event_type == "response.function_call_arguments.done":
                    # Tool call completed, execute it
                    call_id = data.get("call_id")
                    tool_name = data.get("name")
                    arguments = json.loads(data.get("arguments", "{}"))
                    
                    result = await self.handle_tool_call(tool_name, arguments)
                    result_data = json.loads(result)
                    
                    # Send products to frontend if this was a search
                    if tool_name in ["search_products", "search_similar_products", "get_project_recommendations"]:
                        if "products" in result_data or "error" not in result_data:
                            if not self.websocket_closed:
                                await self.websocket.send_json({
                                    "type": "products",
                                    "tool": tool_name,
                                    "data": result_data
                                })
                    
                    # Send cart actions to frontend
                    if tool_name in ["add_to_cart", "view_cart", "remove_from_cart", "clear_cart"]:
                        print(f"[CART] Sending cart_action to frontend: {tool_name}, data: {result_data}")
                        if not self.websocket_closed:
                            await self.websocket.send_json({
                                "type": "cart_action",
                                "action": result_data.get("action"),
                                "data": result_data
                            })
                    
                    # Send DIY videos to frontend
                    if tool_name == "get_diy_videos":
                        if result_data.get("videos") and len(result_data["videos"]) > 0:
                            print(f"[DIY VIDEOS] Sending {len(result_data['videos'])} videos to frontend")
                            if not self.websocket_closed:
                                await self.websocket.send_json({
                                    "type": "diy_videos",
                                    "data": result_data
                                })
                    
                    # Send order actions to frontend
                    if tool_name in ["view_orders", "get_order_by_number"]:
                        print(f"[ORDERS] Sending order_action to frontend: {tool_name}, data: {result_data}")
                        if not self.websocket_closed:
                            await self.websocket.send_json({
                                "type": "order_action",
                                "action": result_data.get("action"),
                                "order_number": result_data.get("order_number"),
                                "data": result_data
                            })
                    
                    # Send tool result back to GPT-4o
                    await self.openai_ws.send(json.dumps({
                        "type": "conversation.item.create",
                        "item": {
                            "type": "function_call_output",
                            "call_id": call_id,
                            "output": result
                        }
                    }))
                    
                    # Trigger response generation
                    await self.openai_ws.send(json.dumps({
                        "type": "response.create"
                    }))
                
                elif event_type == "response.done":
                    # Response completed
                    if not self.websocket_closed:
                        await self.websocket.send_json({
                            "type": "response.complete"
                        })
                
                elif event_type == "error":
                    error_msg = data.get("error", {}).get("message", "Unknown error")
                    logger.error("OpenAI error", error=error_msg, session_id=self.session_id)
                    if not self.websocket_closed:
                        await self.websocket.send_json({
                            "type": "error",
                            "message": error_msg
                        })
                    
        except Exception as e:
            logger.error("Error processing OpenAI messages", error=str(e), session_id=self.session_id)
            if self.is_active and not self.websocket_closed:
                try:
                    await self.websocket.send_json({
                        "type": "error",
                        "message": str(e)
                    })
                except Exception:
                    pass  # WebSocket already closed
    
    async def process_client_messages(self):
        """Process messages from the client WebSocket."""
        try:
            while self.is_active:
                message = await self.websocket.receive_json()
                msg_type = message.get("type", "")
                
                if msg_type == "audio" or msg_type == "input_audio_buffer.append":
                    # Forward audio to GPT-4o Realtime
                    audio_data = message.get("audio", "")
                    await self.openai_ws.send(json.dumps({
                        "type": "input_audio_buffer.append",
                        "audio": audio_data
                    }))
                
                elif msg_type == "audio.commit" or msg_type == "input_audio_buffer.commit":
                    # Commit audio buffer (manual VAD mode)
                    await self.openai_ws.send(json.dumps({
                        "type": "input_audio_buffer.commit"
                    }))
                
                elif msg_type == "session.update":
                    # Client sending session config - we already configured, just acknowledge
                    logger.info("Client session update received (ignored - using server config)", 
                               session_id=self.session_id)
                
                elif msg_type == "response.cancel":
                    # Cancel current response (barge-in)
                    await self.openai_ws.send(json.dumps({
                        "type": "response.cancel"
                    }))
                
                elif msg_type == "text":
                    # Text input (for testing without voice)
                    text = message.get("text", "")
                    await self.openai_ws.send(json.dumps({
                        "type": "conversation.item.create",
                        "item": {
                            "type": "message",
                            "role": "user",
                            "content": [
                                {
                                    "type": "input_text",
                                    "text": text
                                }
                            ]
                        }
                    }))
                    await self.openai_ws.send(json.dumps({
                        "type": "response.create"
                    }))
                
                elif msg_type == "cancel":
                    # Cancel current response (barge-in from client) - legacy
                    await self.openai_ws.send(json.dumps({
                        "type": "response.cancel"
                    }))
                
                elif msg_type == "image.uploaded":
                    # Image was uploaded for search
                    image_id = message.get("image_id")
                    await self.websocket.send_json({
                        "type": "image.ready",
                        "image_id": image_id,
                        "message": "Image uploaded. Ask me to find similar products!"
                    })
                    
        except WebSocketDisconnect:
            logger.info("Client disconnected", session_id=self.session_id)
            self.websocket_closed = True
        except Exception as e:
            logger.error("Error processing client messages", error=str(e), session_id=self.session_id)
            self.websocket_closed = True
    
    async def run(self):
        """Run the realtime session."""
        try:
            await self.connect_to_openai()
            
            # Run both message handlers concurrently
            await asyncio.gather(
                self.process_openai_messages(),
                self.process_client_messages()
            )
            
        finally:
            await self.close()
    
    async def close(self):
        """Close the session."""
        self.is_active = False
        if self.openai_ws:
            await self.openai_ws.close()
        logger.info("Session closed", session_id=self.session_id)


@router.websocket("/ws")
async def realtime_websocket(websocket: WebSocket):
    """WebSocket endpoint for GPT-4o Realtime voice communication."""
    await websocket.accept()
    
    session_id = str(uuid.uuid4())
    logger.info("New realtime connection", session_id=session_id)
    
    session = RealtimeSession(
        session_id=session_id,
        websocket=websocket,
        app_state=websocket.app.state
    )
    
    try:
        await session.run()
    except Exception as e:
        logger.error("Session error", error=str(e), session_id=session_id)
    finally:
        await session.close()


@router.get("/status")
async def realtime_status():
    """Check realtime endpoint status."""
    return {
        "status": "ready",
        "features": {
            "voice_to_voice": True,
            "barge_in": True,
            "tools": len(TOOLS),
            "vad": "server_side"
        }
    }
