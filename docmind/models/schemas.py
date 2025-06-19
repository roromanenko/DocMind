"""
Simple Pydantic schemas for DocMind application
"""
from pydantic import BaseModel
from typing import Optional, Dict, Any
from enum import Enum


class DocumentStatus(str, Enum):
    """Document processing status"""
    UPLOADED = "uploaded"
    PROCESSING = "processing"
    COMPLETED = "completed"
    ERROR = "error"


class DocumentCreate(BaseModel):
    """Schema for document creation"""
    filename: str
    content_type: str
    file_size: int


class DocumentResponse(BaseModel):
    """Schema for document response"""
    id: str
    filename: str
    file_size: int
    content_type: str
    status: DocumentStatus
    content_preview: Optional[str] = None
    created_at: Optional[str] = None
    chunk_count: Optional[int] = 0
    vectorized: Optional[bool] = False


class DocumentList(BaseModel):
    """Schema for document list response"""
    documents: list[DocumentResponse]
    total: int
    page: int
    per_page: int


class UploadResponse(BaseModel):
    """Schema for upload response"""
    message: str
    document_id: str
    filename: str
    file_size: int
    status: DocumentStatus


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
    document_id: str
    text_content: str
