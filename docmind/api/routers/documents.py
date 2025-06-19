"""
Documents API router
"""
from fastapi import APIRouter, UploadFile, File, Depends
from typing import List
import logging

from docmind.models.schemas import (
    DocumentResponse, 
    UploadResponse, 
    DocumentStatus
)
from docmind.core.text_processing.ingestion import DocumentIngestionService
from docmind.api.dependencies import get_document_service
from docmind.api.exceptions import raise_bad_request

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/documents", tags=["documents"])


@router.post("/upload", response_model=UploadResponse)
async def upload_document(
    file: UploadFile = File(...),
    service: DocumentIngestionService = Depends(get_document_service)
):
    """Upload a document"""
    if not file.filename:
        raise_bad_request("Имя файла не может быть пустым")
    
    # Read file content
    content = await file.read()
    
    # Process document using service
    document = service.process_document(
        filename=file.filename or "",
        content=content,
        content_type=file.content_type
    )
    return UploadResponse(
        message="Документ успешно загружен",
        document_id=document.id,
        filename=document.filename,
        file_size=document.file_size,
        status=document.status
    )


@router.get("/", response_model=List[DocumentResponse])
async def get_documents(
    skip: int = 0, 
    limit: int = 20,
    service: DocumentIngestionService = Depends(get_document_service)
):
    """Get list of documents with pagination"""
    documents = service.get_documents(skip=skip, limit=limit)
    return documents


@router.get("/{document_id}", response_model=DocumentResponse)
async def get_document(
    document_id: str,
    service: DocumentIngestionService = Depends(get_document_service)
):
    """Get specific document by ID"""
    document = service.get_document(document_id)
    return document


@router.get("/{document_id}/text")
async def get_document_text(
    document_id: str,
    service: DocumentIngestionService = Depends(get_document_service)
):
    """Get extracted text content of document"""
    text_content = service.get_document_text(document_id)
    return {"document_id": document_id, "text_content": text_content}


@router.delete("/{document_id}")
async def delete_document(
    document_id: str,
    service: DocumentIngestionService = Depends(get_document_service)
):
    """Delete document"""
    service.delete_document(document_id)
    return {"message": "Документ успешно удален"}


@router.put("/{document_id}/status")
async def update_document_status(
    document_id: str, 
    status: DocumentStatus,
    service: DocumentIngestionService = Depends(get_document_service)
):
    """Update document processing status"""
    service.update_document_status(document_id, status)
    return {"message": "Статус документа обновлен"}


@router.get("/status/health")
async def documents_health(
    service: DocumentIngestionService = Depends(get_document_service)
):
    """Health check and service statistics"""
    stats = service.get_stats()
    
    return {
        "status": "healthy",
        "message": "Document service is running",
        "statistics": stats
    }