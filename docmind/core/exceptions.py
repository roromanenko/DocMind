"""
Business logic exceptions for DocMind application
These are domain-specific exceptions that represent business rule violations
"""
from typing import Optional


class DocMindBusinessException(Exception):
    """Base exception for DocMind business logic"""
    def __init__(self, message: str, details: Optional[str] = None):
        self.message = message
        self.details = details
        super().__init__(self.message)


class DocumentValidationError(DocMindBusinessException):
    """Raised when document validation fails (business rule violation)"""
    pass


class DocumentNotFoundError(DocMindBusinessException):
    """Raised when document is not found (business rule violation)"""
    pass


class TextExtractionError(DocMindBusinessException):
    """Raised when text extraction fails (business rule violation)"""
    pass


class FileStorageError(DocMindBusinessException):
    """Raised when file storage operations fail (business rule violation)"""
    pass

class RAGError(DocMindBusinessException):
    """Raised when RAG operations fail (business rule violation)"""
    pass

class VectorStoreError(DocMindBusinessException):
    """Raised when vector store operations fail (business rule violation)"""
    pass


class ChunkingError(DocMindBusinessException):
    """Raised when text chunking fails (business rule violation)"""
    pass


class EmbeddingError(DocMindBusinessException):
    """Raised when embedding generation fails (business rule violation)"""
    pass
