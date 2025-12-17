"""
AI Search Setup Script
=======================

Creates the product search index in Azure AI Search with 
vector search, semantic ranking, and synonym map configuration.
"""

import asyncio
import os
import sys
from azure.search.documents.indexes import SearchIndexClient
from azure.search.documents.indexes.models import (
    SearchIndex,
    SearchField,
    SearchFieldDataType,
    SimpleField,
    SearchableField,
    VectorSearch,
    HnswAlgorithmConfiguration,
    VectorSearchProfile,
    SemanticConfiguration,
    SemanticField,
    SemanticPrioritizedFields,
    SemanticSearch,
)
from azure.core.credentials import AzureKeyCredential

# Synonym map name (must be created first via setup_synonyms.py)
SYNONYM_MAP_NAME = "product-synonyms"


def create_product_index(use_synonyms: bool = True):
    """Create the products search index.
    
    Args:
        use_synonyms: If True, link synonym map to searchable fields.
                     Make sure to run setup_synonyms.py first!
    """
    print("🔍 Setting up Azure AI Search index...")
    
    # Get configuration from environment
    endpoint = os.getenv("AZURE_SEARCH_ENDPOINT")
    key = os.getenv("AZURE_SEARCH_KEY")
    index_name = os.getenv("AZURE_SEARCH_INDEX", "products")
    
    if not endpoint or not key:
        print("❌ AZURE_SEARCH_ENDPOINT and AZURE_SEARCH_KEY must be set")
        sys.exit(1)
    
    print(f"   Endpoint: {endpoint}")
    print(f"   Index: {index_name}")
    print(f"   Synonyms: {'enabled' if use_synonyms else 'disabled'}")
    
    # Initialize client
    credential = AzureKeyCredential(key)
    client = SearchIndexClient(endpoint, credential)
    
    # Synonym map reference (if enabled)
    synonym_maps = [SYNONYM_MAP_NAME] if use_synonyms else None
    
    # Define fields - name, description, and brand use synonym map for better search
    fields = [
        SimpleField(name="id", type=SearchFieldDataType.String, key=True),
        # These fields use synonym map for query expansion
        SearchableField(name="name", type=SearchFieldDataType.String, 
                       analyzer_name="en.microsoft", synonym_map_names=synonym_maps),
        SearchableField(name="description", type=SearchFieldDataType.String, 
                       analyzer_name="en.microsoft", synonym_map_names=synonym_maps),
        SearchableField(name="category", type=SearchFieldDataType.String, filterable=True, facetable=True, sortable=True),
        SearchableField(name="subcategory", type=SearchFieldDataType.String, filterable=True, facetable=True),
        SearchableField(name="brand", type=SearchFieldDataType.String, filterable=True, facetable=True,
                       synonym_map_names=synonym_maps),
        SimpleField(name="sku", type=SearchFieldDataType.String, filterable=True),
        SimpleField(name="price", type=SearchFieldDataType.Double, filterable=True, sortable=True, facetable=True),
        SimpleField(name="sale_price", type=SearchFieldDataType.Double, filterable=True, sortable=True),
        SimpleField(name="rating", type=SearchFieldDataType.Double, filterable=True, sortable=True),
        SimpleField(name="review_count", type=SearchFieldDataType.Int32, filterable=True, sortable=True),
        SimpleField(name="review_score", type=SearchFieldDataType.Double, filterable=True, sortable=True),
        SimpleField(name="return_count", type=SearchFieldDataType.Int32, filterable=True, sortable=True),
        SimpleField(name="in_stock", type=SearchFieldDataType.Boolean, filterable=True, facetable=True),
        SimpleField(name="featured", type=SearchFieldDataType.Boolean, filterable=True),
        SimpleField(name="image_url", type=SearchFieldDataType.String),
        
        # Vector field for image embeddings (1024 dimensions for Florence/AI Vision)
        SearchField(
            name="image_embedding",
            type=SearchFieldDataType.Collection(SearchFieldDataType.Single),
            searchable=True,
            vector_search_dimensions=1024,
            vector_search_profile_name="image-vector-profile"
        ),
        
        # Vector field for text embeddings (3072 dimensions for text-embedding-3-large)
        SearchField(
            name="text_embedding",
            type=SearchFieldDataType.Collection(SearchFieldDataType.Single),
            searchable=True,
            vector_search_dimensions=3072,
            vector_search_profile_name="text-vector-profile"
        ),
    ]
    
    print("   Configuring vector search...")
    
    # Vector search configuration
    vector_search = VectorSearch(
        algorithms=[
            HnswAlgorithmConfiguration(
                name="hnsw-config",
                parameters={
                    "m": 4,
                    "efConstruction": 400,
                    "efSearch": 500,
                    "metric": "cosine"
                }
            )
        ],
        profiles=[
            VectorSearchProfile(
                name="image-vector-profile",
                algorithm_configuration_name="hnsw-config"
            ),
            VectorSearchProfile(
                name="text-vector-profile",
                algorithm_configuration_name="hnsw-config"
            )
        ]
    )
    
    print("   Configuring semantic search...")
    
    # Semantic configuration
    semantic_config = SemanticConfiguration(
        name="product-semantic-config",
        prioritized_fields=SemanticPrioritizedFields(
            title_field=SemanticField(field_name="name"),
            content_fields=[
                SemanticField(field_name="description")
            ],
            keywords_fields=[
                SemanticField(field_name="category"),
                SemanticField(field_name="brand"),
                SemanticField(field_name="subcategory")
            ]
        )
    )
    
    semantic_search = SemanticSearch(
        configurations=[semantic_config],
        default_configuration_name="product-semantic-config"
    )
    
    # Create index
    print("   Creating index...")
    index = SearchIndex(
        name=index_name,
        fields=fields,
        vector_search=vector_search,
        semantic_search=semantic_search
    )
    
    result = client.create_or_update_index(index)
    print(f"✅ Index '{result.name}' created successfully!")
    
    # Print field summary
    print("\n📋 Index fields:")
    for field in fields:
        field_type = getattr(field, 'type', 'unknown')
        print(f"   - {field.name}: {field_type}")
    
    return result


if __name__ == "__main__":
    create_product_index()
