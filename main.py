"""
DocMind FastAPI application entry point
"""
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, HTMLResponse
import logging
from fastapi.staticfiles import StaticFiles
import os

from docmind.config.settings import settings
from docmind.api.routers import documents, search, rag, chats
from docmind.api.exceptions import APIExceptionHandler
from docmind.api.middleware import setup_middleware
from docmind.core.exceptions import DocMindBusinessException
from docmind.models.database import create_tables

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

# Initialize database
try:
    create_tables()
    logger.info("✅ Database tables initialized")
except Exception as e:
    logger.error(f"❌ Failed to initialize database: {e}")

# Create FastAPI app
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    debug=settings.debug
)

# Подключаем папку static
app.mount("/static", StaticFiles(directory="static"), name="static")
app.mount("/assets", StaticFiles(directory="assets"), name="assets")

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
app.include_router(chats.router, prefix="/api/v1")
app.include_router(documents.router, prefix="/api/v1")
app.include_router(search.router, prefix="/api/v1")
app.include_router(rag.router, prefix="/api/v1")


@app.get("/", response_class=HTMLResponse)
async def root():
    """Root endpoint: web chat UI"""
    index_path = os.path.join("static", "chat.html")
    with open(index_path, encoding="utf-8") as f:
        return f.read()


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
        "version": settings.app_version,
        "features": [
            "Document processing",
            "Text extraction",
            "File storage",
            "Document management",
            "PostgreSQL database"
        ],
        "services": {
            "fastapi": "running",
            "document_ingestion": "running",
            "file_storage": "configured",
            "database": "initialized"
        }
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug
    ) 