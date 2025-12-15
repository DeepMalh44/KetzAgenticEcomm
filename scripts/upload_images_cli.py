"""
Upload Product Images using Azure CLI
======================================

Downloads images and uploads using az storage blob upload (OAuth auth).
"""

import asyncio
import aiohttp
import os
import subprocess
import tempfile

# Configuration
STORAGE_ACCOUNT = "stketzagentickh7xm2"
CONTAINER = "product-images"

# Curated images for each category
CATEGORY_IMAGES = {
    "power_tools": [
        ("https://images.unsplash.com/photo-1504148455328-c376907d081c?w=400&h=400&fit=crop", "power_tools_1.jpg"),
        ("https://images.unsplash.com/photo-1572981779307-38b8cabb2407?w=400&h=400&fit=crop", "power_tools_2.jpg"),
        ("https://images.unsplash.com/photo-1530124566582-a618bc2615dc?w=400&h=400&fit=crop", "power_tools_3.jpg"),
        ("https://images.unsplash.com/photo-1586864387789-628af9feed72?w=400&h=400&fit=crop", "power_tools_4.jpg"),
    ],
    "hand_tools": [
        ("https://images.unsplash.com/photo-1426927308491-6380b6a9936f?w=400&h=400&fit=crop", "hand_tools_1.jpg"),
        ("https://images.unsplash.com/photo-1581092921461-eab62e97a780?w=400&h=400&fit=crop", "hand_tools_2.jpg"),
        ("https://images.unsplash.com/photo-1504917595217-d4dc5ebb6122?w=400&h=400&fit=crop", "hand_tools_3.jpg"),
    ],
    "building_materials": [
        ("https://images.unsplash.com/photo-1541123603104-512919d6a96c?w=400&h=400&fit=crop", "building_materials_1.jpg"),
        ("https://images.unsplash.com/photo-1558618666-fcd25c85cd64?w=400&h=400&fit=crop", "building_materials_2.jpg"),
        ("https://images.unsplash.com/photo-1503387762-592deb58ef4e?w=400&h=400&fit=crop", "building_materials_3.jpg"),
    ],
    "paint": [
        ("https://images.unsplash.com/photo-1562259949-e8e7689d7828?w=400&h=400&fit=crop", "paint_1.jpg"),
        ("https://images.unsplash.com/photo-1525909002-1b05e0c869d8?w=400&h=400&fit=crop", "paint_2.jpg"),
        ("https://images.unsplash.com/photo-1589939705384-5185137a7f0f?w=400&h=400&fit=crop", "paint_3.jpg"),
    ],
    "flooring": [
        ("https://images.unsplash.com/photo-1558618666-fcd25c85cd64?w=400&h=400&fit=crop", "flooring_1.jpg"),
        ("https://images.unsplash.com/photo-1600585152220-90363fe7e115?w=400&h=400&fit=crop", "flooring_2.jpg"),
        ("https://images.unsplash.com/photo-1541123603104-512919d6a96c?w=400&h=400&fit=crop", "flooring_3.jpg"),
    ],
    "plumbing": [
        ("https://images.unsplash.com/photo-1585704032915-c3400ca199e7?w=400&h=400&fit=crop", "plumbing_1.jpg"),
        ("https://images.unsplash.com/photo-1552321554-5fefe8c9ef14?w=400&h=400&fit=crop", "plumbing_2.jpg"),
    ],
    "electrical": [
        ("https://images.unsplash.com/photo-1524484485831-a92ffc0de03f?w=400&h=400&fit=crop", "electrical_1.jpg"),
        ("https://images.unsplash.com/photo-1507473885765-e6ed057f782c?w=400&h=400&fit=crop", "electrical_2.jpg"),
        ("https://images.unsplash.com/photo-1558002038-1055907df827?w=400&h=400&fit=crop", "electrical_3.jpg"),
    ],
    "kitchen_bath": [
        ("https://images.unsplash.com/photo-1556909114-f6e7ad7d3136?w=400&h=400&fit=crop", "kitchen_bath_1.jpg"),
        ("https://images.unsplash.com/photo-1600585152220-90363fe7e115?w=400&h=400&fit=crop", "kitchen_bath_2.jpg"),
        ("https://images.unsplash.com/photo-1552321554-5fefe8c9ef14?w=400&h=400&fit=crop", "kitchen_bath_3.jpg"),
    ],
    "outdoor_garden": [
        ("https://images.unsplash.com/photo-1529692236671-f1f6cf9683ba?w=400&h=400&fit=crop", "outdoor_garden_1.jpg"),
        ("https://images.unsplash.com/photo-1600210492486-724fe5c67fb0?w=400&h=400&fit=crop", "outdoor_garden_2.jpg"),
        ("https://images.unsplash.com/photo-1416879595882-3373a0480b5b?w=400&h=400&fit=crop", "outdoor_garden_3.jpg"),
    ],
    "storage": [
        ("https://images.unsplash.com/photo-1558618666-fcd25c85cd64?w=400&h=400&fit=crop", "storage_1.jpg"),
        ("https://images.unsplash.com/photo-1530124566582-a618bc2615dc?w=400&h=400&fit=crop", "storage_2.jpg"),
    ],
    "hardware": [
        ("https://images.unsplash.com/photo-1572981779307-38b8cabb2407?w=400&h=400&fit=crop", "hardware_1.jpg"),
        ("https://images.unsplash.com/photo-1558618666-fcd25c85cd64?w=400&h=400&fit=crop", "hardware_2.jpg"),
    ],
    "appliances": [
        ("https://images.unsplash.com/photo-1571175443880-49e1d25b2bc5?w=400&h=400&fit=crop", "appliances_1.jpg"),
        ("https://images.unsplash.com/photo-1556909114-f6e7ad7d3136?w=400&h=400&fit=crop", "appliances_2.jpg"),
        ("https://images.unsplash.com/photo-1626806787461-102c1bfaaea1?w=400&h=400&fit=crop", "appliances_3.jpg"),
    ],
}


async def download_image(session: aiohttp.ClientSession, url: str) -> bytes | None:
    """Download an image from URL."""
    try:
        async with session.get(url, timeout=30) as response:
            if response.status == 200:
                return await response.read()
            return None
    except Exception as e:
        print(f"  ❌ Download error: {e}")
        return None


def upload_blob(local_file: str, blob_name: str) -> bool:
    """Upload file to blob storage using az CLI with OAuth."""
    cmd = f'az storage blob upload --account-name {STORAGE_ACCOUNT} --container-name {CONTAINER} --name "{blob_name}" --file "{local_file}" --auth-mode login --overwrite --content-type "image/jpeg"'
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    return result.returncode == 0


async def main():
    print("=" * 60)
    print("🖼️  Product Image Uploader (Azure CLI)")
    print("=" * 60)
    
    uploaded_urls = {}
    total_uploaded = 0
    
    async with aiohttp.ClientSession() as session:
        for category, images in CATEGORY_IMAGES.items():
            print(f"\n📂 {category}:")
            uploaded_urls[category] = []
            
            for url, filename in images:
                print(f"   📥 Downloading {filename}...", end=" ")
                
                image_data = await download_image(session, url)
                if not image_data:
                    print("❌ Failed")
                    continue
                
                # Save to temp file
                with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as f:
                    f.write(image_data)
                    temp_path = f.name
                
                # Upload using az CLI
                blob_name = f"{category}/{filename}"
                if upload_blob(temp_path, blob_name):
                    blob_url = f"https://{STORAGE_ACCOUNT}.blob.core.windows.net/{CONTAINER}/{blob_name}"
                    uploaded_urls[category].append(blob_url)
                    total_uploaded += 1
                    print("✅")
                else:
                    print("❌ Upload failed")
                
                # Cleanup
                os.unlink(temp_path)
    
    # Print summary
    print("\n" + "=" * 60)
    print("📊 Uploaded URLs for seed_products.py")
    print("=" * 60)
    
    print("\nIMAGE_URLS = {")
    for category, urls in uploaded_urls.items():
        print(f'    "{category}": [')
        for url in urls:
            print(f'        "{url}",')
        print("    ],")
    print("}")
    
    print(f"\n✅ Total images uploaded: {total_uploaded}")


if __name__ == "__main__":
    asyncio.run(main())
