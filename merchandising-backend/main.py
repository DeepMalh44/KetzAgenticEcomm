"""
Merchandising Portal Backend - Main FastAPI Application
========================================================

Business-friendly merchandising rules engine for Azure AI Search.
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config import settings
from services.cosmos_db_service import CosmosDBService
from api import rules
from api import products
from api import synonyms

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan - startup and shutdown events."""
    # Startup
    logger.info("🚀 Starting Merchandising Portal Backend...")
    
    # Initialize Cosmos DB and create containers if needed
    cosmos_service = CosmosDBService()
    await cosmos_service.ensure_containers()
    
    logger.info("✅ Merchandising Portal Backend ready!")
    
    yield
    
    # Shutdown
    logger.info("👋 Shutting down Merchandising Portal Backend...")


# Create FastAPI app
app = FastAPI(
    title="Merchandising Portal API",
    description="Business-friendly merchandising rules engine",
    version="1.0.0",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(rules.router, prefix="/api", tags=["rules"])
app.include_router(products.router, prefix="/api", tags=["products"])
app.include_router(synonyms.router, prefix="/api", tags=["synonyms"])


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "merchandising-portal-backend",
        "version": "1.0.0"
    }


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Merchandising Portal API",
        "version": "1.0.0",
        "docs": "/docs"
    }
