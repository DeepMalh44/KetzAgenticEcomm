"""
KetzAgenticEcomm - Main FastAPI Application
============================================

Entry point for the voice commerce API with:
- GPT-4o Realtime WebSocket endpoint
- Product search and image search APIs
- Multi-agent orchestration
"""

import asyncio
import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import structlog

from config import settings
from services.cosmos_db import CosmosDBService
from services.ai_search import AISearchService
from services.blob_storage import BlobStorageService
from services.search_analytics import SearchAnalyticsService
from api.v1.endpoints import realtime, products, orders, images, images_proxy


# Configure structured logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer()
    ],
    wrapper_class=structlog.stdlib.BoundLogger,
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator:
    """Application lifespan manager for startup/shutdown."""
    
    logger.info("Starting KetzAgenticEcomm", environment=settings.environment)
    
    # Check if using managed identity
    use_mi = settings.use_managed_identity
    logger.info("Authentication mode", use_managed_identity=use_mi)
    
    # Initialize services
    try:
        # Cosmos DB - still uses connection string for MongoDB API
        cosmos_service = CosmosDBService(
            connection_string=settings.azure_cosmos_connection_string,
            database_name=settings.azure_cosmos_database
        )
        app.state.cosmos = cosmos_service
        logger.info("Cosmos DB initialized")
        
        # AI Search - supports managed identity
        search_service = AISearchService(
            endpoint=settings.azure_search_endpoint,
            key=settings.azure_search_key if not use_mi else None,
            index_name=settings.azure_search_index,
            use_managed_identity=use_mi
        )
        app.state.search = search_service
        logger.info("AI Search initialized")
        
        # Blob Storage - supports managed identity
        blob_service = BlobStorageService(
            connection_string=settings.azure_storage_connection_string if not use_mi else None,
            account_url=settings.azure_storage_account_url if use_mi else None,
            account_name=settings.azure_storage_account_name,
            container_name=settings.azure_storage_container,
            use_managed_identity=use_mi
        )
        app.state.blob = blob_service
        app.state.blob_service = blob_service  # Also store as blob_service for image proxy
        logger.info("Blob Storage initialized")
        
        # Search Analytics - for tracking search traffic
        analytics_service = SearchAnalyticsService(
            connection_string=settings.applicationinsights_connection_string
        )
        app.state.analytics = analytics_service
        logger.info("Search Analytics initialized", 
                   enabled=analytics_service.enabled)
        
        logger.info("All services initialized successfully")
        
    except Exception as e:
        logger.error("Failed to initialize services", error=str(e))
        raise
    
    yield
    
    # Cleanup
    logger.info("Shutting down KetzAgenticEcomm")
    
    # Flush analytics before shutdown
    if hasattr(app.state, 'analytics') and app.state.analytics:
        app.state.analytics.close()
        logger.info("Search Analytics flushed")


# Create FastAPI app
app = FastAPI(
    title="KetzAgenticEcomm API",
    description="AI-powered Home Improvement Voice Commerce Platform",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Health check
@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "app": settings.app_name,
        "environment": settings.environment
    }


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Welcome to KetzAgenticEcomm API",
        "docs": "/docs",
        "version": "1.0.0"
    }


# Include routers
app.include_router(
    realtime.router,
    prefix="/api/v1/realtime",
    tags=["Realtime Voice"]
)

app.include_router(
    products.router,
    prefix="/api/v1/products",
    tags=["Products"]
)

app.include_router(
    orders.router,
    prefix="/api/v1/orders",
    tags=["Orders"]
)

app.include_router(
    images.router,
    prefix="/api/v1/images",
    tags=["Image Search"]
)

app.include_router(
    images_proxy.router,
    prefix="/api/v1/img",
    tags=["Image Proxy"]
)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug
    )
