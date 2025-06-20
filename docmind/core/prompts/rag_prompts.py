"""
Prompt templates for RAG system
"""
from typing import List


class PromptManager:
    """Manager for RAG prompt templates"""
    
    @staticmethod
    def create_rag_prompt(question: str, context_chunks: List[str]) -> str:
        """
        Create RAG prompt with context and question
        
        Args:
            question: User's question
            context_chunks: Retrieved context chunks
            
        Returns:
            Formatted prompt
        """
        context = "\n\n".join(context_chunks)
        
        return f"""Используй следующую информацию для ответа на вопрос:

Контекст:
{context}

Вопрос: {question}

Ответ:"""
    
    @staticmethod
    def get_system_prompt() -> str:
        """Get system prompt for RAG assistant"""
        return """Ты помощник, который отвечает на вопросы, используя предоставленный контекст. 
Отвечай кратко и по существу. Если в контексте нет информации для ответа, 
честно скажи об этом."""
    
    @staticmethod
    def create_no_context_prompt(question: str) -> str:
        """Create prompt when no context is available"""
        return f"""Вопрос: {question}

Ответ: Извините, не удалось найти релевантную информацию для ответа на ваш вопрос.""" 