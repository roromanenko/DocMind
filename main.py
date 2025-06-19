"""
DocMind FastAPI application entry point
"""
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import logging

from docmind.config.settings import settings
from docmind.api.routers import documents
from docmind.api.exceptions import APIExceptionHandler
from docmind.api.middleware import setup_middleware
from docmind.core.exceptions import DocMindBusinessException

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    debug=settings.debug
)

# Setup middleware
setup_middleware(app)

# Exception handlers
@app.exception_handler(DocMindBusinessException)
async def business_exception_handler(request: Request, exc: DocMindBusinessException):
    """Handle business logic exceptions"""
    return APIExceptionHandler.handle_business_exception(request, exc)


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle general exceptions"""
    return APIExceptionHandler.handle_general_exception(request, exc)


# Include routers
app.include_router(documents.router)


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": f"Welcome to {settings.app_name}",
        "version": settings.app_version,
        "status": "running"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": settings.app_name,
        "version": settings.app_version
    }


@app.get("/api/v1/status")
async def api_status():
    """API status endpoint."""
    return {
        "status": "running",
        "version": "0.1.0",
        "features": [
            "Document processing",
            "Text extraction",
            "File storage",
            "Document management"
        ],
        "services": {
            "fastapi": "running",
            "document_ingestion": "running",
            "file_storage": "configured"
        }
    }


@app.get("/api/v1/qdrant/status")
async def qdrant_status():
    """Qdrant Cloud status endpoint."""
    try:
        from docmind.core.vector_store import vector_store
        stats = vector_store.get_stats()
        
        return {
            "status": "connected",
            "cloud": True,
            "collection": stats
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "message": "Qdrant Cloud service not available",
            "cloud": True
        }


@app.get("/api/v1/qdrant/cluster")
async def qdrant_cluster_info():
    """Get detailed Qdrant Cloud cluster information."""
    try:
        from docmind.core.vector_store import vector_store
        stats = vector_store.get_stats()
        
        return {
            "status": "connected",
            "cluster_info": stats
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "message": "Cannot connect to Qdrant Cloud cluster"
        }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug
    ) 