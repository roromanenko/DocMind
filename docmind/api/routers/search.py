"""
Async search API router for semantic document search
"""
import logging
from fastapi import APIRouter, Depends, Query, HTTPException
from typing import List, Dict, Any, Optional
from pydantic import BaseModel

from docmind.core.vector_store import async_vector_store
from docmind.core.text_processing.embedding import EmbeddingService
from docmind.api.dependencies import get_document_service
from docmind.core.text_processing.ingestion import DocumentIngestionService

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/search", tags=["search"])


class SearchQuery(BaseModel):
    """Search query model"""
    query: str
    limit: Optional[int] = 10
    score_threshold: Optional[float] = 0.7


class SearchResult(BaseModel):
    """Search result model"""
    id: str
    score: float
    text: str
    document_id: str
    metadata: Dict[str, Any]


class SearchResponse(BaseModel):
    """Search response model"""
    query: str
    results: List[SearchResult]
    total_results: int
    search_stats: Dict[str, Any]


@router.post("/", response_model=SearchResponse)
async def search_documents_async(
    search_query: SearchQuery,
    service: DocumentIngestionService = Depends(get_document_service)
):
    """
    Search documents using semantic similarity (async)
    
    Args:
        search_query: Search query with parameters
        
    Returns:
        Search results with similarity scores
    """
    try:
        # Validate query
        if not search_query.query.strip():
            raise HTTPException(status_code=400, detail="Search query cannot be empty")
        
        # Perform semantic search asynchronously
        results = await async_vector_store.search_async(
            query=search_query.query,
            limit=search_query.limit or 10,
            score_threshold=search_query.score_threshold or 0.7
        )
        
        # Format results
        formatted_results = []
        for result in results:
            formatted_results.append(SearchResult(
                id=result["id"],
                score=result["score"],
                text=result["text"],
                document_id=result["document_id"],
                metadata=result.get("metadata", {})
            ))
        
        # Get search statistics asynchronously
        embedding_service = EmbeddingService()
        search_stats = {
            "query_length": len(search_query.query),
            "results_count": len(formatted_results),
            "score_threshold": search_query.score_threshold,
            "embedding_stats": await embedding_service.get_stats_async()
        }
        
        logger.info(f"Async search completed: '{search_query.query}' -> {len(formatted_results)} results")
        
        return SearchResponse(
            query=search_query.query,
            results=formatted_results,
            total_results=len(formatted_results),
            search_stats=search_stats
        )
        
    except Exception as e:
        logger.error(f"Async search failed: {e}")
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")


@router.get("/stats")
async def get_search_stats_async():
    """Get search and embedding service statistics asynchronously"""
    try:
        # Get vector store stats asynchronously
        vector_stats = await async_vector_store.get_stats_async()
        
        # Get embedding stats asynchronously
        embedding_service = EmbeddingService()
        embedding_stats = await embedding_service.get_stats_async()
        
        return {
            "vector_store": vector_stats,
            "embeddings": embedding_stats,
            "search_available": True,
            "async": True
        }
        
    except Exception as e:
        logger.error(f"Failed to get async search stats: {e}")
        return {
            "vector_store": {"error": str(e)},
            "embeddings": {"error": str(e)},
            "search_available": False,
            "async": True
        }


@router.get("/health")
async def search_health_async():
    """Health check for search functionality (async)"""
    try:
        # Test embedding generation asynchronously
        embedding_service = EmbeddingService()
        embedding_stats = await embedding_service.get_stats_async()
        
        # Test vector store connection asynchronously
        vector_stats = await async_vector_store.get_stats_async()
        
        return {
            "status": "healthy",
            "embeddings": embedding_stats.get("model_available", False),
            "vector_store": vector_stats.get("status", "unknown"),
            "message": "Async search service is operational",
            "async": True
        }
        
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
            "message": "Async search service is not operational",
            "async": True
        }

# Backward compatibility aliases
search_documents = search_documents_async
get_search_stats = get_search_stats_async
search_health = search_health_async 