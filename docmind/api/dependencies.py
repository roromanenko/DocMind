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
from docmind.core.vector_store import AsyncVectorStore
from docmind.core.services.rag_service import RAGService
from docmind.api.controllers.rag_controller import RAGController
from docmind.api.controllers.document_controller import DocumentController
from docmind.api.controllers.search_controller import SearchController

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


def get_rag_controller(
    rag_service: RAGService = Depends(get_rag_service)
) -> RAGController:
    """Get RAG controller with service dependency"""
    return RAGController(rag_service=rag_service)


def get_document_controller(
    document_service: DocumentIngestionService = Depends(get_document_service)
) -> DocumentController:
    """Get document controller with service dependency"""
    return DocumentController(document_service=document_service)


def get_search_controller(
    embedding_service: EmbeddingService = Depends(get_embedding_service)
) -> SearchController:
    """Get search controller with service dependency"""
    return SearchController(embedding_service=embedding_service)
