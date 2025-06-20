"""
RAG Controller for handling RAG-related requests
"""
import logging
from typing import Dict, Any
from fastapi import HTTPException

from docmind.core.services.rag_service import RAGService
from docmind.core.exceptions import RAGError

logger = logging.getLogger(__name__)


class RAGController:
    """Controller for RAG operations"""
    
    def __init__(self, rag_service: RAGService):
        self.rag_service = rag_service
    
    async def ask_question(self, question: str, top_k: int = 5) -> Dict[str, Any]:
        """
        Handle question asking through RAG
        
        Args:
            question: User's question
            top_k: Number of top chunks to retrieve
            
        Returns:
            RAG response with answer and metadata
        """
        try:
            if not question.strip():
                raise HTTPException(status_code=400, detail="Question cannot be empty")
            
            result = await self.rag_service.ask(question=question, top_k=top_k)
            
            logger.info(f"RAG question answered: '{question}' -> confidence: {result['confidence']:.2f}")
            
            return result
            
        except RAGError as e:
            logger.error(f"RAG error: {e}")
            raise HTTPException(status_code=500, detail=str(e))
        except Exception as e:
            logger.error(f"Unexpected error in RAG controller: {e}")
            raise HTTPException(status_code=500, detail="Internal server error")
    
    async def get_stats(self) -> Dict[str, Any]:
        """Get RAG service statistics"""
        try:
            return await self.rag_service.get_stats()
        except Exception as e:
            logger.error(f"Failed to get RAG stats: {e}")
            return {
                "rag_available": False,
                "error": str(e)
            }
    
    async def health_check(self) -> Dict[str, Any]:
        """Health check for RAG functionality"""
        try:
            stats = await self.rag_service.get_stats()
            return {
                "status": "healthy" if stats.get("rag_available", False) else "unhealthy",
                "llm_available": stats.get("llm_available", False),
                "vector_store_available": "status" in stats.get("vector_store", {}),
                "message": "RAG service is operational" if stats.get("rag_available", False) else "RAG service is not operational"
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "message": "RAG service is not operational"
            } 