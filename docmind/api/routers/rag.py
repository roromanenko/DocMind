"""
RAG (Retrieval-Augmented Generation) API router
"""
import logging
import uuid

from fastapi import APIRouter, Depends, status

from docmind.api.dependencies import get_rag_service
from docmind.core.services.rag_service import RAGService
from docmind.api.exceptions import handle_errors
from docmind.models.schemas import (
    AskRequest,
    AskResponse, 
    RAGStatsResponse,
    RAGHealthResponse
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/rag", tags=["rag"])


# --- Endpoints ---

@router.post(
    "/{chat_id}/ask",
    response_model=AskResponse,
    summary="Ask a question to the RAG system within a chat context",
    description="Receives a question, finds relevant context from documents in the specified chat, and generates an answer."
)
@handle_errors
async def ask_question(
    chat_id: uuid.UUID,
    request: AskRequest,
    service: RAGService = Depends(get_rag_service),
):
    return await service.ask(question=request.question, chat_id=str(chat_id), top_k=request.top_k)

@router.get(
    "/stats",
    response_model=RAGStatsResponse,
    summary="Get RAG service statistics",
    description="Provides statistics about the RAG components, including the vector store and embedding models."
)
@handle_errors
async def get_rag_stats(
    service: RAGService = Depends(get_rag_service),
):
    return await service.get_stats()

@router.get(
    "/health",
    response_model=RAGHealthResponse,
    summary="Health check for the RAG service",
    description="Performs a real-time health check on the RAG service and its dependencies."
)
@handle_errors
async def rag_health(
    service: RAGService = Depends(get_rag_service),
) -> RAGHealthResponse:
    health_status = await service.health_check()
    return RAGHealthResponse(**health_status) 