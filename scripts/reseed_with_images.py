"""
Reseed Products Script
======================
Clears all products and reseeds with the exact 99 products 
that have matching images in blob storage.
"""

import asyncio
import httpx
import uuid
import random
from urllib.parse import quote

# Backend URL
BACKEND_URL = "https://backend-vnet.happyisland-58d32b38.eastus2.azurecontainerapps.io"
CONTAINER_NAME = "product-images"

# Exact product list matching blob storage images
# Format: (name, blob_filename, category, subcategory, brand, description, base_price)
PRODUCTS = [
    # Power Tools - Drills
    ("DeWalt 20V MAX Cordless Drill/Driver Kit", "DeWalt 20V MAX Cordless Drill Driver Kit.jpg", "power_tools", "drills", "DeWalt", 
     "Powerful 20V MAX battery system delivers 300 unit watts out of power. High-speed transmission delivers 2 speeds (0-450 & 1,500 RPM) for a range of fastening and drilling applications.", 149.00),
    ("Milwaukee 20V MAX Cordless Drill/Driver Kit", "Milwaukee 20V MAX Cordless Drill Driver Kit.jpg", "power_tools", "drills", "Milwaukee",
     "Powerful 20V MAX battery system with compact design. High-speed transmission delivers 2 speeds for a range of fastening and drilling applications.", 179.00),
    ("Makita 20V MAX Cordless Drill/Driver Kit", "Makita 20V MAX Cordless Drill Driver Kit.jpg", "power_tools", "drills", "Makita",
     "Compact and lightweight design fits into tight areas. Variable speed motor delivers 0-400 & 0-1,500 RPM for a range of drilling and driving applications.", 159.00),
    ("Bosch 20V MAX Cordless Drill/Driver Kit", "Bosch 20V MAX Cordless Drill Driver Kit.jpg", "power_tools", "drills", "Bosch",
     "High-performance motor delivers 350 in-lbs of torque. Two-speed gearbox provides flexibility for a range of applications.", 169.00),
    
    # Power Tools - Hammer Drills
    ("DeWalt 18V Brushless Hammer Drill", "DeWalt 18V Brushless Hammer Drill.jpg", "power_tools", "drills", "DeWalt",
     "Brushless motor delivers up to 57% more runtime. High power motor delivers 820 unit watts out of power for heavy-duty drilling applications.", 199.00),
    ("Milwaukee 18V Brushless Hammer Drill", "Milwaukee 18V Brushless Hammer Drill.jpg", "power_tools", "drills", "Milwaukee",
     "Powerstate brushless motor delivers unmatched power in its class. Redlink Plus intelligence provides optimized performance and overload protection.", 229.00),
    ("Makita 18V Brushless Hammer Drill", "Makita 18V Brushless Hammer Drill.jpg", "power_tools", "drills", "Makita",
     "Efficient BL brushless motor delivers 1,090 in-lbs of max torque. Variable 2-speed design for a wide range of drilling and driving applications.", 189.00),
    ("Bosch 18V Brushless Hammer Drill", "Bosch 18V Brushless Hammer Drill.jpg", "power_tools", "drills", "Bosch",
     "EC Brushless motor delivers more runtime per charge. KickBack Control reduces the risk of sudden tool reactions in binding conditions.", 209.00),
    
    # Power Tools - Circular Saws
    ("DeWalt 7-1/4 in. Circular Saw", "DeWalt 7-14 in. Circular Saw.jpg", "power_tools", "saws", "DeWalt",
     "Powerful 15 Amp motor delivers 5,200 RPM for aggressive cutting. 51-degree bevel capacity with positive stops at 22.5 and 45 degrees.", 139.00),
    ("Milwaukee 7-1/4 in. Circular Saw", "Milwaukee 7-1 4 in. Circular Saw.jpg", "power_tools", "saws", "Milwaukee",
     "Powerful 15 Amp motor delivers 5,000 RPM for aggressive cutting. Aircraft aluminum shoe provides a lightweight and durable base.", 149.00),
    ("Makita 7-1/4 in. Circular Saw", "Makita 7-1 4 in. Circular Saw.jpg", "power_tools", "saws", "Makita",
     "Powerful 15 Amp motor delivers 5,800 RPM for faster cuts. Built-in LED light illuminates the line of cut for increased accuracy.", 129.00),
    ("Ryobi 7-1/4 in. Circular Saw", "Ryobi 7-1 4 in. Circular Saw.jpg", "power_tools", "saws", "Ryobi",
     "13 Amp motor provides the power to cut through tough applications. Adjustable depth of cut lever makes depth changes quick and easy.", 79.00),
    
    # Power Tools - Miter Saws
    ("DeWalt 12 in. Sliding Miter Saw", "DeWalt 12 in. Sliding Miter Saw.jpg", "power_tools", "saws", "DeWalt",
     "Dual horizontal rails with innovative clamping system allows saw to be placed flat against wall. 15 Amp motor delivers 3,800 RPM for extended power and durability.", 449.00),
    ("Milwaukee 12 in. Sliding Miter Saw", "Milwaukee 12 in. Sliding Miter Saw.jpg", "power_tools", "saws", "Milwaukee",
     "15 Amp motor with constant power technology maintains speed under load. Shadow Cut Line provides a crisp shadow on the material for increased accuracy.", 499.00),
    ("Makita 12 in. Sliding Miter Saw", "Makita 12 in. Sliding Miter Saw.jpg", "power_tools", "saws", "Makita",
     "Direct drive gearbox eliminates maintenance and provides high efficiency power transfer. Linear ball bearing system provides smooth, accurate cuts.", 429.00),
    ("Ryobi 12 in. Sliding Miter Saw", "Ryobi 12 in. Sliding Miter Saw.jpg", "power_tools", "saws", "Ryobi",
     "Sliding head design allows for cuts up to 13-3/4 in. wide. LED cut line indicator for accurate cuts.", 249.00),
    
    # Power Tools - Sanders
    ("DeWalt 5 in. Random Orbit Sander", "DeWalt 5 in. Random Orbit Sander.jpg", "power_tools", "sanders", "DeWalt",
     "3.0 Amp motor for smooth, swirl-free finishes. Variable speed dial (8,000-12,000 OPM) for maximum control on all applications.", 79.00),
    ("Bosch 5 in. Random Orbit Sander", "Bosch 5 in. Random Orbit Sander.jpg", "power_tools", "sanders", "Bosch",
     "2.5 Amp motor delivers 7,500 to 12,000 OPM. Microfilter dust canister captures debris down to 0.5 microns.", 69.00),
    ("Makita 5 in. Random Orbit Sander", "Makita 5 in. Random Orbit Sander.jpg", "power_tools", "sanders", "Makita",
     "3.0 Amp motor with variable speed (4,000-12,000 OPM). Palm grip design with rubberized body for comfort and control.", 89.00),
    
    # Hand Tools - Hammers
    ("Estwing 16 oz. Fiberglass Claw Hammer", "Estwing 16 oz. Fiberglass Claw Hammer.jpg", "hand_tools", "hammers", "Estwing",
     "Fiberglass handle absorbs shock and reduces vibration. Curved claw for pulling nails. Slip-resistant grip for comfort.", 29.99),
    ("Stanley 16 oz. Fiberglass Claw Hammer", "Stanley 16 oz. Fiberglass Claw Hammer.jpg", "hand_tools", "hammers", "Stanley",
     "Fiberglass handle absorbs shock 3x better than wood. Curve claw provides max leverage. Rim temper striking face for durability.", 24.99),
    ("Craftsman 16 oz. Fiberglass Claw Hammer", "Craftsman 16 oz. Fiberglass Claw Hammer.jpg", "hand_tools", "hammers", "Craftsman",
     "Fiberglass core for improved strength. Cushion grip for comfort. Rim temper for durability and safety.", 22.99),
    ("Estwing 20 oz. Framing Hammer", "Estwing 20 oz. Framing Hammer.jpg", "hand_tools", "hammers", "Estwing",
     "Solid steel construction for durability. Milled face for positive nail grip. Shock-reducing grip for comfort.", 49.99),
    ("Stanley 20 oz. Framing Hammer", "Stanley 20 oz. Framing Hammer.jpg", "hand_tools", "hammers", "Stanley",
     "AntiVibe technology reduces shock and vibration. Milled striking face for positive grip on nail heads. Straight rip claw.", 44.99),
    ("Craftsman 20 oz. Framing Hammer", "Craftsman 20 oz. Framing Hammer.jpg", "hand_tools", "hammers", "Craftsman",
     "Fiberglass handle with cushion grip. Milled face for secure nail positioning. Straight claw for prying.", 39.99),
    
    # Hand Tools - Screwdrivers
    ("Klein Tools 11-Piece Screwdriver Set", "Klein Tools 11-Piece Screwdriver Set.jpg", "hand_tools", "screwdrivers", "Klein Tools",
     "Includes Phillips, slotted, and cabinet tip screwdrivers. Chrome vanadium steel shafts. Cushion-Grip handles for comfort and torque.", 59.99),
    ("Stanley 11-Piece Screwdriver Set", "Stanley 11-Piece Screwdriver Set.jpg", "hand_tools", "screwdrivers", "Stanley",
     "Chrome vanadium steel bar for strength and durability. Soft grip handles for comfort. Magnetic tips for fastener retention.", 34.99),
    ("Craftsman 11-Piece Screwdriver Set", "Craftsman 11-Piece Screwdriver Set.jpg", "hand_tools", "screwdrivers", "Craftsman",
     "Bi-material handles for comfort and grip. Chrome vanadium steel blades. Magnetic tips hold fasteners securely.", 29.99),
    
    # Hand Tools - Wrenches
    ("Channellock 12-Piece Combination Wrench Set", "Channellock 12-Piece Combination Wrench Set.jpg", "hand_tools", "wrenches", "Channellock",
     "Chrome vanadium steel construction. Open and box end design. Roll-up storage pouch included. Sizes 1/4\" to 1\".", 79.99),
    ("Craftsman 12-Piece Combination Wrench Set", "Craftsman 12-Piece Combination Wrench Set.jpg", "hand_tools", "wrenches", "Craftsman",
     "Forged alloy steel construction. Open and box end design. Chrome finish resists corrosion. Sizes 8mm to 19mm.", 49.99),
    ("Husky 12-Piece Combination Wrench Set", "Husky 12-Piece Combination Wrench Set.jpg", "hand_tools", "wrenches", "Husky",
     "Heat treated alloy steel. Full polish chrome finish. 12-point box end for greater access. Lifetime warranty.", 39.99),
    
    # Paint
    ("Behr Premium Plus Interior Eggshell Paint - 1 Gal", "Behr Premium Plus Interior Eggshell Paint - 1 Gal.jpg", "paint", "interior_paint", "Behr",
     "Premium quality interior paint with primer. Low odor formula with easy clean-up. Covers up to 400 sq. ft. per gallon.", 38.98),
    ("Sherwin-Williams Premium Plus Interior Eggshell Paint - 1 Gal", "Sherwin-Williams Premium Plus Interior Eggshell Paint - 1 Gal.jpg", "paint", "interior_paint", "Sherwin-Williams",
     "Exceptional hiding and coverage. Scrubbable and washable finish. Zero VOC for improved indoor air quality.", 54.99),
    ("Benjamin Moore Premium Plus Interior Eggshell Paint - 1 Gal", "Benjamin Moore Premium Plus Interior Eggshell Paint - 1 Gal.jpg", "paint", "interior_paint", "Benjamin Moore",
     "Regal Select quality with excellent hide. Easy application and touch-up. Durable, washable finish.", 69.99),
    ("Behr Ultra Interior Flat White Ceiling Paint", "Behr Ultra Interior Flat White Ceiling Paint.jpg", "paint", "interior_paint", "Behr",
     "Ultra flat finish hides imperfections. Spatter resistant formula. Self-priming one-coat coverage.", 32.98),
    ("Sherwin-Williams Ultra Interior Flat White Ceiling Paint", "Sherwin-Williams Ultra Interior Flat White Ceiling Paint.jpg", "paint", "interior_paint", "Sherwin-Williams",
     "Ultra flat finish for ceilings. Excellent hide and coverage. Low splatter formula.", 44.99),
    ("Benjamin Moore Ultra Interior Flat White Ceiling Paint", "Benjamin Moore Ultra Interior Flat White Ceiling Paint.jpg", "paint", "interior_paint", "Benjamin Moore",
     "Ceiling paint specifically designed for overhead application. Ultra flat finish. Excellent coverage.", 54.99),
    ("Behr All-Weather Exterior Satin Paint - 1 Gal", "Behr All-Weather Exterior Satin Paint - 1 Gal.jpg", "paint", "exterior_paint", "Behr",
     "Advanced durability for extreme weather protection. Mildew and algae resistant. Rain resistant in 60 minutes.", 44.98),
    ("Sherwin-Williams All-Weather Exterior Satin Paint - 1 Gal", "Sherwin-Williams All-Weather Exterior Satin Paint - 1 Gal.jpg", "paint", "exterior_paint", "Sherwin-Williams",
     "Superior durability against weather extremes. Excellent color retention. Self-priming formula.", 64.99),
    ("PPG All-Weather Exterior Satin Paint - 1 Gal", "PPG All-Weather Exterior Satin Paint - 1 Gal.jpg", "paint", "exterior_paint", "PPG",
     "Advanced acrylic formula for lasting protection. UV resistant for color retention. Excellent adhesion.", 49.99),
    
    # Plumbing - Kitchen Faucets
    ("Moen Single-Handle Pull-Down Kitchen Faucet", "Moen Single-Handle Pull-Down Kitchen Faucet.jpg", "plumbing", "faucets", "Moen",
     "Power Clean spray technology provides 50% more spray power. Reflex system for smooth operation and secure docking. Spot Resist stainless finish.", 199.00),
    ("Delta Single-Handle Pull-Down Kitchen Faucet", "Delta Single-Handle Pull-Down Kitchen Faucet.jpg", "plumbing", "faucets", "Delta",
     "Touch2O Technology allows you to turn the faucet on and off with just a touch. ShieldSpray Technology. SpotShield Technology resists fingerprints.", 249.00),
    ("Kohler Single-Handle Pull-Down Kitchen Faucet", "Kohler Single-Handle Pull-Down Kitchen Faucet.jpg", "plumbing", "faucets", "Kohler",
     "Three-function sprayhead with sweep spray, boost, and stream. Magnetic docking. Temperature memory feature.", 279.00),
    ("Pfister Single-Handle Pull-Down Kitchen Faucet", "Pfister Single-Handle Pull-Down Kitchen Faucet.jpg", "plumbing", "faucets", "Pfister",
     "Xtract system with 2-in-1 faucet has built-in water filtration. React touch-free technology. Stainless steel finish.", 169.00),
    
    # Plumbing - Bathroom Faucets
    ("Moen Widespread Bathroom Faucet", "Moen Widespread Bathroom Faucet.jpg", "plumbing", "faucets", "Moen",
     "Spot Resist brushed nickel finish resists fingerprints. WaterSense certified to save water without sacrificing performance. Easy-install system.", 179.00),
    ("Delta Widespread Bathroom Faucet", "Delta Widespread Bathroom Faucet.jpg", "plumbing", "faucets", "Delta",
     "Diamond Seal Technology ensures leak-free operation. WaterSense labeled. Metal drain assembly included.", 199.00),
    ("Kohler Widespread Bathroom Faucet", "Kohler Widespread Bathroom Faucet.jpg", "plumbing", "faucets", "Kohler",
     "Elegant widespread design with ceramic disc valving. WaterSense certified. Metal pop-up drain included.", 229.00),
    ("Pfister Widespread Bathroom Faucet", "Pfister Widespread Bathroom Faucet.jpg", "plumbing", "faucets", "Pfister",
     "Pforever Seal advanced ceramic disc valve technology. WaterSense certified. Metal pop-up drain included.", 149.00),
    
    # Plumbing - Toilets
    ("Kohler Comfort Height Elongated Toilet", "Kohler Comfort Height Elongated Toilet.jpg", "plumbing", "toilets", "Kohler",
     "Comfort Height seating for ease of sitting and standing. Powerful AquaPiston canister flush technology. 1.28 GPF WaterSense certified.", 279.00),
    ("American Standard Comfort Height Elongated Toilet", "American Standard Comfort Height Elongated Toilet.jpg", "plumbing", "toilets", "American Standard",
     "Right Height elongated bowl for maximum comfort. PowerWash rim scrubs the bowl with each flush. 1.28 GPF WaterSense certified.", 249.00),
    ("TOTO Comfort Height Elongated Toilet", "TOTO Comfort Height Elongated Toilet.jpg", "plumbing", "toilets", "TOTO",
     "Universal Height with elongated bowl. Tornado Flush system for powerful, quiet flush. CeFiONtect ceramic glaze.", 349.00),
    
    # Flooring - Hardwood
    ("Bruce Oak Solid Hardwood Flooring - Sq Ft", "Bruce Oak Solid Hardwood Flooring - Sq Ft.jpg", "flooring", "hardwood", "Bruce",
     "3/4 in. thick x 5 in. wide solid oak hardwood. Aluminum oxide finish for durability. Easy nail-down installation.", 4.99),
    ("Mohawk Oak Solid Hardwood Flooring - Sq Ft", "Mohawk Oak Solid Hardwood Flooring - Sq Ft.jpg", "flooring", "hardwood", "Mohawk",
     "3/4 in. thick x 3-1/4 in. wide solid oak. Prefinished with aluminum oxide coating. 25-year residential warranty.", 5.49),
    ("Shaw Oak Solid Hardwood Flooring - Sq Ft", "Shaw Oak Solid Hardwood Flooring - Sq Ft.jpg", "flooring", "hardwood", "Shaw",
     "3/4 in. thick x 5 in. wide red oak hardwood. ScufResist Platinum finish. Lifetime structural warranty.", 5.99),
    ("Bruce Maple Engineered Hardwood - Sq Ft", "Bruce Maple Engineered Hardwood - Sq Ft.jpg", "flooring", "hardwood", "Bruce",
     "3/8 in. thick x 5 in. wide engineered maple. Click-lock installation system. Below, on, or above grade installation.", 4.49),
    ("Mohawk Maple Engineered Hardwood - Sq Ft", "Mohawk Maple Engineered Hardwood - Sq Ft.jpg", "flooring", "hardwood", "Mohawk",
     "1/2 in. thick x 5 in. wide engineered maple. Uniclic locking system. 25-year residential warranty.", 4.99),
    ("Shaw Maple Engineered Hardwood - Sq Ft", "Shaw Maple Engineered Hardwood - Sq Ft.jpg", "flooring", "hardwood", "Shaw",
     "5/16 in. thick x 5 in. wide engineered maple. Epic Plus technology for performance. Multi-level installation.", 5.49),
    
    # Flooring - Laminate
    ("Pergo Water-Resistant Laminate Flooring - Sq Ft", "Pergo Water-Resistant Laminate Flooring - Sq Ft.jpg", "flooring", "laminate", "Pergo",
     "PergoExtreme water resistant technology. SpillProtect Plus surface. Realistic wood look with attached underlayment.", 3.49),
    ("Lifeproof Water-Resistant Laminate Flooring - Sq Ft", "Lifeproof Water-Resistant Laminate Flooring - Sq Ft.jpg", "flooring", "laminate", "Lifeproof",
     "100% waterproof core. Drop Lock installation system. Built-in underlayment for easy installation.", 2.99),
    ("TrafficMaster Water-Resistant Laminate Flooring - Sq Ft", "TrafficMaster Water-Resistant Laminate Flooring - Sq Ft.jpg", "flooring", "laminate", "TrafficMaster",
     "Water-resistant for up to 24 hours. Easy click-lock installation. Realistic wood grain texture.", 1.99),
    
    # Flooring - Vinyl
    ("Lifeproof Luxury Vinyl Plank Flooring - Sq Ft", "Lifeproof Luxury Vinyl Plank Flooring - Sq Ft.jpg", "flooring", "vinyl", "Lifeproof",
     "100% waterproof rigid core construction. Drop Lock installation. Scratch and stain resistant.", 3.49),
    ("TrafficMaster Luxury Vinyl Plank Flooring - Sq Ft", "TrafficMaster Luxury Vinyl Plank Flooring - Sq Ft.jpg", "flooring", "vinyl", "TrafficMaster",
     "Allure-style click together vinyl planks. 100% waterproof. Easy DIY installation.", 2.49),
    ("Shaw Luxury Vinyl Plank Flooring - Sq Ft", "Shaw Luxury Vinyl Plank Flooring - Sq Ft.jpg", "flooring", "vinyl", "Shaw",
     "Floorte waterproof core technology. LifeGuard spill-proof warranty. Commercial-grade durability.", 3.99),
    
    # Electrical - Outlets
    ("Leviton 15 Amp GFCI Outlet with LED", "Leviton 15 Amp GFCI Outlet with LED.jpg", "electrical", "outlets", "Leviton",
     "Self-testing GFCI outlet automatically tests every 3 seconds. LED status indicator. Slim design fits standard wallplates.", 19.97),
    ("Lutron 15 Amp GFCI Outlet with LED", "Lutron 15 Amp GFCI Outlet with LED.jpg", "electrical", "outlets", "Lutron",
     "Advanced protection against electrical shock. LED indicator shows protection status. Easy-to-use test and reset buttons.", 24.97),
    ("GE 15 Amp GFCI Outlet with LED", "GE 15 Amp GFCI Outlet with LED.jpg", "electrical", "outlets", "GE",
     "Advanced self-test technology. LED indicator. Meets latest NEC requirements. Heavy-duty construction.", 17.97),
    ("Leviton USB Wall Outlet Dual Port", "Leviton USB Wall Outlet Dual Port.jpg", "electrical", "outlets", "Leviton",
     "Dual USB ports provide 3.6A total charging capacity. Tamper-resistant receptacles. Standard outlet included.", 24.97),
    ("Lutron USB Wall Outlet Dual Port", "Lutron USB Wall Outlet Dual Port.jpg", "electrical", "outlets", "Lutron",
     "USB Type-A and Type-C ports. Fast charging capability. Standard duplex outlet included.", 29.97),
    ("GE USB Wall Outlet Dual Port", "GE USB Wall Outlet Dual Port.jpg", "electrical", "outlets", "GE",
     "Dual USB ports with 4.0A total output. Tamper-resistant. UL listed for safety.", 22.97),
    
    # Electrical - Lighting
    ("Philips LED Recessed Downlight 6 inch", "Philips LED Recessed Downlight 6 inch.jpg", "electrical", "lighting", "Philips",
     "65W equivalent using only 10W. Dimmable LED technology. Easy retrofit installation. 3000K warm white light.", 14.97),
    ("GE LED Recessed Downlight 6 inch", "GE LED Recessed Downlight 6 inch.jpg", "electrical", "lighting", "GE",
     "65W equivalent LED. Daylight 5000K for bright, energizing light. 35,000-hour rated life. Dimmable.", 12.97),
    ("Kichler LED Recessed Downlight 6 inch", "Kichler LED Recessed Downlight 6 inch.jpg", "electrical", "lighting", "Kichler",
     "Premium LED with high CRI for true color rendering. Smooth dimming capability. IC-rated for insulated ceilings.", 24.97),
    ("Philips Modern Pendant Light", "Philips Modern Pendant Light.jpg", "electrical", "lighting", "Philips",
     "Modern geometric design with brushed nickel finish. Compatible with LED bulbs. 60-inch adjustable cord.", 89.00),
    ("GE Modern Pendant Light", "GE Modern Pendant Light.jpg", "electrical", "lighting", "GE",
     "Contemporary dome design in matte black. E26 base accepts LED bulbs. Adjustable height cord.", 69.00),
    ("Kichler Modern Pendant Light", "Kichler Modern Pendant Light.jpg", "electrical", "lighting", "Kichler",
     "Designer pendant with clear seeded glass shade. Olde Bronze finish. Adjustable hanging height.", 129.00),
    
    # Outdoor - Grills
    ("Weber 3-Burner Gas Grill", "Weber 3-Burner Gas Grill.jpg", "outdoor_garden", "grills", "Weber",
     "3 burners deliver 30,000 BTU-per-hour. GS4 grilling system for reliability. Porcelain-enameled lid and body.", 549.00),
    ("Traeger 3-Burner Gas Grill", "Traeger 3-Burner Gas Grill.jpg", "outdoor_garden", "grills", "Traeger",
     "Wood pellet grill with WiFIRE technology. 575 sq. in. cooking capacity. Digital controller for precise temperature.", 699.00),
    ("Char-Broil 3-Burner Gas Grill", "Char-Broil 3-Burner Gas Grill.jpg", "outdoor_garden", "grills", "Char-Broil",
     "3 burners with 30,000 BTU. Tru-Infrared cooking system. Stainless steel lid and firebox.", 379.00),
    ("Weber Pellet Smoker Grill", "Weber Pellet Smoker Grill.jpg", "outdoor_garden", "grills", "Weber",
     "SmokeFire EX4 with WEBER CONNECT smart grilling technology. 672 sq. in. cooking area. Flavorizer bars for smoke infusion.", 899.00),
    ("Traeger Pellet Smoker Grill", "Traeger Pellet Smoker Grill.jpg", "outdoor_garden", "grills", "Traeger",
     "Pro Series with D2 Direct Drive. 575 sq. in. grilling space. WiFIRE technology for app control.", 799.00),
    ("Char-Broil Pellet Smoker Grill", "Char-Broil Pellet Smoker Grill.jpg", "outdoor_garden", "grills", "Char-Broil",
     "Auto Auger feeds pellets automatically. Digital controller. 540 sq. in. primary cooking area.", 499.00),
    
    # Outdoor - Patio Furniture
    ("Hampton Bay 5-Piece Patio Dining Set", "Hampton Bay 5-Piece Patio Dining Set.jpg", "outdoor_garden", "patio_furniture", "Hampton Bay",
     "Includes 4 sling chairs and round table with umbrella hole. Powder-coated steel frame. Weather-resistant construction.", 349.00),
    ("Home Decorators 5-Piece Patio Dining Set", "Home Decorators 5-Piece Patio Dining Set.jpg", "outdoor_garden", "patio_furniture", "Home Decorators",
     "Premium wicker design with cushions included. Rust-resistant aluminum frame. UV-resistant fabric.", 599.00),
    
    # Appliances - Refrigerators
    ("Samsung French Door Refrigerator 28 cu ft", "Samsung French Door Refrigerator 28 cu ft.jpg", "appliances", "refrigerators", "Samsung",
     "28 cu. ft. capacity with Family Hub. Wi-Fi enabled with touch screen. FlexZone drawer with 4 temperature settings.", 2499.00),
    ("LG French Door Refrigerator 28 cu ft", "LG French Door Refrigerator 28 cu ft.jpg", "appliances", "refrigerators", "LG",
     "28 cu. ft. Smart wi-fi Enabled InstaView. Door-in-Door design. Dual ice maker with craft ice.", 2299.00),
    ("Whirlpool French Door Refrigerator 28 cu ft", "Whirlpool French Door Refrigerator 28 cu ft.jpg", "appliances", "refrigerators", "Whirlpool",
     "27 cu. ft. capacity with LED lighting. Temperature-controlled pantry drawer. Fingerprint-resistant stainless steel.", 1899.00),
    ("GE French Door Refrigerator 28 cu ft", "GE French Door Refrigerator 28 cu ft.jpg", "appliances", "refrigerators", "GE",
     "27.8 cu. ft. capacity with hands-free autofill. Internal water dispenser. TwinChill evaporators for freshness.", 1999.00),
    
    # Appliances - Washers
    ("Samsung Front Load Washer 4.5 cu ft", "Samsung Front Load Washer 4.5 cu ft.jpg", "appliances", "washers", "Samsung",
     "4.5 cu. ft. capacity with Wi-Fi connectivity. Steam cleaning option. Self Clean+ technology.", 899.00),
    ("LG Front Load Washer 4.5 cu ft", "LG Front Load Washer 4.5 cu ft.jpg", "appliances", "washers", "LG",
     "4.5 cu. ft. ultra large capacity. TurboWash360 technology. Built-in intelligence with AI fabric detection.", 849.00),
    ("Whirlpool Front Load Washer 4.5 cu ft", "Whirlpool Front Load Washer 4.5 cu ft.jpg", "appliances", "washers", "Whirlpool",
     "4.5 cu. ft. capacity with Load & Go dispenser. Intuitive touch controls. Steam clean option.", 799.00),
    ("Maytag Front Load Washer 4.5 cu ft", "Maytag Front Load Washer 4.5 cu ft.jpg", "appliances", "washers", "Maytag",
     "4.5 cu. ft. capacity with Extra Power button. Fresh Hold option keeps clothes fresh. 12-hour Fresh Spin.", 849.00),
    
    # Building Materials
    ("2 in. x 4 in. x 8 ft. Premium Kiln-Dried Stud", "2 in. x 4 in. x 8 ft. Premium Kiln-Dried Stud.jpg", "building_materials", "lumber", "Generic",
     "Premium Grade SPF stud. Kiln-dried for stability and strength. Ideal for framing walls and structural applications.", 7.97),
    ("2 in. x 6 in. x 10 ft. Pressure-Treated Lumber", "2 in. x 6 in. x 10 ft. Pressure-Treated Lumber.jpg", "building_materials", "lumber", "Generic",
     "Ground contact rated pressure-treated lumber. Protected against termites and fungal decay. Ideal for decks and outdoor structures.", 12.97),
    ("1/2 in. x 4 ft. x 8 ft. Drywall Panel", "1 2 in. x 4 ft. x 8 ft. Drywall Panel.jpg", "building_materials", "drywall", "Generic",
     "Standard 1/2 in. thick gypsum board. Fire-resistant core. For walls and ceilings in interior applications.", 14.48),
    
    # Hardware - Door Hardware
    ("Schlage Entry Door Handleset", "Schlage Entry Door Handleset.jpg", "hardware", "door_hardware", "Schlage",
     "Camelot style handleset with Accent lever. Built-in deadbolt.DERA 40 residential security rating.", 179.00),
    ("Kwikset Entry Door Handleset", "Kwikset Entry Door Handleset.jpg", "hardware", "door_hardware", "Kwikset",
     "Arlington handleset with Tustin lever. SmartKey Security re-key technology. Grade 2 certified.", 149.00),
    ("Baldwin Entry Door Handleset", "Baldwin Entry Door Handleset.jpg", "hardware", "door_hardware", "Baldwin",
     "Reserve Collection estate style. Lifetime warranty on finish. Solid brass construction.", 399.00),
    ("Schlage Smart Lock with Keypad", "Schlage Smart Lock with Keypad.jpg", "hardware", "smart_home", "Schlage",
     "Encode Plus smart WiFi deadbolt with Apple Home Key. No hub required. Built-in alarm technology.", 299.00),
    ("Kwikset Smart Lock with Keypad", "Kwikset Smart Lock with Keypad.jpg", "hardware", "smart_home", "Kwikset",
     "Halo WiFi smart lock with touchscreen. Remote access via app. SmartKey Security for easy rekeying.", 229.00),
    ("Baldwin Smart Lock with Keypad", "Baldwin Smart Lock with Keypad.jpg", "hardware", "smart_home", "Baldwin",
     "Evolved smart lock with WiFi connectivity. Bluetooth enabled. Premium forged brass construction.", 349.00),
]


def generate_sku(brand: str, category: str, index: int) -> str:
    """Generate a unique SKU."""
    prefix = brand[:3].upper()
    cat_code = category[:3].upper()
    return f"{prefix}-{cat_code}-{index:04d}"


def build_image_url(filename: str) -> str:
    """Build proxy URL for image."""
    encoded = quote(filename)
    return f"{BACKEND_URL}/api/v1/img/{CONTAINER_NAME}/{encoded}"


def generate_product(index: int, product_data: tuple) -> dict:
    """Generate a product dictionary."""
    name, blob_filename, category, subcategory, brand, description, base_price = product_data
    
    # Generate price variations
    price = round(base_price * (1 + random.uniform(-0.05, 0.05)), 2)
    sale_price = round(price * 0.9, 2) if random.random() < 0.3 else None
    
    # Generate review_score (0-5 scale, most products have good reviews)
    # Weight towards higher scores (3.5-5.0 for most)
    review_score = round(random.uniform(3.0, 5.0), 1)
    
    # Generate return_count - most products have 0 returns
    # About 15% of products have some returns (1-10)
    # About 5% of products have high returns (10-50) - these are the "problem" products
    return_rand = random.random()
    if return_rand < 0.80:  # 80% have 0 returns
        return_count = 0
    elif return_rand < 0.95:  # 15% have low returns (1-10)
        return_count = random.randint(1, 10)
    else:  # 5% have high returns (15-50)
        return_count = random.randint(15, 50)
    
    return {
        "id": str(uuid.uuid4()),
        "name": name,
        "description": description,
        "category": category,
        "subcategory": subcategory,
        "brand": brand,
        "sku": generate_sku(brand, category, index),
        "price": price,
        "sale_price": sale_price,
        "image_url": build_image_url(blob_filename),
        "rating": round(random.uniform(3.5, 5.0), 1),
        "review_count": random.randint(10, 500),
        "review_score": review_score,
        "return_count": return_count,
        "in_stock": random.random() > 0.1,
        "stock_quantity": random.randint(5, 100) if random.random() > 0.1 else 0,
        "featured": random.random() < 0.2
    }


async def clear_all_products():
    """Clear all products from the database."""
    print("Clearing all products from database...")
    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.delete(f"{BACKEND_URL}/api/v1/products/all")
        if response.status_code == 200:
            result = response.json()
            print(f"✓ Deleted {result.get('message', 'all products')}")
            return True
        else:
            print(f"✗ Failed to delete: {response.status_code} - {response.text}")
            return False


async def create_products():
    """Create all products via API."""
    print(f"\nCreating {len(PRODUCTS)} products...")
    
    products = [generate_product(i, p) for i, p in enumerate(PRODUCTS)]
    
    async with httpx.AsyncClient(timeout=120.0) as client:
        # Try bulk insert first
        response = await client.post(
            f"{BACKEND_URL}/api/v1/products/bulk",
            json={"products": products}
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"✓ {result.get('message', 'Products created')}")
            return True
        else:
            print(f"Bulk insert failed: {response.status_code}, trying individual inserts...")
            
            # Fall back to individual inserts
            success_count = 0
            for product in products:
                try:
                    response = await client.post(
                        f"{BACKEND_URL}/api/v1/products/",
                        json=product
                    )
                    if response.status_code == 200:
                        success_count += 1
                        print(f"  ✓ Created: {product['name']}")
                    else:
                        print(f"  ✗ Failed: {product['name']} - {response.status_code}")
                except Exception as e:
                    print(f"  ✗ Error: {product['name']} - {e}")
            
            print(f"\n✓ Created {success_count}/{len(products)} products")
            return success_count > 0


async def trigger_reindex():
    """Trigger search index reindexing."""
    print("\nTriggering search index reindex...")
    async with httpx.AsyncClient(timeout=300.0) as client:
        response = await client.post(f"{BACKEND_URL}/api/v1/products/reindex")
        if response.status_code == 200:
            result = response.json()
            print(f"✓ Reindex complete: {result}")
            return True
        else:
            print(f"✗ Reindex failed: {response.status_code} - {response.text}")
            return False


async def verify_products():
    """Verify products were created correctly."""
    print("\nVerifying products...")
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.get(f"{BACKEND_URL}/api/v1/products/?limit=5")
        if response.status_code == 200:
            data = response.json()
            products = data.get("products", [])
            print(f"✓ Found {len(products)} products in sample")
            for p in products[:3]:
                print(f"  - {p['name']}")
                print(f"    Image: {p.get('image_url', 'N/A')[:80]}...")
            return True
        else:
            print(f"✗ Verification failed: {response.status_code}")
            return False


async def main():
    """Main execution."""
    print("=" * 60)
    print("Product Database Reseed Script")
    print("=" * 60)
    
    # Step 1: Clear all products
    if not await clear_all_products():
        print("\nFailed to clear products. Exiting.")
        return
    
    # Step 2: Create new products with correct images
    if not await create_products():
        print("\nFailed to create products. Exiting.")
        return
    
    # Step 3: Reindex search
    await trigger_reindex()
    
    # Step 4: Verify
    await verify_products()
    
    print("\n" + "=" * 60)
    print("Done! Products have been reseeded with correct images.")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
