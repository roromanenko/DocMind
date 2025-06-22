"""
Simple Pydantic schemas for DocMind application
"""
import uuid
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, Dict, Any, List, Literal
from datetime import datetime

from docmind.models.database import DocumentStatusEnum


# --- Chat Schemas ---

class ChatSessionCreate(BaseModel):
    """Schema for creating a new chat session"""
    name: str = Field(..., min_length=1, max_length=255, description="Name of the chat session")
    description: Optional[str] = Field(None, max_length=1000, description="Optional description of the chat session")


class ChatSessionUpdate(BaseModel):
    """Schema for updating a chat session"""
    name: Optional[str] = Field(None, min_length=1, max_length=255, description="Updated name of the chat session")
    description: Optional[str] = Field(None, max_length=1000, description="Updated description of the chat session")


class ChatSessionResponse(BaseModel):
    """Schema for chat session response"""
    model_config = ConfigDict(from_attributes=True)
    
    id: uuid.UUID
    name: str
    description: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    document_count: int


class ChatSessionWithDocuments(ChatSessionResponse):
    """Schema for chat session response with documents"""
    documents: List["DocumentResponse"] = []


# --- Document Schemas ---

class DocumentResponse(BaseModel):
    """Schema for document response"""
    model_config = ConfigDict(from_attributes=True)
    
    id: uuid.UUID
    chat_id: uuid.UUID
    filename: str
    file_size: int
    content_type: str
    status: DocumentStatusEnum
    content_preview: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    chunk_count: int
    vectorized: bool


class UploadResponse(BaseModel):
    """Schema for document upload response"""
    message: str
    document_id: uuid.UUID
    chat_id: uuid.UUID
    filename: str
    file_size: int
    status: DocumentStatusEnum


# --- General Purpose Schemas ---

class ErrorResponse(BaseModel):
    """Schema for error response"""
    error: str
    detail: str
    status_code: int


class HealthResponse(BaseModel):
    """Schema for health check response"""
    status: str
    message: str
    statistics: Optional[Dict[str, Any]] = None


class TextResponse(BaseModel):
    """Schema for text content response"""
    document_id: uuid.UUID
    text_content: str


# --- Search Schemas ---

class SearchQuery(BaseModel):
    """Schema for search query"""
    query: str = Field(..., min_length=1, description="Search query text")
    limit: int = Field(10, ge=1, le=100, description="Maximum number of results")
    score_threshold: float = Field(0.7, ge=0.0, le=1.0, description="Minimum similarity score")
    chat_id: Optional[uuid.UUID] = Field(None, description="Optional chat ID to filter search results")


class SearchResult(BaseModel):
    """Schema for individual search result"""
    id: str
    score: float
    text: str
    document_id: str
    chat_id: str
    metadata: dict


class SearchResponse(BaseModel):
    """Schema for search response"""
    query: str
    results: List[SearchResult]
    total_results: int
    chat_id: Optional[uuid.UUID] = None


class SearchQueryParams(BaseModel):
    """POST body for search queries"""
    query: str = Field(..., min_length=1, description="The text query for semantic search.")
    limit: int = Field(10, ge=1, le=100, description="Maximum number of results to return.")
    score_threshold: float = Field(0.7, ge=0.0, le=1.0, description="Minimum similarity score for results.")


class SearchHealthResponse(BaseModel):
    """Search service health check model"""
    status: Literal["healthy", "unhealthy"]
    vector_store_ok: bool
    embeddings_ok: bool
    message: str


# --- RAG Schemas ---

class AskRequest(BaseModel):
    """Ask question request model"""
    question: str = Field(..., min_length=1, description="The question to ask the RAG model.")
    top_k: int = Field(5, ge=1, le=20, description="The number of relevant chunks to retrieve.")


class Source(BaseModel):
    """Source document model"""
    document_id: str
    score: float
    text: str


class AskResponse(BaseModel):
    """Ask question response model"""
    answer: str
    context_chunks: List[str]
    sources: List[Source]
    confidence: float
    chunks_used: int


class RAGStatsResponse(BaseModel):
    """RAG service statistics model"""
    rag_available: bool
    vector_store: Dict[str, Any]
    embeddings: Dict[str, Any]
    llm_model: str
    llm_available: bool


class RAGHealthResponse(BaseModel):
    """RAG service health check model"""
    status: Literal["healthy", "unhealthy"]
    llm_ok: bool
    vector_store_ok: bool
    rag_ok: bool
    message: Optional[str]


# Update forward references
ChatSessionWithDocuments.model_rebuild()
