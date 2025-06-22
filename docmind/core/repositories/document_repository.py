"""
Document repository for database operations
"""
import logging
import uuid
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import desc

from docmind.models.database import Document, DocumentStatusEnum, get_db
from docmind.models.schemas import DocumentResponse
from docmind.core.exceptions import DocumentNotFoundError

logger = logging.getLogger(__name__)


class DocumentRepository:
    """Repository for document database operations"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create_document(self, document_data: Dict[str, Any]) -> Document:
        """Create new document in database"""
        try:
            db_document = Document(**document_data)
            self.db.add(db_document)
            self.db.commit()
            self.db.refresh(db_document)
            logger.info(f"Document created in database: {document_data['filename']} (ID: {document_data['id']})")
            return db_document
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to create document in database: {e}")
            raise
    
    def get_document_by_id(self, document_id: uuid.UUID) -> Optional[Document]:
        """Get document by ID"""
        return self.db.query(Document).filter(Document.id == document_id).first()
    
    def get_documents(self, chat_id: Optional[uuid.UUID] = None, skip: int = 0, limit: int = 20) -> List[Document]:
        """Get documents with pagination, optionally filtered by chat_id"""
        query = self.db.query(Document)
        if chat_id:
            query = query.filter(Document.chat_id == chat_id)
        return query.order_by(desc(Document.created_at)).offset(skip).limit(limit).all()
    
    def get_document_count(self) -> int:
        """Get total number of documents"""
        return self.db.query(Document).count()
    
    def update_document_status(self, document_id: uuid.UUID, status: DocumentStatusEnum) -> bool:
        """Update document status"""
        try:
            document = self.get_document_by_id(document_id)
            if not document:
                return False
            
            setattr(document, 'status', status)
            self.db.commit()
            logger.info(f"Document status updated: {document_id} -> {status}")
            return True
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to update document status: {e}")
            return False
    
    def update_document_chunk_count(self, document_id: uuid.UUID, chunk_count: int) -> bool:
        """Update document chunk count"""
        try:
            document = self.get_document_by_id(document_id)
            if not document:
                return False
            
            setattr(document, 'chunk_count', chunk_count)
            self.db.commit()
            return True
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to update document chunk count: {e}")
            return False
    
    def update_document_vectorized(self, document_id: uuid.UUID, vectorized: bool) -> bool:
        """Update document vectorized status"""
        try:
            document = self.get_document_by_id(document_id)
            if not document:
                return False
            
            setattr(document, 'vectorized', vectorized)
            self.db.commit()
            return True
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to update document vectorized status: {e}")
            return False
    
    def delete_document(self, document_id: uuid.UUID) -> bool:
        """Delete document from database"""
        try:
            document = self.get_document_by_id(document_id)
            if not document:
                return False
            
            self.db.delete(document)
            self.db.commit()
            logger.info(f"Document deleted from database: {document_id}")
            return True
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to delete document from database: {e}")
            return False
    
    def get_documents_by_status(self, status: DocumentStatusEnum) -> List[Document]:
        """Get documents by status"""
        return self.db.query(Document).filter(Document.status == status).all()
    
    def get_documents_by_format(self, file_extension: str) -> List[Document]:
        """Get documents by file format"""
        return self.db.query(Document).filter(Document.filename.like(f"%{file_extension}")).all()
    
    def get_stats(self) -> Dict[str, Any]:
        """Get document statistics"""
        total_docs = self.get_document_count()
        
        # Status distribution
        status_counts = {}
        for status in DocumentStatusEnum:
            count = self.db.query(Document).filter(Document.status == status).count()
            status_counts[status.value] = count
        
        # Format distribution and total size
        format_counts = {}
        documents = self.db.query(Document).all()
        total_size = 0
        for doc in documents:
            ext = str(doc.filename).split('.')[-1].lower() if '.' in str(doc.filename) else 'unknown'
            format_counts[f'.{ext}'] = format_counts.get(f'.{ext}', 0) + 1
            total_size += getattr(doc, 'file_size', 0)  # Get actual value, not Column object
        
        return {
            "total_documents": total_docs,
            "status_distribution": status_counts,
            "format_distribution": format_counts,
            "total_size_bytes": total_size,
            "total_size_mb": round(total_size / (1024 * 1024), 2)
        } 