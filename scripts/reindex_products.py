"""
Product Re-Indexing Script
===========================

Re-indexes products from Cosmos DB to Azure AI Search.
Uses Azure CLI credentials for authentication.
"""

import os
import sys
import subprocess
import json
from pymongo import MongoClient
from azure.search.documents import SearchClient
from azure.core.credentials import AzureKeyCredential
import time
import httpx


class ProductReindexer:
    """Re-indexes products in Azure AI Search."""
    
    def __init__(self):
        # Cosmos DB
        self.cosmos_conn = os.getenv("AZURE_COSMOS_CONNECTION_STRING")
        self.cosmos_db = os.getenv("AZURE_COSMOS_DATABASE", "ketzagenticecomm")
        
        # AI Search
        self.search_endpoint = os.getenv("AZURE_SEARCH_ENDPOINT")
        self.search_key = os.getenv("AZURE_SEARCH_KEY")
        self.search_index = os.getenv("AZURE_SEARCH_INDEX", "products")
        
        # OpenAI
        self.openai_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
        self.embedding_deployment = os.getenv("AZURE_OPENAI_EMBEDDING_DEPLOYMENT", "text-embedding-3-large")
        
        # Cache the token
        self._token = None
        self._token_expires = 0
        
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
    
    def get_azure_token(self):
        """Get Azure AD token using Azure CLI."""
        if self._token and time.time() < self._token_expires - 60:
            return self._token
            
        try:
            # Use shell=True for Windows compatibility
            result = subprocess.run(
                'az account get-access-token --resource https://cognitiveservices.azure.com --query accessToken -o tsv',
                capture_output=True,
                text=True,
                timeout=30,
                shell=True
            )
            if result.returncode == 0:
                self._token = result.stdout.strip()
                self._token_expires = time.time() + 3600  # Token valid for 1 hour
                return self._token
            else:
                print(f"⚠️ az command failed: {result.stderr}")
        except Exception as e:
            print(f"⚠️ Failed to get Azure token: {e}")
        return None
    
    def get_text_embedding(self, text: str) -> list:
        """Generate text embedding using Azure OpenAI."""
        token = self.get_azure_token()
        if not token:
            return []
            
        url = f"{self.openai_endpoint.rstrip('/')}/openai/deployments/{self.embedding_deployment}/embeddings"
        params = {"api-version": "2024-02-15-preview"}
        
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        try:
            with httpx.Client(timeout=60.0) as client:
                response = client.post(
                    url,
                    params=params,
                    headers=headers,
                    json={"input": text[:8000]}  # Truncate to avoid token limits
                )
                response.raise_for_status()
                result = response.json()
                return result["data"][0]["embedding"]
        except Exception as e:
            print(f"   ⚠️ Embedding error: {str(e)[:100]}")
            return []
    
    def reindex(self):
        """Re-index all products from Cosmos DB to AI Search."""
        print("🔄 Starting product re-indexing...")
        
        if not self.validate_config():
            sys.exit(1)
        
        # Test Azure token first
        print("🔑 Getting Azure AD token...")
        token = self.get_azure_token()
        if not token:
            print("❌ Could not get Azure AD token. Make sure you're logged in with 'az login'")
            sys.exit(1)
        print("✅ Azure AD token obtained")
        
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
        
        # Delete all existing documents first
        print("🗑️ Clearing existing index documents...")
        try:
            # Get all document IDs
            results = list(search_client.search("*", select=["id"], top=10000))
            if results:
                ids_to_delete = [{"id": r["id"]} for r in results]
                if ids_to_delete:
                    search_client.delete_documents(ids_to_delete)
                    print(f"   Deleted {len(ids_to_delete)} documents")
        except Exception as e:
            print(f"   Note: Could not clear index: {e}")
        
        # Get all products
        products = list(products_collection.find({}))
        print(f"📋 Found {len(products)} products to index")
        
        # Process products in batches
        batch_size = 10  # Smaller batches for reliability
        indexed = 0
        failed = 0
        
        for i in range(0, len(products), batch_size):
            batch = products[i:i + batch_size]
            documents = []
            
            for product in batch:
                try:
                    # Create search text
                    search_text = f"{product['name']} {product.get('description', '')} {product.get('category', '')} {product.get('subcategory', '')} {product.get('brand', '')}"
                    
                    # Generate text embedding
                    text_embedding = self.get_text_embedding(search_text)
                    
                    if not text_embedding:
                        print(f"   ⚠️ No embedding for: {product['name'][:40]}...")
                        failed += 1
                        continue
                    
                    # Create search document - use the SAME ID as Cosmos DB
                    doc = {
                        "id": str(product["id"]),  # Ensure it's a string
                        "name": product["name"],
                        "description": product.get("description", ""),
                        "category": product.get("category", ""),
                        "subcategory": product.get("subcategory", ""),
                        "brand": product.get("brand", ""),
                        "sku": product.get("sku", ""),
                        "price": float(product.get("price", 0)),
                        "sale_price": float(product.get("sale_price")) if product.get("sale_price") else None,
                        "rating": float(product.get("rating", 0)),
                        "review_count": int(product.get("review_count", 0)),
                        "in_stock": bool(product.get("in_stock", True)),
                        "featured": bool(product.get("featured", False)),
                        "image_url": product.get("image_url", ""),
                        "text_embedding": text_embedding,
                        "image_embedding": []  # Placeholder
                    }
                    documents.append(doc)
                    
                except Exception as e:
                    print(f"   ❌ Error processing {product.get('name', 'unknown')[:30]}: {e}")
                    failed += 1
            
            # Upload batch to search
            if documents:
                try:
                    result = search_client.upload_documents(documents)
                    success = len([r for r in result if r.succeeded])
                    fail = len([r for r in result if not r.succeeded])
                    indexed += success
                    failed += fail
                    if fail > 0:
                        for r in result:
                            if not r.succeeded:
                                print(f"   ❌ Failed: {r.key}: {r.error_message}")
                except Exception as e:
                    print(f"   ❌ Batch upload error: {e}")
                    failed += len(documents)
            
            progress = min(i + batch_size, len(products))
            print(f"   📤 Progress: {progress}/{len(products)} ({indexed} indexed, {failed} failed)")
            
            # Rate limiting
            time.sleep(0.3)
        
        print(f"\n✨ Re-indexing complete!")
        print(f"   ✅ Indexed: {indexed}")
        print(f"   ❌ Failed: {failed}")
        
        mongo_client.close()
        
        return indexed > 0


if __name__ == "__main__":
    indexer = ProductReindexer()
    indexer.reindex()
