"""
API-specific exceptions and error handling
These handle the translation between business exceptions and HTTP responses
"""
from typing import Dict, Any, Type
from fastapi import HTTPException, status
from fastapi.responses import JSONResponse
from fastapi.requests import Request
import logging

from docmind.core.exceptions import (
    DocMindBusinessException,
    DocumentValidationError,
    DocumentNotFoundError,
    TextExtractionError,
    FileStorageError,
    VectorStoreError,
    ChunkingError
)

logger = logging.getLogger(__name__)


class APIExceptionHandler:
    """Handles conversion of business exceptions to HTTP responses"""
    
    # Mapping of business exceptions to HTTP status codes
    EXCEPTION_STATUS_MAPPING: Dict[Type[DocMindBusinessException], int] = {
        # 4xx Client Errors
        DocumentValidationError: status.HTTP_400_BAD_REQUEST,
        DocumentNotFoundError: status.HTTP_404_NOT_FOUND,
        
        # 5xx Server Errors  
        TextExtractionError: status.HTTP_422_UNPROCESSABLE_ENTITY,
        FileStorageError: status.HTTP_500_INTERNAL_SERVER_ERROR,
        VectorStoreError: status.HTTP_500_INTERNAL_SERVER_ERROR,
        ChunkingError: status.HTTP_500_INTERNAL_SERVER_ERROR,
    }
    
    @classmethod
    def handle_business_exception(cls, request: Request, exc: DocMindBusinessException) -> JSONResponse:
        """Convert business exception to HTTP response"""
        # Log the exception
        logger.error(f"Business exception: {exc.message} - {exc.details}")
        
        # Get appropriate status code
        status_code = cls.EXCEPTION_STATUS_MAPPING.get(
            type(exc), 
            status.HTTP_500_INTERNAL_SERVER_ERROR
        )
        
        # Return structured error response
        return JSONResponse(
            status_code=status_code,
            content={
                "error": exc.message,
                "details": exc.details,
                "type": exc.__class__.__name__,
                "path": str(request.url.path)
            }
        )
    
    @classmethod
    def handle_general_exception(cls, request: Request, exc: Exception) -> JSONResponse:
        """Handle unexpected exceptions"""
        logger.error(f"Unhandled exception: {str(exc)}", exc_info=True)
        
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": "Internal server error",
                "details": "An unexpected error occurred",
                "type": "InternalServerError",
                "path": str(request.url.path)
            }
        )


# Convenience functions for common API errors
def raise_not_found(message: str = "Resource not found") -> HTTPException:
    """Raise 404 Not Found exception"""
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=message)


def raise_bad_request(message: str = "Bad request") -> HTTPException:
    """Raise 400 Bad Request exception"""
    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=message)


def raise_validation_error(message: str = "Validation error") -> HTTPException:
    """Raise 422 Unprocessable Entity exception"""
    raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=message)