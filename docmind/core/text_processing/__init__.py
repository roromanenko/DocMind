"""
Text processing module for DocMind
"""
from .ingestion import DocumentIngestionService
from .chunking import chunker
from .embedding import get_embeddings, get_embedding

__all__ = [
    'DocumentIngestionService',
    'chunker', 
    'get_embeddings',
    'get_embedding'
] 
