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
        """Get system prompt for the assistant"""
        return """Ты — DocMind, умный ассистент. Отвечай на вопросы развернуто и по существу.
Если вопрос касается предоставленного контекста, основывай свой ответ на нем.
Если контекста нет или он нерелевантен, используй свои общие знания.
Всегда отвечай на русском языке."""
    
    @staticmethod
    def create_no_context_prompt(question: str) -> str:
        """Create a direct prompt when no context is available."""
        return question 