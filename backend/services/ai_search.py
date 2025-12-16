"""
Azure AI Search Service
========================

Full-text, semantic, and vector search for products.
Uses Azure AI Search with integrated vectorization.
Supports both API key and managed identity authentication.
"""

from typing import Optional, List, Dict, Any
import base64
import httpx
import structlog
from azure.search.documents import SearchClient
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
from azure.search.documents.models import VectorizedQuery
from azure.core.credentials import AzureKeyCredential
from azure.identity import DefaultAzureCredential

logger = structlog.get_logger(__name__)


class AISearchService:
    """Service for Azure AI Search operations."""
    
    def __init__(
        self, 
        endpoint: str, 
        key: Optional[str] = None, 
        index_name: str = "products",
        use_managed_identity: bool = False
    ):
        """
        Initialize the AI Search service.
        
        Args:
            endpoint: Azure AI Search endpoint URL
            key: API key (optional if using managed identity)
            index_name: Name of the search index
            use_managed_identity: Use DefaultAzureCredential instead of API key
        """
        self.endpoint = endpoint.rstrip("/")
        self.index_name = index_name
        self.key = key
        self.use_managed_identity = use_managed_identity
        
        # Choose credential type
        if use_managed_identity or not key:
            self.credential = DefaultAzureCredential()
            logger.info("AI Search using managed identity authentication")
        else:
            self.credential = AzureKeyCredential(key)
            logger.info("AI Search using API key authentication")
        
        # Initialize clients
        self.index_client = SearchIndexClient(endpoint, self.credential)
        self.search_client = SearchClient(endpoint, index_name, self.credential)
        
        # HTTP client for REST API calls (for multimodal search)
        self.http_client = httpx.AsyncClient(timeout=30.0)
        
        # Store for query embeddings (in production, use Redis or similar)
        self._query_embeddings: Dict[str, List[float]] = {}
        
        logger.info("AI Search service initialized", index=index_name)
    
    async def create_index(self):
        """Create or update the product search index."""
        fields = [
            SimpleField(name="id", type=SearchFieldDataType.String, key=True),
            SearchableField(name="name", type=SearchFieldDataType.String, analyzer_name="en.microsoft"),
            SearchableField(name="description", type=SearchFieldDataType.String, analyzer_name="en.microsoft"),
            SearchableField(name="category", type=SearchFieldDataType.String, filterable=True, facetable=True),
            SearchableField(name="subcategory", type=SearchFieldDataType.String, filterable=True, facetable=True),
            SearchableField(name="brand", type=SearchFieldDataType.String, filterable=True, facetable=True),
            SimpleField(name="sku", type=SearchFieldDataType.String),
            SimpleField(name="price", type=SearchFieldDataType.Double, filterable=True, sortable=True),
            SimpleField(name="sale_price", type=SearchFieldDataType.Double, filterable=True, sortable=True),
            SimpleField(name="rating", type=SearchFieldDataType.Double, filterable=True, sortable=True),
            SimpleField(name="review_count", type=SearchFieldDataType.Int32, filterable=True),
            SimpleField(name="in_stock", type=SearchFieldDataType.Boolean, filterable=True),
            SimpleField(name="image_url", type=SearchFieldDataType.String),
            # Vector field for image embeddings (1024 dimensions for Florence)
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
        
        # Semantic configuration
        semantic_config = SemanticConfiguration(
            name="product-semantic-config",
            prioritized_fields=SemanticPrioritizedFields(
                title_field=SemanticField(field_name="name"),
                content_fields=[SemanticField(field_name="description")],
                keywords_fields=[
                    SemanticField(field_name="category"),
                    SemanticField(field_name="brand")
                ]
            )
        )
        
        semantic_search = SemanticSearch(configurations=[semantic_config])
        
        # Create index
        index = SearchIndex(
            name=self.index_name,
            fields=fields,
            vector_search=vector_search,
            semantic_search=semantic_search
        )
        
        self.index_client.create_or_update_index(index)
        logger.info("Search index created/updated", index=self.index_name)
    
    async def search_products(
        self,
        query: str,
        category: Optional[str] = None,
        min_price: Optional[float] = None,
        max_price: Optional[float] = None,
        limit: int = 10,
        use_semantic: bool = True  # Enabled - Standard tier available
    ) -> List[Dict[str, Any]]:
        """
        Search for products using semantic search.
        Semantic search provides better understanding of search intent.
        """
        # Build filter
        filters = []
        if category:
            filters.append(f"category eq '{category}'")
        if min_price is not None:
            filters.append(f"price ge {min_price}")
        if max_price is not None:
            filters.append(f"price le {max_price}")
        
        filter_str = " and ".join(filters) if filters else None
        
        logger.info(f"Searching with semantic={use_semantic}, query={query}, filter={filter_str}")
        
        # Perform search
        results = self.search_client.search(
            search_text=query,
            filter=filter_str,
            query_type="semantic" if use_semantic else "simple",
            semantic_configuration_name="product-semantic-config" if use_semantic else None,
            top=limit,
            include_total_count=True,
            select=["id", "name", "description", "category", "subcategory", 
                   "brand", "sku", "price", "sale_price", "rating", 
                   "review_count", "in_stock", "image_url"]
        )
        
        products = []
        for result in results:
            product = {k: v for k, v in result.items() if not k.startswith("@")}
            product["@search.score"] = result.get("@search.score", 0)
            products.append(product)
        
        logger.info("Product search completed", query=query, results=len(products))
        return products
    
    async def search_by_vector(
        self,
        embedding: List[float],
        limit: int = 5,
        category: Optional[str] = None,
        field_name: str = "image_embedding"
    ) -> List[Dict[str, Any]]:
        """
        Search for products using vector similarity.
        """
        # Build filter
        filter_str = f"category eq '{category}'" if category else None
        
        # Create vector query
        vector_query = VectorizedQuery(
            vector=embedding,
            k_nearest_neighbors=limit,
            fields=field_name
        )
        
        results = self.search_client.search(
            search_text=None,
            vector_queries=[vector_query],
            filter=filter_str,
            top=limit,
            select=["id", "name", "description", "category", "price", "image_url"]
        )
        
        products = []
        for result in results:
            product = {k: v for k, v in result.items() if not k.startswith("@")}
            product["@search.score"] = result.get("@search.score", 0)
            products.append(product)
        
        logger.info("Vector search completed", results=len(products))
        return products
    
    async def search_by_image_multimodal(
        self,
        image_data: bytes,
        limit: int = 5,
        category: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Search for products using AI Search multimodal capabilities.
        
        Uses VectorizableImageBinaryQuery to send raw image bytes to AI Search,
        which uses the integrated AI Vision vectorizer to convert the image
        to a vector and perform similarity search.
        """
        # Encode image as base64
        image_base64 = base64.b64encode(image_data).decode("utf-8")
        
        # Build filter
        filter_str = f"category eq '{category}'" if category else None
        
        # Build the search request with vectorizable image query
        search_body = {
            "search": "*",
            "vectorQueries": [
                {
                    "kind": "imageBinary",
                    "base64Image": image_base64,
                    "fields": "image_embedding",
                    "k": limit
                }
            ],
            "select": "id,name,description,category,subcategory,brand,price,sale_price,rating,review_count,in_stock,image_url",
            "top": limit
        }
        
        if filter_str:
            search_body["filter"] = filter_str
        
        # Get auth headers
        headers = {"Content-Type": "application/json"}
        if self.use_managed_identity:
            token = self.credential.get_token("https://search.azure.com/.default")
            headers["Authorization"] = f"Bearer {token.token}"
        else:
            headers["api-key"] = self.key
        
        try:
            # Use preview API version for multimodal support
            url = f"{self.endpoint}/indexes/{self.index_name}/docs/search?api-version=2024-05-01-preview"
            
            response = await self.http_client.post(
                url,
                headers=headers,
                json=search_body
            )
            
            # Log response for debugging
            if response.status_code != 200:
                logger.error("AI Search error response", 
                           status=response.status_code, 
                           body=response.text)
            
            response.raise_for_status()
            
            result = response.json()
            products = []
            
            for doc in result.get("value", []):
                product = {k: v for k, v in doc.items() if not k.startswith("@")}
                product["@search.score"] = doc.get("@search.score", 0)
                products.append(product)
            
            logger.info("Multimodal image search completed", results=len(products))
            return products
            
        except Exception as e:
            logger.error("Multimodal image search failed", error=str(e))
            raise

    async def search_by_image_embedding(
        self,
        image_id: str,
        limit: int = 5,
        category: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Search for products using a stored image embedding.
        """
        embedding = self._query_embeddings.get(image_id)
        if not embedding:
            logger.warning("Embedding not found", image_id=image_id)
            return []
        
        return await self.search_by_vector(
            embedding=embedding,
            limit=limit,
            category=category,
            field_name="image_embedding"
        )
    
    async def store_query_embedding(self, image_id: str, embedding: List[float]):
        """Store a query embedding for later use."""
        self._query_embeddings[image_id] = embedding
        logger.debug("Query embedding stored", image_id=image_id)
    
    async def hybrid_search(
        self,
        query: str,
        text_embedding: Optional[List[float]] = None,
        limit: int = 10,
        category: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Hybrid search combining text and vector search.
        """
        filter_str = f"category eq '{category}'" if category else None
        
        vector_queries = []
        if text_embedding:
            vector_queries.append(VectorizedQuery(
                vector=text_embedding,
                k_nearest_neighbors=limit,
                fields="text_embedding"
            ))
        
        results = self.search_client.search(
            search_text=query,
            vector_queries=vector_queries if vector_queries else None,
            filter=filter_str,
            query_type="semantic",
            semantic_configuration_name="product-semantic-config",
            top=limit,
            select=["id", "name", "description", "category", "price", "image_url"]
        )
        
        products = []
        for result in results:
            product = {k: v for k, v in result.items() if not k.startswith("@")}
            product["@search.score"] = result.get("@search.score", 0)
            products.append(product)
        
        return products
    
    async def index_product(self, product: Dict[str, Any]):
        """Index a single product."""
        self.search_client.upload_documents([product])
        logger.debug("Product indexed", product_id=product.get("id"))
    
    async def index_products_batch(self, products: List[Dict[str, Any]]):
        """Index multiple products in batch."""
        if not products:
            return
        
        # Upload in batches of 1000
        batch_size = 1000
        for i in range(0, len(products), batch_size):
            batch = products[i:i + batch_size]
            self.search_client.upload_documents(batch)
        
        logger.info("Products indexed", count=len(products))
    
    async def delete_product(self, product_id: str):
        """Delete a product from the index."""
        self.search_client.delete_documents([{"id": product_id}])
        logger.debug("Product deleted from index", product_id=product_id)
