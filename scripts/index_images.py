"""
Image Indexing Script
======================

Generates image embeddings for products using Azure AI Vision
and indexes them in Azure AI Search for visual similarity search.
"""

import asyncio
import os
import sys
import httpx
from motor.motor_asyncio import AsyncIOMotorClient
from azure.search.documents import SearchClient
from azure.core.credentials import AzureKeyCredential


class ImageIndexer:
    """Indexes product images for visual search."""
    
    def __init__(self):
        # Cosmos DB
        self.cosmos_conn = os.getenv("AZURE_COSMOS_CONNECTION_STRING")
        self.cosmos_db = os.getenv("AZURE_COSMOS_DATABASE", "ketzagenticecomm")
        
        # AI Search
        self.search_endpoint = os.getenv("AZURE_SEARCH_ENDPOINT")
        self.search_key = os.getenv("AZURE_SEARCH_KEY")
        self.search_index = os.getenv("AZURE_SEARCH_INDEX", "products")
        
        # AI Vision
        self.vision_endpoint = os.getenv("AZURE_VISION_ENDPOINT")
        self.vision_key = os.getenv("AZURE_VISION_KEY")
        
        # OpenAI (for text embeddings)
        self.openai_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
        self.openai_key = os.getenv("AZURE_OPENAI_API_KEY")
        self.embedding_deployment = os.getenv("AZURE_OPENAI_EMBEDDING_DEPLOYMENT", "text-embedding-3-large")
        
        # HTTP client
        self.http_client = httpx.AsyncClient(timeout=60.0)
    
    def validate_config(self):
        """Validate required environment variables."""
        required = [
            ("AZURE_COSMOS_CONNECTION_STRING", self.cosmos_conn),
            ("AZURE_SEARCH_ENDPOINT", self.search_endpoint),
            ("AZURE_SEARCH_KEY", self.search_key),
            ("AZURE_VISION_ENDPOINT", self.vision_endpoint),
            ("AZURE_VISION_KEY", self.vision_key),
            ("AZURE_OPENAI_ENDPOINT", self.openai_endpoint),
            ("AZURE_OPENAI_API_KEY", self.openai_key),
        ]
        
        missing = [name for name, value in required if not value]
        if missing:
            print("❌ Missing required environment variables:")
            for name in missing:
                print(f"   - {name}")
            return False
        return True
    
    async def get_image_embedding_from_url(self, image_url: str) -> list:
        """Generate image embedding using Azure AI Vision."""
        url = f"{self.vision_endpoint.rstrip('/')}/computervision/retrieval:vectorizeImage"
        params = {"api-version": "2024-02-01", "model-version": "2023-04-15"}
        headers = {
            "Ocp-Apim-Subscription-Key": self.vision_key,
            "Content-Type": "application/json"
        }
        
        try:
            response = await self.http_client.post(
                url,
                params=params,
                headers=headers,
                json={"url": image_url}
            )
            response.raise_for_status()
            result = response.json()
            return result.get("vector", [])
        except Exception as e:
            print(f"   ⚠️ Failed to get image embedding: {e}")
            return []
    
    async def get_text_embedding(self, text: str) -> list:
        """Generate text embedding using Azure OpenAI."""
        url = f"{self.openai_endpoint.rstrip('/')}/openai/deployments/{self.embedding_deployment}/embeddings"
        params = {"api-version": "2024-02-15-preview"}
        headers = {
            "api-key": self.openai_key,
            "Content-Type": "application/json"
        }
        
        try:
            response = await self.http_client.post(
                url,
                params=params,
                headers=headers,
                json={"input": text}
            )
            response.raise_for_status()
            result = response.json()
            return result["data"][0]["embedding"]
        except Exception as e:
            print(f"   ⚠️ Failed to get text embedding: {e}")
            return []
    
    async def index_products(self, batch_size: int = 50, limit: int = None):
        """Index all products with embeddings."""
        print("🖼️ Starting image indexing...")
        
        if not self.validate_config():
            sys.exit(1)
        
        # Connect to Cosmos DB
        print(f"📦 Connecting to Cosmos DB: {self.cosmos_db}")
        cosmos_client = AsyncIOMotorClient(self.cosmos_conn)
        db = cosmos_client[self.cosmos_db]
        products_collection = db["products"]
        
        # Initialize Search client
        print(f"🔍 Connecting to AI Search: {self.search_index}")
        search_credential = AzureKeyCredential(self.search_key)
        search_client = SearchClient(
            self.search_endpoint,
            self.search_index,
            search_credential
        )
        
        # Get products
        query = {}
        cursor = products_collection.find(query)
        if limit:
            cursor = cursor.limit(limit)
        
        products = await cursor.to_list(length=limit or 10000)
        print(f"📊 Found {len(products)} products to index")
        
        # Process in batches
        indexed_count = 0
        error_count = 0
        documents = []
        
        for i, product in enumerate(products):
            print(f"\n[{i+1}/{len(products)}] Processing: {product['name'][:50]}...")
            
            # Create search document
            doc = {
                "id": product["id"],
                "name": product["name"],
                "description": product.get("description", ""),
                "category": product.get("category", ""),
                "subcategory": product.get("subcategory", ""),
                "brand": product.get("brand", ""),
                "sku": product.get("sku", ""),
                "price": product.get("price", 0),
                "sale_price": product.get("sale_price"),
                "rating": product.get("rating", 0),
                "review_count": product.get("review_count", 0),
                "in_stock": product.get("in_stock", True),
                "featured": product.get("featured", False),
                "image_url": product.get("image_url", ""),
            }
            
            # Get image embedding
            if product.get("image_url"):
                print("   📷 Generating image embedding...")
                image_embedding = await self.get_image_embedding_from_url(product["image_url"])
                if image_embedding:
                    doc["image_embedding"] = image_embedding
                    print(f"   ✅ Image embedding: {len(image_embedding)} dimensions")
            
            # Get text embedding
            text_for_embedding = f"{product['name']} {product.get('description', '')} {product.get('category', '')} {product.get('brand', '')}"
            print("   📝 Generating text embedding...")
            text_embedding = await self.get_text_embedding(text_for_embedding[:8000])  # Limit input length
            if text_embedding:
                doc["text_embedding"] = text_embedding
                print(f"   ✅ Text embedding: {len(text_embedding)} dimensions")
            
            documents.append(doc)
            
            # Upload batch
            if len(documents) >= batch_size:
                print(f"\n📤 Uploading batch of {len(documents)} documents...")
                try:
                    result = search_client.upload_documents(documents)
                    success = sum(1 for r in result if r.succeeded)
                    indexed_count += success
                    error_count += len(documents) - success
                    print(f"   ✅ Batch uploaded: {success} succeeded")
                except Exception as e:
                    print(f"   ❌ Batch upload failed: {e}")
                    error_count += len(documents)
                documents = []
                
                # Small delay to avoid rate limiting
                await asyncio.sleep(1)
        
        # Upload remaining documents
        if documents:
            print(f"\n📤 Uploading final batch of {len(documents)} documents...")
            try:
                result = search_client.upload_documents(documents)
                success = sum(1 for r in result if r.succeeded)
                indexed_count += success
                error_count += len(documents) - success
            except Exception as e:
                print(f"   ❌ Final batch upload failed: {e}")
                error_count += len(documents)
        
        # Cleanup
        await self.http_client.aclose()
        
        print("\n" + "="*50)
        print("✨ Indexing complete!")
        print(f"   ✅ Successfully indexed: {indexed_count}")
        print(f"   ❌ Errors: {error_count}")
        print("="*50)


async def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Index product images for visual search")
    parser.add_argument("--batch-size", type=int, default=50, help="Batch size for uploads")
    parser.add_argument("--limit", type=int, help="Limit number of products to index")
    args = parser.parse_args()
    
    indexer = ImageIndexer()
    await indexer.index_products(batch_size=args.batch_size, limit=args.limit)


if __name__ == "__main__":
    asyncio.run(main())
