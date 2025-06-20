"""
Search Controller for handling search-related requests
"""
import logging
from typing import Dict, Any, List
from fastapi import HTTPException

from docmind.core.vector_store import async_vector_store
from docmind.core.services.embedding_service import EmbeddingService
from docmind.models.schemas import SearchQuery, SearchResult, SearchResponse

logger = logging.getLogger(__name__)


class SearchController:
    """Controller for search operations"""
    
    def __init__(self, embedding_service: EmbeddingService):
        self.embedding_service = embedding_service
    
    async def search_documents(self, search_query: SearchQuery) -> SearchResponse:
        """
        Handle document search
        
        Args:
            search_query: Search query with parameters
            
        Returns:
            Search results with similarity scores
        """
        try:
            if not search_query.query.strip():
                raise HTTPException(status_code=400, detail="Search query cannot be empty")
            
            results = await async_vector_store.search_async(
                query=search_query.query,
                limit=search_query.limit or 10,
                score_threshold=search_query.score_threshold or 0.7
            )
            
            formatted_results = []
            for result in results:
                formatted_results.append(SearchResult(
                    id=result["id"],
                    score=result["score"],
                    text=result["text"],
                    document_id=result["document_id"],
                    metadata=result.get("metadata", {})
                ))
            
            search_stats = {
                "query_length": len(search_query.query),
                "results_count": len(formatted_results),
                "score_threshold": search_query.score_threshold,
                "embedding_stats": await self.embedding_service.get_stats_async()
            }
            
            logger.info(f"Search completed: '{search_query.query}' -> {len(formatted_results)} results")
            
            return SearchResponse(
                query=search_query.query,
                results=formatted_results,
                total_results=len(formatted_results),
                search_stats=search_stats
            )
            
        except Exception as e:
            logger.error(f"Search failed: {e}")
            raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")
    
    async def get_search_stats(self) -> Dict[str, Any]:
        """Get search and embedding service statistics"""
        try:
            vector_stats = await async_vector_store.get_stats_async()
            embedding_stats = await self.embedding_service.get_stats_async()
            
            return {
                "vector_store": vector_stats,
                "embeddings": embedding_stats,
                "search_available": True
            }
            
        except Exception as e:
            logger.error(f"Failed to get search stats: {e}")
            return {
                "vector_store": {"error": str(e)},
                "embeddings": {"error": str(e)},
                "search_available": False
            }
    
    async def get_health_status(self) -> Dict[str, Any]:
        """Health check for search functionality"""
        try:
            embedding_stats = await self.embedding_service.get_stats_async()
            vector_stats = await async_vector_store.get_stats_async()
            
            return {
                "status": "healthy",
                "embeddings": embedding_stats.get("model_available", False),
                "vector_store": vector_stats.get("status", "unknown"),
                "message": "Search service is operational"
            }
            
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "message": "Search service is not operational"
            } 