"""
API dependencies and utilities
"""
from typing import Annotated
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer

from docmind.core.text_processing.ingestion import ingestion_service
from docmind.api.exceptions import raise_not_found

# Security
security = HTTPBearer(auto_error=False)


async def get_current_user(token: Annotated[str, Depends(security)]):
    """Get current user from token (placeholder for auth)"""
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required"
        )
    # TODO: Implement actual token validation
    return {"user_id": "test_user", "token": token}


async def get_document_service():
    """Dependency to get document ingestion service"""
    return ingestion_service
