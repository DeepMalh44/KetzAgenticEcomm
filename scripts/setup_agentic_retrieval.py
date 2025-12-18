"""
Setup script to create Knowledge Source and Knowledge Base for Agentic Retrieval.
This creates the necessary Azure AI Search objects to enable agentic retrieval.

Run this script once to set up the knowledge base:
    python scripts/setup_agentic_retrieval.py
"""

import os
import sys
import json
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configuration - load from backend/.env
load_dotenv("backend/.env")

SEARCH_ENDPOINT = os.getenv("AZURE_SEARCH_ENDPOINT", "https://search-ketzagentic-kh7xm2.search.windows.net")
SEARCH_API_KEY = os.getenv("AZURE_SEARCH_KEY")
AOAI_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT", "https://aoai-ketzagentic-kh7xm2.openai.azure.com")
AOAI_API_KEY = os.getenv("AZURE_OPENAI_API_KEY") or os.getenv("AZURE_OPENAI_KEY")
AOAI_GPT_DEPLOYMENT = os.getenv("AZURE_OPENAI_DEPLOYMENT", "gpt-4o")
AOAI_GPT_MODEL = os.getenv("AZURE_OPENAI_GPT_MODEL", "gpt-4o")

# Names for the agentic retrieval objects
INDEX_NAME = "products"
KNOWLEDGE_SOURCE_NAME = "products-ks"
KNOWLEDGE_BASE_NAME = "products-kb"

# API version for agentic retrieval (preview)
API_VERSION = "2025-11-01-preview"

def get_headers():
    """Get headers for Azure AI Search API calls."""
    return {
        "Content-Type": "application/json",
        "api-key": SEARCH_API_KEY
    }

def check_prerequisites():
    """Check that all required environment variables are set."""
    missing = []
    if not SEARCH_API_KEY:
        missing.append("AZURE_SEARCH_KEY")
    # Note: Azure OpenAI API key is optional if using managed identity
    # which is the case when disableLocalAuth=true
    
    if missing:
        print(f"❌ Missing environment variables: {', '.join(missing)}")
        print("Please set these in your .env file or environment.")
        sys.exit(1)
    
    print("✅ All prerequisites met")
    print(f"   Search: {SEARCH_ENDPOINT}")
    print(f"   OpenAI: {AOAI_ENDPOINT}")
    print(f"   Deployment: {AOAI_GPT_DEPLOYMENT}")
    if not AOAI_API_KEY:
        print("   Note: OpenAI API key not set - using managed identity")

def list_existing_knowledge_bases():
    """List existing knowledge bases."""
    url = f"{SEARCH_ENDPOINT}/knowledgebases?api-version={API_VERSION}&$select=name"
    response = requests.get(url, headers=get_headers())
    
    if response.status_code == 200:
        data = response.json()
        kb_names = [kb.get("name") for kb in data.get("value", [])]
        print(f"📋 Existing knowledge bases: {kb_names if kb_names else 'None'}")
        return kb_names
    else:
        print(f"⚠️ Could not list knowledge bases: {response.status_code}")
        return []

def list_existing_knowledge_sources():
    """List existing knowledge sources."""
    url = f"{SEARCH_ENDPOINT}/knowledgesources?api-version={API_VERSION}&$select=name"
    response = requests.get(url, headers=get_headers())
    
    if response.status_code == 200:
        data = response.json()
        ks_names = [ks.get("name") for ks in data.get("value", [])]
        print(f"📋 Existing knowledge sources: {ks_names if ks_names else 'None'}")
        return ks_names
    else:
        print(f"⚠️ Could not list knowledge sources: {response.status_code}")
        return []

def create_knowledge_source():
    """Create a knowledge source pointing to the products index."""
    print(f"\n🔧 Creating Knowledge Source: {KNOWLEDGE_SOURCE_NAME}")
    
    url = f"{SEARCH_ENDPOINT}/knowledgesources/{KNOWLEDGE_SOURCE_NAME}?api-version={API_VERSION}"
    
    # Knowledge source definition for search index (2025-11-01-preview schema)
    knowledge_source = {
        "name": KNOWLEDGE_SOURCE_NAME,
        "description": "Knowledge source for hardware store products catalog",
        "kind": "searchIndex",
        "searchIndexParameters": {
            "searchIndexName": INDEX_NAME,
            "semanticConfigurationName": "product-semantic-config",
            "sourceDataFields": [
                {"name": "name"},
                {"name": "description"},
                {"name": "category"},
                {"name": "subcategory"},
                {"name": "brand"},
                {"name": "price"},
                {"name": "sale_price"},
                {"name": "rating"},
                {"name": "review_count"},
                {"name": "in_stock"},
                {"name": "image_url"},
                {"name": "sku"},
                {"name": "id"}
            ],
            "searchFields": [
                {"name": "*"}
            ]
        }
    }
    
    response = requests.put(url, headers=get_headers(), json=knowledge_source)
    
    if response.status_code in [200, 201]:
        print(f"✅ Knowledge Source '{KNOWLEDGE_SOURCE_NAME}' created/updated successfully")
        return True
    else:
        print(f"❌ Failed to create Knowledge Source: {response.status_code}")
        print(f"   Response: {response.text}")
        return False

def create_knowledge_base():
    """Create a knowledge base that uses the knowledge source and connects to Azure OpenAI."""
    print(f"\n🔧 Creating Knowledge Base: {KNOWLEDGE_BASE_NAME}")
    
    url = f"{SEARCH_ENDPOINT}/knowledgebases/{KNOWLEDGE_BASE_NAME}?api-version={API_VERSION}"
    
    # Knowledge base definition - using managed identity for Azure OpenAI
    # The Search service's managed identity needs "Cognitive Services User" role on AOAI
    models_config = {
        "kind": "azureOpenAI",
        "azureOpenAIParameters": {
            "resourceUri": AOAI_ENDPOINT,
            "deploymentId": AOAI_GPT_DEPLOYMENT,
            "modelName": AOAI_GPT_MODEL
        }
    }
    
    # Only add API key if available (for non-managed-identity scenarios)
    if AOAI_API_KEY:
        models_config["azureOpenAIParameters"]["apiKey"] = AOAI_API_KEY
    
    knowledge_base = {
        "name": KNOWLEDGE_BASE_NAME,
        "description": "Knowledge base for hardware store product search with agentic retrieval. Handles complex queries about tools, appliances, flooring, plumbing, electrical, and outdoor products.",
        "retrievalInstructions": """Use this knowledge source to answer questions about hardware store products.
The catalog includes: power tools (drills, saws, sanders), hand tools (hammers, screwdrivers, wrenches), 
paint, plumbing fixtures (faucets, toilets), flooring (hardwood, laminate, vinyl), 
electrical (outlets, lights), outdoor (grills, patio furniture), appliances (refrigerators, washers),
building materials (lumber, drywall), and door hardware (locks, handlesets).
When users ask about products, search for relevant items and include pricing, ratings, and availability information.""",
        "answerInstructions": """Provide helpful, concise answers about products. 
Include product names, prices, ratings, and availability when relevant.
If comparing products, highlight key differences.
If the user asks about a specific brand, prioritize those results.
Format prices with $ and ratings out of 5 stars.""",
        "outputMode": "extractiveData",  # Use extractiveData so we can format products ourselves
        "knowledgeSources": [
            {"name": KNOWLEDGE_SOURCE_NAME}
        ],
        "models": [models_config],
        "retrievalReasoningEffort": {
            "kind": "low"  # Options: minimal, low, medium
        }
    }
    
    response = requests.put(url, headers=get_headers(), json=knowledge_base)
    
    if response.status_code in [200, 201]:
        print(f"✅ Knowledge Base '{KNOWLEDGE_BASE_NAME}' created/updated successfully")
        return True
    else:
        print(f"❌ Failed to create Knowledge Base: {response.status_code}")
        print(f"   Response: {response.text}")
        return False

def test_knowledge_base():
    """Test the knowledge base with a sample query."""
    print(f"\n🧪 Testing Knowledge Base with sample query...")
    
    url = f"{SEARCH_ENDPOINT}/knowledgebases/{KNOWLEDGE_BASE_NAME}/retrieve?api-version={API_VERSION}"
    
    test_request = {
        "messages": [
            {
                "role": "user",
                "content": [{"type": "text", "text": "What drills do you have under $200?"}]
            }
        ],
        "knowledgeSourceParams": [
            {
                "knowledgeSourceName": KNOWLEDGE_SOURCE_NAME,
                "includeReferences": True,
                "includeReferenceSourceData": True
            }
        ],
        "includeActivity": True
    }
    
    response = requests.post(url, headers=get_headers(), json=test_request)
    
    if response.status_code == 200:
        result = response.json()
        print("✅ Knowledge Base query successful!")
        
        # Check if we got results
        if "response" in result and result["response"]:
            print(f"   Response contains {len(result.get('references', []))} references")
            if "activity" in result:
                print(f"   Query plan: {result['activity'].get('queryPlan', 'N/A')}")
        return True
    else:
        print(f"❌ Knowledge Base query failed: {response.status_code}")
        print(f"   Response: {response.text}")
        return False

def delete_knowledge_base():
    """Delete the knowledge base (for cleanup)."""
    url = f"{SEARCH_ENDPOINT}/knowledgebases/{KNOWLEDGE_BASE_NAME}?api-version={API_VERSION}"
    response = requests.delete(url, headers=get_headers())
    if response.status_code in [200, 204]:
        print(f"🗑️ Knowledge Base '{KNOWLEDGE_BASE_NAME}' deleted")
    else:
        print(f"⚠️ Could not delete Knowledge Base: {response.status_code}")

def delete_knowledge_source():
    """Delete the knowledge source (for cleanup)."""
    url = f"{SEARCH_ENDPOINT}/knowledgesources/{KNOWLEDGE_SOURCE_NAME}?api-version={API_VERSION}"
    response = requests.delete(url, headers=get_headers())
    if response.status_code in [200, 204]:
        print(f"🗑️ Knowledge Source '{KNOWLEDGE_SOURCE_NAME}' deleted")
    else:
        print(f"⚠️ Could not delete Knowledge Source: {response.status_code}")

def main():
    """Main setup function."""
    print("=" * 60)
    print("🚀 Azure AI Search - Agentic Retrieval Setup")
    print("=" * 60)
    
    # Check if running with --delete flag
    if len(sys.argv) > 1 and sys.argv[1] == "--delete":
        print("\n🗑️ Deleting existing knowledge base and source...")
        delete_knowledge_base()
        delete_knowledge_source()
        print("\n✅ Cleanup complete!")
        return
    
    # Check prerequisites
    check_prerequisites()
    
    # List existing objects
    print("\n📋 Checking existing objects...")
    existing_kb = list_existing_knowledge_bases()
    existing_ks = list_existing_knowledge_sources()
    
    # Create knowledge source
    if not create_knowledge_source():
        print("\n❌ Setup failed at Knowledge Source creation")
        sys.exit(1)
    
    # Create knowledge base
    if not create_knowledge_base():
        print("\n❌ Setup failed at Knowledge Base creation")
        sys.exit(1)
    
    # Test the knowledge base
    if not test_knowledge_base():
        print("\n⚠️ Knowledge Base created but test query failed. This may be due to API latency.")
        print("   Try running the test again in a few seconds.")
    
    print("\n" + "=" * 60)
    print("✅ Agentic Retrieval Setup Complete!")
    print("=" * 60)
    print(f"\n📝 Configuration:")
    print(f"   Knowledge Source: {KNOWLEDGE_SOURCE_NAME}")
    print(f"   Knowledge Base: {KNOWLEDGE_BASE_NAME}")
    print(f"   Index: {INDEX_NAME}")
    print(f"\n🔗 You can now use the agentic search endpoint in your application.")

if __name__ == "__main__":
    main()
