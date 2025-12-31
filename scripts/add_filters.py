"""
Script to add Water Filters and HVAC Air Filters via Backend API
================================================================
Restores water filters from backup JSON and adds new HVAC air filters.
Uses the backend API since Cosmos DB has network firewall.
"""

import asyncio
import httpx
import json
import uuid
import os
from datetime import datetime

# Backend URL
BACKEND_URL = "https://backend-vnet.happyisland-58d32b38.eastus2.azurecontainerapps.io"

# HVAC Air Filter products
# Pricing: Individual $15-30, 2-packs 10% off, 10-packs 25% off
HVAC_FILTERS = [
    # ============== MERV 8 (Basic) - Dust & Pollen ==============
    # Individual
    {
        "id": str(uuid.uuid4()),
        "name": "Filtrete 20x25x1 MERV 8 Basic Dust Air Filter",
        "description": "3M Filtrete Basic Dust & Lint air filter with MERV 8 rating. Captures large particles like household dust, lint, and pollen. Ideal for homes without pets or allergies. Electrostatically charged fibers attract and capture airborne particles. Replace every 90 days for optimal performance. Fits standard 20x25x1 inch HVAC systems, furnaces, and air conditioners.",
        "category": "appliance_parts",
        "subcategory": "hvac_filters",
        "brand": "Filtrete",
        "sku": "HVAC-3M-M8-2025-1",
        "price": 15.99,
        "sale_price": None,
        "rating": 4.4,
        "review_count": 2847,
        "in_stock": True,
        "stock_quantity": 324,
        "image_url": "https://images.unsplash.com/photo-1585771724684-38269d6639fd?w=400&h=400&fit=crop&q=80",
        "featured": False,
        "specifications": {
            "size": "20x25x1",
            "merv_rating": 8,
            "filter_life": "90 days",
            "pack_count": 1,
            "captures": "dust, lint, pollen",
            "compatible_systems": "furnaces, air conditioners, HVAC systems"
        },
    },
    {
        "id": str(uuid.uuid4()),
        "name": "Honeywell 16x25x1 MERV 8 FPR 5 Air Filter",
        "description": "Honeywell Home MERV 8 pleated air filter for residential HVAC systems. Traps common household particles including dust mites, mold spores, and pet dander. FPR 5 rating for good air quality. Sturdy beverage board frame prevents air bypass. 16x25x1 inch size fits most central heating and cooling systems.",
        "category": "appliance_parts",
        "subcategory": "hvac_filters",
        "brand": "Honeywell",
        "sku": "HVAC-HW-M8-1625-1",
        "price": 14.99,
        "sale_price": 12.99,
        "rating": 4.3,
        "review_count": 1923,
        "in_stock": True,
        "stock_quantity": 456,
        "image_url": "https://images.unsplash.com/photo-1558618666-fcd25c85cd64?w=400&h=400&fit=crop&q=80",
        "featured": False,
        "specifications": {
            "size": "16x25x1",
            "merv_rating": 8,
            "fpr_rating": 5,
            "filter_life": "90 days",
            "pack_count": 1,
            "captures": "dust mites, mold spores, pet dander",
            "compatible_systems": "central heating, air conditioning"
        },
    },
    {
        "id": str(uuid.uuid4()),
        "name": "Nordic Pure 20x20x1 MERV 8 Pleated AC Furnace Filter",
        "description": "Nordic Pure MERV 8 pleated air filter for AC and furnace systems. Made in USA with electrostatically charged synthetic media. Captures dust, pollen, and mold spores. Antimicrobial protection prevents bacteria growth on filter. Hypoallergenic and eco-friendly. 20x20x1 inch dimensions.",
        "category": "appliance_parts",
        "subcategory": "hvac_filters",
        "brand": "Nordic Pure",
        "sku": "HVAC-NP-M8-2020-1",
        "price": 16.99,
        "sale_price": None,
        "rating": 4.5,
        "review_count": 3156,
        "in_stock": True,
        "stock_quantity": 289,
        "image_url": "https://images.unsplash.com/photo-1585687433217-7c70f2146a32?w=400&h=400&fit=crop&q=80",
        "featured": False,
        "specifications": {
            "size": "20x20x1",
            "merv_rating": 8,
            "filter_life": "90 days",
            "pack_count": 1,
            "captures": "dust, pollen, mold spores",
            "made_in": "USA",
            "antimicrobial": True
        },
    },
    # 2-Pack (10% off)
    {
        "id": str(uuid.uuid4()),
        "name": "Filtrete 20x25x1 MERV 8 Air Filter 2-Pack",
        "description": "Value 2-pack of 3M Filtrete Basic Dust & Lint air filters. MERV 8 rating captures household dust, lint, and pollen. Save 10% compared to buying individually. 6-month supply when replaced every 90 days. Fits standard 20x25x1 inch HVAC systems. Electrostatically charged fibers for enhanced particle capture.",
        "category": "appliance_parts",
        "subcategory": "hvac_filters",
        "brand": "Filtrete",
        "sku": "HVAC-3M-M8-2025-2PK",
        "price": 28.78,
        "sale_price": None,
        "rating": 4.5,
        "review_count": 1456,
        "in_stock": True,
        "stock_quantity": 178,
        "image_url": "https://images.unsplash.com/photo-1584568694244-14fbdf83bd30?w=400&h=400&fit=crop&q=80",
        "featured": False,
        "specifications": {
            "size": "20x25x1",
            "merv_rating": 8,
            "filter_life": "90 days each",
            "pack_count": 2,
            "captures": "dust, lint, pollen",
            "savings": "10% off individual price"
        },
    },
    # 10-Pack Bundle (25% off)
    {
        "id": str(uuid.uuid4()),
        "name": "Filtrete 20x25x1 MERV 8 Air Filter 10-Pack Bundle",
        "description": "Bulk 10-pack of 3M Filtrete MERV 8 air filters for maximum savings. Perfect for landlords, property managers, or stocking up for the year. Save 25% compared to individual purchases. Each filter lasts 90 days - this pack provides over 2 years of clean air. 20x25x1 inch size. Electrostatically charged for superior dust capture.",
        "category": "appliance_parts",
        "subcategory": "hvac_filters",
        "brand": "Filtrete",
        "sku": "HVAC-3M-M8-2025-10PK",
        "price": 119.93,
        "sale_price": None,
        "rating": 4.7,
        "review_count": 892,
        "in_stock": True,
        "stock_quantity": 45,
        "image_url": "https://images.unsplash.com/photo-1558618666-fcd25c85cd64?w=400&h=400&fit=crop&q=80",
        "featured": True,
        "specifications": {
            "size": "20x25x1",
            "merv_rating": 8,
            "filter_life": "90 days each",
            "pack_count": 10,
            "captures": "dust, lint, pollen",
            "savings": "25% off individual price",
            "supply_duration": "2.5 years"
        },
    },

    # ============== MERV 11 (Better) - Allergens & Pet Dander ==============
    # Individual
    {
        "id": str(uuid.uuid4()),
        "name": "Filtrete 20x25x1 MERV 11 Allergen Defense Air Filter",
        "description": "3M Filtrete Allergen Defense air filter with MERV 11 rating. Captures microscopic particles including dust mites, pet dander, smog, and smoke. 3-in-1 technology traps unwanted particles while letting air flow through. Outperforms fiberglass, washable, and non-electrostatic filters. Replace every 90 days. 20x25x1 inch size.",
        "category": "appliance_parts",
        "subcategory": "hvac_filters",
        "brand": "Filtrete",
        "sku": "HVAC-3M-M11-2025-1",
        "price": 22.99,
        "sale_price": 19.99,
        "rating": 4.6,
        "review_count": 4521,
        "in_stock": True,
        "stock_quantity": 267,
        "image_url": "https://images.unsplash.com/photo-1585771724684-38269d6639fd?w=400&h=400&fit=crop&q=80",
        "featured": True,
        "specifications": {
            "size": "20x25x1",
            "merv_rating": 11,
            "filter_life": "90 days",
            "pack_count": 1,
            "captures": "allergens, dust mites, pet dander, smog, smoke",
            "technology": "3-in-1 electrostatic"
        },
    },
    {
        "id": str(uuid.uuid4()),
        "name": "Honeywell 16x20x1 MERV 11 Elite Allergen Air Filter",
        "description": "Honeywell Elite Allergen MERV 11 air filter for superior indoor air quality. Captures up to 90% of airborne particles including pollen, dust mite debris, and mold spores. Ideal for allergy sufferers and homes with pets. Reinforced wire backing prevents filter collapse. 16x20x1 inch dimensions.",
        "category": "appliance_parts",
        "subcategory": "hvac_filters",
        "brand": "Honeywell",
        "sku": "HVAC-HW-M11-1620-1",
        "price": 21.99,
        "sale_price": None,
        "rating": 4.5,
        "review_count": 2134,
        "in_stock": True,
        "stock_quantity": 198,
        "image_url": "https://images.unsplash.com/photo-1584568694244-14fbdf83bd30?w=400&h=400&fit=crop&q=80",
        "featured": False,
        "specifications": {
            "size": "16x20x1",
            "merv_rating": 11,
            "filter_life": "90 days",
            "pack_count": 1,
            "captures": "pollen, dust mite debris, mold spores, pet dander",
            "efficiency": "90% particle capture"
        },
    },
    {
        "id": str(uuid.uuid4()),
        "name": "Nordic Pure 16x25x1 MERV 11 Pleated Air Filter",
        "description": "Nordic Pure MERV 11 pleated air filter with antimicrobial treatment. Made in USA with premium synthetic electrostatically charged media. Captures allergens, bacteria, and virus carriers. Hypoallergenic construction safe for sensitive individuals. 16x25x1 inch size fits most residential systems.",
        "category": "appliance_parts",
        "subcategory": "hvac_filters",
        "brand": "Nordic Pure",
        "sku": "HVAC-NP-M11-1625-1",
        "price": 23.99,
        "sale_price": None,
        "rating": 4.7,
        "review_count": 2876,
        "in_stock": True,
        "stock_quantity": 156,
        "image_url": "https://images.unsplash.com/photo-1585687433217-7c70f2146a32?w=400&h=400&fit=crop&q=80",
        "featured": False,
        "specifications": {
            "size": "16x25x1",
            "merv_rating": 11,
            "filter_life": "90 days",
            "pack_count": 1,
            "captures": "allergens, bacteria, virus carriers",
            "made_in": "USA",
            "antimicrobial": True
        },
    },
    # 2-Pack (10% off)
    {
        "id": str(uuid.uuid4()),
        "name": "Filtrete 20x25x1 MERV 11 Allergen Defense 2-Pack",
        "description": "Value 2-pack of 3M Filtrete Allergen Defense MERV 11 filters. Save 10% compared to buying individually. Captures allergens, pet dander, smoke, and smog. Ideal for homes with allergy sufferers or pets. 6-month supply with 90-day replacement cycle. 20x25x1 inch size.",
        "category": "appliance_parts",
        "subcategory": "hvac_filters",
        "brand": "Filtrete",
        "sku": "HVAC-3M-M11-2025-2PK",
        "price": 41.38,
        "sale_price": 35.98,
        "rating": 4.6,
        "review_count": 1789,
        "in_stock": True,
        "stock_quantity": 134,
        "image_url": "https://images.unsplash.com/photo-1558618666-fcd25c85cd64?w=400&h=400&fit=crop&q=80",
        "featured": True,
        "specifications": {
            "size": "20x25x1",
            "merv_rating": 11,
            "filter_life": "90 days each",
            "pack_count": 2,
            "captures": "allergens, pet dander, smoke, smog",
            "savings": "10% off individual price"
        },
    },
    {
        "id": str(uuid.uuid4()),
        "name": "Honeywell 16x20x1 MERV 11 Elite Allergen 2-Pack",
        "description": "2-pack of Honeywell Elite Allergen MERV 11 filters. 10% savings versus individual purchase. Premium filtration for allergy relief. Captures pollen, pet dander, and mold spores. Reinforced construction for durability. 16x20x1 inch size fits standard residential HVAC systems.",
        "category": "appliance_parts",
        "subcategory": "hvac_filters",
        "brand": "Honeywell",
        "sku": "HVAC-HW-M11-1620-2PK",
        "price": 39.58,
        "sale_price": None,
        "rating": 4.5,
        "review_count": 967,
        "in_stock": True,
        "stock_quantity": 89,
        "image_url": "https://images.unsplash.com/photo-1585771724684-38269d6639fd?w=400&h=400&fit=crop&q=80",
        "featured": False,
        "specifications": {
            "size": "16x20x1",
            "merv_rating": 11,
            "filter_life": "90 days each",
            "pack_count": 2,
            "captures": "pollen, pet dander, mold spores",
            "savings": "10% off individual price"
        },
    },
    # 10-Pack Bundle (25% off)
    {
        "id": str(uuid.uuid4()),
        "name": "Filtrete 20x25x1 MERV 11 Allergen Defense 10-Pack Bundle",
        "description": "Bulk 10-pack of 3M Filtrete MERV 11 Allergen Defense filters. Save 25% - best value for year-round protection. Perfect for multi-unit properties or stocking up. Each filter provides 90 days of allergen, pet dander, and smog protection. 20x25x1 inch size. Over 2 years supply per pack.",
        "category": "appliance_parts",
        "subcategory": "hvac_filters",
        "brand": "Filtrete",
        "sku": "HVAC-3M-M11-2025-10PK",
        "price": 172.43,
        "sale_price": 149.93,
        "rating": 4.8,
        "review_count": 654,
        "in_stock": True,
        "stock_quantity": 34,
        "image_url": "https://images.unsplash.com/photo-1584568694244-14fbdf83bd30?w=400&h=400&fit=crop&q=80",
        "featured": True,
        "specifications": {
            "size": "20x25x1",
            "merv_rating": 11,
            "filter_life": "90 days each",
            "pack_count": 10,
            "captures": "allergens, pet dander, smoke, smog",
            "savings": "25% off individual price",
            "supply_duration": "2.5 years"
        },
    },

    # ============== MERV 13 (Best) - Bacteria & Virus Carriers ==============
    # Individual
    {
        "id": str(uuid.uuid4()),
        "name": "Filtrete 20x25x1 MERV 13 Ultimate Allergen Air Filter",
        "description": "3M Filtrete Ultimate Allergen MERV 13 air filter - highest residential rating. Captures 99% of airborne particles including bacteria, virus carriers, and ultrafine particles. Hospital-grade filtration for your home. Exclusive Filtrete Brand 3-in-1 technology. Ideal for asthma and severe allergy sufferers. 20x25x1 inch.",
        "category": "appliance_parts",
        "subcategory": "hvac_filters",
        "brand": "Filtrete",
        "sku": "HVAC-3M-M13-2025-1",
        "price": 29.99,
        "sale_price": 24.99,
        "rating": 4.8,
        "review_count": 5678,
        "in_stock": True,
        "stock_quantity": 189,
        "image_url": "https://images.unsplash.com/photo-1585687433217-7c70f2146a32?w=400&h=400&fit=crop&q=80",
        "featured": True,
        "specifications": {
            "size": "20x25x1",
            "merv_rating": 13,
            "filter_life": "90 days",
            "pack_count": 1,
            "captures": "bacteria, virus carriers, ultrafine particles, allergens",
            "efficiency": "99% particle capture",
            "recommended_for": "asthma, severe allergies"
        },
    },
    {
        "id": str(uuid.uuid4()),
        "name": "Honeywell 16x25x1 MERV 13 Superior Allergen Air Filter",
        "description": "Honeywell Superior Allergen MERV 13 filter for maximum air purification. Captures microscopic particles down to 0.3 microns including bacteria and virus carriers. Ideal for immunocompromised individuals and healthcare settings. Sturdy construction with wire backing. 16x25x1 inch size.",
        "category": "appliance_parts",
        "subcategory": "hvac_filters",
        "brand": "Honeywell",
        "sku": "HVAC-HW-M13-1625-1",
        "price": 27.99,
        "sale_price": None,
        "rating": 4.7,
        "review_count": 3421,
        "in_stock": True,
        "stock_quantity": 145,
        "image_url": "https://images.unsplash.com/photo-1558618666-fcd25c85cd64?w=400&h=400&fit=crop&q=80",
        "featured": False,
        "specifications": {
            "size": "16x25x1",
            "merv_rating": 13,
            "filter_life": "90 days",
            "pack_count": 1,
            "captures": "bacteria, virus carriers, particles 0.3 microns+",
            "recommended_for": "immunocompromised, healthcare"
        },
    },
    {
        "id": str(uuid.uuid4()),
        "name": "Nordic Pure 20x20x1 MERV 13 Premium Air Filter",
        "description": "Nordic Pure MERV 13 premium air filter - made in USA. Hospital-grade filtration with antimicrobial protection. Captures 98% of particles including bacteria, smoke, and microscopic allergens. Hypoallergenic electrostatically charged media. Eco-friendly and recyclable frame. 20x20x1 inch.",
        "category": "appliance_parts",
        "subcategory": "hvac_filters",
        "brand": "Nordic Pure",
        "sku": "HVAC-NP-M13-2020-1",
        "price": 28.99,
        "sale_price": None,
        "rating": 4.8,
        "review_count": 4123,
        "in_stock": True,
        "stock_quantity": 112,
        "image_url": "https://images.unsplash.com/photo-1585771724684-38269d6639fd?w=400&h=400&fit=crop&q=80",
        "featured": True,
        "specifications": {
            "size": "20x20x1",
            "merv_rating": 13,
            "filter_life": "90 days",
            "pack_count": 1,
            "captures": "bacteria, smoke, microscopic allergens",
            "efficiency": "98% particle capture",
            "made_in": "USA",
            "antimicrobial": True
        },
    },
    # 2-Pack (10% off)
    {
        "id": str(uuid.uuid4()),
        "name": "Filtrete 20x25x1 MERV 13 Ultimate Allergen 2-Pack",
        "description": "Premium 2-pack of 3M Filtrete MERV 13 Ultimate Allergen filters. Save 10% for hospital-grade air filtration at home. Captures 99% of bacteria, virus carriers, and ultrafine particles. Essential for asthma sufferers and immunocompromised individuals. 6-month supply. 20x25x1 inch.",
        "category": "appliance_parts",
        "subcategory": "hvac_filters",
        "brand": "Filtrete",
        "sku": "HVAC-3M-M13-2025-2PK",
        "price": 53.98,
        "sale_price": 44.98,
        "rating": 4.8,
        "review_count": 2345,
        "in_stock": True,
        "stock_quantity": 98,
        "image_url": "https://images.unsplash.com/photo-1584568694244-14fbdf83bd30?w=400&h=400&fit=crop&q=80",
        "featured": True,
        "specifications": {
            "size": "20x25x1",
            "merv_rating": 13,
            "filter_life": "90 days each",
            "pack_count": 2,
            "captures": "bacteria, virus carriers, ultrafine particles",
            "efficiency": "99% particle capture",
            "savings": "10% off individual price"
        },
    },
    {
        "id": str(uuid.uuid4()),
        "name": "Nordic Pure 20x20x1 MERV 13 Premium 2-Pack",
        "description": "2-pack of Nordic Pure MERV 13 premium filters. Made in USA with antimicrobial protection. 10% savings on hospital-grade filtration. Captures bacteria, smoke, and microscopic allergens. Hypoallergenic and eco-friendly. Perfect for health-conscious homes. 20x20x1 inch size.",
        "category": "appliance_parts",
        "subcategory": "hvac_filters",
        "brand": "Nordic Pure",
        "sku": "HVAC-NP-M13-2020-2PK",
        "price": 52.18,
        "sale_price": None,
        "rating": 4.8,
        "review_count": 1567,
        "in_stock": True,
        "stock_quantity": 67,
        "image_url": "https://images.unsplash.com/photo-1585687433217-7c70f2146a32?w=400&h=400&fit=crop&q=80",
        "featured": False,
        "specifications": {
            "size": "20x20x1",
            "merv_rating": 13,
            "filter_life": "90 days each",
            "pack_count": 2,
            "captures": "bacteria, smoke, microscopic allergens",
            "savings": "10% off individual price",
            "made_in": "USA"
        },
    },
    # 10-Pack Bundle (25% off)
    {
        "id": str(uuid.uuid4()),
        "name": "Filtrete 20x25x1 MERV 13 Ultimate Allergen 10-Pack Bundle",
        "description": "Ultimate value 10-pack of 3M Filtrete MERV 13 filters. Save 25% for premium hospital-grade filtration. Perfect for families with severe allergies, asthma, or immunocompromised members. Each filter captures 99% of bacteria and virus carriers. Over 2 years of maximum protection. 20x25x1 inch size.",
        "category": "appliance_parts",
        "subcategory": "hvac_filters",
        "brand": "Filtrete",
        "sku": "HVAC-3M-M13-2025-10PK",
        "price": 224.93,
        "sale_price": 187.43,
        "rating": 4.9,
        "review_count": 876,
        "in_stock": True,
        "stock_quantity": 23,
        "image_url": "https://images.unsplash.com/photo-1558618666-fcd25c85cd64?w=400&h=400&fit=crop&q=80",
        "featured": True,
        "specifications": {
            "size": "20x25x1",
            "merv_rating": 13,
            "filter_life": "90 days each",
            "pack_count": 10,
            "captures": "bacteria, virus carriers, ultrafine particles",
            "efficiency": "99% particle capture",
            "savings": "25% off individual price",
            "supply_duration": "2.5 years"
        },
    },
    {
        "id": str(uuid.uuid4()),
        "name": "Honeywell 16x25x1 MERV 13 Superior Allergen 10-Pack Bundle",
        "description": "Bulk 10-pack of Honeywell Superior Allergen MERV 13 filters. Maximum savings of 25% off individual price. Hospital-grade filtration for commercial or residential use. Ideal for property managers or families prioritizing air quality. Captures particles down to 0.3 microns. 16x25x1 inch dimensions.",
        "category": "appliance_parts",
        "subcategory": "hvac_filters",
        "brand": "Honeywell",
        "sku": "HVAC-HW-M13-1625-10PK",
        "price": 209.93,
        "sale_price": None,
        "rating": 4.7,
        "review_count": 543,
        "in_stock": True,
        "stock_quantity": 18,
        "image_url": "https://images.unsplash.com/photo-1585771724684-38269d6639fd?w=400&h=400&fit=crop&q=80",
        "featured": False,
        "specifications": {
            "size": "16x25x1",
            "merv_rating": 13,
            "filter_life": "90 days each",
            "pack_count": 10,
            "captures": "bacteria, virus carriers, particles 0.3 microns+",
            "savings": "25% off individual price",
            "supply_duration": "2.5 years"
        },
    },
]


def load_water_filters():
    """Load water filters from backup JSON file."""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    json_path = os.path.join(script_dir, "..", "water_filters.json")
    
    try:
        with open(json_path, "r") as f:
            filters = json.load(f)
        print(f"✓ Loaded {len(filters)} water filters from backup JSON")
        return filters
    except FileNotFoundError:
        print(f"✗ water_filters.json not found at {json_path}")
        return []
    except json.JSONDecodeError as e:
        print(f"✗ Error parsing water_filters.json: {e}")
        return []


async def create_product(client: httpx.AsyncClient, product: dict) -> bool:
    """Create a single product via API."""
    try:
        # Ensure timestamps are set
        now = datetime.utcnow().isoformat()
        if "created_at" not in product:
            product["created_at"] = now
        if "updated_at" not in product:
            product["updated_at"] = now
        
        # Ensure ID exists
        if "id" not in product:
            product["id"] = str(uuid.uuid4())
        
        response = await client.post(
            f"{BACKEND_URL}/api/v1/products/",
            json=product,
            timeout=30.0
        )
        
        if response.status_code == 200:
            return True
        else:
            print(f"    ✗ Failed ({response.status_code}): {product['name'][:40]}")
            return False
    except Exception as e:
        print(f"    ✗ Error: {product['name'][:40]} - {e}")
        return False


async def trigger_reindex():
    """Trigger search index reindexing."""
    print("\n" + "=" * 60)
    print("Triggering Azure AI Search reindex...")
    print("=" * 60)
    
    async with httpx.AsyncClient(timeout=300.0) as client:
        response = await client.post(f"{BACKEND_URL}/api/v1/products/reindex")
        if response.status_code == 200:
            result = response.json()
            print(f"✓ Reindex complete: {result}")
            return True
        else:
            print(f"✗ Reindex failed: {response.status_code} - {response.text}")
            return False


async def main():
    """Main execution."""
    print("=" * 60)
    print("Filter Products Import Script")
    print("=" * 60)
    print(f"Backend URL: {BACKEND_URL}")
    print()
    
    # Load water filters from backup
    water_filters = load_water_filters()
    
    # Combine all products
    all_products = water_filters + HVAC_FILTERS
    
    print(f"\nTotal products to add:")
    print(f"  - Water Filters: {len(water_filters)}")
    print(f"  - HVAC Air Filters: {len(HVAC_FILTERS)}")
    print(f"  - Total: {len(all_products)}")
    
    # HVAC summary
    merv_8 = [p for p in HVAC_FILTERS if p.get('specifications', {}).get('merv_rating') == 8]
    merv_11 = [p for p in HVAC_FILTERS if p.get('specifications', {}).get('merv_rating') == 11]
    merv_13 = [p for p in HVAC_FILTERS if p.get('specifications', {}).get('merv_rating') == 13]
    print(f"\nHVAC Filters by MERV Rating:")
    print(f"  - MERV 8 (Basic): {len(merv_8)}")
    print(f"  - MERV 11 (Better): {len(merv_11)}")
    print(f"  - MERV 13 (Best): {len(merv_13)}")
    
    print("\n" + "-" * 60)
    print("Adding products via API...")
    print("-" * 60)
    
    success_count = 0
    failed_count = 0
    
    async with httpx.AsyncClient() as client:
        # Add water filters
        if water_filters:
            print("\n[Water Filters]")
            for i, product in enumerate(water_filters):
                result = await create_product(client, product)
                if result:
                    success_count += 1
                    print(f"  ✓ {i+1}/{len(water_filters)}: {product['name'][:50]}")
                else:
                    failed_count += 1
        
        # Add HVAC filters
        print("\n[HVAC Air Filters]")
        for i, product in enumerate(HVAC_FILTERS):
            result = await create_product(client, product)
            if result:
                success_count += 1
                merv = product.get('specifications', {}).get('merv_rating', '?')
                pack = product.get('specifications', {}).get('pack_count', 1)
                pack_label = f" ({pack}-Pack)" if pack > 1 else ""
                print(f"  ✓ {i+1}/{len(HVAC_FILTERS)}: [MERV {merv}] {product['name'][:40]}{pack_label}")
            else:
                failed_count += 1
    
    print("\n" + "=" * 60)
    print("Import Summary")
    print("=" * 60)
    print(f"✓ Successfully added: {success_count}")
    print(f"✗ Failed: {failed_count}")
    
    # Trigger reindex
    if success_count > 0:
        await trigger_reindex()
    
    print("\n" + "=" * 60)
    print("Done!")
    print("=" * 60)
    print("\nYou can now search for:")
    print("  - 'water filter' to find refrigerator water filters")
    print("  - 'HVAC filter' or 'air filter' to find HVAC air filters")
    print("  - 'MERV 13' for hospital-grade air filtration")


if __name__ == "__main__":
    asyncio.run(main())
