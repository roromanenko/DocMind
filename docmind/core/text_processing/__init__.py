"""
Text processing module for DocMind
"""
from .ingestion import ingestion_service
from .chunking import chunker
from .embedding import get_embeddings, get_embedding

__all__ = [
    'ingestion_service',
    'chunker', 
    'get_embeddings',
    'get_embedding'
] 