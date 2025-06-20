"""
Document Controller for handling document-related requests
"""
import logging
import uuid
from typing import Dict, Any, List
from fastapi import HTTPException, UploadFile

from docmind.core.services.document_service import DocumentIngestionService
from docmind.models.database import DocumentStatusEnum
from docmind.models.schemas import DocumentResponse, UploadResponse
from docmind.core.exceptions import (
    DocumentValidationError, 
    DocumentNotFoundError, 
    TextExtractionError,
    FileStorageError
)

logger = logging.getLogger(__name__)


class DocumentController:
    """Controller for document operations"""
    
    def __init__(self, document_service: DocumentIngestionService):
        self.document_service = document_service
    
    async def upload_document(self, file: UploadFile) -> UploadResponse:
        """
        Handle document upload
        
        Args:
            file: Uploaded file
            
        Returns:
            Upload response with document info
        """
        try:
            if not file.filename:
                raise HTTPException(status_code=400, detail="Имя файла не может быть пустым")
            
            content = await file.read()
            document = self.document_service.process_document(
                filename=file.filename or "",
                content=content,
                content_type=file.content_type
            )
            
            logger.info(f"Document uploaded: {file.filename} (ID: {document.id})")
            
            return UploadResponse(
                message="Документ успешно загружен",
                document_id=document.id,
                filename=document.filename,
                file_size=document.file_size,
                status=document.status
            )
            
        except DocumentValidationError as e:
            logger.error(f"Document validation error: {e}")
            raise HTTPException(status_code=400, detail=str(e))
        except (TextExtractionError, FileStorageError) as e:
            logger.error(f"Document processing error: {e}")
            raise HTTPException(status_code=500, detail=str(e))
        except Exception as e:
            logger.error(f"Unexpected error in document upload: {e}")
            raise HTTPException(status_code=500, detail="Internal server error")
    
    def get_documents(self, skip: int = 0, limit: int = 20) -> List[DocumentResponse]:
        """Get list of documents with pagination"""
        try:
            return self.document_service.get_documents(skip=skip, limit=limit)
        except Exception as e:
            logger.error(f"Failed to get documents: {e}")
            raise HTTPException(status_code=500, detail="Failed to retrieve documents")
    
    def get_document(self, document_id: uuid.UUID) -> DocumentResponse:
        """Get specific document by ID"""
        try:
            return self.document_service.get_document(document_id)
        except DocumentNotFoundError as e:
            logger.error(f"Document not found: {e}")
            raise HTTPException(status_code=404, detail=str(e))
        except Exception as e:
            logger.error(f"Failed to get document {document_id}: {e}")
            raise HTTPException(status_code=500, detail="Failed to retrieve document")
    
    def get_document_text(self, document_id: uuid.UUID, cleaned: bool = True) -> Dict[str, Any]:
        """Get extracted text content of document"""
        try:
            text_content = self.document_service.get_document_text(document_id, cleaned=cleaned)
            return {
                "document_id": document_id,
                "text_content": text_content,
                "cleaned": cleaned
            }
        except DocumentNotFoundError as e:
            logger.error(f"Document not found: {e}")
            raise HTTPException(status_code=404, detail=str(e))
        except Exception as e:
            logger.error(f"Failed to get document text {document_id}: {e}")
            raise HTTPException(status_code=500, detail="Failed to retrieve document text")
    
    def get_document_chunks(self, document_id: uuid.UUID) -> Dict[str, Any]:
        """Get chunks for a specific document"""
        try:
            chunks = self.document_service.get_document_chunks(document_id)
            return {
                "document_id": document_id,
                "chunks_count": len(chunks),
                "chunks": chunks
            }
        except DocumentNotFoundError as e:
            logger.error(f"Document not found: {e}")
            raise HTTPException(status_code=404, detail=str(e))
        except Exception as e:
            logger.error(f"Failed to get document chunks {document_id}: {e}")
            raise HTTPException(status_code=500, detail="Failed to retrieve document chunks")
    
    def delete_document(self, document_id: uuid.UUID) -> Dict[str, str]:
        """Delete document"""
        try:
            self.document_service.delete_document(document_id)
            logger.info(f"Document deleted: {document_id}")
            return {"message": "Документ успешно удален"}
        except DocumentNotFoundError as e:
            logger.error(f"Document not found: {e}")
            raise HTTPException(status_code=404, detail=str(e))
        except Exception as e:
            logger.error(f"Failed to delete document {document_id}: {e}")
            raise HTTPException(status_code=500, detail="Failed to delete document")
    
    def update_document_status(self, document_id: uuid.UUID, status: DocumentStatusEnum) -> Dict[str, str]:
        """Update document processing status"""
        try:
            self.document_service.update_document_status(document_id, status)
            logger.info(f"Document status updated: {document_id} -> {status}")
            return {"message": "Статус документа обновлен"}
        except DocumentNotFoundError as e:
            logger.error(f"Document not found: {e}")
            raise HTTPException(status_code=404, detail=str(e))
        except Exception as e:
            logger.error(f"Failed to update document status {document_id}: {e}")
            raise HTTPException(status_code=500, detail="Failed to update document status")
    
    def get_health_status(self) -> Dict[str, Any]:
        """Health check and service statistics"""
        try:
            stats = self.document_service.get_stats()
            return {
                "status": "healthy",
                "message": "Document service is running",
                "statistics": stats
            }
        except Exception as e:
            logger.error(f"Failed to get document service health: {e}")
            return {
                "status": "unhealthy",
                "error": str(e),
                "message": "Document service is not operational"
            } 