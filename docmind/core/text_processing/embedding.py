"""
Text embedding functionality
"""
import logging
from typing import List
import numpy as np

from docmind.config.settings import settings

logger = logging.getLogger(__name__)


def get_embeddings(texts: List[str]) -> List[np.ndarray]:
    """Generate embeddings for a list of texts"""
    # TODO: Implement actual embedding generation
    # For now, return random embeddings for testing
    embeddings = []
    for text in texts:
        embedding = np.random.rand(settings.embedding_dimension)
        embedding = embedding / np.linalg.norm(embedding)
        embeddings.append(embedding)
    
    return embeddings


def get_embedding(text: str) -> np.ndarray:
    """Generate embedding for a single text"""
    return get_embeddings([text])[0]