"""
Product Image Populator
========================

Downloads real product images from Unsplash and uploads them to Azure Blob Storage,
then updates product records in Cosmos DB with the actual image URLs.

Usage:
    python scripts/populate_images.py

Requirements:
    pip install aiohttp azure-storage-blob motor
"""

import asyncio
import aiohttp
import os
import sys
from datetime import datetime
from azure.storage.blob import BlobServiceClient, ContentSettings
from motor.motor_asyncio import AsyncIOMotorClient
import hashlib

# Configuration
STORAGE_ACCOUNT_NAME = os.getenv("AZURE_STORAGE_ACCOUNT", "stketzagentickh7xm2")
STORAGE_CONTAINER = "product-images"
COSMOS_CONNECTION_STRING = os.getenv("AZURE_COSMOS_CONNECTION_STRING")
DATABASE_NAME = "ketzagenticdb"
PRODUCTS_COLLECTION = "products"

# Unsplash Source URLs for each category/subcategory
# Using specific search terms to get relevant home improvement images
UNSPLASH_IMAGES = {
    "power_tools": {
        "drills": [
            "https://images.unsplash.com/photo-1504148455328-c376907d081c?w=400&h=400&fit=crop",  # Power drill
            "https://images.unsplash.com/photo-1572981779307-38b8cabb2407?w=400&h=400&fit=crop",  # Drill set
            "https://images.unsplash.com/photo-1530124566582-a618bc2615dc?w=400&h=400&fit=crop",  # Tool workshop
        ],
        "saws": [
            "https://images.unsplash.com/photo-1586864387789-628af9feed72?w=400&h=400&fit=crop",  # Circular saw
            "https://images.unsplash.com/photo-1622042498918-99f7d07a0f78?w=400&h=400&fit=crop",  # Saw cutting
            "https://images.unsplash.com/photo-1572981779307-38b8cabb2407?w=400&h=400&fit=crop",  # Tools
        ],
        "sanders": [
            "https://images.unsplash.com/photo-1580901368919-7738efb0f87e?w=400&h=400&fit=crop",  # Sander
            "https://images.unsplash.com/photo-1530124566582-a618bc2615dc?w=400&h=400&fit=crop",  # Workshop
        ],
        "routers": [
            "https://images.unsplash.com/photo-1530124566582-a618bc2615dc?w=400&h=400&fit=crop",  # Workshop
            "https://images.unsplash.com/photo-1572981779307-38b8cabb2407?w=400&h=400&fit=crop",  # Tools
        ],
        "grinders": [
            "https://images.unsplash.com/photo-1504148455328-c376907d081c?w=400&h=400&fit=crop",  # Power tool
            "https://images.unsplash.com/photo-1572981779307-38b8cabb2407?w=400&h=400&fit=crop",  # Tools
        ],
        "impact_drivers": [
            "https://images.unsplash.com/photo-1504148455328-c376907d081c?w=400&h=400&fit=crop",  # Impact driver
            "https://images.unsplash.com/photo-1530124566582-a618bc2615dc?w=400&h=400&fit=crop",  # Workshop
        ],
    },
    "hand_tools": {
        "hammers": [
            "https://images.unsplash.com/photo-1586864387789-628af9feed72?w=400&h=400&fit=crop",  # Hammer
            "https://images.unsplash.com/photo-1416879595882-3373a0480b5b?w=400&h=400&fit=crop",  # Tool set
        ],
        "screwdrivers": [
            "https://images.unsplash.com/photo-1426927308491-6380b6a9936f?w=400&h=400&fit=crop",  # Screwdriver
            "https://images.unsplash.com/photo-1572981779307-38b8cabb2407?w=400&h=400&fit=crop",  # Tools
        ],
        "wrenches": [
            "https://images.unsplash.com/photo-1581092921461-eab62e97a780?w=400&h=400&fit=crop",  # Wrench
            "https://images.unsplash.com/photo-1572981779307-38b8cabb2407?w=400&h=400&fit=crop",  # Tools
        ],
        "pliers": [
            "https://images.unsplash.com/photo-1572981779307-38b8cabb2407?w=400&h=400&fit=crop",  # Pliers
            "https://images.unsplash.com/photo-1426927308491-6380b6a9936f?w=400&h=400&fit=crop",  # Tools
        ],
        "measuring": [
            "https://images.unsplash.com/photo-1504917595217-d4dc5ebb6122?w=400&h=400&fit=crop",  # Measuring tape
            "https://images.unsplash.com/photo-1572981779307-38b8cabb2407?w=400&h=400&fit=crop",  # Tools
        ],
        "levels": [
            "https://images.unsplash.com/photo-1504917595217-d4dc5ebb6122?w=400&h=400&fit=crop",  # Level
            "https://images.unsplash.com/photo-1572981779307-38b8cabb2407?w=400&h=400&fit=crop",  # Tools
        ],
    },
    "building_materials": {
        "lumber": [
            "https://images.unsplash.com/photo-1541123603104-512919d6a96c?w=400&h=400&fit=crop",  # Lumber
            "https://images.unsplash.com/photo-1558618666-fcd25c85cd64?w=400&h=400&fit=crop",  # Wood planks
        ],
        "drywall": [
            "https://images.unsplash.com/photo-1503387762-592deb58ef4e?w=400&h=400&fit=crop",  # Construction
            "https://images.unsplash.com/photo-1558618666-fcd25c85cd64?w=400&h=400&fit=crop",  # Materials
        ],
        "plywood": [
            "https://images.unsplash.com/photo-1541123603104-512919d6a96c?w=400&h=400&fit=crop",  # Plywood
            "https://images.unsplash.com/photo-1558618666-fcd25c85cd64?w=400&h=400&fit=crop",  # Wood
        ],
        "concrete": [
            "https://images.unsplash.com/photo-1503387762-592deb58ef4e?w=400&h=400&fit=crop",  # Concrete
            "https://images.unsplash.com/photo-1504307651254-35680f356dfd?w=400&h=400&fit=crop",  # Construction
        ],
        "insulation": [
            "https://images.unsplash.com/photo-1504307651254-35680f356dfd?w=400&h=400&fit=crop",  # Insulation
            "https://images.unsplash.com/photo-1503387762-592deb58ef4e?w=400&h=400&fit=crop",  # Building
        ],
        "roofing": [
            "https://images.unsplash.com/photo-1558618666-fcd25c85cd64?w=400&h=400&fit=crop",  # Roofing
            "https://images.unsplash.com/photo-1503387762-592deb58ef4e?w=400&h=400&fit=crop",  # Materials
        ],
    },
    "paint": {
        "interior_paint": [
            "https://images.unsplash.com/photo-1562259949-e8e7689d7828?w=400&h=400&fit=crop",  # Paint cans
            "https://images.unsplash.com/photo-1525909002-1b05e0c869d8?w=400&h=400&fit=crop",  # Paint swatches
            "https://images.unsplash.com/photo-1589939705384-5185137a7f0f?w=400&h=400&fit=crop",  # Painting
        ],
        "exterior_paint": [
            "https://images.unsplash.com/photo-1562259949-e8e7689d7828?w=400&h=400&fit=crop",  # Paint
            "https://images.unsplash.com/photo-1525909002-1b05e0c869d8?w=400&h=400&fit=crop",  # Colors
        ],
        "primers": [
            "https://images.unsplash.com/photo-1562259949-e8e7689d7828?w=400&h=400&fit=crop",  # Primer
            "https://images.unsplash.com/photo-1589939705384-5185137a7f0f?w=400&h=400&fit=crop",  # Paint
        ],
        "stains": [
            "https://images.unsplash.com/photo-1562259949-e8e7689d7828?w=400&h=400&fit=crop",  # Stain
            "https://images.unsplash.com/photo-1558618666-fcd25c85cd64?w=400&h=400&fit=crop",  # Wood stain
        ],
        "spray_paint": [
            "https://images.unsplash.com/photo-1562259949-e8e7689d7828?w=400&h=400&fit=crop",  # Spray paint
            "https://images.unsplash.com/photo-1525909002-1b05e0c869d8?w=400&h=400&fit=crop",  # Paint
        ],
        "supplies": [
            "https://images.unsplash.com/photo-1589939705384-5185137a7f0f?w=400&h=400&fit=crop",  # Brushes
            "https://images.unsplash.com/photo-1562259949-e8e7689d7828?w=400&h=400&fit=crop",  # Supplies
        ],
    },
    "flooring": {
        "hardwood": [
            "https://images.unsplash.com/photo-1558618666-fcd25c85cd64?w=400&h=400&fit=crop",  # Hardwood floor
            "https://images.unsplash.com/photo-1541123603104-512919d6a96c?w=400&h=400&fit=crop",  # Wood
        ],
        "laminate": [
            "https://images.unsplash.com/photo-1558618666-fcd25c85cd64?w=400&h=400&fit=crop",  # Laminate
            "https://images.unsplash.com/photo-1541123603104-512919d6a96c?w=400&h=400&fit=crop",  # Floor
        ],
        "vinyl": [
            "https://images.unsplash.com/photo-1558618666-fcd25c85cd64?w=400&h=400&fit=crop",  # Vinyl floor
            "https://images.unsplash.com/photo-1600585152220-90363fe7e115?w=400&h=400&fit=crop",  # Floor
        ],
        "tile": [
            "https://images.unsplash.com/photo-1600585152220-90363fe7e115?w=400&h=400&fit=crop",  # Tile
            "https://images.unsplash.com/photo-1558618666-fcd25c85cd64?w=400&h=400&fit=crop",  # Floor tile
        ],
        "carpet": [
            "https://images.unsplash.com/photo-1600585152220-90363fe7e115?w=400&h=400&fit=crop",  # Carpet
            "https://images.unsplash.com/photo-1558618666-fcd25c85cd64?w=400&h=400&fit=crop",  # Floor
        ],
        "underlayment": [
            "https://images.unsplash.com/photo-1558618666-fcd25c85cd64?w=400&h=400&fit=crop",  # Underlayment
            "https://images.unsplash.com/photo-1541123603104-512919d6a96c?w=400&h=400&fit=crop",  # Materials
        ],
    },
    "plumbing": {
        "faucets": [
            "https://images.unsplash.com/photo-1585704032915-c3400ca199e7?w=400&h=400&fit=crop",  # Faucet
            "https://images.unsplash.com/photo-1552321554-5fefe8c9ef14?w=400&h=400&fit=crop",  # Kitchen faucet
        ],
        "toilets": [
            "https://images.unsplash.com/photo-1552321554-5fefe8c9ef14?w=400&h=400&fit=crop",  # Bathroom
            "https://images.unsplash.com/photo-1585704032915-c3400ca199e7?w=400&h=400&fit=crop",  # Plumbing
        ],
        "pipes": [
            "https://images.unsplash.com/photo-1585704032915-c3400ca199e7?w=400&h=400&fit=crop",  # Pipes
            "https://images.unsplash.com/photo-1504307651254-35680f356dfd?w=400&h=400&fit=crop",  # Plumbing
        ],
        "water_heaters": [
            "https://images.unsplash.com/photo-1585704032915-c3400ca199e7?w=400&h=400&fit=crop",  # Water heater
            "https://images.unsplash.com/photo-1504307651254-35680f356dfd?w=400&h=400&fit=crop",  # Appliance
        ],
        "sinks": [
            "https://images.unsplash.com/photo-1552321554-5fefe8c9ef14?w=400&h=400&fit=crop",  # Sink
            "https://images.unsplash.com/photo-1585704032915-c3400ca199e7?w=400&h=400&fit=crop",  # Kitchen sink
        ],
        "shower_heads": [
            "https://images.unsplash.com/photo-1552321554-5fefe8c9ef14?w=400&h=400&fit=crop",  # Shower
            "https://images.unsplash.com/photo-1585704032915-c3400ca199e7?w=400&h=400&fit=crop",  # Bathroom
        ],
    },
    "electrical": {
        "outlets": [
            "https://images.unsplash.com/photo-1558618666-fcd25c85cd64?w=400&h=400&fit=crop",  # Outlet
            "https://images.unsplash.com/photo-1504307651254-35680f356dfd?w=400&h=400&fit=crop",  # Electrical
        ],
        "switches": [
            "https://images.unsplash.com/photo-1558618666-fcd25c85cd64?w=400&h=400&fit=crop",  # Switch
            "https://images.unsplash.com/photo-1504307651254-35680f356dfd?w=400&h=400&fit=crop",  # Electrical
        ],
        "lighting": [
            "https://images.unsplash.com/photo-1524484485831-a92ffc0de03f?w=400&h=400&fit=crop",  # Light bulb
            "https://images.unsplash.com/photo-1507473885765-e6ed057f782c?w=400&h=400&fit=crop",  # Pendant light
            "https://images.unsplash.com/photo-1513506003901-1e6a229e2d15?w=400&h=400&fit=crop",  # Lighting
        ],
        "wiring": [
            "https://images.unsplash.com/photo-1504307651254-35680f356dfd?w=400&h=400&fit=crop",  # Wiring
            "https://images.unsplash.com/photo-1558618666-fcd25c85cd64?w=400&h=400&fit=crop",  # Electrical
        ],
        "circuit_breakers": [
            "https://images.unsplash.com/photo-1504307651254-35680f356dfd?w=400&h=400&fit=crop",  # Breaker
            "https://images.unsplash.com/photo-1558618666-fcd25c85cd64?w=400&h=400&fit=crop",  # Electrical
        ],
        "smart_home": [
            "https://images.unsplash.com/photo-1558002038-1055907df827?w=400&h=400&fit=crop",  # Smart home
            "https://images.unsplash.com/photo-1524484485831-a92ffc0de03f?w=400&h=400&fit=crop",  # Smart bulb
        ],
    },
    "kitchen_bath": {
        "countertops": [
            "https://images.unsplash.com/photo-1556909114-f6e7ad7d3136?w=400&h=400&fit=crop",  # Countertop
            "https://images.unsplash.com/photo-1600585152220-90363fe7e115?w=400&h=400&fit=crop",  # Kitchen
        ],
        "cabinets": [
            "https://images.unsplash.com/photo-1556909114-f6e7ad7d3136?w=400&h=400&fit=crop",  # Cabinets
            "https://images.unsplash.com/photo-1600585152220-90363fe7e115?w=400&h=400&fit=crop",  # Kitchen
        ],
        "vanities": [
            "https://images.unsplash.com/photo-1552321554-5fefe8c9ef14?w=400&h=400&fit=crop",  # Vanity
            "https://images.unsplash.com/photo-1556909114-f6e7ad7d3136?w=400&h=400&fit=crop",  # Bathroom
        ],
        "backsplash": [
            "https://images.unsplash.com/photo-1556909114-f6e7ad7d3136?w=400&h=400&fit=crop",  # Backsplash
            "https://images.unsplash.com/photo-1600585152220-90363fe7e115?w=400&h=400&fit=crop",  # Tile
        ],
        "fixtures": [
            "https://images.unsplash.com/photo-1585704032915-c3400ca199e7?w=400&h=400&fit=crop",  # Fixtures
            "https://images.unsplash.com/photo-1552321554-5fefe8c9ef14?w=400&h=400&fit=crop",  # Bath
        ],
        "accessories": [
            "https://images.unsplash.com/photo-1552321554-5fefe8c9ef14?w=400&h=400&fit=crop",  # Accessories
            "https://images.unsplash.com/photo-1556909114-f6e7ad7d3136?w=400&h=400&fit=crop",  # Bath
        ],
    },
    "outdoor_garden": {
        "grills": [
            "https://images.unsplash.com/photo-1529692236671-f1f6cf9683ba?w=400&h=400&fit=crop",  # Grill
            "https://images.unsplash.com/photo-1555939594-58d7cb561ad1?w=400&h=400&fit=crop",  # BBQ
        ],
        "patio_furniture": [
            "https://images.unsplash.com/photo-1600210492486-724fe5c67fb0?w=400&h=400&fit=crop",  # Patio
            "https://images.unsplash.com/photo-1595526051245-4506e0005bd0?w=400&h=400&fit=crop",  # Outdoor furniture
        ],
        "lawn_mowers": [
            "https://images.unsplash.com/photo-1590212151175-e58edd96185b?w=400&h=400&fit=crop",  # Lawn mower
            "https://images.unsplash.com/photo-1600210492486-724fe5c67fb0?w=400&h=400&fit=crop",  # Garden
        ],
        "plants": [
            "https://images.unsplash.com/photo-1416879595882-3373a0480b5b?w=400&h=400&fit=crop",  # Plants
            "https://images.unsplash.com/photo-1459411552884-841db9b3cc2a?w=400&h=400&fit=crop",  # Garden plants
        ],
        "outdoor_lighting": [
            "https://images.unsplash.com/photo-1524484485831-a92ffc0de03f?w=400&h=400&fit=crop",  # Outdoor light
            "https://images.unsplash.com/photo-1600210492486-724fe5c67fb0?w=400&h=400&fit=crop",  # Patio lights
        ],
        "fencing": [
            "https://images.unsplash.com/photo-1558618666-fcd25c85cd64?w=400&h=400&fit=crop",  # Fence
            "https://images.unsplash.com/photo-1600210492486-724fe5c67fb0?w=400&h=400&fit=crop",  # Outdoor
        ],
    },
    "storage": {
        "shelving": [
            "https://images.unsplash.com/photo-1558618666-fcd25c85cd64?w=400&h=400&fit=crop",  # Shelving
            "https://images.unsplash.com/photo-1600585152220-90363fe7e115?w=400&h=400&fit=crop",  # Shelves
        ],
        "garage_storage": [
            "https://images.unsplash.com/photo-1530124566582-a618bc2615dc?w=400&h=400&fit=crop",  # Garage
            "https://images.unsplash.com/photo-1558618666-fcd25c85cd64?w=400&h=400&fit=crop",  # Storage
        ],
        "closet_systems": [
            "https://images.unsplash.com/photo-1600585152220-90363fe7e115?w=400&h=400&fit=crop",  # Closet
            "https://images.unsplash.com/photo-1558618666-fcd25c85cd64?w=400&h=400&fit=crop",  # Organization
        ],
        "bins": [
            "https://images.unsplash.com/photo-1558618666-fcd25c85cd64?w=400&h=400&fit=crop",  # Storage bins
            "https://images.unsplash.com/photo-1600585152220-90363fe7e115?w=400&h=400&fit=crop",  # Containers
        ],
        "workbenches": [
            "https://images.unsplash.com/photo-1530124566582-a618bc2615dc?w=400&h=400&fit=crop",  # Workbench
            "https://images.unsplash.com/photo-1572981779307-38b8cabb2407?w=400&h=400&fit=crop",  # Workshop
        ],
        "tool_chests": [
            "https://images.unsplash.com/photo-1572981779307-38b8cabb2407?w=400&h=400&fit=crop",  # Tool chest
            "https://images.unsplash.com/photo-1530124566582-a618bc2615dc?w=400&h=400&fit=crop",  # Tools
        ],
    },
    "hardware": {
        "fasteners": [
            "https://images.unsplash.com/photo-1572981779307-38b8cabb2407?w=400&h=400&fit=crop",  # Screws
            "https://images.unsplash.com/photo-1558618666-fcd25c85cd64?w=400&h=400&fit=crop",  # Hardware
        ],
        "hinges": [
            "https://images.unsplash.com/photo-1558618666-fcd25c85cd64?w=400&h=400&fit=crop",  # Hinges
            "https://images.unsplash.com/photo-1572981779307-38b8cabb2407?w=400&h=400&fit=crop",  # Hardware
        ],
        "locks": [
            "https://images.unsplash.com/photo-1558618666-fcd25c85cd64?w=400&h=400&fit=crop",  # Lock
            "https://images.unsplash.com/photo-1504307651254-35680f356dfd?w=400&h=400&fit=crop",  # Security
        ],
        "door_hardware": [
            "https://images.unsplash.com/photo-1558618666-fcd25c85cd64?w=400&h=400&fit=crop",  # Door handle
            "https://images.unsplash.com/photo-1504307651254-35680f356dfd?w=400&h=400&fit=crop",  # Hardware
        ],
        "hooks": [
            "https://images.unsplash.com/photo-1558618666-fcd25c85cd64?w=400&h=400&fit=crop",  # Hooks
            "https://images.unsplash.com/photo-1572981779307-38b8cabb2407?w=400&h=400&fit=crop",  # Hardware
        ],
        "anchors": [
            "https://images.unsplash.com/photo-1572981779307-38b8cabb2407?w=400&h=400&fit=crop",  # Anchors
            "https://images.unsplash.com/photo-1558618666-fcd25c85cd64?w=400&h=400&fit=crop",  # Hardware
        ],
    },
    "appliances": {
        "refrigerators": [
            "https://images.unsplash.com/photo-1571175443880-49e1d25b2bc5?w=400&h=400&fit=crop",  # Refrigerator
            "https://images.unsplash.com/photo-1556909114-f6e7ad7d3136?w=400&h=400&fit=crop",  # Kitchen
        ],
        "washers": [
            "https://images.unsplash.com/photo-1626806787461-102c1bfaaea1?w=400&h=400&fit=crop",  # Washer
            "https://images.unsplash.com/photo-1556909114-f6e7ad7d3136?w=400&h=400&fit=crop",  # Appliance
        ],
        "dryers": [
            "https://images.unsplash.com/photo-1626806787461-102c1bfaaea1?w=400&h=400&fit=crop",  # Dryer
            "https://images.unsplash.com/photo-1556909114-f6e7ad7d3136?w=400&h=400&fit=crop",  # Laundry
        ],
        "dishwashers": [
            "https://images.unsplash.com/photo-1556909114-f6e7ad7d3136?w=400&h=400&fit=crop",  # Dishwasher
            "https://images.unsplash.com/photo-1571175443880-49e1d25b2bc5?w=400&h=400&fit=crop",  # Kitchen
        ],
        "ranges": [
            "https://images.unsplash.com/photo-1556909114-f6e7ad7d3136?w=400&h=400&fit=crop",  # Range/Stove
            "https://images.unsplash.com/photo-1571175443880-49e1d25b2bc5?w=400&h=400&fit=crop",  # Kitchen
        ],
        "microwaves": [
            "https://images.unsplash.com/photo-1556909114-f6e7ad7d3136?w=400&h=400&fit=crop",  # Microwave
            "https://images.unsplash.com/photo-1571175443880-49e1d25b2bc5?w=400&h=400&fit=crop",  # Kitchen
        ],
    },
}


async def download_image(session: aiohttp.ClientSession, url: str) -> bytes | None:
    """Download an image from URL."""
    try:
        async with session.get(url, timeout=30) as response:
            if response.status == 200:
                return await response.read()
            print(f"  ❌ Failed to download {url}: Status {response.status}")
            return None
    except Exception as e:
        print(f"  ❌ Error downloading {url}: {e}")
        return None


async def upload_to_blob(blob_service: BlobServiceClient, container_name: str, 
                         blob_name: str, data: bytes) -> str | None:
    """Upload image data to Azure Blob Storage."""
    try:
        container_client = blob_service.get_container_client(container_name)
        
        # Ensure container exists
        try:
            container_client.create_container()
        except Exception:
            pass  # Container already exists
        
        blob_client = container_client.get_blob_client(blob_name)
        
        # Upload with proper content type
        content_settings = ContentSettings(content_type="image/jpeg")
        blob_client.upload_blob(data, overwrite=True, content_settings=content_settings)
        
        return blob_client.url
    except Exception as e:
        print(f"  ❌ Error uploading to blob {blob_name}: {e}")
        return None


def get_image_for_product(category: str, subcategory: str, product_id: str) -> str | None:
    """Get an image URL for a product based on its category and subcategory."""
    cat_images = UNSPLASH_IMAGES.get(category, {})
    subcat_images = cat_images.get(subcategory, [])
    
    if not subcat_images:
        # Fallback to any subcategory in the category
        for subcat_imgs in cat_images.values():
            if subcat_imgs:
                subcat_images = subcat_imgs
                break
    
    if not subcat_images:
        # Ultimate fallback - use power tools
        subcat_images = UNSPLASH_IMAGES.get("power_tools", {}).get("drills", [])
    
    if subcat_images:
        # Use product_id hash to consistently pick same image
        idx = hash(product_id) % len(subcat_images)
        return subcat_images[idx]
    
    return None


async def populate_images():
    """Main function to populate product images."""
    print("=" * 60)
    print("🖼️  Product Image Populator")
    print("=" * 60)
    
    # Validate environment
    if not COSMOS_CONNECTION_STRING:
        print("❌ AZURE_COSMOS_CONNECTION_STRING environment variable not set")
        print("   Run: $env:AZURE_COSMOS_CONNECTION_STRING = '<your-connection-string>'")
        sys.exit(1)
    
    # Connect to Cosmos DB
    print("\n📡 Connecting to Cosmos DB...")
    try:
        client = AsyncIOMotorClient(COSMOS_CONNECTION_STRING)
        db = client[DATABASE_NAME]
        products_collection = db[PRODUCTS_COLLECTION]
        
        # Test connection
        await client.admin.command('ping')
        print("   ✅ Connected to Cosmos DB")
    except Exception as e:
        print(f"   ❌ Failed to connect to Cosmos DB: {e}")
        sys.exit(1)
    
    # Connect to Azure Blob Storage
    print("\n📦 Connecting to Azure Blob Storage...")
    try:
        # Get connection string from az CLI
        import subprocess
        result = subprocess.run(
            ["az", "storage", "account", "show-connection-string", 
             "--name", STORAGE_ACCOUNT_NAME, 
             "--resource-group", "rg-ketzagentic-kh7xm2",
             "-o", "tsv"],
            capture_output=True, text=True
        )
        storage_conn_str = result.stdout.strip()
        
        if not storage_conn_str:
            print(f"   ❌ Could not get storage connection string")
            sys.exit(1)
        
        blob_service = BlobServiceClient.from_connection_string(storage_conn_str)
        print(f"   ✅ Connected to storage account: {STORAGE_ACCOUNT_NAME}")
    except Exception as e:
        print(f"   ❌ Failed to connect to Blob Storage: {e}")
        sys.exit(1)
    
    # Get all products with placeholder images
    print("\n🔍 Finding products with placeholder images...")
    
    # Query for products with placeholder URLs
    cursor = products_collection.find({
        "$or": [
            {"image_url": {"$regex": "placehold.co"}},
            {"image_url": {"$regex": "placeholder"}},
            {"image_url": None},
            {"image_url": ""}
        ]
    })
    
    products = await cursor.to_list(length=None)
    print(f"   📦 Found {len(products)} products needing images")
    
    if not products:
        print("\n✅ All products already have real images!")
        return
    
    # Track downloaded images to avoid duplicates
    downloaded_images = {}  # URL -> blob_url
    
    # Process products
    print(f"\n📥 Downloading and uploading images...")
    
    async with aiohttp.ClientSession() as session:
        updated_count = 0
        failed_count = 0
        
        for i, product in enumerate(products, 1):
            product_id = str(product.get("_id", ""))
            category = product.get("category", "power_tools")
            subcategory = product.get("subcategory", "drills")
            name = product.get("name", "Unknown")
            
            print(f"\n[{i}/{len(products)}] {name[:50]}...")
            
            # Get source image URL for this product
            source_url = get_image_for_product(category, subcategory, product_id)
            
            if not source_url:
                print(f"   ⚠️ No image available for category: {category}/{subcategory}")
                failed_count += 1
                continue
            
            # Check if we already downloaded this image
            if source_url in downloaded_images:
                blob_url = downloaded_images[source_url]
                print(f"   ♻️ Using cached image")
            else:
                # Download image
                image_data = await download_image(session, source_url)
                
                if not image_data:
                    failed_count += 1
                    continue
                
                # Generate blob name
                url_hash = hashlib.md5(source_url.encode()).hexdigest()[:8]
                blob_name = f"{category}/{subcategory}/{url_hash}.jpg"
                
                # Upload to blob storage
                blob_url = await upload_to_blob(blob_service, STORAGE_CONTAINER, blob_name, image_data)
                
                if not blob_url:
                    failed_count += 1
                    continue
                
                downloaded_images[source_url] = blob_url
                print(f"   ⬆️ Uploaded to: {blob_name}")
            
            # Update product in Cosmos DB
            try:
                await products_collection.update_one(
                    {"_id": product["_id"]},
                    {"$set": {
                        "image_url": blob_url,
                        "updated_at": datetime.utcnow()
                    }}
                )
                print(f"   ✅ Updated product")
                updated_count += 1
            except Exception as e:
                print(f"   ❌ Failed to update product: {e}")
                failed_count += 1
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 Summary")
    print("=" * 60)
    print(f"   ✅ Updated: {updated_count} products")
    print(f"   ❌ Failed: {failed_count} products")
    print(f"   📁 Unique images uploaded: {len(downloaded_images)}")
    print("\n🎉 Done!")


if __name__ == "__main__":
    asyncio.run(populate_images())
