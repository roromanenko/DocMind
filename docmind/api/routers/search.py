"""
Async search API router for semantic document search
"""
import logging
import uuid
from fastapi import APIRouter, Depends, Body, HTTPException, status

from docmind.core.vector_store.qdrant_store import AsyncVectorStore
from docmind.core.services.embedding_service import EmbeddingService
from docmind.api.dependencies import get_vector_store, get_embedding_service
from docmind.api.exceptions import handle_errors
from docmind.core.exceptions import VectorStoreError
from docmind.models.schemas import (
    SearchQueryParams,
    SearchResult,
    SearchResponse,
    SearchHealthResponse
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/search", tags=["search"])


@router.post("/{chat_id}", response_model=SearchResponse, summary="Perform a semantic search within a chat")
@handle_errors
async def search_documents(
    chat_id: uuid.UUID,
    params: SearchQueryParams = Body(...),
    vector_store: AsyncVectorStore = Depends(get_vector_store),
):
    try:
        search_results_raw = await vector_store.search_async(
            query=params.query,
            chat_id=str(chat_id),
            limit=params.limit,
            score_threshold=params.score_threshold
        )
    except VectorStoreError as e:
        logger.error(f"Vector store search failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"The search service is currently unavailable: {e}"
        )

    results = [SearchResult(**res) for res in search_results_raw]
    return SearchResponse(
        query=params.query,
        results=results,
        total_results=len(results)
    )

@router.get("/health", response_model=SearchHealthResponse, summary="Health check for the Search service")
@handle_errors
async def search_health(
    vector_store: AsyncVectorStore = Depends(get_vector_store),
    embedding_service: EmbeddingService = Depends(get_embedding_service)
):
    vector_store_ok = False
    embeddings_ok = False
    
    try:
        await vector_store.get_stats_async()
        vector_store_ok = True
    except Exception:
        pass

    try:
        # A simple check on the embedding service could be to get its stats
        await embedding_service.get_stats_async()
        embeddings_ok = True
    except Exception:
        pass
        
    is_healthy = vector_store_ok and embeddings_ok
    return SearchHealthResponse(
        status="healthy" if is_healthy else "unhealthy",
        vector_store_ok=vector_store_ok,
        embeddings_ok=embeddings_ok,
        message="All search components are operational." if is_healthy else "One or more search components are down."
    ) 