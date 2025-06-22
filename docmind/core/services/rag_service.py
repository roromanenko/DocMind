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
    
    async def ask(self, question: str, chat_id: Optional[str] = None, top_k: int = 5) -> Dict[str, Any]:
        """
        Ask a question and get an answer.
        The answer is RAG-based if relevant documents are found, otherwise general knowledge is used.
        """
        try:
            # 0. Ensure vector store collection exists
            try:
                await self.vector_store.get_stats_async()
            except:
                logger.info("Initializing vector store collection for RAG...")
                await self.vector_store.initialize()
            
            # 1. Retrieve relevant chunks (filtered by chat_id if provided)
            search_results = await self.vector_store.search_async(
                query=question,
                chat_id=chat_id,
                limit=top_k,
                score_threshold=0.75  # Increased threshold for better relevance
            )
            
            prompt: str
            context_chunks: List[str] = []
            sources: List[Dict[str, Any]] = []
            confidence: float = 0.0
            
            if search_results:
                # RAG path: context is available
                logger.info(f"Found {len(search_results)} relevant chunks for the question.")
                context_chunks = [result["text"] for result in search_results]
                prompt = self.prompt_manager.create_rag_prompt(question, context_chunks)
                sources = [
                    {
                        "document_id": result["document_id"],
                        "score": result["score"],
                        "text": result["text"][:200] + "..."
                    }
                    for result in search_results
                ]
                confidence = sum(result["score"] for result in search_results) / len(search_results)
            else:
                # General knowledge path: no context found
                logger.info("No relevant chunks found. Using general knowledge.")
                prompt = self.prompt_manager.create_no_context_prompt(question)

            # 2. Generate answer using LLM with the prepared prompt
            answer = await self._generate_answer(prompt)
            
            # 3. Prepare response
            return {
                "answer": answer,
                "context_chunks": context_chunks,
                "sources": sources,
                "confidence": confidence,
                "chunks_used": len(search_results)
            }
            
        except Exception as e:
            logger.error(f"RAG ask failed: {e}", exc_info=True)
            raise RAGError(f"Failed to generate answer: {str(e)}")
    
    async def _generate_answer(self, prompt: str) -> str:
        """
        Generate answer using OpenAI LLM with a given prompt.
        """
        try:
            client = self._get_openai_client()
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
            logger.error(f"LLM generation failed: {e}", exc_info=True)
            raise RAGError(f"Failed to generate answer with LLM: {str(e)}")
    
    async def health_check(self) -> Dict[str, Any]:
        """Performs a health check on RAG dependencies (LLM and Vector Store)."""
        llm_ok = False
        vector_store_ok = False
        message_parts = []

        # 1. Check LLM connection
        try:
            client = self._get_openai_client()
            await client.models.list()  # A cheap API call to check connectivity
            llm_ok = True
        except Exception as e:
            logger.error(f"LLM health check failed: {e}")
            message_parts.append("LLM connection failed.")

        # 2. Check Vector Store connection
        try:
            stats = await self.vector_store.get_stats_async()
            if stats.get("status") == "connected" and stats.get("points_count", -1) >= 0:
                vector_store_ok = True
            else:
                error_msg = stats.get('error', 'Unknown error')
                message_parts.append(f"Vector store error: {error_msg}")
        except Exception as e:
            logger.error(f"Vector store health check failed: {e}")
            message_parts.append("Vector store connection failed.")

        is_healthy = llm_ok and vector_store_ok
        message = " ".join(message_parts) or "All services are operational."

        return {
            "status": "healthy" if is_healthy else "unhealthy",
            "llm_ok": llm_ok,
            "vector_store_ok": vector_store_ok,
            "rag_ok": is_healthy,
            "message": message
        }
    
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