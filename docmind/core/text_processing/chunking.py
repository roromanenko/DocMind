"""
Text chunking functionality for document processing
"""
import logging
import uuid
from typing import List, Dict, Any, Optional
from pathlib import Path
import re

from docmind.config.settings import settings
from docmind.core.exceptions import ChunkingError
from docmind.core.text_processing.cleaning import TextCleaner

logger = logging.getLogger(__name__)


class TextChunker:
    """
    Service for splitting text into chunks for vector storage
    """
    
    def __init__(self, 
                 chunk_size: Optional[int] = None, 
                 chunk_overlap: Optional[int] = None,
                 text_cleaner: Optional[TextCleaner] = None):
        self.chunk_size = chunk_size or settings.chunk_size
        self.chunk_overlap = chunk_overlap or settings.chunk_overlap
        self.text_cleaner = text_cleaner or TextCleaner()
        
    def split_text(self, text: str, document_id: uuid.UUID, chat_id: Optional[uuid.UUID] = None, metadata: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Split text into chunks with metadata
        
        Args:
            text: Text content to split
            document_id: UUID of the source document
            chat_id: UUID of the chat session
            metadata: Additional metadata to include in chunks
            
        Returns:
            List of chunk dictionaries
        """
        if not text.strip():
            return []
        
        # Clean and normalize text using the text cleaner
        cleaned_text = self.text_cleaner.clean_text(text)
        
        if not cleaned_text.strip():
            logger.warning(f"No content after cleaning for document {document_id}")
            return []
        
        # Split into sentences first (better semantic boundaries)
        sentences = self._split_into_sentences(cleaned_text)
        
        # Clean individual sentences
        cleaned_sentences = self.text_cleaner.clean_sentences(sentences)
        
        if not cleaned_sentences:
            logger.warning(f"No valid sentences after cleaning for document {document_id}")
            return []
        
        chunks = []
        current_chunk = ""
        chunk_start = 0
        chunk_index = 0
        
        for i, sentence in enumerate(cleaned_sentences):
            # Check if adding this sentence would exceed chunk size
            if len(current_chunk) + len(sentence) > self.chunk_size and current_chunk:
                # Save current chunk
                chunk_data = self._create_chunk_data(
                    current_chunk.strip(),
                    document_id,
                    chat_id,
                    chunk_start,
                    len(current_chunk),
                    chunk_index,
                    metadata,
                )
                chunks.append(chunk_data)
                chunk_index += 1

                # Start new chunk with overlap
                overlap_text = self._get_overlap_text(current_chunk)
                original_length = len(current_chunk)
                chunk_start += original_length - len(overlap_text)
                current_chunk = overlap_text + sentence
            else:
                current_chunk += sentence
        
        # Add final chunk if there's content
        if current_chunk.strip():
            chunk_data = self._create_chunk_data(
                current_chunk.strip(),
                document_id,
                chat_id,
                chunk_start,
                len(current_chunk),
                chunk_index,
                metadata
            )
            chunks.append(chunk_data)
        
        # Log cleaning statistics
        cleaning_stats = self.text_cleaner.get_cleaning_stats(text, cleaned_text)
        logger.info(f"Разбито на {len(chunks)} чанков для документа {document_id}. "
                   f"Очистка: {cleaning_stats['reduction_percent']}% сокращение текста")
        
        return chunks
    
    def _split_into_sentences(self, text: str) -> List[str]:
        """Split text into sentences using regex"""
        # Simple sentence splitting (can be improved with NLP libraries)
        sentences = re.split(r'(?<=[.!?])\s+', text)
        return [s.strip() for s in sentences if s.strip()]
    
    def _get_overlap_text(self, text: str) -> str:
        """Get overlap text from the end of current chunk"""
        if len(text) <= self.chunk_overlap:
            return text
        
        # Try to break at sentence boundary
        overlap_text = text[-self.chunk_overlap:]
        last_sentence_end = overlap_text.rfind('.')
        
        if last_sentence_end > 0:
            return overlap_text[last_sentence_end + 1:]
        
        return overlap_text
    
    def _create_chunk_data(self, text: str, document_id: uuid.UUID, chat_id: Optional[uuid.UUID], start_pos: int, 
                          length: int, chunk_index: int, metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Create chunk data structure"""
        chunk_data = {
            "id": str(uuid.uuid4()),  # Generate unique ID for each chunk
            "document_id": str(document_id),
            "chat_id": str(chat_id) if chat_id else None,
            "text": text,
            "start_position": start_pos,
            "end_position": start_pos + length,
            "length": len(text),
            "chunk_index": chunk_index,
            "metadata": metadata or {}
        }
        
        return chunk_data


# Global chunker instance
chunker = TextChunker()
