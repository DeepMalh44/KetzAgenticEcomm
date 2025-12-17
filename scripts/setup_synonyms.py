"""
Setup Synonym Map for Azure AI Search
======================================

Creates a synonym map for home improvement product searches.
This enables users to search using common synonyms like:
- "fridge" → finds "refrigerator"
- "tap" → finds "faucet"
- "bbq" → finds "grill"

Run this script once to create the synonym map, then update the index.
"""

import os
import httpx
from dotenv import load_dotenv

load_dotenv()

# Azure AI Search configuration
SEARCH_ENDPOINT = os.getenv("AZURE_SEARCH_ENDPOINT", "").rstrip("/")
SEARCH_KEY = os.getenv("AZURE_SEARCH_KEY", "")
SYNONYM_MAP_NAME = "product-synonyms"

# Comprehensive synonyms for home improvement products
# Format: "word1, word2, word3" means all are equivalent (bidirectional)
# Format: "word1, word2 => canonical" means word1/word2 map to canonical (one-way)

SYNONYM_RULES = [
    # ============================================
    # APPLIANCES
    # ============================================
    # Refrigerators - most common synonym issue!
    "fridge, refrigerator, icebox, cooler",
    "freezer, deep freeze",
    
    # Washers & Dryers
    "washer, washing machine, clothes washer, laundry machine",
    "dryer, clothes dryer, tumble dryer",
    "laundry, wash",
    
    # ============================================
    # POWER TOOLS
    # ============================================
    # Drills
    "drill, power drill, cordless drill, electric drill",
    "driver, screwdriver, screw gun",
    "hammer drill, rotary hammer, impact drill",
    
    # Saws
    "circular saw, skilsaw, circ saw, power saw",
    "miter saw, mitre saw, chop saw, compound saw",
    "jigsaw, jig saw, sabre saw",
    "reciprocating saw, recip saw, sawzall",
    
    # Sanders
    "sander, power sander, electric sander",
    "orbital sander, random orbit sander, palm sander",
    
    # ============================================
    # HAND TOOLS
    # ============================================
    "hammer, claw hammer, framing hammer, mallet",
    "screwdriver, screw driver",
    "wrench, spanner, socket wrench",
    "pliers, pincers, grippers",
    "tape measure, measuring tape, tape",
    "level, spirit level, bubble level",
    
    # ============================================
    # PLUMBING
    # ============================================
    # Faucets - another common synonym issue!
    "faucet, tap, spigot, fixture, valve",
    "kitchen faucet, kitchen tap, sink faucet",
    "bathroom faucet, bath faucet, lavatory faucet",
    
    # Toilets
    "toilet, commode, lavatory, wc, water closet",
    
    # General plumbing
    "pipe, tubing, piping",
    "fitting, connector, coupling",
    
    # ============================================
    # FLOORING
    # ============================================
    "flooring, floor, floors",
    "hardwood, wood floor, wooden floor, solid wood",
    "engineered hardwood, engineered wood",
    "laminate, laminate flooring, laminated floor",
    "vinyl, vinyl plank, lvp, luxury vinyl, vinyl flooring",
    "tile, tiles, ceramic tile, porcelain tile",
    "carpet, carpeting, rug",
    
    # ============================================
    # PAINT
    # ============================================
    "paint, coating, finish, wall paint",
    "interior paint, indoor paint, inside paint",
    "exterior paint, outdoor paint, outside paint",
    "primer, undercoat, base coat",
    "stain, wood stain",
    "eggshell, satin, semi-gloss",
    
    # ============================================
    # ELECTRICAL
    # ============================================
    # Outlets
    "outlet, receptacle, plug, socket, electrical outlet",
    "gfci, gfi, ground fault",
    "usb outlet, usb port, charging outlet",
    
    # Lighting
    "light, lighting, lamp, fixture, luminaire",
    "bulb, light bulb, led bulb",
    "recessed light, can light, downlight, pot light",
    "pendant, pendant light, hanging light",
    "chandelier, ceiling light",
    "switch, light switch, dimmer",
    
    # ============================================
    # OUTDOOR / PATIO
    # ============================================
    # Grills - common synonym issue
    "grill, barbecue, bbq, barbeque",
    "gas grill, propane grill",
    "smoker, pellet smoker, pellet grill, offset smoker",
    "charcoal grill, charcoal bbq",
    
    # Patio furniture
    "patio, deck, outdoor, backyard",
    "patio furniture, outdoor furniture, deck furniture",
    "patio set, dining set, outdoor set",
    
    # ============================================
    # HARDWARE / DOORS
    # ============================================
    "lock, door lock, deadbolt, bolt",
    "smart lock, electronic lock, keypad lock, keyless entry",
    "handle, handleset, door handle, lever",
    "knob, door knob, doorknob",
    "hinge, door hinge",
    
    # ============================================
    # BUILDING MATERIALS
    # ============================================
    "lumber, wood, timber, board",
    "stud, 2x4, two by four",
    "plywood, ply, sheet wood",
    "drywall, sheetrock, gypsum board, wallboard, plasterboard",
    "insulation, batting, foam board",
    "concrete, cement",
    
    # ============================================
    # BRAND VARIATIONS (common misspellings)
    # ============================================
    "dewalt, de walt",
    "milwaukee, milwaukie",
    "makita, mikita",
    "ryobi, ryobe",
    "kohler, koehler",
    "moen, moane",
    
    # ============================================
    # GENERAL TERMS
    # ============================================
    "tool, tools, equipment",
    "kit, set, combo",
    "cordless, battery powered, wireless",
    "brushless, brushless motor",
    "heavy duty, professional, pro",
    "diy, do it yourself, home improvement",
]


def create_synonym_map():
    """Create or update the synonym map in Azure AI Search."""
    
    if not SEARCH_ENDPOINT or not SEARCH_KEY:
        print("ERROR: Missing AZURE_SEARCH_ENDPOINT or AZURE_SEARCH_KEY")
        print("Make sure your .env file has these values set")
        return False
    
    # Build the synonym map definition
    synonym_map = {
        "name": SYNONYM_MAP_NAME,
        "format": "solr",
        "synonyms": "\n".join(SYNONYM_RULES)
    }
    
    # API endpoint for synonym maps
    url = f"{SEARCH_ENDPOINT}/synonymmaps/{SYNONYM_MAP_NAME}?api-version=2024-07-01"
    
    headers = {
        "Content-Type": "application/json",
        "api-key": SEARCH_KEY
    }
    
    print(f"Creating synonym map '{SYNONYM_MAP_NAME}'...")
    print(f"Endpoint: {SEARCH_ENDPOINT}")
    print(f"Total synonym rules: {len(SYNONYM_RULES)}")
    
    # Use PUT to create or update
    with httpx.Client(timeout=30.0) as client:
        response = client.put(url, json=synonym_map, headers=headers)
        
        if response.status_code in [200, 201]:
            print(f"✅ Synonym map '{SYNONYM_MAP_NAME}' created/updated successfully!")
            return True
        else:
            print(f"❌ Failed to create synonym map: {response.status_code}")
            print(f"Response: {response.text}")
            return False


def list_synonym_maps():
    """List all synonym maps in the search service."""
    
    url = f"{SEARCH_ENDPOINT}/synonymmaps?api-version=2024-07-01"
    headers = {"api-key": SEARCH_KEY}
    
    with httpx.Client(timeout=30.0) as client:
        response = client.get(url, headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            maps = data.get("value", [])
            print(f"\n📋 Existing synonym maps ({len(maps)}):")
            for sm in maps:
                print(f"  - {sm['name']}")
            return maps
        else:
            print(f"Failed to list synonym maps: {response.status_code}")
            return []


def get_synonym_map_details():
    """Get details of the product synonyms map."""
    
    url = f"{SEARCH_ENDPOINT}/synonymmaps/{SYNONYM_MAP_NAME}?api-version=2024-07-01"
    headers = {"api-key": SEARCH_KEY}
    
    with httpx.Client(timeout=30.0) as client:
        response = client.get(url, headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            synonyms = data.get("synonyms", "").split("\n")
            print(f"\n📖 Synonym map '{SYNONYM_MAP_NAME}' details:")
            print(f"   Rules: {len(synonyms)}")
            print(f"\n   Sample rules:")
            for rule in synonyms[:10]:
                print(f"   • {rule}")
            if len(synonyms) > 10:
                print(f"   ... and {len(synonyms) - 10} more rules")
            return data
        else:
            print(f"Synonym map '{SYNONYM_MAP_NAME}' not found")
            return None


if __name__ == "__main__":
    print("=" * 60)
    print("Azure AI Search - Synonym Map Setup")
    print("=" * 60)
    
    # List existing maps
    list_synonym_maps()
    
    # Create/update the synonym map
    print()
    success = create_synonym_map()
    
    if success:
        # Show details
        get_synonym_map_details()
        
        print("\n" + "=" * 60)
        print("NEXT STEPS:")
        print("=" * 60)
        print("1. Run 'python scripts/setup_search.py' to recreate the index")
        print("   with synonym map linked to name/description fields")
        print("2. Reindex products with 'python scripts/reseed_with_images.py'")
        print("3. Test searches like 'fridge', 'tap', 'bbq'")
