"""
Documents API router using new core architecture
"""
from fastapi import APIRouter, UploadFile, File, HTTPException
from typing import List, Dict, Any
import logging
from uuid import uuid4
from datetime import datetime

from docmind.models.schemas import (
    DocumentResponse, 
    UploadResponse, 
    DocumentStatus
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/documents", tags=["documents"])

# In-memory storage (temporary, will be replaced by proper services)
_documents: Dict[str, Dict[str, Any]] = {}
_supported_extensions = {'.pdf', '.docx', '.txt', '.md'}
_max_file_size = 50 * 1024 * 1024  # 50MB


def _validate_file(filename: str, file_size: int) -> tuple[bool, str]:
    """Validate uploaded file"""
    if not filename:
        return False, "Имя файла не может быть пустым"
    
    file_extension = '.' + filename.split('.')[-1].lower()
    if file_extension not in _supported_extensions:
        return False, f"Неподдерживаемый формат файла. Поддерживаемые: {', '.join(_supported_extensions)}"
    
    if file_size > _max_file_size:
        return False, f"Файл слишком большой. Максимальный размер: {_max_file_size // (1024*1024)}MB"
    
    return True, ""


def _create_document(filename: str, content: bytes, content_type: str) -> DocumentResponse:
    """Create new document record"""
    document_id = str(uuid4())
    
    # Extract text preview for text files
    content_preview = ""
    if filename.endswith('.txt'):
        try:
            content_preview = content[:200].decode('utf-8', errors='ignore')
        except Exception:
            content_preview = "Cannot decode text"
    else:
        content_preview = f"Binary content ({content_type})"
    
    # Create document record
    document_data = {
        "id": document_id,
        "filename": filename,
        "file_size": len(content),
        "content_type": content_type,
        "status": DocumentStatus.UPLOADED,
        "content_preview": content_preview,
        "created_at": datetime.now().isoformat(),
        "content": content
    }
    
    _documents[document_id] = document_data
    logger.info(f"Документ создан: {filename} (ID: {document_id})")
    
    return DocumentResponse(**{k: v for k, v in document_data.items() if k != 'content'})


def _get_document(document_id: str) -> DocumentResponse | None:
    """Get document by ID"""
    if document_id not in _documents:
        return None
    
    doc_data = _documents[document_id]
    return DocumentResponse(**{k: v for k, v in doc_data.items() if k != 'content'})


def _get_documents(skip: int = 0, limit: int = 20) -> List[DocumentResponse]:
    """Get list of documents with pagination"""
    all_docs = list(_documents.values())
    paginated_docs = all_docs[skip:skip + limit]
    
    return [
        DocumentResponse(**{k: v for k, v in doc.items() if k != 'content'})
        for doc in paginated_docs
    ]


def _delete_document(document_id: str) -> bool:
    """Delete document"""
    if document_id not in _documents:
        return False
    
    deleted_doc = _documents.pop(document_id)
    logger.info(f"Документ удален: {deleted_doc['filename']} (ID: {document_id})")
    return True


def _get_stats() -> Dict[str, Any]:
    """Get service statistics"""
    total_docs = len(_documents)
    status_counts = {}
    
    for doc in _documents.values():
        status = doc["status"]
        status_counts[status] = status_counts.get(status, 0) + 1
    
    total_size = sum(doc["file_size"] for doc in _documents.values())
    
    return {
        "total_documents": total_docs,
        "status_distribution": status_counts,
        "total_size_bytes": total_size,
        "total_size_mb": round(total_size / (1024 * 1024), 2)
    }


@router.post("/upload", response_model=UploadResponse)
async def upload_document(file: UploadFile = File(...)):
    """
    Upload a document
    """
    # Validate file
    is_valid, error_message = _validate_file(
        file.filename or "", 
        file.size or 0
    )
    
    if not is_valid:
        raise HTTPException(status_code=400, detail=error_message)
    
    # Read file content
    content = await file.read()
    
    # Create document
    document = _create_document(
        filename=file.filename or "unknown",
        content=content,
        content_type=file.content_type or "application/octet-stream"
    )
    
    return UploadResponse(
        message="Документ успешно загружен",
        document_id=document.id,
        filename=document.filename,
        file_size=document.file_size,
        status=document.status
    )


@router.get("/", response_model=List[DocumentResponse])
async def get_documents(skip: int = 0, limit: int = 20):
    """
    Get list of documents with pagination
    """
    documents = _get_documents(skip=skip, limit=limit)
    return documents


@router.get("/{document_id}", response_model=DocumentResponse)
async def get_document(document_id: str):
    """
    Get specific document by ID
    """
    document = _get_document(document_id)
    
    if not document:
        raise HTTPException(status_code=404, detail="Документ не найден")
    
    return document


@router.delete("/{document_id}")
async def delete_document(document_id: str):
    """
    Delete document
    """
    success = _delete_document(document_id)
    
    if not success:
        raise HTTPException(status_code=404, detail="Документ не найден")
    
    return {"message": "Документ успешно удален"}


@router.get("/status/health")
async def documents_health():
    """
    Health check and service statistics
    """
    try:
        stats = _get_stats()
        
        return {
            "status": "healthy",
            "message": "Document service is running",
            "statistics": stats
        }
        
    except Exception as e:
        return {
            "status": "error",
            "message": f"Service error: {str(e)}",
            "statistics": {}
        }