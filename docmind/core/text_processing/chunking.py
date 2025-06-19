"""
Text chunking functionality for document processing
"""
import logging
from typing import List, Dict, Any, Optional
from pathlib import Path
import re

from docmind.config.settings import settings
from docmind.core.exceptions import ChunkingError

logger = logging.getLogger(__name__)


class TextChunker:
    """
    Service for splitting text into chunks for vector storage
    """
    
    def __init__(self, chunk_size: Optional[int] = None, chunk_overlap: Optional[int] = None):
        self.chunk_size = chunk_size or settings.chunk_size
        self.chunk_overlap = chunk_overlap or settings.chunk_overlap
        
    def split_text(self, text: str, document_id: str, metadata: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Split text into chunks with metadata
        
        Args:
            text: Text content to split
            document_id: ID of the source document
            metadata: Additional metadata to include in chunks
            
        Returns:
            List of chunk dictionaries
        """
        if not text.strip():
            return []
        
        # Clean and normalize text
        text = self._clean_text(text)
        
        # Split into sentences first (better semantic boundaries)
        sentences = self._split_into_sentences(text)
        
        chunks = []
        current_chunk = ""
        chunk_start = 0
        
        for i, sentence in enumerate(sentences):
            # Check if adding this sentence would exceed chunk size
            if len(current_chunk) + len(sentence) > self.chunk_size and current_chunk:
                # Save current chunk
                chunk_data = self._create_chunk_data(
                    current_chunk.strip(),
                    document_id,
                    chunk_start,
                    len(current_chunk),
                    metadata
                )
                chunks.append(chunk_data)
                
                # Start new chunk with overlap
                overlap_text = self._get_overlap_text(current_chunk)
                current_chunk = overlap_text + sentence
                chunk_start = max(0, chunk_start + len(current_chunk) - len(overlap_text) - len(sentence))
            else:
                current_chunk += sentence
        
        # Add final chunk if there's content
        if current_chunk.strip():
            chunk_data = self._create_chunk_data(
                current_chunk.strip(),
                document_id,
                chunk_start,
                len(current_chunk),
                metadata
            )
            chunks.append(chunk_data)
        
        logger.info(f"Разбито на {len(chunks)} чанков для документа {document_id}")
        return chunks
    
    def _clean_text(self, text: str) -> str:
        """Clean and normalize text"""
        # Remove excessive whitespace
        text = re.sub(r'\s+', ' ', text)
        # Remove excessive newlines
        text = re.sub(r'\n\s*\n', '\n\n', text)
        return text.strip()
    
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
    
    def _create_chunk_data(self, text: str, document_id: str, start_pos: int, 
                          length: int, metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Create chunk data structure"""
        chunk_id = f"{document_id}_{start_pos}_{start_pos + length}"
        
        chunk_data = {
            "id": chunk_id,
            "document_id": document_id,
            "text": text,
            "start_position": start_pos,
            "end_position": start_pos + length,
            "length": len(text),
            "metadata": metadata or {}
        }
        
        return chunk_data

# Global chunker instance
chunker = TextChunker()
