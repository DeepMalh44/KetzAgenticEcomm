"""
Product Seeder Script (Synchronous)
===================================

Seeds 350+ home improvement products into Cosmos DB.
Uses synchronous PyMongo for Cosmos DB compatibility.
"""

import os
import sys
import random
import uuid
from datetime import datetime, timezone
from pymongo import MongoClient

# Minimum products target
MIN_PRODUCTS_TARGET = 350

# Product categories matching a home improvement store
CATEGORIES = {
    "power_tools": {
        "subcategories": ["drills", "saws", "sanders", "routers", "grinders", "impact_drivers"],
        "brands": ["DeWalt", "Milwaukee", "Makita", "Bosch", "Ryobi", "Craftsman", "Ridgid"],
        "base_price_range": (79, 599)
    },
    "hand_tools": {
        "subcategories": ["hammers", "screwdrivers", "wrenches", "pliers", "measuring", "levels"],
        "brands": ["Stanley", "Klein Tools", "Channellock", "Craftsman", "Estwing", "Husky"],
        "base_price_range": (9, 149)
    },
    "building_materials": {
        "subcategories": ["lumber", "drywall", "plywood", "concrete", "insulation", "roofing"],
        "brands": ["Generic", "Simpson Strong-Tie", "Owens Corning", "CertainTeed", "Georgia-Pacific"],
        "base_price_range": (8, 299)
    },
    "paint": {
        "subcategories": ["interior_paint", "exterior_paint", "primers", "stains", "spray_paint", "supplies"],
        "brands": ["Behr", "Sherwin-Williams", "Benjamin Moore", "PPG", "Valspar", "Rust-Oleum"],
        "base_price_range": (12, 89)
    },
    "flooring": {
        "subcategories": ["hardwood", "laminate", "vinyl", "tile", "carpet", "underlayment"],
        "brands": ["Pergo", "Shaw", "Mohawk", "Lifeproof", "TrafficMaster", "Bruce", "Armstrong"],
        "base_price_range": (29, 299)
    },
    "plumbing": {
        "subcategories": ["faucets", "toilets", "pipes", "water_heaters", "sinks", "shower_heads"],
        "brands": ["Moen", "Delta", "Kohler", "American Standard", "Pfister", "Glacier Bay", "TOTO"],
        "base_price_range": (19, 899)
    },
    "electrical": {
        "subcategories": ["outlets", "switches", "wire", "lighting", "breakers", "conduit"],
        "brands": ["Leviton", "Lutron", "Eaton", "Siemens", "Square D", "GE", "Legrand"],
        "base_price_range": (5, 299)
    },
    "hardware": {
        "subcategories": ["door_hardware", "cabinet_hardware", "fasteners", "hinges", "locks", "brackets"],
        "brands": ["Schlage", "Kwikset", "Baldwin", "Emtek", "Liberty", "Amerock", "Richelieu"],
        "base_price_range": (4, 199)
    },
    "outdoor_living": {
        "subcategories": ["grills", "patio_furniture", "fire_pits", "outdoor_lighting", "planters", "decking"],
        "brands": ["Weber", "Traeger", "Big Green Egg", "Hampton Bay", "Trex", "TimberTech", "AZEK"],
        "base_price_range": (29, 1999)
    },
    "appliances": {
        "subcategories": ["washers", "dryers", "refrigerators", "dishwashers", "microwaves", "ranges"],
        "brands": ["Samsung", "LG", "Whirlpool", "GE", "Maytag", "KitchenAid", "Bosch"],
        "base_price_range": (199, 2499)
    }
}

# Product name templates by subcategory
PRODUCT_TEMPLATES = {
    "drills": [
        "{brand} 20V MAX Cordless Drill/Driver Kit",
        "{brand} 18V Brushless Hammer Drill",
        "{brand} 12V Compact Drill Driver",
        "{brand} Variable Speed Corded Drill",
        "{brand} Right Angle Drill",
    ],
    "saws": [
        "{brand} 7-1/4 in. Circular Saw",
        "{brand} 10 in. Sliding Compound Miter Saw",
        "{brand} Reciprocating Saw Kit",
        "{brand} 12 in. Dual-Bevel Miter Saw",
        "{brand} Jigsaw with LED Light",
    ],
    "sanders": [
        "{brand} Random Orbit Sander",
        "{brand} Sheet Sander",
        "{brand} Detail Sander",
        "{brand} Belt Sander 3x21 in.",
        "{brand} Oscillating Multi-Tool",
    ],
    "hammers": [
        "{brand} 16 oz. Claw Hammer",
        "{brand} 20 oz. Framing Hammer",
        "{brand} Ball Peen Hammer",
        "{brand} Dead Blow Hammer",
        "{brand} Rubber Mallet",
    ],
    "screwdrivers": [
        "{brand} 6-Piece Screwdriver Set",
        "{brand} Ratcheting Screwdriver",
        "{brand} Precision Screwdriver Set",
        "{brand} Multi-Bit Screwdriver",
        "{brand} Impact Driver Bit Set",
    ],
    "faucets": [
        "{brand} Single-Handle Kitchen Faucet",
        "{brand} Pull-Down Sprayer Kitchen Faucet",
        "{brand} Widespread Bathroom Faucet",
        "{brand} Single-Handle Bathroom Faucet",
        "{brand} Touchless Kitchen Faucet",
    ],
    "toilets": [
        "{brand} 2-Piece Elongated Toilet",
        "{brand} One-Piece Comfort Height Toilet",
        "{brand} Dual Flush Toilet",
        "{brand} Water-Saving Toilet",
        "{brand} ADA Compliant Toilet",
    ],
    "interior_paint": [
        "{brand} Interior Eggshell Paint - 1 Gal",
        "{brand} Ultra Interior Flat Paint",
        "{brand} Premium Plus Interior Semi-Gloss",
        "{brand} Interior Satin Paint and Primer",
        "{brand} Ceiling Paint Flat White",
    ],
    "exterior_paint": [
        "{brand} Exterior House Paint - 1 Gal",
        "{brand} All-Weather Exterior Paint",
        "{brand} Wood Stain Exterior",
        "{brand} Porch and Floor Paint",
        "{brand} Masonry and Stucco Paint",
    ],
    "hardwood": [
        "{brand} Oak Hardwood Flooring - {size}",
        "{brand} Maple Engineered Hardwood",
        "{brand} Hickory Solid Hardwood",
        "{brand} Walnut Engineered Floor",
        "{brand} Bamboo Flooring Natural",
    ],
    "laminate": [
        "{brand} Laminate Wood Plank Flooring",
        "{brand} Water-Resistant Laminate",
        "{brand} Textured Laminate Flooring",
        "{brand} High-Traffic Laminate",
        "{brand} Easy Install Laminate Planks",
    ],
    "outlets": [
        "{brand} 15 Amp Duplex Outlet",
        "{brand} 20 Amp GFCI Outlet",
        "{brand} USB Wall Outlet",
        "{brand} Smart Wi-Fi Outlet",
        "{brand} Weather-Resistant Outlet",
    ],
    "switches": [
        "{brand} Single Pole Switch",
        "{brand} 3-Way Switch",
        "{brand} Dimmer Switch",
        "{brand} Smart Switch Wi-Fi",
        "{brand} Motion Sensor Switch",
    ],
    "grills": [
        "{brand} 3-Burner Gas Grill",
        "{brand} Charcoal Kettle Grill",
        "{brand} Pellet Smoker Grill",
        "{brand} Portable Gas Grill",
        "{brand} Built-In Gas Grill",
    ],
    "refrigerators": [
        "{brand} French Door Refrigerator",
        "{brand} Side-by-Side Refrigerator",
        "{brand} Top Freezer Refrigerator",
        "{brand} Counter-Depth Refrigerator",
        "{brand} Mini Fridge",
    ],
    # Default templates for other subcategories
    "default": [
        "{brand} Professional Grade {subcategory}",
        "{brand} Premium {subcategory} Set",
        "{brand} Heavy-Duty {subcategory}",
        "{brand} Contractor Grade {subcategory}",
        "{brand} DIY {subcategory} Kit",
    ]
}

# Features by category
FEATURES = {
    "power_tools": [
        "Brushless motor for extended runtime",
        "Variable speed control",
        "LED work light",
        "Battery fuel gauge",
        "Ergonomic grip design",
        "Includes carrying case",
    ],
    "hand_tools": [
        "Heat-treated steel construction",
        "Comfort grip handle",
        "Lifetime warranty",
        "Precision machined",
        "Rust-resistant finish",
    ],
    "paint": [
        "Low VOC formula",
        "One-coat coverage",
        "Mildew resistant",
        "Washable finish",
        "Self-priming",
    ],
    "plumbing": [
        "WaterSense certified",
        "Easy installation",
        "Corrosion-resistant finish",
        "Includes mounting hardware",
        "Limited lifetime warranty",
    ],
    "electrical": [
        "UL Listed",
        "Easy wire terminals",
        "Tamper-resistant",
        "Commercial grade",
        "Energy efficient",
    ],
    "default": [
        "High quality materials",
        "Easy to install",
        "Durable construction",
        "Professional results",
        "Great value",
    ]
}


def generate_sku():
    """Generate a unique SKU."""
    return f"KTZ-{uuid.uuid4().hex[:8].upper()}"


def generate_product(category: str, subcategory: str, brand: str, price_range: tuple) -> dict:
    """Generate a single product."""
    # Get product name template
    templates = PRODUCT_TEMPLATES.get(subcategory, PRODUCT_TEMPLATES["default"])
    template = random.choice(templates)
    
    # Format name
    name = template.format(brand=brand, subcategory=subcategory.replace("_", " ").title(), size="sq ft")
    
    # Generate price
    base_price = random.uniform(price_range[0], price_range[1])
    price = round(base_price, 2)
    
    # Some products have sale prices
    sale_price = None
    if random.random() < 0.3:  # 30% on sale
        sale_price = round(price * random.uniform(0.7, 0.9), 2)
    
    # Generate rating and reviews
    rating = round(random.uniform(3.5, 5.0), 1)
    review_count = random.randint(5, 500)
    
    # Generate stock
    stock_quantity = random.randint(0, 200)
    in_stock = stock_quantity > 0
    
    # Get features
    category_features = FEATURES.get(category, FEATURES["default"])
    features = random.sample(category_features, min(3, len(category_features)))
    
    # Generate description
    description = f"The {name} is a premium {subcategory.replace('_', ' ')} from {brand}. "
    description += "Features include: " + ", ".join(features) + ". "
    description += f"Perfect for both DIY enthusiasts and professionals."
    
    # Image URL (placeholder - will be actual images after upload)
    image_url = f"https://stketzagentickh7xm2.blob.core.windows.net/product-images/{category}/{subcategory}/{generate_sku().lower()}.jpg"
    
    now = datetime.now(timezone.utc)
    
    return {
        "id": str(uuid.uuid4()),
        "sku": generate_sku(),
        "name": name,
        "description": description,
        "category": category,
        "subcategory": subcategory,
        "brand": brand,
        "price": price,
        "sale_price": sale_price,
        "rating": rating,
        "review_count": review_count,
        "stock_quantity": stock_quantity,
        "in_stock": in_stock,
        "featured": random.random() < 0.1,  # 10% featured
        "image_url": image_url,
        "features": features,
        "specifications": {
            "weight": f"{random.uniform(0.5, 50):.1f} lbs",
            "dimensions": f"{random.randint(5, 36)}x{random.randint(5, 36)}x{random.randint(5, 36)} in"
        },
        "created_at": now,
        "updated_at": now
    }


def generate_products() -> list:
    """Generate all products."""
    products = []
    
    # Calculate products per category to reach minimum
    products_per_category = (MIN_PRODUCTS_TARGET // len(CATEGORIES)) + 10
    
    for category, config in CATEGORIES.items():
        for subcategory in config["subcategories"]:
            # Generate multiple products per subcategory
            products_per_sub = products_per_category // len(config["subcategories"])
            
            for _ in range(max(3, products_per_sub)):
                brand = random.choice(config["brands"])
                product = generate_product(
                    category=category,
                    subcategory=subcategory,
                    brand=brand,
                    price_range=config["base_price_range"]
                )
                products.append(product)
    
    return products


def seed_database():
    """Main function to seed the database."""
    print("🌱 Starting product seeding...")
    print(f"   Target: {MIN_PRODUCTS_TARGET}+ products")
    
    # Get connection string
    connection_string = os.getenv("AZURE_COSMOS_CONNECTION_STRING")
    if not connection_string:
        print("❌ AZURE_COSMOS_CONNECTION_STRING not set")
        print("Please set the environment variable and try again.")
        sys.exit(1)
    
    database_name = os.getenv("AZURE_COSMOS_DATABASE", "ketzagenticecomm")
    
    # Connect to Cosmos DB
    print(f"📦 Connecting to database: {database_name}")
    client = MongoClient(connection_string)
    db = client[database_name]
    products_collection = db["products"]
    
    # Generate products
    print("🏭 Generating products...")
    products = generate_products()
    print(f"✅ Generated {len(products)} products (target was {MIN_PRODUCTS_TARGET}+)")
    
    # Clear existing products
    print("🗑️ Clearing existing products...")
    products_collection.delete_many({})
    
    # Insert products in batches
    batch_size = 100
    print(f"📤 Inserting products in batches of {batch_size}...")
    
    for i in range(0, len(products), batch_size):
        batch = products[i:i + batch_size]
        products_collection.insert_many(batch)
        print(f"   Inserted {min(i + batch_size, len(products))}/{len(products)} products")
    
    # Create indexes
    print("📇 Creating indexes...")
    products_collection.create_index("category")
    products_collection.create_index("subcategory")
    products_collection.create_index("brand")
    products_collection.create_index("sku", unique=True)
    products_collection.create_index("stock_quantity")
    
    print("\n✨ Seeding complete!")
    print(f"   Total products: {len(products)}")
    
    # Print summary by category
    print("\n📊 Products by category:")
    for category in CATEGORIES.keys():
        count = len([p for p in products if p["category"] == category])
        print(f"   {category}: {count}")
    
    # Print stock summary
    in_stock = len([p for p in products if p["in_stock"]])
    out_of_stock = len(products) - in_stock
    print(f"\n📦 Stock summary:")
    print(f"   In stock: {in_stock}")
    print(f"   Out of stock: {out_of_stock}")
    
    client.close()


if __name__ == "__main__":
    seed_database()
