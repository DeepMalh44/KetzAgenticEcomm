"""
Product Search Indexing Script (Synchronous)
=============================================

Indexes products from Cosmos DB to Azure AI Search with text embeddings.
Uses synchronous operations for Cosmos DB compatibility.
Uses Azure AD authentication for Azure OpenAI (DefaultAzureCredential).
"""

import os
import sys
import httpx
from pymongo import MongoClient
from azure.search.documents import SearchClient
from azure.core.credentials import AzureKeyCredential
from azure.identity import DefaultAzureCredential, get_bearer_token_provider
import time


class ProductIndexer:
    """Indexes products in Azure AI Search."""
    
    def __init__(self):
        # Cosmos DB
        self.cosmos_conn = os.getenv("AZURE_COSMOS_CONNECTION_STRING")
        self.cosmos_db = os.getenv("AZURE_COSMOS_DATABASE", "ketzagenticecomm")
        
        # AI Search
        self.search_endpoint = os.getenv("AZURE_SEARCH_ENDPOINT")
        self.search_key = os.getenv("AZURE_SEARCH_KEY")
        self.search_index = os.getenv("AZURE_SEARCH_INDEX", "products")
        
        # OpenAI (for text embeddings) - Use Azure AD auth
        self.openai_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
        self.embedding_deployment = os.getenv("AZURE_OPENAI_EMBEDDING_DEPLOYMENT", "text-embedding-3-large")
        
        # Get Azure AD token for OpenAI
        self.credential = DefaultAzureCredential()
        self.token_provider = get_bearer_token_provider(
            self.credential,
            "https://cognitiveservices.azure.com/.default"
        )
        
    def validate_config(self):
        """Validate required environment variables."""
        required = [
            ("AZURE_COSMOS_CONNECTION_STRING", self.cosmos_conn),
            ("AZURE_SEARCH_ENDPOINT", self.search_endpoint),
            ("AZURE_SEARCH_KEY", self.search_key),
            ("AZURE_OPENAI_ENDPOINT", self.openai_endpoint),
        ]
        
        missing = [name for name, value in required if not value]
        if missing:
            print("❌ Missing required environment variables:")
            for name in missing:
                print(f"   - {name}")
            return False
        return True
    
    def get_text_embedding(self, text: str) -> list:
        """Generate text embedding using Azure OpenAI with Azure AD auth."""
        url = f"{self.openai_endpoint.rstrip('/')}/openai/deployments/{self.embedding_deployment}/embeddings"
        params = {"api-version": "2024-02-15-preview"}
        
        # Get fresh token
        token = self.token_provider()
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        try:
            with httpx.Client(timeout=30.0) as client:
                response = client.post(
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
    
    def index_products(self):
        """Index all products from Cosmos DB to AI Search."""
        print("🔍 Starting product indexing...")
        
        if not self.validate_config():
            sys.exit(1)
        
        # Connect to Cosmos DB
        print(f"📦 Connecting to Cosmos DB: {self.cosmos_db}")
        mongo_client = MongoClient(self.cosmos_conn)
        db = mongo_client[self.cosmos_db]
        products_collection = db["products"]
        
        # Connect to AI Search
        print(f"🔎 Connecting to AI Search: {self.search_index}")
        search_credential = AzureKeyCredential(self.search_key)
        search_client = SearchClient(
            endpoint=self.search_endpoint,
            index_name=self.search_index,
            credential=search_credential
        )
        
        # Get all products
        products = list(products_collection.find({}))
        print(f"📋 Found {len(products)} products to index")
        
        # Process products in batches
        batch_size = 20
        indexed = 0
        failed = 0
        
        for i in range(0, len(products), batch_size):
            batch = products[i:i + batch_size]
            documents = []
            
            for product in batch:
                try:
                    # Create search text
                    search_text = f"{product['name']} {product['description']} {product['category']} {product['subcategory']} {product['brand']}"
                    
                    # Generate text embedding
                    text_embedding = self.get_text_embedding(search_text)
                    
                    if not text_embedding:
                        print(f"   ⚠️ Skipping {product['name']} - no embedding")
                        failed += 1
                        continue
                    
                    # Create search document
                    doc = {
                        "id": product["id"],
                        "name": product["name"],
                        "description": product["description"],
                        "category": product["category"],
                        "subcategory": product["subcategory"],
                        "brand": product["brand"],
                        "sku": product["sku"],
                        "price": product["price"],
                        "sale_price": product.get("sale_price"),
                        "rating": product.get("rating", 0),
                        "review_count": product.get("review_count", 0),
                        "in_stock": product.get("in_stock", True),
                        "featured": product.get("featured", False),
                        "image_url": product.get("image_url", ""),
                        "text_embedding": text_embedding,
                        "image_embedding": []  # Placeholder - no actual images yet
                    }
                    documents.append(doc)
                    
                except Exception as e:
                    print(f"   ❌ Error processing {product.get('name', 'unknown')}: {e}")
                    failed += 1
            
            # Upload batch to search
            if documents:
                try:
                    result = search_client.upload_documents(documents)
                    indexed += len([r for r in result if r.succeeded])
                    failed += len([r for r in result if not r.succeeded])
                except Exception as e:
                    print(f"   ❌ Batch upload error: {e}")
                    failed += len(documents)
            
            print(f"   📤 Indexed {min(i + batch_size, len(products))}/{len(products)} products")
            
            # Rate limiting
            time.sleep(0.5)
        
        print(f"\n✨ Indexing complete!")
        print(f"   ✅ Indexed: {indexed}")
        print(f"   ❌ Failed: {failed}")
        
        mongo_client.close()


if __name__ == "__main__":
    indexer = ProductIndexer()
    indexer.index_products()
