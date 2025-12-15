"""
Azure AI Vision Embedding Service
==================================

Generates image embeddings using Azure AI Vision (Florence model).
Used for visual similarity search.
Supports both API key and managed identity authentication.
"""

from typing import List, Optional
import httpx
import structlog
from azure.ai.vision.imageanalysis import ImageAnalysisClient
from azure.ai.vision.imageanalysis.models import VisualFeatures
from azure.core.credentials import AzureKeyCredential
from azure.identity import DefaultAzureCredential

logger = structlog.get_logger(__name__)


class VisionEmbeddingService:
    """Service for generating image embeddings using Azure AI Vision."""
    
    def __init__(
        self, 
        endpoint: str, 
        key: Optional[str] = None,
        use_managed_identity: bool = False
    ):
        """
        Initialize the Vision Embedding service.
        
        Args:
            endpoint: Azure AI Vision endpoint URL
            key: API key (optional if using managed identity)
            use_managed_identity: Use DefaultAzureCredential instead of API key
        """
        self.endpoint = endpoint.rstrip("/")
        self.key = key
        self.use_managed_identity = use_managed_identity
        
        # Choose credential type
        if use_managed_identity or not key:
            self.credential = DefaultAzureCredential()
            logger.info("Vision service using managed identity authentication")
        else:
            self.credential = AzureKeyCredential(key)
            logger.info("Vision service using API key authentication")
        
        # Initialize the Image Analysis client
        self.client = ImageAnalysisClient(endpoint, self.credential)
        
        # HTTP client for vectorize endpoint (not available in SDK yet)
        self.http_client = httpx.AsyncClient(timeout=30.0)
        
        logger.info("Vision Embedding service initialized")
    
    async def _get_auth_headers(self) -> dict:
        """Get authentication headers for HTTP requests."""
        if self.use_managed_identity:
            # Get token from DefaultAzureCredential
            token = self.credential.get_token("https://cognitiveservices.azure.com/.default")
            return {"Authorization": f"Bearer {token.token}"}
        else:
            return {"Ocp-Apim-Subscription-Key": self.key}
    
    async def get_image_embedding(self, image_data: bytes) -> List[float]:
        """
        Generate an embedding vector for an image.
        
        Uses the Florence model to create a 1024-dimensional vector.
        """
        # Use the vectorize endpoint
        url = f"{self.endpoint}/computervision/retrieval:vectorizeImage"
        params = {"api-version": "2024-02-01", "model-version": "2023-04-15"}
        headers = await self._get_auth_headers()
        headers["Content-Type"] = "application/octet-stream"
        
        try:
            response = await self.http_client.post(
                url,
                params=params,
                headers=headers,
                content=image_data
            )
            response.raise_for_status()
            
            result = response.json()
            embedding = result.get("vector", [])
            
            logger.debug("Image embedding generated", dimensions=len(embedding))
            return embedding
            
        except Exception as e:
            logger.error("Failed to generate image embedding", error=str(e))
            raise
    
    async def get_image_embedding_from_url(self, image_url: str) -> List[float]:
        """
        Generate an embedding vector for an image from URL.
        """
        url = f"{self.endpoint}/computervision/retrieval:vectorizeImage"
        params = {"api-version": "2024-02-01", "model-version": "2023-04-15"}
        headers = await self._get_auth_headers()
        headers["Content-Type"] = "application/json"
        
        try:
            response = await self.http_client.post(
                url,
                params=params,
                headers=headers,
                json={"url": image_url}
            )
            response.raise_for_status()
            
            result = response.json()
            embedding = result.get("vector", [])
            
            logger.debug("Image embedding from URL generated", dimensions=len(embedding))
            return embedding
            
        except Exception as e:
            logger.error("Failed to generate image embedding from URL", error=str(e))
            raise
    
    async def get_text_embedding(self, text: str) -> List[float]:
        """
        Generate a text embedding for text-to-image search.
        
        Uses the Florence model's text encoder.
        """
        url = f"{self.endpoint}/computervision/retrieval:vectorizeText"
        params = {"api-version": "2024-02-01", "model-version": "2023-04-15"}
        headers = {
            "Ocp-Apim-Subscription-Key": self.key,
            "Content-Type": "application/json"
        }
        
        try:
            response = await self.http_client.post(
                url,
                params=params,
                headers=headers,
                json={"text": text}
            )
            response.raise_for_status()
            
            result = response.json()
            embedding = result.get("vector", [])
            
            logger.debug("Text embedding generated", dimensions=len(embedding))
            return embedding
            
        except Exception as e:
            logger.error("Failed to generate text embedding", error=str(e))
            raise
    
    async def analyze_image(self, image_data: bytes) -> dict:
        """
        Analyze an image to get captions, tags, and objects.
        
        Useful for generating product descriptions from images.
        """
        try:
            result = self.client.analyze(
                image_data=image_data,
                visual_features=[
                    VisualFeatures.CAPTION,
                    VisualFeatures.DENSE_CAPTIONS,
                    VisualFeatures.TAGS,
                    VisualFeatures.OBJECTS,
                    VisualFeatures.READ
                ]
            )
            
            analysis = {
                "caption": result.caption.text if result.caption else None,
                "confidence": result.caption.confidence if result.caption else None,
                "dense_captions": [
                    {"text": dc.text, "confidence": dc.confidence}
                    for dc in (result.dense_captions.list if result.dense_captions else [])
                ],
                "tags": [
                    {"name": tag.name, "confidence": tag.confidence}
                    for tag in (result.tags.list if result.tags else [])
                ],
                "objects": [
                    {
                        "name": obj.tags[0].name if obj.tags else "unknown",
                        "confidence": obj.tags[0].confidence if obj.tags else 0,
                        "bounding_box": {
                            "x": obj.bounding_box.x,
                            "y": obj.bounding_box.y,
                            "width": obj.bounding_box.width,
                            "height": obj.bounding_box.height
                        }
                    }
                    for obj in (result.objects.list if result.objects else [])
                ]
            }
            
            logger.debug("Image analyzed", tags=len(analysis["tags"]))
            return analysis
            
        except Exception as e:
            logger.error("Image analysis failed", error=str(e))
            raise
    
    async def compare_images(
        self, 
        image1_data: bytes, 
        image2_data: bytes
    ) -> float:
        """
        Compare two images and return a similarity score.
        
        Returns a score between 0 (different) and 1 (identical).
        """
        import numpy as np
        
        # Get embeddings for both images
        embedding1 = await self.get_image_embedding(image1_data)
        embedding2 = await self.get_image_embedding(image2_data)
        
        # Calculate cosine similarity
        vec1 = np.array(embedding1)
        vec2 = np.array(embedding2)
        
        similarity = np.dot(vec1, vec2) / (np.linalg.norm(vec1) * np.linalg.norm(vec2))
        
        return float(similarity)
    
    async def close(self):
        """Close the HTTP client."""
        await self.http_client.aclose()
        logger.info("Vision Embedding service closed")
