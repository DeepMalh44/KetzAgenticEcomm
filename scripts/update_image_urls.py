"""
Update Product Image URLs to Azure Blob Storage
================================================
Updates product image_url fields from Unsplash to Azure Blob Storage URLs.
"""

import requests
import urllib.parse

# Backend URL
BACKEND_URL = "https://backend-vnet.happyisland-58d32b38.eastus2.azurecontainerapps.io"

# Use backend proxy URL for images (same pattern as existing products)
STORAGE_ACCOUNT = "stketzagentickh7xm2"
CONTAINER = "product-images"
# Proxy URL pattern: /api/v1/img/product-images/{filename}
BLOB_BASE_URL = f"{BACKEND_URL}/api/v1/img/{CONTAINER}"

# Mapping of product names to blob filenames
# This maps product names (or partial matches) to the actual blob filenames
IMAGE_MAPPINGS = {
    # Water Filters
    "GE MWF Refrigerator Water Filter": "GE MWF Refrigerator Water Filter.jpg",
    "Samsung DA29-00020B Refrigerator Water Filter": "Samsung French Door Refrigerator 28 cu ft.jpg",  # Use Samsung image
    "LG LT1000P Refrigerator Water Filter": "LG French Door Refrigerator 28 cu ft.jpg",  # Use LG image
    "Whirlpool EveryDrop EDR1RXD1 Water Filter": "Whirlpool French Door Refrigerator 28 cu ft.jpg",  # Use Whirlpool image
    "Frigidaire EPTWFU01 PureSource Ultra II Water Filter": "Frigidaire EPTWFU01 PureSource Ultra II Water Filter.jpg",
    "GE RPWFE Refrigerator Water Filter with RFID": "GE RPWFE Refrigerator Water Filter with RFID.jpg",
    "Samsung DA97-17376B Water Filter HAF-QIN": "Samsung French Door Refrigerator 28 cu ft.jpg",  # Use Samsung image
    "Kenmore 9083 Refrigerator Water Filter": "Whirlpool French Door Refrigerator 28 cu ft.jpg",  # Kenmore is Whirlpool
    
    # HVAC Filters - MERV 8
    "Filtrete 20x25x1 MERV 8 Basic Dust Air Filter": "Filtrete 20x25x1 MERV 8 Basic Dust Air Filter.jpg",
    "Honeywell 16x25x1 MERV 8 FPR 5 Air Filter": "Honeywell 16x25x1 MERV 8 FPR 5 Air Filter",  # Note: no .jpg extension in blob
    "Nordic Pure 20x20x1 MERV 8 Pleated AC Furnace Filter": "Filtrete 20x25x1 MERV 8 Basic Dust Air Filter.jpg",  # Use Filtrete
    "Filtrete 20x25x1 MERV 8 Air Filter 2-Pack": "Filtrete 20x25x1 MERV 8 Basic Dust Air Filter.jpg",
    "Filtrete 20x25x1 MERV 8 Air Filter 10-Pack Bundle": "Filtrete 20x25x1 MERV 8 Basic Dust Air Filter.jpg",
    
    # HVAC Filters - MERV 11
    "Filtrete 20x25x1 MERV 11 Allergen Defense Air Filter": "Honeywell 16x20x1 MERV 11 Elite Allergen 2-Pack.jpg",
    "Honeywell 16x20x1 MERV 11 Elite Allergen Air Filter": "Honeywell 16x20x1 MERV 11 Elite Allergen 2-Pack.jpg",
    "Nordic Pure 16x25x1 MERV 11 Pleated Air Filter": "Honeywell 16x20x1 MERV 11 Elite Allergen 2-Pack.jpg",
    "Filtrete 20x25x1 MERV 11 Allergen Defense 2-Pack": "Honeywell 16x20x1 MERV 11 Elite Allergen 2-Pack.jpg",
    "Honeywell 16x20x1 MERV 11 Elite Allergen 2-Pack": "Honeywell 16x20x1 MERV 11 Elite Allergen 2-Pack.jpg",
    "Filtrete 20x25x1 MERV 11 Allergen Defense 10-Pack Bundle": "Honeywell 16x20x1 MERV 11 Elite Allergen 2-Pack.jpg",
    
    # HVAC Filters - MERV 13
    "Filtrete 20x25x1 MERV 13 Ultimate Allergen Air Filter": "Honeywell 16x20x1 MERV 11 Elite Allergen 2-Pack.jpg",
    "Honeywell 16x25x1 MERV 13 Superior Allergen Air Filter": "Honeywell 16x20x1 MERV 11 Elite Allergen 2-Pack.jpg",
    "Nordic Pure 20x20x1 MERV 13 Premium Air Filter": "Honeywell 16x20x1 MERV 11 Elite Allergen 2-Pack.jpg",
    "Filtrete 20x25x1 MERV 13 Ultimate Allergen 2-Pack": "Honeywell 16x20x1 MERV 11 Elite Allergen 2-Pack.jpg",
    "Nordic Pure 20x20x1 MERV 13 Premium 2-Pack": "Honeywell 16x20x1 MERV 11 Elite Allergen 2-Pack.jpg",
    "Filtrete 20x25x1 MERV 13 Ultimate Allergen 10-Pack Bundle": "Honeywell 16x20x1 MERV 11 Elite Allergen 2-Pack.jpg",
    "Honeywell 16x25x1 MERV 13 Superior Allergen 10-Pack Bundle": "Honeywell 16x20x1 MERV 11 Elite Allergen 2-Pack.jpg",
    
    # Power Tools
    "DeWalt 20V MAX Cordless Drill/Driver Kit": "Bosch 20V MAX Cordless Drill Driver Kit.jpg",
    "Milwaukee M18 FUEL Brushless Drill/Driver": "Milwaukee 20V MAX Cordless Drill Driver Kit.jpg",
    "Makita 18V LXT Brushless Drill/Driver Kit": "Makita 20V MAX Cordless Drill Driver Kit.jpg",
    "Bosch 18V Brushless Drill/Driver Kit": "Bosch 20V MAX Cordless Drill Driver Kit.jpg",
    "DeWalt 20V MAX XR Hammer Drill": "DeWalt 18V Brushless Hammer Drill.jpg",
    "Milwaukee M18 FUEL Hammer Drill": "Milwaukee 18V Brushless Hammer Drill.jpg",
    "Makita 18V LXT Hammer Drill": "Makita 18V Brushless Hammer Drill.jpg",
    "Bosch 18V Brushless Hammer Drill": "Bosch 18V Brushless Hammer Drill.jpg",
    "DeWalt 7-1/4 in. Circular Saw": "DeWalt 7-14 in. Circular Saw.jpg",
    "Milwaukee 7-1/4 in. Circular Saw": "Milwaukee 7-1 4 in. Circular Saw.jpg",
    "Makita 7-1/4 in. Circular Saw": "Makita 7-1 4 in. Circular Saw.jpg",
    "Ryobi 7-1/4 in. Circular Saw": "Ryobi 7-1 4 in. Circular Saw.jpg",
    "DeWalt 12 in. Sliding Compound Miter Saw": "DeWalt 12 in. Sliding Miter Saw.jpg",
    "Milwaukee 12 in. Sliding Miter Saw": "Milwaukee 12 in. Sliding Miter Saw.jpg",
    "Makita 12 in. Sliding Compound Miter Saw": "Makita 12 in. Sliding Miter Saw.jpg",
    "Ryobi 12 in. Sliding Miter Saw": "Ryobi 12 in. Sliding Miter Saw.jpg",
    "DeWalt 5 in. Random Orbit Sander": "DeWalt 5 in. Random Orbit Sander.jpg",
    "Milwaukee 5 in. Random Orbit Sander": "DeWalt 5 in. Random Orbit Sander.jpg",  # Use DeWalt
    "Makita 5 in. Random Orbit Sander": "Makita 5 in. Random Orbit Sander.jpg",
    "Bosch 5 in. Random Orbit Sander": "Bosch 5 in. Random Orbit Sander.jpg",
    
    # Hand Tools
    "Stanley 16 oz. Fiberglass Claw Hammer": "Stanley 16 oz. Fiberglass Claw Hammer.jpg",
    "Estwing 16 oz. Leather Grip Claw Hammer": "Estwing 16 oz. Fiberglass Claw Hammer.jpg",
    "Craftsman 16 oz. Fiberglass Hammer": "Craftsman 16 oz. Fiberglass Claw Hammer.jpg",
    "Stanley 20 oz. Framing Hammer": "Stanley 20 oz. Framing Hammer.jpg",
    "Estwing 20 oz. Framing Hammer": "Estwing 20 oz. Framing Hammer.jpg",
    "Craftsman 20 oz. Framing Hammer": "Craftsman 20 oz. Framing Hammer.jpg",
    "Klein Tools 11-Piece Screwdriver Set": "Klein Tools 11-Piece Screwdriver Set.jpg",
    "Stanley 11-Piece Screwdriver Set": "Stanley 11-Piece Screwdriver Set.jpg",
    "Craftsman 11-Piece Screwdriver Set": "Craftsman 11-Piece Screwdriver Set.jpg",
    "Craftsman 12-Piece Combination Wrench Set": "Craftsman 12-Piece Combination Wrench Set.jpg",
    "Husky 12-Piece Combination Wrench Set": "Husky 12-Piece Combination Wrench Set.jpg",
    "Channellock 12-Piece Combination Wrench Set": "Channellock 12-Piece Combination Wrench Set.jpg",
    
    # Flooring
    "Lifeproof Luxury Vinyl Plank Flooring - Oak": "Lifeproof Luxury Vinyl Plank Flooring - Sq Ft.jpg",
    "Shaw Luxury Vinyl Plank Flooring - Hickory": "Shaw Luxury Vinyl Plank Flooring - Sq Ft.jpg",
    "TrafficMaster Luxury Vinyl Plank Flooring - Walnut": "TrafficMaster Luxury Vinyl Plank Flooring - Sq Ft.jpg",
    "Pergo Water-Resistant Laminate Flooring - Oak": "Pergo Water-Resistant Laminate Flooring - Sq Ft.jpg",
    "Lifeproof Water-Resistant Laminate Flooring - Maple": "Lifeproof Water-Resistant Laminate Flooring - Sq Ft.jpg",
    "TrafficMaster Water-Resistant Laminate Flooring - Cherry": "TrafficMaster Water-Resistant Laminate Flooring - Sq Ft.jpg",
    "Bruce Oak Solid Hardwood Flooring": "Bruce Oak Solid Hardwood Flooring - Sq Ft.jpg",
    "Shaw Oak Solid Hardwood Flooring": "Shaw Oak Solid Hardwood Flooring - Sq Ft.jpg",
    "Mohawk Oak Solid Hardwood Flooring": "Mohawk Oak Solid Hardwood Flooring - Sq Ft.jpg",
    "Bruce Maple Engineered Hardwood Flooring": "Bruce Maple Engineered Hardwood - Sq Ft.jpg",
    "Shaw Maple Engineered Hardwood Flooring": "Shaw Maple Engineered Hardwood - Sq Ft.jpg",
    "Mohawk Maple Engineered Hardwood Flooring": "Mohawk Maple Engineered Hardwood - Sq Ft.jpg",
    
    # Plumbing
    "Delta Single-Handle Pull-Down Kitchen Faucet": "Delta Single-Handle Pull-Down Kitchen Faucet.jpg",
    "Moen Single-Handle Pull-Down Kitchen Faucet": "Moen Single-Handle Pull-Down Kitchen Faucet.jpg",
    "Pfister Single-Handle Pull-Down Kitchen Faucet": "Pfister Single-Handle Pull-Down Kitchen Faucet.jpg",
    "Delta Widespread Bathroom Faucet": "Delta Widespread Bathroom Faucet.jpg",
    "Moen Widespread Bathroom Faucet": "Moen Widespread Bathroom Faucet.jpg",
    "Kohler Widespread Bathroom Faucet": "Kohler Widespread Bathroom Faucet.jpg",
    "Pfister Widespread Bathroom Faucet": "Pfister Widespread Bathroom Faucet.jpg",
    "Kohler Comfort Height Elongated Toilet": "Kohler Comfort Height Elongated Toilet.jpg",
    "American Standard Comfort Height Elongated Toilet": "American Standard Comfort Height Elongated Toilet.jpg",
    "TOTO Comfort Height Elongated Toilet": "TOTO Comfort Height Elongated Toilet.jpg",
    
    # Electrical
    "Leviton 15 Amp GFCI Outlet": "Leviton 15 Amp GFCI Outlet with LED.jpg",
    "GE 15 Amp GFCI Outlet": "GE 15 Amp GFCI Outlet with LED.jpg",
    "Lutron 15 Amp GFCI Outlet": "Lutron 15 Amp GFCI Outlet with LED.jpg",
    "Leviton USB Wall Outlet - Dual Port": "Leviton USB Wall Outlet Dual Port.jpg",
    "GE USB Wall Outlet - Dual Port": "GE USB Wall Outlet Dual Port.jpg",
    "Lutron USB Wall Outlet - Dual Port": "Lutron USB Wall Outlet Dual Port.jpg",
    
    # Lighting
    "Philips LED Recessed Downlight 6 inch": "Philips LED Recessed Downlight 6 inch.jpg",
    "GE LED Recessed Downlight 6 inch": "GE LED Recessed Downlight 6 inch.jpg",
    "Kichler LED Recessed Downlight 6 inch": "Kichler LED Recessed Downlight 6 inch.jpg",
    "Kichler Modern Pendant Light": "Kichler Modern Pendant Light.jpg",
    "GE Modern Pendant Light": "GE Modern Pendant Light.jpg",
    "Philips Modern Pendant Light": "Philips Modern Pendant Light.jpg",
    
    # Door Hardware
    "Schlage Entry Door Handleset": "Schlage Entry Door Handleset.jpg",
    "Kwikset Entry Door Handleset": "Kwikset Entry Door Handleset.jpg",
    "Baldwin Entry Door Handleset": "Baldwin Entry Door Handleset.jpg",
    "Schlage Smart Lock with Keypad": "Schlage Smart Lock with Keypad.jpg",
    "Kwikset Smart Lock with Keypad": "Kwikset Smart Lock with Keypad.jpg",
    "Baldwin Smart Lock with Keypad": "Baldwin Smart Lock with Keypad.jpg",
    
    # Paint
    "Behr Premium Plus Interior Eggshell Paint - 1 Gal": "Behr Premium Plus Interior Eggshell Paint - 1 Gal.jpg",
    "Sherwin-Williams Premium Plus Interior Eggshell Paint - 1 Gal": "Sherwin-Williams Premium Plus Interior Eggshell Paint - 1 Gal.jpg",
    "Benjamin Moore Premium Plus Interior Eggshell Paint - 1 Gal": "Benjamin Moore Premium Plus Interior Eggshell Paint - 1 Gal.jpg",
    "Behr Ultra Interior Flat White Ceiling Paint": "Behr Ultra Interior Flat White Ceiling Paint.jpg",
    "Sherwin-Williams Ultra Interior Flat White Ceiling Paint": "Sherwin-Williams Ultra Interior Flat White Ceiling Paint.jpg",
    "Benjamin Moore Ultra Interior Flat White Ceiling Paint": "Benjamin Moore Ultra Interior Flat White Ceiling Paint.jpg",
    "Behr All-Weather Exterior Satin Paint - 1 Gal": "Behr All-Weather Exterior Satin Paint - 1 Gal.jpg",
    "Sherwin-Williams All-Weather Exterior Satin Paint - 1 Gal": "Sherwin-Williams All-Weather Exterior Satin Paint - 1 Gal.jpg",
    "PPG All-Weather Exterior Satin Paint - 1 Gal": "PPG All-Weather Exterior Satin Paint - 1 Gal.jpg",
    
    # Appliances
    "Samsung French Door Refrigerator 28 cu. ft.": "Samsung French Door Refrigerator 28 cu ft.jpg",
    "LG French Door Refrigerator 28 cu. ft.": "LG French Door Refrigerator 28 cu ft.jpg",
    "GE French Door Refrigerator 28 cu. ft.": "GE French Door Refrigerator 28 cu ft.jpg",
    "Whirlpool French Door Refrigerator 28 cu. ft.": "Whirlpool French Door Refrigerator 28 cu ft.jpg",
    "Samsung Front Load Washer 4.5 cu. ft.": "Samsung Front Load Washer 4.5 cu ft.jpg",
    "LG Front Load Washer 4.5 cu. ft.": "LG Front Load Washer 4.5 cu ft.jpg",
    "Maytag Front Load Washer 4.5 cu. ft.": "Maytag Front Load Washer 4.5 cu ft.jpg",
    "Whirlpool Front Load Washer 4.5 cu. ft.": "Whirlpool Front Load Washer 4.5 cu ft.jpg",
    
    # Outdoor/Grills
    "Weber 3-Burner Gas Grill": "Weber 3-Burner Gas Grill.jpg",
    "Char-Broil 3-Burner Gas Grill": "Char-Broil 3-Burner Gas Grill.jpg",
    "Traeger 3-Burner Gas Grill": "Traeger 3-Burner Gas Grill.jpg",
    "Weber Pellet Smoker Grill": "Weber Pellet Smoker Grill.jpg",
    "Traeger Pellet Smoker Grill": "Traeger Pellet Smoker Grill.jpg",
    "Char-Broil Pellet Smoker Grill": "Char-Broil Pellet Smoker Grill.jpg",
    "Hampton Bay 5-Piece Patio Dining Set": "Hampton Bay 5-Piece Patio Dining Set.jpg",
    "Home Decorators 5-Piece Patio Dining Set": "Home Decorators 5-Piece Patio Dining Set.jpg",
    
    # Lumber
    "2 in. x 4 in. x 8 ft. Premium Kiln-Dried Stud": "2 in. x 4 in. x 8 ft. Premium Kiln-Dried Stud.jpg",
    "2 in. x 6 in. x 10 ft. Pressure-Treated Lumber": "2 in. x 6 in. x 10 ft. Pressure-Treated Lumber.jpg",
    "1/2 in. x 4 ft. x 8 ft. Drywall Panel": "1 2 in. x 4 ft. x 8 ft. Drywall Panel.jpg",
}


def get_blob_url(filename: str) -> str:
    """Generate the full blob URL for a filename."""
    encoded_filename = urllib.parse.quote(filename, safe='')
    return f"{BLOB_BASE_URL}/{encoded_filename}"


def find_matching_blob(product_name: str) -> str | None:
    """Find a matching blob filename for a product name."""
    # Exact match first
    if product_name in IMAGE_MAPPINGS:
        return IMAGE_MAPPINGS[product_name]
    
    # Partial match
    for key, value in IMAGE_MAPPINGS.items():
        if key.lower() in product_name.lower() or product_name.lower() in key.lower():
            return value
    
    return None


def get_all_products() -> list:
    """Fetch all products from the API."""
    products = []
    skip = 0
    limit = 100
    
    while True:
        print(f"  Fetching batch (skip={skip})...")
        response = requests.get(
            f"{BACKEND_URL}/api/v1/products/",
            params={"limit": limit, "skip": skip},
            timeout=30
        )
        
        if response.status_code != 200:
            print(f"Error fetching products: {response.status_code}")
            break
        
        data = response.json()
        batch = data.get("products", []) if isinstance(data, dict) else data
        
        if not batch:
            break
            
        products.extend(batch)
        skip += limit
        
        if len(batch) < limit:
            break
    
    return products


def update_product_image(product_id: str, product_name: str, new_image_url: str) -> bool:
    """Update a product's image URL via the API."""
    response = requests.patch(
        f"{BACKEND_URL}/api/v1/products/{product_id}",
        json={"image_url": new_image_url},
        timeout=30
    )
    
    if response.status_code == 200:
        return True
    else:
        print(f"  ✗ Failed to update {product_name}: {response.status_code}")
        return False


def main():
    """Main execution."""
    print("=" * 70)
    print("Update Product Image URLs to Azure Blob Storage")
    print("=" * 70)
    print(f"Storage Account: {STORAGE_ACCOUNT}")
    print(f"Container: {CONTAINER}")
    print()
    
    # Get all products
    print("Fetching all products...")
    products = get_all_products()
    print(f"Found {len(products)} products\n")
    
    # Track statistics
    updated = 0
    skipped = 0
    not_found = 0
    already_azure = 0
    
    print("-" * 70)
    print("Updating image URLs...")
    print("-" * 70)
    
    for product in products:
        product_id = product.get("id")
        product_name = product.get("name", "Unknown")
        current_url = product.get("image_url", "")
        
        # Skip if already pointing to Azure (via proxy or direct)
        # Proxy URLs contain /api/v1/img/, direct URLs contain the storage account
        if "/api/v1/img/" in current_url or STORAGE_ACCOUNT in current_url:
            already_azure += 1
            continue
        
        # Only update if it's an Unsplash URL
        if "unsplash.com" not in current_url:
            not_found += 1
            continue
        
        # Find matching blob
        blob_filename = find_matching_blob(product_name)
        
        if blob_filename:
            new_url = get_blob_url(blob_filename)
            success = update_product_image(product_id, product_name, new_url)
            
            if success:
                updated += 1
                print(f"  ✓ {product_name[:50]}")
            else:
                skipped += 1
        else:
            not_found += 1
            print(f"  ? No image mapping for: {product_name[:50]}")
    
    print()
    print("=" * 70)
    print("Summary")
    print("=" * 70)
    print(f"✓ Updated: {updated}")
    print(f"○ Already Azure: {already_azure}")
    print(f"? No mapping found: {not_found}")
    print(f"✗ Failed: {skipped}")
    print()
    
    # Trigger reindex
    if updated > 0:
        print("Triggering search index reindex...")
        response = requests.post(f"{BACKEND_URL}/api/v1/products/reindex", timeout=300)
        if response.status_code == 200:
            result = response.json()
            print(f"✓ Reindex complete: {result}")
        else:
            print(f"✗ Reindex failed: {response.status_code}")
    
    print("\nDone!")


if __name__ == "__main__":
    main()
