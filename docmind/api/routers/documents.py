"""
Documents API router
"""
import uuid
from fastapi import APIRouter, UploadFile, File, Depends, Query, BackgroundTasks, status, Response
from typing import List, Dict, Any
import logging

from docmind.models.database import DocumentStatusEnum
from docmind.models.schemas import (
    DocumentResponse, 
    UploadResponse
)
from docmind.api.dependencies import get_document_service
from docmind.core.services.document_service import DocumentIngestionService
from docmind.api.exceptions import handle_errors

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/documents", tags=["documents"])


@router.post(
    "/{chat_id}/upload",
    response_model=UploadResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Upload a document to a specific chat"
)
@handle_errors
async def upload_document(
    chat_id: uuid.UUID,
    background_tasks: BackgroundTasks,
    file: UploadFile = File(..., description="The document file to upload."),
    service: DocumentIngestionService = Depends(get_document_service),
):
    """
    Uploads a document to a specific chat session.

    This endpoint immediately accepts the file and initiates a background task
    for its processing (text extraction, chunking, and vectorization).
    The response is returned immediately.
    """
    content = await file.read()
    document = service.create_upload_record(
        chat_id=chat_id,
        filename=file.filename or "untitled",
        content=content,
        content_type=file.content_type
    )
    background_tasks.add_task(service.process_and_vectorize_document, document_id=document.id)
    return UploadResponse(
        message="Document upload accepted and is being processed in the background.",
        document_id=document.id,
        chat_id=chat_id,
        filename=document.filename,
        file_size=document.file_size,
        status=document.status,
    )


@router.get(
    "/{chat_id}",
    response_model=List[DocumentResponse],
    summary="Get documents for a specific chat"
)
@handle_errors
async def get_documents_for_chat(
    chat_id: uuid.UUID,
    skip: int = Query(0, ge=0, description="Number of documents to skip"),
    limit: int = Query(20, ge=1, le=100, description="Number of documents to return"),
    service: DocumentIngestionService = Depends(get_document_service),
):
    """Retrieves a paginated list of documents for a specific chat."""
    return service.get_documents(chat_id=chat_id, skip=skip, limit=limit)


@router.get(
    "/{document_id}",
    response_model=DocumentResponse,
    summary="Get a specific document by its ID"
)
@handle_errors
async def get_document(
    document_id: uuid.UUID,
    service: DocumentIngestionService = Depends(get_document_service),
):
    """Retrieves detailed information about a single document by its UUID."""
    return service.get_document(document_id)


@router.delete(
    "/{document_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a document"
)
@handle_errors
async def delete_document(
    document_id: uuid.UUID,
    service: DocumentIngestionService = Depends(get_document_service),
):
    """
    Deletes a document and all its associated data, including the source file,
    and its vector embeddings.
    """
    await service.delete_document(document_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
