"""
KetzAgenticEcomm - Configuration Settings
==========================================

Environment-based configuration for all Azure services.
Supports both managed identity and API key authentication.
"""

import os
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # App Configuration
    app_name: str = "KetzAgenticEcomm"
    debug: bool = False
    environment: str = "development"
    
    # Authentication mode - prefer managed identity in production
    use_managed_identity: bool = False
    
    # Azure OpenAI Configuration
    azure_openai_endpoint: str = ""
    azure_openai_api_key: str = ""  # Optional - not needed with managed identity
    azure_openai_api_version: str = "2024-10-01-preview"
    azure_openai_realtime_deployment: str = "gpt-4o-realtime-preview"
    azure_openai_deployment: str = "gpt-4o"
    azure_openai_embedding_deployment: str = "text-embedding-3-large"
    
    # Azure AI Search Configuration
    azure_search_endpoint: str = ""
    azure_search_key: str = ""  # Optional - not needed with managed identity
    azure_search_index: str = "products"
    azure_search_image_index: str = "product-images"
    
    # Azure Cosmos DB Configuration
    azure_cosmos_endpoint: str = ""  # For managed identity auth
    azure_cosmos_connection_string: str = ""  # For connection string auth (MongoDB API)
    azure_cosmos_database: str = "ketzagenticecomm"
    
    # Azure Blob Storage Configuration
    azure_storage_account_url: str = ""  # For managed identity auth
    azure_storage_account_name: str = ""  # For managed identity auth
    azure_storage_connection_string: str = ""  # For connection string auth
    azure_storage_container: str = "product-images"
    azure_storage_upload_container: str = "uploads"
    
    # Azure Communication Services Configuration
    acs_connection_string: str = ""
    acs_phone_number: str = ""
    
    # Application Insights
    applicationinsights_connection_string: str = ""
    
    # Server Configuration
    host: str = "0.0.0.0"
    port: int = 8000
    
    # CORS Configuration
    cors_origins: list[str] = ["*"]
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
        extra = "ignore"  # Allow extra env vars (like VITE_* from frontend)


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


# Convenience export
settings = get_settings()
