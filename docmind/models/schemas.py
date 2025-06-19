"""
Simple Pydantic schemas for DocMind application
"""
import uuid
from pydantic import BaseModel
from typing import Optional, Dict, Any
from datetime import datetime

from docmind.models.database import DocumentStatusEnum


class DocumentCreate(BaseModel):
    """Schema for document creation"""
    filename: str
    content_type: str
    file_size: int


class DocumentResponse(BaseModel):
    """Schema for document response"""
    id: uuid.UUID
    filename: str
    file_size: int
    content_type: str
    status: DocumentStatusEnum
    content_preview: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
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
    document_id: uuid.UUID
    filename: str
    file_size: int
    status: DocumentStatusEnum


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
