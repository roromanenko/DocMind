"""
Main application entry point.
"""
import uvicorn
import logging
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Import routers
from docmind.api.routers import documents

# Create FastAPI app
app = FastAPI(
    title="DocMind",
    version="0.1.0",
    description="Scalable RAG application for document processing and AI-powered search",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global Exception Handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Handle HTTP exceptions (400, 404, 422, etc.)"""
    logger.warning(
        f"HTTP Exception: {exc.status_code} - {exc.detail} | "
        f"Method: {request.method} | URL: {request.url} | "
        f"Client: {request.client.host if request.client else 'unknown'}"
    )
    
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": "HTTP Error",
            "status_code": exc.status_code,
            "detail": exc.detail,
            "path": str(request.url.path)
        }
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle all unhandled exceptions"""
    logger.error(
        f"Unhandled Exception: {type(exc).__name__}: {str(exc)} | "
        f"Method: {request.method} | URL: {request.url} | "
        f"Client: {request.client.host if request.client else 'unknown'}",
        exc_info=True
    )
    
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal Server Error",
            "status_code": 500,
            "detail": "An unexpected error occurred. Please try again later.",
            "path": str(request.url.path)
        }
    )

# Include routers
app.include_router(documents.router, prefix="/api/v1")


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Welcome to DocMind API",
        "version": "0.1.0",
        "docs": "/docs"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}


@app.get("/api/v1/status")
async def api_status():
    """API status endpoint."""
    return {
        "status": "running",
        "version": "0.1.0",
        "features": [
            "Document processing",
            "RAG pipeline with Qdrant Cloud",
            "Vector search",
            "OpenAI integration"
        ],
        "services": {
            "fastapi": "running",
            "qdrant_cloud": "configured",
            "postgresql": "configured",
            "redis": "configured"
        }
    }


@app.get("/api/v1/qdrant/status")
async def qdrant_status():
    """Qdrant Cloud status endpoint."""
    try:
        from docmind.services.vector_store.qdrant_service import QdrantService
        qdrant_service = QdrantService()
        collection_info = qdrant_service.get_collection_info()
        cluster_info = qdrant_service.get_cluster_info()
        
        return {
            "status": "connected",
            "cloud": True,
            "collection": collection_info,
            "cluster": cluster_info
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
        from docmind.services.vector_store.qdrant_service import QdrantService
        qdrant_service = QdrantService()
        cluster_info = qdrant_service.get_cluster_info()
        
        return {
            "status": "connected",
            "cluster_info": cluster_info
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "message": "Cannot connect to Qdrant Cloud cluster"
        }


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info",
    ) 