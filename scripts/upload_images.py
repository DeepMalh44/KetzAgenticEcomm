"""
Upload Product Images to Azure Blob Storage
=============================================

Downloads real product images from Unsplash and uploads them to Azure Blob Storage.
Then outputs the URLs to use in seed_products.py.

Usage:
    python scripts/upload_images.py
"""

import asyncio
import aiohttp
import os
import subprocess
from azure.storage.blob import BlobServiceClient, ContentSettings
import hashlib

# Configuration
STORAGE_ACCOUNT_NAME = "stketzagentickh7xm2"
RESOURCE_GROUP = "rg-ketzagentic-kh7xm2"
STORAGE_CONTAINER = "product-images"

# Curated Unsplash images for each category
CATEGORY_IMAGES = {
    "power_tools": [
        "https://images.unsplash.com/photo-1504148455328-c376907d081c?w=400&h=400&fit=crop",
        "https://images.unsplash.com/photo-1572981779307-38b8cabb2407?w=400&h=400&fit=crop",
        "https://images.unsplash.com/photo-1530124566582-a618bc2615dc?w=400&h=400&fit=crop",
        "https://images.unsplash.com/photo-1586864387789-628af9feed72?w=400&h=400&fit=crop",
    ],
    "hand_tools": [
        "https://images.unsplash.com/photo-1426927308491-6380b6a9936f?w=400&h=400&fit=crop",
        "https://images.unsplash.com/photo-1581092921461-eab62e97a780?w=400&h=400&fit=crop",
        "https://images.unsplash.com/photo-1504917595217-d4dc5ebb6122?w=400&h=400&fit=crop",
    ],
    "building_materials": [
        "https://images.unsplash.com/photo-1541123603104-512919d6a96c?w=400&h=400&fit=crop",
        "https://images.unsplash.com/photo-1558618666-fcd25c85cd64?w=400&h=400&fit=crop",
        "https://images.unsplash.com/photo-1503387762-592deb58ef4e?w=400&h=400&fit=crop",
    ],
    "paint": [
        "https://images.unsplash.com/photo-1562259949-e8e7689d7828?w=400&h=400&fit=crop",
        "https://images.unsplash.com/photo-1525909002-1b05e0c869d8?w=400&h=400&fit=crop",
        "https://images.unsplash.com/photo-1589939705384-5185137a7f0f?w=400&h=400&fit=crop",
    ],
    "flooring": [
        "https://images.unsplash.com/photo-1558618666-fcd25c85cd64?w=400&h=400&fit=crop",
        "https://images.unsplash.com/photo-1600585152220-90363fe7e115?w=400&h=400&fit=crop",
        "https://images.unsplash.com/photo-1541123603104-512919d6a96c?w=400&h=400&fit=crop",
    ],
    "plumbing": [
        "https://images.unsplash.com/photo-1585704032915-c3400ca199e7?w=400&h=400&fit=crop",
        "https://images.unsplash.com/photo-1552321554-5fefe8c9ef14?w=400&h=400&fit=crop",
    ],
    "electrical": [
        "https://images.unsplash.com/photo-1524484485831-a92ffc0de03f?w=400&h=400&fit=crop",
        "https://images.unsplash.com/photo-1507473885765-e6ed057f782c?w=400&h=400&fit=crop",
        "https://images.unsplash.com/photo-1558002038-1055907df827?w=400&h=400&fit=crop",
    ],
    "kitchen_bath": [
        "https://images.unsplash.com/photo-1556909114-f6e7ad7d3136?w=400&h=400&fit=crop",
        "https://images.unsplash.com/photo-1600585152220-90363fe7e115?w=400&h=400&fit=crop",
        "https://images.unsplash.com/photo-1552321554-5fefe8c9ef14?w=400&h=400&fit=crop",
    ],
    "outdoor_garden": [
        "https://images.unsplash.com/photo-1529692236671-f1f6cf9683ba?w=400&h=400&fit=crop",
        "https://images.unsplash.com/photo-1600210492486-724fe5c67fb0?w=400&h=400&fit=crop",
        "https://images.unsplash.com/photo-1416879595882-3373a0480b5b?w=400&h=400&fit=crop",
    ],
    "storage": [
        "https://images.unsplash.com/photo-1558618666-fcd25c85cd64?w=400&h=400&fit=crop",
        "https://images.unsplash.com/photo-1530124566582-a618bc2615dc?w=400&h=400&fit=crop",
    ],
    "hardware": [
        "https://images.unsplash.com/photo-1572981779307-38b8cabb2407?w=400&h=400&fit=crop",
        "https://images.unsplash.com/photo-1558618666-fcd25c85cd64?w=400&h=400&fit=crop",
    ],
    "appliances": [
        "https://images.unsplash.com/photo-1571175443880-49e1d25b2bc5?w=400&h=400&fit=crop",
        "https://images.unsplash.com/photo-1556909114-f6e7ad7d3136?w=400&h=400&fit=crop",
        "https://images.unsplash.com/photo-1626806787461-102c1bfaaea1?w=400&h=400&fit=crop",
    ],
}


async def download_image(session: aiohttp.ClientSession, url: str) -> bytes | None:
    """Download an image from URL."""
    try:
        async with session.get(url, timeout=30) as response:
            if response.status == 200:
                return await response.read()
            print(f"  ❌ Failed to download: Status {response.status}")
            return None
    except Exception as e:
        print(f"  ❌ Error downloading: {e}")
        return None


def upload_to_blob(blob_service: BlobServiceClient, container_name: str, 
                   blob_name: str, data: bytes) -> str | None:
    """Upload image data to Azure Blob Storage."""
    try:
        container_client = blob_service.get_container_client(container_name)
        blob_client = container_client.get_blob_client(blob_name)
        
        # Upload with proper content type
        content_settings = ContentSettings(content_type="image/jpeg")
        blob_client.upload_blob(data, overwrite=True, content_settings=content_settings)
        
        return blob_client.url
    except Exception as e:
        print(f"  ❌ Error uploading {blob_name}: {e}")
        return None


async def main():
    print("=" * 60)
    print("🖼️  Product Image Uploader")
    print("=" * 60)
    
    # Get storage connection string
    print("\n📦 Getting storage connection string...")
    result = subprocess.run(
        f'az storage account show-connection-string --name {STORAGE_ACCOUNT_NAME} --resource-group {RESOURCE_GROUP} -o tsv',
        capture_output=True, text=True, shell=True
    )
    storage_conn_str = result.stdout.strip()
    
    if not storage_conn_str:
        print(f"❌ Could not get storage connection string: {result.stderr}")
        return
    
    print("   ✅ Got connection string")
    
    # Connect to blob storage
    blob_service = BlobServiceClient.from_connection_string(storage_conn_str)
    
    # Ensure container exists with public access
    print(f"\n📁 Creating container '{STORAGE_CONTAINER}' with public access...")
    try:
        container_client = blob_service.get_container_client(STORAGE_CONTAINER)
        container_client.create_container(public_access="blob")
        print("   ✅ Container created with public blob access")
    except Exception as e:
        if "ContainerAlreadyExists" in str(e):
            print("   ℹ️ Container already exists")
            # Set public access on existing container
            container_client.set_container_access_policy(public_access="blob")
            print("   ✅ Updated to public blob access")
        else:
            print(f"   ⚠️ {e}")
    
    # Download and upload images
    print(f"\n📥 Downloading and uploading images...")
    
    uploaded_urls = {}
    
    async with aiohttp.ClientSession() as session:
        for category, urls in CATEGORY_IMAGES.items():
            print(f"\n📂 {category}:")
            uploaded_urls[category] = []
            
            for i, url in enumerate(urls, 1):
                print(f"   [{i}/{len(urls)}] Downloading...")
                
                image_data = await download_image(session, url)
                if not image_data:
                    continue
                
                # Generate blob name
                blob_name = f"{category}/image_{i}.jpg"
                
                # Upload
                blob_url = upload_to_blob(blob_service, STORAGE_CONTAINER, blob_name, image_data)
                
                if blob_url:
                    uploaded_urls[category].append(blob_url)
                    print(f"   ✅ Uploaded: {blob_name}")
    
    # Print summary and URL mapping
    print("\n" + "=" * 60)
    print("📊 Summary - Copy this to seed_products.py")
    print("=" * 60)
    
    print("\nIMAGE_URLS = {")
    for category, urls in uploaded_urls.items():
        print(f'    "{category}": [')
        for url in urls:
            print(f'        "{url}",')
        print("    ],")
    print("}")
    
    total = sum(len(urls) for urls in uploaded_urls.values())
    print(f"\n✅ Total images uploaded: {total}")
    print(f"🔗 Base URL: https://{STORAGE_ACCOUNT_NAME}.blob.core.windows.net/{STORAGE_CONTAINER}/")


if __name__ == "__main__":
    asyncio.run(main())
