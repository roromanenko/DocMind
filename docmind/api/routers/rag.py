"""
RAG (Retrieval-Augmented Generation) API router
"""
import logging
from fastapi import APIRouter, Depends
from typing import List, Dict, Any, Optional
from pydantic import BaseModel

from docmind.api.controllers.rag_controller import RAGController
from docmind.api.dependencies import get_rag_controller

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/rag", tags=["rag"])


class AskRequest(BaseModel):
    """Ask question request model"""
    question: str
    top_k: Optional[int] = 5


class Source(BaseModel):
    """Source document model"""
    document_id: str
    score: float
    text: str


class AskResponse(BaseModel):
    """Ask question response model"""
    answer: str
    context_chunks: List[str]
    sources: List[Source]
    confidence: float
    chunks_used: int


@router.post("/ask", response_model=AskResponse)
async def ask_question(
    request: AskRequest,
    controller: RAGController = Depends(get_rag_controller)
):
    """
    Ask a question and get RAG-based answer
    
    Args:
        request: Question request with parameters
        controller: RAG controller dependency
        
    Returns:
        RAG answer with sources and metadata
    """
    result = await controller.ask_question(
        question=request.question,
        top_k=request.top_k or 5
    )
    
    return AskResponse(**result)


@router.get("/stats")
async def get_rag_stats(
    controller: RAGController = Depends(get_rag_controller)
):
    """Get RAG service statistics"""
    return await controller.get_stats()


@router.get("/health")
async def rag_health(
    controller: RAGController = Depends(get_rag_controller)
):
    """Health check for RAG functionality"""
    return await controller.health_check() 