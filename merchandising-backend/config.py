"""
Configuration Settings for Merchandising Portal
================================================

Reuses existing Azure resources from main backend.
"""

import os
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # App Configuration
    app_name: str = "Merchandising Portal"
    debug: bool = False
    
    # Azure Cosmos DB Configuration (MongoDB API)
    azure_cosmos_connection_string: str = os.getenv("COSMOS_CONNECTION_STRING", "")
    azure_cosmos_database: str = os.getenv("COSMOS_DATABASE_NAME", "ketzagenticecomm")
    
    # Azure AI Search Configuration
    azure_search_endpoint: str = os.getenv("SEARCH_ENDPOINT", "")
    azure_search_key: str = os.getenv("SEARCH_KEY", "")
    azure_search_index: str = os.getenv("SEARCH_INDEX", "products")
    
    # Main Backend URL (for integration)
    main_backend_url: str = os.getenv("MAIN_BACKEND_URL", "http://localhost:8000")
    
    class Config:
        env_file = ".env"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


settings = get_settings()
