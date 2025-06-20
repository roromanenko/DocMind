"""
Minimal RAG (Retrieval-Augmented Generation) service
"""
import logging
from typing import List, Dict, Any, Optional
from openai import AsyncOpenAI

from docmind.config.settings import settings
from docmind.core.services.embedding_service import EmbeddingService
from docmind.core.vector_store.qdrant_store import AsyncVectorStore
from docmind.core.prompts.rag_prompts import PromptManager
from docmind.core.exceptions import RAGError

logger = logging.getLogger(__name__)


class RAGService:
    """
    Minimal RAG service for question answering
    """
    
    def __init__(
        self, 
        embedding_service: Optional[EmbeddingService] = None,
        vector_store: Optional[AsyncVectorStore] = None
    ):
        self.embedding_service = embedding_service or EmbeddingService()
        self.vector_store = vector_store or AsyncVectorStore()
        self.prompt_manager = PromptManager()
        self._openai_client: Optional[AsyncOpenAI] = None
    
    def _get_openai_client(self) -> AsyncOpenAI:
        """Get or create OpenAI client"""
        if self._openai_client is None:
            if not settings.openai_api_key:
                raise RAGError("OpenAI API key not configured")
            
            self._openai_client = AsyncOpenAI(api_key=settings.openai_api_key)
            logger.info("OpenAI client initialized for RAG")
        
        return self._openai_client
    
    async def ask(self, question: str, top_k: int = 5) -> Dict[str, Any]:
        """
        Ask a question and get RAG-based answer
        
        Args:
            question: User's question
            top_k: Number of top chunks to retrieve
            
        Returns:
            Dictionary with answer and metadata
        """
        try:
            # 1. Retrieve relevant chunks
            search_results = await self.vector_store.search_async(
                query=question,
                limit=top_k,
                score_threshold=0.7
            )
            
            if not search_results:
                return {
                    "answer": "Извините, не удалось найти релевантную информацию для ответа на ваш вопрос.",
                    "context_chunks": [],
                    "sources": [],
                    "confidence": 0.0,
                    "chunks_used": 0
                }
            
            # 2. Extract context from chunks
            context_chunks = [result["text"] for result in search_results]
            
            # 3. Generate answer using LLM
            answer = await self._generate_answer(question, context_chunks)
            
            # 4. Prepare response
            sources = [
                {
                    "document_id": result["document_id"],
                    "score": result["score"],
                    "text": result["text"][:200] + "..." if len(result["text"]) > 200 else result["text"]
                }
                for result in search_results
            ]
            
            avg_confidence = sum(result["score"] for result in search_results) / len(search_results)
            
            return {
                "answer": answer,
                "context_chunks": context_chunks,
                "sources": sources,
                "confidence": avg_confidence,
                "chunks_used": len(search_results)
            }
            
        except Exception as e:
            logger.error(f"RAG ask failed: {e}")
            raise RAGError(f"Failed to generate answer: {str(e)}")
    
    async def _generate_answer(self, question: str, context_chunks: List[str]) -> str:
        """
        Generate answer using OpenAI LLM
        
        Args:
            question: User's question
            context_chunks: Retrieved context chunks
            
        Returns:
            Generated answer
        """
        try:
            client = self._get_openai_client()
            
            # Use PromptManager for prompt creation
            prompt = self.prompt_manager.create_rag_prompt(question, context_chunks)
            system_prompt = self.prompt_manager.get_system_prompt()
            
            response = await client.chat.completions.create(
                model=settings.openai_model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=settings.openai_max_tokens,
                temperature=settings.openai_temperature
            )
            
            answer = response.choices[0].message.content.strip() if response.choices[0].message.content else ""
            return answer
            
        except Exception as e:
            logger.error(f"LLM generation failed: {e}")
            raise RAGError(f"Failed to generate answer with LLM: {str(e)}")
    
    async def get_stats(self) -> Dict[str, Any]:
        """Get RAG service statistics"""
        try:
            vector_stats = await self.vector_store.get_stats_async()
            embedding_stats = await self.embedding_service.get_stats_async()
            
            return {
                "rag_available": True,
                "vector_store": vector_stats,
                "embeddings": embedding_stats,
                "llm_model": settings.openai_model,
                "llm_available": self._openai_client is not None
            }
        except Exception as e:
            return {
                "rag_available": False,
                "error": str(e)
            }


# Global RAG service instance for backward compatibility
rag_service = RAGService() 