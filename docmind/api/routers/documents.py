"""
Documents API router
"""
import uuid
from fastapi import APIRouter, UploadFile, File, Depends, Query
from typing import List, Dict, Any
import logging

from docmind.models.database import DocumentStatusEnum
from docmind.models.schemas import (
    DocumentResponse, 
    UploadResponse
)
from docmind.api.controllers.document_controller import DocumentController
from docmind.api.dependencies import get_document_controller

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/documents", tags=["documents"])


@router.post("/upload", response_model=UploadResponse)
async def upload_document(
    file: UploadFile = File(...),
    controller: DocumentController = Depends(get_document_controller)
):
    """Upload a document"""
    return await controller.upload_document(file)


@router.get("/", response_model=List[DocumentResponse])
async def get_documents(
    skip: int = 0, 
    limit: int = 20,
    controller: DocumentController = Depends(get_document_controller)
):
    """Get list of documents with pagination"""
    return controller.get_documents(skip=skip, limit=limit)


@router.get("/{document_id}", response_model=DocumentResponse)
async def get_document(
    document_id: uuid.UUID,
    controller: DocumentController = Depends(get_document_controller)
):
    """Get specific document by ID"""
    return controller.get_document(document_id)


@router.get("/{document_id}/text")
async def get_document_text(
    document_id: uuid.UUID,
    cleaned: bool = Query(True, description="Whether to return cleaned text"),
    controller: DocumentController = Depends(get_document_controller)
):
    """Get extracted text content of document"""
    return controller.get_document_text(document_id, cleaned=cleaned)


@router.get("/{document_id}/chunks")
async def get_document_chunks(
    document_id: uuid.UUID,
    controller: DocumentController = Depends(get_document_controller)
):
    """Get chunks for a specific document"""
    return controller.get_document_chunks(document_id)


@router.delete("/{document_id}")
async def delete_document(
    document_id: uuid.UUID,
    controller: DocumentController = Depends(get_document_controller)
):
    """Delete document"""
    return controller.delete_document(document_id)


@router.put("/{document_id}/status")
async def update_document_status(
    document_id: uuid.UUID, 
    status: DocumentStatusEnum,
    controller: DocumentController = Depends(get_document_controller)
):
    """Update document processing status"""
    return controller.update_document_status(document_id, status)


@router.get("/health/status")
async def documents_health(
    controller: DocumentController = Depends(get_document_controller)
):
    """Health check and service statistics"""
    return controller.get_health_status()
