"""
Async search API router for semantic document search
"""
import logging
from fastapi import APIRouter, Depends
from typing import List, Dict, Any

from docmind.models.schemas import SearchQuery, SearchResponse
from docmind.api.controllers.search_controller import SearchController
from docmind.api.dependencies import get_search_controller

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/search", tags=["search"])


@router.post("/", response_model=SearchResponse)
async def search_documents(
    search_query: SearchQuery,
    controller: SearchController = Depends(get_search_controller)
):
    """
    Search documents using semantic similarity
    
    Args:
        search_query: Search query with parameters
        
    Returns:
        Search results with similarity scores
    """
    return await controller.search_documents(search_query)


@router.get("/stats")
async def get_search_stats(
    controller: SearchController = Depends(get_search_controller)
):
    """Get search and embedding service statistics"""
    return await controller.get_search_stats()


@router.get("/health")
async def search_health(
    controller: SearchController = Depends(get_search_controller)
):
    """Health check for search functionality"""
    return await controller.get_health_status() 