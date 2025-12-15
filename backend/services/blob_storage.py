"""
Azure Blob Storage Service
===========================

Storage service for product images and user uploads.
Supports both connection string and managed identity authentication.
"""

from typing import Optional
from datetime import datetime, timedelta
import structlog
from azure.storage.blob.aio import BlobServiceClient, ContainerClient
from azure.storage.blob import generate_blob_sas, BlobSasPermissions
from azure.identity.aio import DefaultAzureCredential

logger = structlog.get_logger(__name__)


class BlobStorageService:
    """Service for Azure Blob Storage operations."""
    
    def __init__(
        self, 
        connection_string: Optional[str] = None,
        account_url: Optional[str] = None,
        account_name: Optional[str] = None,
        container_name: str = "product-images",
        use_managed_identity: bool = False
    ):
        """
        Initialize the Blob Storage service.
        
        Args:
            connection_string: Azure Storage connection string (optional if using MI)
            account_url: Storage account URL for managed identity auth
            account_name: Storage account name for URL generation
            container_name: Name of the blob container
            use_managed_identity: Use DefaultAzureCredential instead of connection string
        """
        self.container_name = container_name
        self.account_name = account_name or ""
        self.account_key = ""  # Not available with managed identity
        
        if use_managed_identity or not connection_string:
            # Use managed identity authentication
            if not account_url:
                if account_name:
                    account_url = f"https://{account_name}.blob.core.windows.net"
                else:
                    raise ValueError("account_url or account_name required for managed identity auth")
            
            self.credential = DefaultAzureCredential()
            self.client = BlobServiceClient(account_url, credential=self.credential)
            self.account_name = account_name or account_url.split("//")[1].split(".")[0]
            logger.info("Blob Storage using managed identity authentication")
        else:
            # Use connection string authentication
            self.connection_string = connection_string
            
            # Parse account info from connection string
            parts = dict(x.split("=", 1) for x in connection_string.split(";") if "=" in x)
            self.account_name = parts.get("AccountName", "")
            self.account_key = parts.get("AccountKey", "")
            
            self.client = BlobServiceClient.from_connection_string(connection_string)
            logger.info("Blob Storage using connection string authentication")
        
        self.container_client = self.client.get_container_client(container_name)
        
        logger.info("Blob Storage service initialized", container=container_name)
    
    async def ensure_container_exists(self):
        """Ensure the container exists."""
        try:
            await self.container_client.create_container()
            logger.info("Container created", container=self.container_name)
        except Exception as e:
            if "ContainerAlreadyExists" not in str(e):
                raise
    
    async def upload_image(
        self,
        content: bytes,
        blob_name: str,
        content_type: str = "image/jpeg"
    ) -> str:
        """
        Upload an image to blob storage.
        
        Returns the URL of the uploaded blob.
        """
        blob_client = self.container_client.get_blob_client(blob_name)
        
        await blob_client.upload_blob(
            content,
            content_settings={"content_type": content_type},
            overwrite=True
        )
        
        # Generate public URL
        url = f"https://{self.account_name}.blob.core.windows.net/{self.container_name}/{blob_name}"
        
        logger.info("Image uploaded", blob_name=blob_name)
        return url
    
    async def upload_image_with_sas(
        self,
        content: bytes,
        blob_name: str,
        content_type: str = "image/jpeg",
        expiry_hours: int = 24
    ) -> str:
        """
        Upload an image and return a SAS URL.
        
        Useful for private containers.
        Note: SAS generation requires account key - not available with managed identity.
        For managed identity, use User Delegation SAS instead.
        """
        blob_client = self.container_client.get_blob_client(blob_name)
        
        await blob_client.upload_blob(
            content,
            content_settings={"content_type": content_type},
            overwrite=True
        )
        
        if self.account_key:
            # Generate SAS token with account key
            sas_token = generate_blob_sas(
                account_name=self.account_name,
                container_name=self.container_name,
                blob_name=blob_name,
                account_key=self.account_key,
                permission=BlobSasPermissions(read=True),
                expiry=datetime.utcnow() + timedelta(hours=expiry_hours)
        )
        
        url = f"https://{self.account_name}.blob.core.windows.net/{self.container_name}/{blob_name}?{sas_token}"
        
        logger.info("Image uploaded with SAS", blob_name=blob_name)
        return url
    
    async def download_image(self, blob_name: str) -> Optional[bytes]:
        """Download an image from blob storage."""
        try:
            blob_client = self.container_client.get_blob_client(blob_name)
            download = await blob_client.download_blob()
            content = await download.readall()
            return content
        except Exception as e:
            logger.error("Download failed", blob_name=blob_name, error=str(e))
            return None
    
    async def delete_image(self, blob_name: str) -> bool:
        """Delete an image from blob storage."""
        try:
            blob_client = self.container_client.get_blob_client(blob_name)
            await blob_client.delete_blob()
            logger.info("Image deleted", blob_name=blob_name)
            return True
        except Exception as e:
            logger.error("Delete failed", blob_name=blob_name, error=str(e))
            return False
    
    async def list_images(
        self, 
        prefix: Optional[str] = None,
        max_results: int = 100
    ) -> list:
        """List images in the container."""
        blobs = []
        async for blob in self.container_client.list_blobs(name_starts_with=prefix):
            blobs.append({
                "name": blob.name,
                "size": blob.size,
                "last_modified": blob.last_modified,
                "url": f"https://{self.account_name}.blob.core.windows.net/{self.container_name}/{blob.name}"
            })
            if len(blobs) >= max_results:
                break
        return blobs
    
    async def get_image_url(self, blob_name: str) -> str:
        """Get the public URL for an image."""
        return f"https://{self.account_name}.blob.core.windows.net/{self.container_name}/{blob_name}"
    
    async def image_exists(self, blob_name: str) -> bool:
        """Check if an image exists."""
        blob_client = self.container_client.get_blob_client(blob_name)
        return await blob_client.exists()
    
    async def close(self):
        """Close the blob service client."""
        await self.client.close()
        logger.info("Blob Storage connection closed")
