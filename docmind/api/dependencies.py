"""
API dependencies for dependency injection
"""
from typing import Annotated, Generator
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer
from sqlalchemy.orm import Session

from docmind.models.database import get_db
from docmind.core.services.document_service import DocumentIngestionService
from docmind.core.services.embedding_service import EmbeddingService
from docmind.core.services.chat_service import ChatService
from docmind.core.vector_store import AsyncVectorStore
from docmind.core.services.rag_service import RAGService

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


def get_chat_service(db: Session = Depends(get_database)) -> ChatService:
    """Get chat service"""
    return ChatService(db)


def get_document_service(db: Session = Depends(get_database)) -> DocumentIngestionService:
    """Get document ingestion service"""
    return DocumentIngestionService(db)


def get_embedding_service() -> EmbeddingService:
    """Get embedding service"""
    return EmbeddingService()


def get_vector_store() -> AsyncVectorStore:
    """Get vector store"""
    return AsyncVectorStore()


def get_rag_service(
    embedding_service: EmbeddingService = Depends(get_embedding_service),
    vector_store: AsyncVectorStore = Depends(get_vector_store)
) -> RAGService:
    """Get RAG service with dependencies"""
    return RAGService(embedding_service=embedding_service, vector_store=vector_store)