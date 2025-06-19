"""
API dependencies and utilities
"""
from typing import Annotated, Generator
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer
from sqlalchemy.orm import Session

from docmind.core.text_processing.ingestion import DocumentIngestionService
from docmind.models.database import get_db
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


def get_database() -> Generator[Session, None, None]:
    """Dependency to get database session"""
    db = next(get_db())
    try:
        yield db
    finally:
        db.close()


def get_document_service(db: Session = Depends(get_database)) -> DocumentIngestionService:
    """Dependency to get document ingestion service with database session"""
    return DocumentIngestionService(db)
