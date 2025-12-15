"""
Product Seeder Script
======================

Seeds 350+ home improvement products into Cosmos DB.
Run this after infrastructure is deployed.
"""

import asyncio
import os
import sys
import random
import uuid
from datetime import datetime
from motor.motor_asyncio import AsyncIOMotorClient

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
        "subcategories": ["outlets", "switches", "lighting", "wiring", "circuit_breakers", "smart_home"],
        "brands": ["Lutron", "Leviton", "GE", "Eaton", "Philips Hue", "Ring", "Legrand"],
        "base_price_range": (4, 299)
    },
    "kitchen_bath": {
        "subcategories": ["countertops", "cabinets", "vanities", "backsplash", "fixtures", "accessories"],
        "brands": ["KraftMaid", "Hampton Bay", "Glacier Bay", "Home Decorators", "Silestone", "Corian"],
        "base_price_range": (49, 1499)
    },
    "outdoor_garden": {
        "subcategories": ["grills", "patio_furniture", "lawn_mowers", "plants", "outdoor_lighting", "fencing"],
        "brands": ["Weber", "Char-Broil", "Toro", "Honda", "Traeger", "Hampton Bay", "Kichler"],
        "base_price_range": (24, 999)
    },
    "storage": {
        "subcategories": ["shelving", "garage_storage", "closet_systems", "bins", "workbenches", "tool_chests"],
        "brands": ["Rubbermaid", "Gladiator", "Husky", "ClosetMaid", "HDX", "Sterilite"],
        "base_price_range": (15, 599)
    },
    "hardware": {
        "subcategories": ["fasteners", "hinges", "locks", "door_hardware", "hooks", "anchors"],
        "brands": ["Schlage", "Kwikset", "Liberty", "Everbilt", "National Hardware", "Hillman"],
        "base_price_range": (3, 199)
    },
    "appliances": {
        "subcategories": ["refrigerators", "washers", "dryers", "dishwashers", "ranges", "microwaves"],
        "brands": ["Samsung", "LG", "Whirlpool", "GE", "Frigidaire", "Maytag", "KitchenAid"],
        "base_price_range": (199, 2499)
    }
}

# Product templates for each category
PRODUCT_TEMPLATES = {
    "power_tools": {
        "drills": [
            {"name": "{brand} 20V MAX Cordless Drill/Driver", "description": "Powerful 20V MAX battery system delivers 300 unit watts out (UWO) of power ability. High-speed transmission delivers 2 speeds (0-450 & 1,500 RPM) for a range of fastening and drilling applications."},
            {"name": "{brand} Hammer Drill Kit 1/2 inch", "description": "Features a high-power motor for heavy-duty drilling in concrete and masonry. Variable speed trigger with reverse for controlled drilling and fastening."},
            {"name": "{brand} Brushless Compact Drill", "description": "Compact and lightweight design fits into tight areas. Brushless motor provides more runtime and longer motor life."},
            {"name": "{brand} Right Angle Drill", "description": "Ideal for drilling in tight spaces. Compact head height for easy access to confined areas between studs and joists."},
        ],
        "saws": [
            {"name": "{brand} 7-1/4 in. Circular Saw", "description": "Powerful 15 Amp motor delivers 5,200 RPM for aggressive cutting. 51-degree bevel capacity with positive stops at 22.5 and 45 degrees."},
            {"name": "{brand} 12 in. Sliding Compound Miter Saw", "description": "Dual horizontal rails with innovative clamping system allows saw to be placed flat against wall. 15 Amp motor delivers 3,800 RPM for extended power and durability."},
            {"name": "{brand} Reciprocating Saw", "description": "Variable speed trigger provides blade control and matches speed to application. Keyless blade clamp allows for quick blade changes."},
            {"name": "{brand} 10 in. Table Saw with Stand", "description": "15 Amp motor delivers 4,000 RPM for powerful, smooth performance. Rack and pinion fence system with front and rear fence lock for accuracy and easy adjustments."},
            {"name": "{brand} Jigsaw with Case", "description": "6.5 Amp motor for heavy-duty cutting. Variable speed from 0-3,000 SPM for cutting a variety of materials."},
        ],
        "sanders": [
            {"name": "{brand} 5 in. Random Orbit Sander", "description": "3.0 Amp motor for smooth, swirl-free finishes. Variable speed dial (8,000-12,000 OPM) for maximum control."},
            {"name": "{brand} Belt Sander 3x21 inch", "description": "8 Amp motor delivers powerful material removal. Dual dust pickup for cleaner work environment."},
            {"name": "{brand} Sheet Sander 1/4 inch", "description": "2.4 Amp motor for smooth finishing. Palm grip design for comfort and control."},
        ],
        "routers": [
            {"name": "{brand} 2-1/4 HP Fixed Base Router", "description": "2-1/4 HP motor for routing in hardwoods. Precision machined sub-base with concentricity of 0.002 in."},
            {"name": "{brand} Compact Palm Router", "description": "1.25 HP motor for light to medium-duty routing applications. Variable speed from 16,000 to 27,000 RPM."},
        ],
        "grinders": [
            {"name": "{brand} 4-1/2 in. Angle Grinder", "description": "7.5 Amp motor outputs 11,000 RPM. Spindle lock for quick and easy wheel changes."},
            {"name": "{brand} 6 in. Bench Grinder", "description": "2.1 Amp motor delivers powerful performance. Cast iron base reduces vibration for accurate sharpening."},
        ],
        "impact_drivers": [
            {"name": "{brand} 20V MAX Impact Driver", "description": "Delivers 1,500 in-lbs of max torque. Variable speed trigger (0-2,800 RPM) provides increased control."},
            {"name": "{brand} Brushless Impact Driver Kit", "description": "Brushless motor provides up to 57% more runtime. 3 LED lights with 20-second trigger release delay."},
        ]
    },
    "hand_tools": {
        "hammers": [
            {"name": "{brand} 16 oz. Fiberglass Claw Hammer", "description": "Fiberglass handle absorbs shock and reduces vibration. Curved claw for pulling nails. Slip-resistant grip."},
            {"name": "{brand} 20 oz. Steel Framing Hammer", "description": "Forged steel head with magnetic nail starter. Straight claw for prying and ripping. Milled face for better grip on nail heads."},
            {"name": "{brand} Dead Blow Hammer 3 lb", "description": "Shot-filled head prevents rebound. Non-marring surface won't damage work pieces. Ideal for automotive and woodworking."},
        ],
        "screwdrivers": [
            {"name": "{brand} 42-Piece Screwdriver Set", "description": "Includes Phillips, slotted, Torx, and square bits. Comfortable tri-lobe handle provides torque and control. Chrome vanadium steel shafts."},
            {"name": "{brand} 6-in-1 Multi-Bit Screwdriver", "description": "Includes 2 Phillips, 2 slotted, and 2 nut driver sizes. Bits store in handle. Cushion grip for comfort."},
            {"name": "{brand} Ratcheting Screwdriver Set", "description": "10-piece set with ratcheting mechanism. 3-position switch for forward, reverse, and lock. Magnetic bit holder."},
        ],
        "wrenches": [
            {"name": "{brand} 22-Piece Combination Wrench Set", "description": "SAE and metric sizes included. Chrome vanadium steel for durability. Roll-up storage pouch included."},
            {"name": "{brand} Adjustable Wrench 10 inch", "description": "Extra-wide jaw capacity. Laser-etched markings for easy sizing. I-beam handle design for strength."},
            {"name": "{brand} 5-Piece Locking Pliers Set", "description": "Includes curved jaw, straight jaw, and needle nose. One-handed release lever. Wire cutter built into jaws."},
        ],
        "pliers": [
            {"name": "{brand} 6-Piece Pliers Set", "description": "Includes slip-joint, needle nose, diagonal cutting, and more. Rust-resistant finish. Comfortable grip handles."},
            {"name": "{brand} Tongue and Groove Pliers 12 inch", "description": "7 jaw positions for versatility. Laser heat-treated teeth grip in any position. High-carbon steel construction."},
        ],
        "measuring": [
            {"name": "{brand} 25 ft. Tape Measure", "description": "Nylon-coated blade for durability. Magnetic hook catches metal for solo measuring. 11 ft. standout for extended reach."},
            {"name": "{brand} Digital Laser Distance Measurer", "description": "Measures up to 100 ft. with accuracy. Calculates area, volume, and continuous measurement. Backlit display."},
        ],
        "levels": [
            {"name": "{brand} 48 in. Aluminum I-Beam Level", "description": "High-visibility vials with 0.0005 in. sensitivity. Shock absorbing end caps. CNC machined surfaces."},
            {"name": "{brand} Torpedo Level 9 inch", "description": "3 vials for plumb, level, and 45-degree readings. Magnetic strip for hands-free use. V-groove edge fits pipes."},
        ]
    },
    "building_materials": {
        "lumber": [
            {"name": "2 in. x 4 in. x 8 ft. Premium Stud", "description": "Grade stamped #2 or better. Kiln-dried for stability. Ideal for framing walls and structural applications."},
            {"name": "2 in. x 6 in. x 10 ft. Pressure-Treated Lumber", "description": "Ground contact rated. Protected against termites and fungal decay. For decks, fences, and outdoor projects."},
            {"name": "4 ft. x 8 ft. x 1/2 in. Plywood Sheathing", "description": "Exposure 1 rated for protected construction. Consistent thickness throughout. Easy to cut and install."},
        ],
        "drywall": [
            {"name": "4 ft. x 8 ft. x 1/2 in. Drywall Sheet", "description": "Standard gypsum panel for walls and ceilings. Fire-resistant. Easy to score and snap for installation."},
            {"name": "4 ft. x 8 ft. x 5/8 in. Fire-Code Drywall", "description": "Type X fire-rated panel. Required in garages and between attached living spaces. Resists fire for 1 hour."},
            {"name": "Drywall Joint Compound 4.5 Gal", "description": "All-purpose ready-mix formula. Easy to sand and feather. Excellent adhesion for taping and finishing."},
        ],
        "concrete": [
            {"name": "60 lb. Concrete Mix", "description": "Just add water high-strength mix. Reaches 4000 PSI in 28 days. For slabs, footings, and setting posts."},
            {"name": "50 lb. Quick-Setting Concrete", "description": "Sets in 20-40 minutes. No mixing required. Perfect for setting fence and mailbox posts."},
            {"name": "94 lb. Portland Cement", "description": "Type I/II general purpose cement. For concrete, mortar, and grout. ASTM C150 compliant."},
        ],
        "insulation": [
            {"name": "R-13 Kraft Faced Fiberglass Insulation", "description": "3-1/2 in. x 15 in. x 32 ft. roll. Fits standard 2x4 walls. Kraft vapor barrier facing."},
            {"name": "R-30 Unfaced Fiberglass Batts", "description": "9-1/2 in. x 16 in. x 48 in. For attic floors and ceilings. Meets building codes for thermal resistance."},
            {"name": "Foam Board Insulation 4x8 ft.", "description": "1 in. thick XPS foam board. R-5 per inch. Moisture resistant for basement and exterior applications."},
        ],
        "roofing": [
            {"name": "Architectural Shingles Bundle", "description": "Dimensional shingles for enhanced curb appeal. Class A fire rating. 30-year warranty."},
            {"name": "Roof Underlayment Roll", "description": "Synthetic roofing felt. Resists tearing during installation. Provides secondary moisture barrier."},
        ],
        "plywood": [
            {"name": "3/4 in. x 4 ft. x 8 ft. Birch Plywood", "description": "Cabinet-grade veneer core plywood. Smooth surface for finishing. Ideal for furniture and cabinetry."},
            {"name": "1/2 in. x 4 ft. x 8 ft. CDX Plywood", "description": "Exterior grade for roof and wall sheathing. APA rated. Exposure 1 glue rating."},
        ]
    },
    "paint": {
        "interior_paint": [
            {"name": "{brand} Premium Interior Paint - Eggshell", "description": "One-coat coverage in most colors. Low VOC formula. Washable and scrubbable. Dries in 1 hour."},
            {"name": "{brand} Interior Paint & Primer - Satin", "description": "Paint and primer in one. Excellent hide and coverage. Mildew resistant. Available in custom colors."},
            {"name": "{brand} Ultra Interior Paint - Flat", "description": "Zero VOC formula. Superior touch-up capability. Great for ceilings and low-traffic areas."},
        ],
        "exterior_paint": [
            {"name": "{brand} Exterior Paint - Semi-Gloss", "description": "Advanced dirt and mildew resistance. UV-resistant color retention. 25-year durability guarantee."},
            {"name": "{brand} Exterior Masonry Paint", "description": "Specifically formulated for concrete and stucco. Breathable to allow moisture vapor to escape. Resists peeling."},
        ],
        "primers": [
            {"name": "{brand} Premium Primer-Sealer", "description": "Seals new drywall and repairs. Blocks stains and odors. Quick-drying formula."},
            {"name": "{brand} Stain-Blocking Primer", "description": "Blocks severe stains including smoke, water, and ink. For interior and exterior use."},
        ],
        "stains": [
            {"name": "{brand} Semi-Transparent Deck Stain", "description": "Enhances wood grain while providing protection. UV resistant. Water-resistant formula."},
            {"name": "{brand} Solid Color Wood Stain", "description": "Complete coverage while allowing texture to show. Resists cracking and peeling. Long-lasting color."},
        ],
        "spray_paint": [
            {"name": "{brand} All-Surface Spray Paint", "description": "Indoor/outdoor use on multiple surfaces. Rust-preventive formula. Dries to touch in 20 minutes."},
            {"name": "{brand} Professional Spray Enamel", "description": "Durable finish for high-use items. Excellent hide with 2x coverage. Comfort spray tip."},
        ],
        "supplies": [
            {"name": "{brand} Premium Paint Roller Cover 3-Pack", "description": "3/8 in. nap for smooth to semi-smooth surfaces. Lint-free finish. Reusable design."},
            {"name": "{brand} 2 in. Angular Sash Brush", "description": "Polyester bristles for all paints. Angular cut for precise edging. Stainless steel ferrule."},
        ]
    },
    "flooring": {
        "hardwood": [
            {"name": "{brand} Oak Hardwood Flooring - Natural", "description": "3/4 in. x 3-1/4 in. solid oak planks. Prefinished with aluminum oxide coating. 25-year warranty."},
            {"name": "{brand} Hickory Engineered Hardwood", "description": "5 in. wide planks with natural variations. Click-lock installation. Scratch-resistant finish."},
        ],
        "laminate": [
            {"name": "{brand} Water-Resistant Laminate Flooring", "description": "AC4 commercial rated durability. Realistic wood grain embossing. Attached foam underlayment."},
            {"name": "{brand} Premium Laminate Plank 12mm", "description": "Extra-thick construction reduces sound. Drop-click installation. 30-year residential warranty."},
        ],
        "vinyl": [
            {"name": "{brand} Luxury Vinyl Plank Flooring", "description": "100% waterproof core. Realistic wood visuals. 22 mil wear layer for durability."},
            {"name": "{brand} Vinyl Tile Flooring Peel & Stick", "description": "Self-adhesive backing for easy installation. Resistant to moisture and stains. DIY friendly."},
        ],
        "tile": [
            {"name": "{brand} Porcelain Floor Tile 12x24", "description": "Wood-look porcelain for any room. Frost-resistant for indoor/outdoor. Easy to clean and maintain."},
            {"name": "{brand} Ceramic Subway Tile 3x6", "description": "Classic white subway tile. Glossy finish. Perfect for kitchen and bath backsplashes."},
            {"name": "{brand} Natural Stone Mosaic Tile", "description": "Real marble mosaic sheets. Mesh-backed for easy installation. Polished finish."},
        ],
        "carpet": [
            {"name": "{brand} Stainmaster Carpet - Plush", "description": "Advanced stain and soil resistance. Soft underfoot feel. Pet-friendly construction."},
            {"name": "{brand} Berber Carpet Tile", "description": "Loop pile construction. Easy DIY installation. Replaces individual tiles if damaged."},
        ],
        "underlayment": [
            {"name": "{brand} Premium Foam Underlayment 100 sq ft", "description": "3mm thick foam padding. Reduces sound transmission. Moisture barrier included."},
            {"name": "{brand} Cork Underlayment Roll", "description": "Natural sound absorption. Thermal insulation properties. Eco-friendly material."},
        ]
    },
    "plumbing": {
        "faucets": [
            {"name": "{brand} Pull-Down Kitchen Faucet", "description": "Single-handle operation. Pull-down sprayer with 3 modes. Spot-resist stainless steel finish."},
            {"name": "{brand} Widespread Bathroom Faucet", "description": "8 in. widespread installation. WaterSense certified. Matching drain included."},
            {"name": "{brand} Touchless Kitchen Faucet", "description": "Motion-activated sensor. Voice-activation compatible. Integrated dock for spray head."},
        ],
        "toilets": [
            {"name": "{brand} Two-Piece Elongated Toilet", "description": "1.28 GPF WaterSense certified. Elongated bowl for comfort. Includes soft-close seat."},
            {"name": "{brand} One-Piece Compact Toilet", "description": "Space-saving design for small bathrooms. Dual flush technology. Chair-height seating."},
            {"name": "{brand} Smart Bidet Toilet", "description": "Integrated bidet functionality. Heated seat with temperature control. Self-cleaning wand."},
        ],
        "sinks": [
            {"name": "{brand} Undermount Kitchen Sink 33x22", "description": "18-gauge stainless steel. Double bowl with low divider. Sound-dampening pads included."},
            {"name": "{brand} Farmhouse Apron Sink", "description": "Fireclay construction. Single bowl design. Reversible front apron."},
            {"name": "{brand} Pedestal Bathroom Sink", "description": "Classic white vitreous china. Space-saving pedestal base. Pre-drilled for 4 in. faucet."},
        ],
        "shower_heads": [
            {"name": "{brand} Rainfall Shower Head 10 inch", "description": "Rain-style coverage. Chrome finish. Easy-clean nozzles."},
            {"name": "{brand} Handheld Shower Head with Hose", "description": "5 spray settings. 72 in. stainless steel hose. Wall-mount holder included."},
        ],
        "water_heaters": [
            {"name": "{brand} 50-Gal Electric Water Heater", "description": "4500W heating elements. Energy Star certified. Self-cleaning system reduces sediment."},
            {"name": "{brand} Tankless Water Heater", "description": "On-demand hot water. 199,000 BTU gas unit. Up to 11 GPM flow rate."},
        ],
        "pipes": [
            {"name": "1/2 in. x 10 ft. PEX Tubing - Red", "description": "Flexible cross-linked polyethylene. For hot water lines. Corrosion and freeze resistant."},
            {"name": "3 in. PVC DWV Pipe 10 ft", "description": "Schedule 40 drain, waste, vent pipe. Solvent-weld joints. Meets ASTM standards."},
        ]
    },
    "electrical": {
        "outlets": [
            {"name": "{brand} 15A Tamper-Resistant Outlet", "description": "Built-in shutters protect children. Residential grade. White finish, includes wall plate."},
            {"name": "{brand} GFCI Outlet 20A", "description": "Ground fault protection for wet areas. Self-test indicator. LED status light."},
            {"name": "{brand} USB Outlet with Type A & C Ports", "description": "Charges devices without adapter. 4.8A total USB power. Includes 15A outlets."},
        ],
        "switches": [
            {"name": "{brand} Single-Pole Light Switch", "description": "15A residential grade switch. Quiet rocker operation. Includes wall plate."},
            {"name": "{brand} Dimmer Switch for LED", "description": "Compatible with LED and CFL bulbs. Preset light level memory. Slide dimmer with on/off."},
            {"name": "{brand} Smart Switch Wi-Fi", "description": "Voice control with Alexa and Google. Schedule and remote control via app. No hub required."},
        ],
        "lighting": [
            {"name": "{brand} LED Flush Mount Ceiling Light 14 in.", "description": "24W LED equals 150W incandescent. 3000K warm white light. Dimmable design."},
            {"name": "{brand} Recessed LED Downlight 6 in.", "description": "Integrated LED retrofit kit. 5 selectable color temperatures. IC rated for insulation contact."},
            {"name": "{brand} Under Cabinet LED Light Bar", "description": "Linkable design for continuous lighting. 3000K color temperature. Hardwired installation."},
            {"name": "{brand} Outdoor Wall Lantern", "description": "Traditional style with clear glass. Weather-resistant construction. Dusk-to-dawn sensor."},
        ],
        "wiring": [
            {"name": "14/2 Romex Wire 250 ft", "description": "NM-B non-metallic sheathed cable. For 15A circuits. UL listed for safety."},
            {"name": "12/2 Romex Wire with Ground 100 ft", "description": "For 20A circuits and heavier loads. Solid copper conductors. PVC jacket."},
        ],
        "circuit_breakers": [
            {"name": "{brand} 20A Single-Pole Breaker", "description": "Plug-on design for easy installation. Trip indicator. UL listed."},
            {"name": "{brand} 30A Double-Pole Breaker", "description": "For 240V circuits and appliances. Compatible with main panel. Thermal-magnetic trip."},
        ],
        "smart_home": [
            {"name": "{brand} Smart Thermostat", "description": "Energy Star certified. Learning schedule capability. Voice and app control."},
            {"name": "{brand} Video Doorbell", "description": "1080p HD video with night vision. Two-way audio. Motion detection alerts."},
            {"name": "{brand} Smart Plug 2-Pack", "description": "Remote on/off control. Voice assistant compatible. Energy monitoring."},
        ]
    },
    "kitchen_bath": {
        "countertops": [
            {"name": "{brand} Quartz Countertop - White", "description": "Non-porous surface resists stains. Heat and scratch resistant. Custom cut to order."},
            {"name": "{brand} Butcher Block Countertop 4 ft", "description": "Solid birch wood construction. Food-safe finish. Sand and refinish as needed."},
            {"name": "{brand} Laminate Countertop - Granite Look", "description": "Realistic stone appearance. Easy to clean surface. Includes backsplash."},
        ],
        "cabinets": [
            {"name": "{brand} Base Cabinet 36 in.", "description": "Shaker-style door. Soft-close hinges and drawers. Ready to assemble."},
            {"name": "{brand} Wall Cabinet 30x30 in.", "description": "Adjustable shelves. Full overlay doors. Includes hardware."},
            {"name": "{brand} Pantry Cabinet 24x84 in.", "description": "Full-height storage. Pull-out shelves. Multiple shelf positions."},
        ],
        "vanities": [
            {"name": "{brand} 36 in. Bathroom Vanity with Sink", "description": "Includes cultured marble top. Soft-close doors and drawer. Pre-drilled for 4 in. faucet."},
            {"name": "{brand} 60 in. Double Sink Vanity", "description": "Two sinks with quartz top. Solid wood construction. Ample storage below."},
        ],
        "backsplash": [
            {"name": "{brand} Peel and Stick Tile Backsplash", "description": "Easy DIY installation. Water and heat resistant. Removable for renters."},
            {"name": "{brand} Glass Mosaic Backsplash Tile", "description": "Mixed glass and stone. Mesh-backed sheets. Contemporary design."},
        ],
        "fixtures": [
            {"name": "{brand} Towel Bar 24 in.", "description": "Chrome finish. Concealed mounting hardware. Solid brass construction."},
            {"name": "{brand} Medicine Cabinet with Mirror", "description": "Recessed or surface mount. Adjustable glass shelves. Beveled mirror."},
        ],
        "accessories": [
            {"name": "{brand} Toilet Paper Holder", "description": "Spring-loaded roller. Chrome finish. Easy installation."},
            {"name": "{brand} Shower Caddy Corner", "description": "Tension pole design. Rust-resistant coating. Adjustable shelves."},
        ]
    },
    "outdoor_garden": {
        "grills": [
            {"name": "{brand} 3-Burner Gas Grill", "description": "30,000 BTU total output. Porcelain-coated grates. Side burner included."},
            {"name": "{brand} Charcoal Kettle Grill 22 in.", "description": "One-touch cleaning system. Built-in thermometer. Rust-resistant coating."},
            {"name": "{brand} Pellet Grill and Smoker", "description": "Set-it-and-forget-it cooking. WiFi enabled temperature control. 700 sq in. cooking area."},
        ],
        "patio_furniture": [
            {"name": "{brand} 7-Piece Patio Dining Set", "description": "Includes table and 6 chairs. All-weather wicker. Cushions included."},
            {"name": "{brand} Outdoor Lounge Chair Set", "description": "Zero-gravity reclining. Padded headrest. Foldable for storage."},
            {"name": "{brand} Patio Umbrella 9 ft.", "description": "Push-button tilt mechanism. Fade-resistant fabric. Includes base."},
        ],
        "lawn_mowers": [
            {"name": "{brand} Self-Propelled Gas Mower 21 in.", "description": "163cc engine. Variable speed rear-wheel drive. 3-in-1 mulch, bag, or discharge."},
            {"name": "{brand} Electric Cordless Lawn Mower", "description": "56V battery power. 21 in. cutting deck. 45 minute runtime."},
            {"name": "{brand} Robotic Lawn Mower", "description": "Automatic mowing schedule. Boundary wire installation. Rain sensor."},
        ],
        "plants": [
            {"name": "Knockout Rose Bush - Red", "description": "Disease-resistant variety. Blooms spring through frost. Full sun to part shade."},
            {"name": "Emerald Green Arborvitae", "description": "Evergreen privacy tree. Grows 12-14 ft tall. Low maintenance."},
            {"name": "Hydrangea Shrub - Blue", "description": "Large mophead blooms. Blooms on old wood. Partial shade preferred."},
        ],
        "outdoor_lighting": [
            {"name": "{brand} Solar Path Lights 6-Pack", "description": "Auto on at dusk. Up to 8 hours runtime. Easy stake installation."},
            {"name": "{brand} LED Landscape Spotlight", "description": "Low voltage 12V system. 400 lumens output. Adjustable angle."},
        ],
        "fencing": [
            {"name": "6 ft. x 8 ft. Cedar Fence Panel", "description": "Dog-ear style. Natural cedar construction. Ready to stain or seal."},
            {"name": "4 ft. x 6 ft. Vinyl Fence Panel", "description": "White privacy fence. Never needs painting. 25-year warranty."},
        ]
    },
    "storage": {
        "shelving": [
            {"name": "{brand} 5-Shelf Steel Shelving Unit", "description": "Holds up to 350 lbs per shelf. No tools assembly. Adjustable shelf heights."},
            {"name": "{brand} Wire Shelving Unit Chrome", "description": "4-tier design. 500 lbs total capacity. NSF certified for food storage."},
        ],
        "garage_storage": [
            {"name": "{brand} Garage Cabinet System", "description": "Wall-mounted steel cabinets. Lockable doors. Includes rail system."},
            {"name": "{brand} Overhead Ceiling Storage Rack", "description": "4 ft. x 8 ft. platform. Holds up to 600 lbs. Adjustable height."},
        ],
        "closet_systems": [
            {"name": "{brand} Closet Organizer Kit 5-8 ft.", "description": "Adjustable shelves and rods. Wire construction. Easy installation."},
            {"name": "{brand} Custom Closet Tower", "description": "Laminate wood finish. Drawers and shelves. 84 in. tall."},
        ],
        "bins": [
            {"name": "{brand} Storage Tote 27 Gal 4-Pack", "description": "Snap-lock lid. Stackable design. See-through for easy ID."},
            {"name": "{brand} Rolling Storage Cart", "description": "3-drawer design. Casters for mobility. Clear drawers."},
        ],
        "workbenches": [
            {"name": "{brand} Workbench 6 ft. Solid Wood", "description": "Laminated hardwood top. 1,500 lbs capacity. Includes pegboard."},
            {"name": "{brand} Mobile Workbench with Drawers", "description": "Locking casters. 4 drawers plus cabinet. Power strip included."},
        ],
        "tool_chests": [
            {"name": "{brand} 5-Drawer Rolling Tool Cabinet", "description": "Ball-bearing drawer slides. Keyed lock. 1,000 lb capacity."},
            {"name": "{brand} Portable Tool Box 19 in.", "description": "Metal latches. Lift-out tray. Impact-resistant plastic."},
        ]
    },
    "hardware": {
        "fasteners": [
            {"name": "{brand} Drywall Screws 1 lb Box", "description": "Coarse thread for wood studs. Phillips bugle head. Black phosphate coating."},
            {"name": "{brand} Deck Screws 5 lb Box", "description": "Star drive for better grip. Exterior rated coating. Self-drilling point."},
            {"name": "{brand} Nail Assortment Kit", "description": "2,000+ nails in various sizes. Includes brads, finish, and common nails. Organizer case."},
        ],
        "hinges": [
            {"name": "{brand} Door Hinge 3-Pack Satin Nickel", "description": "3.5 in. x 3.5 in. interior hinge. Square corners. Includes screws."},
            {"name": "{brand} Self-Closing Cabinet Hinge", "description": "Concealed European style. 110-degree opening. Soft-close feature."},
        ],
        "locks": [
            {"name": "{brand} Entry Door Handleset", "description": "Keyed entry with deadbolt. Smart key security. Satin nickel finish."},
            {"name": "{brand} Smart Lock Deadbolt", "description": "Keyless entry with code. Auto-lock feature. Works with smart home."},
            {"name": "{brand} Padlock 4-Pack", "description": "Keyed alike for convenience. Hardened steel shackle. Weather resistant."},
        ],
        "door_hardware": [
            {"name": "{brand} Privacy Door Knob", "description": "Push-button lock for bathrooms. Satin nickel finish. Easy installation."},
            {"name": "{brand} Barn Door Hardware Kit", "description": "72 in. track for doors up to 36 in. Soft-close mechanism. Modern J-style hangers."},
            {"name": "{brand} Door Stop Spring 5-Pack", "description": "Heavy-duty spring steel. White rubber tip. Protects walls."},
        ],
        "hooks": [
            {"name": "{brand} Heavy-Duty Wall Hooks 10-Pack", "description": "Holds up to 25 lbs each. Black finish. Easy mount hardware."},
            {"name": "{brand} Magnetic Tool Holder 24 in.", "description": "Strong magnetic strip. Holds tools securely. Easy wall mount."},
        ],
        "anchors": [
            {"name": "{brand} Drywall Anchor Kit 200-Piece", "description": "Includes plastic, toggle, and self-drilling anchors. Various sizes. With screws."},
            {"name": "{brand} Heavy-Duty Toggle Bolt", "description": "Holds up to 100 lbs in drywall. 1/4 in. bolt. Spring-loaded wings."},
        ]
    },
    "appliances": {
        "refrigerators": [
            {"name": "{brand} French Door Refrigerator 27 cu. ft.", "description": "Counter-depth design. Internal water and ice dispenser. SmartHQ connected."},
            {"name": "{brand} Side-by-Side Refrigerator 25 cu. ft.", "description": "External ice and water dispenser. Adjustable shelving. LED interior lighting."},
            {"name": "{brand} Top Freezer Refrigerator 18 cu. ft.", "description": "Space-saving design. Reversible door. Humidity-controlled crispers."},
        ],
        "washers": [
            {"name": "{brand} Front Load Washer 4.5 cu. ft.", "description": "Steam cleaning option. Energy Star certified. Vibration reduction technology."},
            {"name": "{brand} Top Load Washer with Agitator", "description": "Deep fill option. Multiple water temperature settings. Porcelain tub."},
        ],
        "dryers": [
            {"name": "{brand} Electric Dryer 7.4 cu. ft.", "description": "Sensor dry technology. Steam refresh cycle. Reversible door."},
            {"name": "{brand} Gas Dryer Large Capacity", "description": "13 dry cycles. Wrinkle prevent option. Interior light."},
        ],
        "dishwashers": [
            {"name": "{brand} Built-In Dishwasher Stainless", "description": "45 dBA quiet operation. 3rd rack for utensils. Pocket handle design."},
            {"name": "{brand} Portable Dishwasher 18 in.", "description": "No permanent installation. 8 place settings. Connects to faucet."},
        ],
        "ranges": [
            {"name": "{brand} Gas Range 30 in.", "description": "5 sealed burners. Convection oven. Self-cleaning cycle."},
            {"name": "{brand} Electric Slide-In Range", "description": "Smooth ceramic glass top. Double oven capacity. True convection."},
        ],
        "microwaves": [
            {"name": "{brand} Over-the-Range Microwave", "description": "1.9 cu. ft. capacity. 400 CFM ventilation. Sensor cooking."},
            {"name": "{brand} Countertop Microwave 1.1 cu. ft.", "description": "1000W power. Turntable design. Quick start feature."},
        ]
    }
}

# Real product images from Unsplash (publicly accessible)
# Using Unsplash Source which provides direct image URLs
IMAGE_URLS = {
    "power_tools": [
        "https://images.unsplash.com/photo-1504148455328-c376907d081c?w=400&h=400&fit=crop&q=80",
        "https://images.unsplash.com/photo-1572981779307-38b8cabb2407?w=400&h=400&fit=crop&q=80",
        "https://images.unsplash.com/photo-1530124566582-a618bc2615dc?w=400&h=400&fit=crop&q=80",
        "https://images.unsplash.com/photo-1586864387789-628af9feed72?w=400&h=400&fit=crop&q=80",
    ],
    "hand_tools": [
        "https://images.unsplash.com/photo-1426927308491-6380b6a9936f?w=400&h=400&fit=crop&q=80",
        "https://images.unsplash.com/photo-1581092921461-eab62e97a780?w=400&h=400&fit=crop&q=80",
        "https://images.unsplash.com/photo-1504917595217-d4dc5ebb6122?w=400&h=400&fit=crop&q=80",
    ],
    "building_materials": [
        "https://images.unsplash.com/photo-1541123603104-512919d6a96c?w=400&h=400&fit=crop&q=80",
        "https://images.unsplash.com/photo-1558618666-fcd25c85cd64?w=400&h=400&fit=crop&q=80",
        "https://images.unsplash.com/photo-1503387762-592deb58ef4e?w=400&h=400&fit=crop&q=80",
    ],
    "paint": [
        "https://images.unsplash.com/photo-1562259949-e8e7689d7828?w=400&h=400&fit=crop&q=80",
        "https://images.unsplash.com/photo-1525909002-1b05e0c869d8?w=400&h=400&fit=crop&q=80",
        "https://images.unsplash.com/photo-1589939705384-5185137a7f0f?w=400&h=400&fit=crop&q=80",
    ],
    "flooring": [
        "https://images.unsplash.com/photo-1558618666-fcd25c85cd64?w=400&h=400&fit=crop&q=80",
        "https://images.unsplash.com/photo-1600585152220-90363fe7e115?w=400&h=400&fit=crop&q=80",
        "https://images.unsplash.com/photo-1541123603104-512919d6a96c?w=400&h=400&fit=crop&q=80",
    ],
    "plumbing": [
        "https://images.unsplash.com/photo-1585704032915-c3400ca199e7?w=400&h=400&fit=crop&q=80",
        "https://images.unsplash.com/photo-1552321554-5fefe8c9ef14?w=400&h=400&fit=crop&q=80",
    ],
    "electrical": [
        "https://images.unsplash.com/photo-1524484485831-a92ffc0de03f?w=400&h=400&fit=crop&q=80",
        "https://images.unsplash.com/photo-1507473885765-e6ed057f782c?w=400&h=400&fit=crop&q=80",
        "https://images.unsplash.com/photo-1558002038-1055907df827?w=400&h=400&fit=crop&q=80",
    ],
    "kitchen_bath": [
        "https://images.unsplash.com/photo-1556909114-f6e7ad7d3136?w=400&h=400&fit=crop&q=80",
        "https://images.unsplash.com/photo-1600585152220-90363fe7e115?w=400&h=400&fit=crop&q=80",
        "https://images.unsplash.com/photo-1552321554-5fefe8c9ef14?w=400&h=400&fit=crop&q=80",
    ],
    "outdoor_garden": [
        "https://images.unsplash.com/photo-1529692236671-f1f6cf9683ba?w=400&h=400&fit=crop&q=80",
        "https://images.unsplash.com/photo-1600210492486-724fe5c67fb0?w=400&h=400&fit=crop&q=80",
        "https://images.unsplash.com/photo-1416879595882-3373a0480b5b?w=400&h=400&fit=crop&q=80",
    ],
    "storage": [
        "https://images.unsplash.com/photo-1558618666-fcd25c85cd64?w=400&h=400&fit=crop&q=80",
        "https://images.unsplash.com/photo-1530124566582-a618bc2615dc?w=400&h=400&fit=crop&q=80",
    ],
    "hardware": [
        "https://images.unsplash.com/photo-1572981779307-38b8cabb2407?w=400&h=400&fit=crop&q=80",
        "https://images.unsplash.com/photo-1558618666-fcd25c85cd64?w=400&h=400&fit=crop&q=80",
    ],
    "appliances": [
        "https://images.unsplash.com/photo-1571175443880-49e1d25b2bc5?w=400&h=400&fit=crop&q=80",
        "https://images.unsplash.com/photo-1556909114-f6e7ad7d3136?w=400&h=400&fit=crop&q=80",
        "https://images.unsplash.com/photo-1626806787461-102c1bfaaea1?w=400&h=400&fit=crop&q=80",
    ],
}


def generate_product_image_url(category: str, subcategory: str, index: int) -> str:
    """Get a real product image URL from Azure Blob Storage."""
    # Get images for this category
    category_images = IMAGE_URLS.get(category, IMAGE_URLS["power_tools"])
    # Rotate through available images based on index
    image_index = index % len(category_images)
    return category_images[image_index]


def generate_sku(category: str, index: int) -> str:
    """Generate a SKU for a product."""
    cat_prefix = category[:3].upper()
    return f"{cat_prefix}-{index:06d}"


def generate_products() -> list:
    """Generate all products - ensures at least MIN_PRODUCTS_TARGET products."""
    products = []
    product_index = 1
    
    for category, cat_data in CATEGORIES.items():
        templates = PRODUCT_TEMPLATES.get(category, {})
        
        for subcategory in cat_data["subcategories"]:
            subcat_templates = templates.get(subcategory, [])
            
            # If no templates, create generic products
            if not subcat_templates:
                subcat_templates = [
                    {"name": "{brand} " + subcategory.replace("_", " ").title(), 
                     "description": f"High-quality {subcategory.replace('_', ' ')} for your home improvement needs."},
                    {"name": "{brand} " + subcategory.replace("_", " ").title() + " Pro", 
                     "description": f"Professional-grade {subcategory.replace('_', ' ')} for demanding applications."},
                ]
            
            # Generate products for each brand and template combination
            for brand in cat_data["brands"]:
                for template in subcat_templates:
                    # Base price with some variation
                    min_price, max_price = cat_data["base_price_range"]
                    base_price = random.uniform(min_price, max_price)
                    
                    # Some products are on sale
                    on_sale = random.random() < 0.25
                    sale_price = round(base_price * 0.8, 2) if on_sale else None
                    
                    # Stock quantity (most in stock, some low, some out)
                    stock_roll = random.random()
                    if stock_roll < 0.05:  # 5% out of stock
                        stock_quantity = 0
                    elif stock_roll < 0.15:  # 10% low stock
                        stock_quantity = random.randint(1, 5)
                    else:  # 85% normal stock
                        stock_quantity = random.randint(10, 200)
                    
                    product = {
                        "id": str(uuid.uuid4()),
                        "name": template["name"].format(brand=brand),
                        "description": template["description"],
                        "category": category,
                        "subcategory": subcategory,
                        "brand": brand,
                        "sku": generate_sku(category, product_index),
                        "price": round(base_price, 2),
                        "sale_price": sale_price,
                        "rating": round(random.uniform(3.5, 5.0), 1),
                        "review_count": random.randint(5, 500),
                        "in_stock": stock_quantity > 0,
                        "stock_quantity": stock_quantity,
                        "image_url": generate_product_image_url(category, subcategory, product_index),
                        "featured": random.random() < 0.1,  # 10% featured
                        "specifications": {},
                        "created_at": datetime.utcnow(),
                        "updated_at": datetime.utcnow()
                    }
                    
                    products.append(product)
                    product_index += 1
    
    # If we haven't hit our target, add more variation products
    while len(products) < MIN_PRODUCTS_TARGET:
        # Pick a random category and create additional products
        category = random.choice(list(CATEGORIES.keys()))
        cat_data = CATEGORIES[category]
        subcategory = random.choice(cat_data["subcategories"])
        brand = random.choice(cat_data["brands"])
        
        min_price, max_price = cat_data["base_price_range"]
        base_price = random.uniform(min_price, max_price)
        
        # Stock quantity
        stock_quantity = random.randint(5, 150)
        
        # Create variation products (different sizes, colors, etc.)
        variations = ["XL", "Compact", "Heavy-Duty", "Premium", "Value", "Pro Series", "Contractor Grade"]
        variation = random.choice(variations)
        
        product = {
            "id": str(uuid.uuid4()),
            "name": f"{brand} {variation} {subcategory.replace('_', ' ').title()}",
            "description": f"{variation} version of our popular {subcategory.replace('_', ' ')} line. Built for performance and durability.",
            "category": category,
            "subcategory": subcategory,
            "brand": brand,
            "sku": generate_sku(category, product_index),
            "price": round(base_price, 2),
            "sale_price": None,
            "rating": round(random.uniform(3.8, 5.0), 1),
            "review_count": random.randint(10, 300),
            "in_stock": True,
            "stock_quantity": stock_quantity,
            "image_url": generate_product_image_url(category, subcategory, product_index),
            "featured": False,
            "specifications": {},
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        
        products.append(product)
        product_index += 1
    
    return products


async def seed_database():
    """Main seeding function."""
    print("🌱 Starting product seeding...")
    print(f"   Target: {MIN_PRODUCTS_TARGET}+ products")
    
    # Get connection string from environment
    connection_string = os.getenv("AZURE_COSMOS_CONNECTION_STRING")
    if not connection_string:
        print("❌ AZURE_COSMOS_CONNECTION_STRING not set")
        print("Please set the environment variable and try again.")
        sys.exit(1)
    
    database_name = os.getenv("AZURE_COSMOS_DATABASE", "ketzagenticecomm")
    
    # Connect to Cosmos DB
    print(f"📦 Connecting to database: {database_name}")
    client = AsyncIOMotorClient(connection_string)
    db = client[database_name]
    products_collection = db["products"]
    
    # Generate products
    print("🏭 Generating products...")
    products = generate_products()
    print(f"✅ Generated {len(products)} products (target was {MIN_PRODUCTS_TARGET}+)")
    
    # Clear existing products
    print("🗑️ Clearing existing products...")
    await products_collection.delete_many({})
    
    # Insert products in batches
    batch_size = 100
    print(f"📤 Inserting products in batches of {batch_size}...")
    
    for i in range(0, len(products), batch_size):
        batch = products[i:i + batch_size]
        await products_collection.insert_many(batch)
        print(f"   Inserted {min(i + batch_size, len(products))}/{len(products)} products")
    
    # Create indexes
    print("📇 Creating indexes...")
    await products_collection.create_index("category")
    await products_collection.create_index("subcategory")
    await products_collection.create_index("brand")
    await products_collection.create_index("sku", unique=True)
    await products_collection.create_index("stock_quantity")
    await products_collection.create_index([("name", "text"), ("description", "text")])
    
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


if __name__ == "__main__":
    asyncio.run(seed_database())
