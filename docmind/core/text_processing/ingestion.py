"""
Document ingestion and processing functionality
Handles file upload, validation, text extraction, and document management
"""
import logging
import os
import shutil
from typing import Dict, Any, Optional, List, Tuple, Union
from uuid import uuid4
from datetime import datetime
import io
import mimetypes
from pathlib import Path

# For text extraction from different formats
try:
    import PyPDF2
    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False

try:
    from docx import Document as DocxDocument
    DOCX_AVAILABLE = True
except ImportError:
    DOCX_AVAILABLE = False

from docmind.models.schemas import DocumentStatus, DocumentResponse
from docmind.config.settings import settings
from docmind.core.exceptions import (
    DocumentValidationError, 
    DocumentNotFoundError, 
    TextExtractionError,
    FileStorageError
)

logger = logging.getLogger(__name__)


class DocumentIngestionService:
    """
    Service for document ingestion, processing, and management
    Handles file validation, text extraction, and document storage
    """
    
    def __init__(self):
        # In-memory storage for metadata only
        self.documents: Dict[str, Dict[str, Any]] = {}
        self.supported_extensions = {'.pdf', '.docx', '.txt', '.md'}
        self.max_file_size = settings.max_file_size
        
        # MIME type mapping
        self.mime_types = {
            '.pdf': 'application/pdf',
            '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            '.txt': 'text/plain',
            '.md': 'text/markdown'
        }
        
        # Ensure storage directories exist
        self._ensure_storage_dirs()
    
    def _ensure_storage_dirs(self):
        """Ensure storage directories exist"""
        try:
            os.makedirs(settings.upload_dir, exist_ok=True)
            os.makedirs(settings.temp_dir, exist_ok=True)
            logger.info(f"Storage directories ensured: {settings.upload_dir}, {settings.temp_dir}")
        except Exception as e:
            logger.error(f"Failed to create storage directories: {e}")
            raise FileStorageError("Failed to create storage directories", str(e))
    
    def _get_file_path(self, document_id: str, filename: str) -> str:
        """Generate file path for storage"""
        file_extension = Path(filename).suffix.lower()
        return os.path.join(settings.upload_dir, f"{document_id}{file_extension}")
    
    def validate_file(self, filename: str, file_size: int):
        """
        Validate uploaded file for format and size
        
        Args:
            filename: Name of the uploaded file
            file_size: Size of the file in bytes
            
        Raises:
            DocumentValidationError: If validation fails
        """
        if not filename:
            raise DocumentValidationError("Имя файла не может быть пустым")
        
        # Check file extension
        file_path = Path(filename)
        file_extension = file_path.suffix.lower()
        
        if file_extension not in self.supported_extensions:
            supported = ', '.join(self.supported_extensions)
            raise DocumentValidationError(
                f"Неподдерживаемый формат файла. Поддерживаемые: {supported}"
            )
        
        # Check file size
        if file_size > self.max_file_size:
            max_size_mb = self.max_file_size // (1024 * 1024)
            raise DocumentValidationError(
                f"Файл слишком большой. Максимальный размер: {max_size_mb}MB"
            )
    
    def extract_text_from_file(self, file_path: str) -> str:
        """
        Extract text content from file based on its format
        
        Args:
            file_path: Path to the file
            
        Returns:
            Extracted text content
            
        Raises:
            TextExtractionError: If text extraction fails
        """
        file_extension = Path(file_path).suffix.lower()
        
        try:
            with open(file_path, 'rb') as f:
                content = f.read()
            
            if file_extension == '.txt':
                return self._extract_text_from_txt(content)
            elif file_extension == '.md':
                return self._extract_text_from_md(content)
            elif file_extension == '.pdf':
                return self._extract_text_from_pdf(content)
            elif file_extension == '.docx':
                return self._extract_text_from_docx(content)
            else:
                raise TextExtractionError(f"Unsupported file format: {file_extension}")
                
        except Exception as e:
            logger.error(f"Ошибка при извлечении текста из {file_path}: {e}")
            raise TextExtractionError(f"Failed to extract text from {file_path}", str(e))
    
    def _extract_text_from_txt(self, content: bytes) -> str:
        """Extract text from TXT file"""
        try:
            return content.decode('utf-8', errors='ignore')
        except UnicodeDecodeError:
            # Try other encodings
            for encoding in ['latin-1', 'cp1252', 'iso-8859-1']:
                try:
                    return content.decode(encoding, errors='ignore')
                except UnicodeDecodeError:
                    continue
            raise TextExtractionError("Cannot decode text content with any supported encoding")
    
    def _extract_text_from_md(self, content: bytes) -> str:
        """Extract text from Markdown file"""
        return self._extract_text_from_txt(content)  # Same as TXT for now
    
    def _extract_text_from_pdf(self, content: bytes) -> str:
        """Extract text from PDF file"""
        if not PDF_AVAILABLE:
            raise TextExtractionError("PDF processing not available (PyPDF2 not installed)")
        
        try:
            pdf_file = io.BytesIO(content)
            pdf_reader = PyPDF2.PdfReader(pdf_file)
            
            text_content = []
            for page_num, page in enumerate(pdf_reader.pages):
                try:
                    page_text = page.extract_text()
                    if page_text.strip():
                        text_content.append(f"--- Page {page_num + 1} ---\n{page_text}")
                except Exception as e:
                    logger.warning(f"Ошибка при извлечении текста со страницы {page_num + 1}: {e}")
            
            if not text_content:
                raise TextExtractionError("No text content found in PDF")
            
            return "\n\n".join(text_content)
            
        except Exception as e:
            logger.error(f"Ошибка при обработке PDF: {e}")
            raise TextExtractionError("Failed to process PDF", str(e))
    
    def _extract_text_from_docx(self, content: bytes) -> str:
        """Extract text from DOCX file"""
        if not DOCX_AVAILABLE:
            raise TextExtractionError("DOCX processing not available (python-docx not installed)")
        
        try:
            docx_file = io.BytesIO(content)
            doc = DocxDocument(docx_file)
            
            text_content = []
            for paragraph in doc.paragraphs:
                if paragraph.text.strip():
                    text_content.append(paragraph.text)
            
            if not text_content:
                raise TextExtractionError("No text content found in DOCX")
            
            return "\n".join(text_content)
            
        except Exception as e:
            logger.error(f"Ошибка при обработке DOCX: {e}")
            raise TextExtractionError("Failed to process DOCX", str(e))
    
    def process_document(self, filename: str, content: bytes, content_type: Optional[str] = None) -> DocumentResponse:
        """
        Process and store uploaded document
        
        Args:
            filename: Name of the uploaded file
            content: File content as bytes
            content_type: MIME type of the file (optional)
            
        Returns:
            DocumentResponse with document information
            
        Raises:
            DocumentValidationError: If file validation fails
            TextExtractionError: If text extraction fails
            FileStorageError: If file storage fails
        """
        # Validate file
        self.validate_file(filename, len(content))
        
        document_id = str(uuid4())
        
        # Determine content type if not provided
        if not content_type:
            file_extension = Path(filename).suffix.lower()
            content_type = self.mime_types.get(file_extension, 'application/octet-stream')
        
        # Save file to disk
        file_path = self._get_file_path(document_id, filename)
        try:
            with open(file_path, 'wb') as f:
                f.write(content)
        except Exception as e:
            logger.error(f"Ошибка при сохранении файла {filename}: {e}")
            raise FileStorageError(f"Failed to save file {filename}", str(e))
        
        # Extract text content
        text_content = self.extract_text_from_file(file_path)
        
        # Create content preview
        content_preview = text_content[:200] + "..." if len(text_content) > 200 else text_content
        
        # Create document metadata record
        document_data = {
            "id": document_id,
            "filename": filename,
            "file_size": len(content),
            "content_type": content_type,
            "status": DocumentStatus.UPLOADED,
            "content_preview": content_preview,
            "file_path": file_path,
            "created_at": datetime.now().isoformat(),
            "chunk_count": 0,
            "vectorized": False
        }
        
        self.documents[document_id] = document_data
        logger.info(f"Документ обработан: {filename} (ID: {document_id}, размер: {len(content)} байт)")
        
        return DocumentResponse(**{k: v for k, v in document_data.items() if k not in ['file_path']})
    
    def get_document(self, document_id: str) -> DocumentResponse:
        """Get document metadata by ID"""
        if document_id not in self.documents:
            raise DocumentNotFoundError(f"Document not found: {document_id}")
        
        doc_data = self.documents[document_id]
        return DocumentResponse(**{k: v for k, v in doc_data.items() if k not in ['file_path']})
    
    def get_document_text(self, document_id: str) -> str:
        """Get extracted text content of document"""
        if document_id not in self.documents:
            raise DocumentNotFoundError(f"Document not found: {document_id}")
        
        file_path = self.documents[document_id].get("file_path")
        if not file_path or not os.path.exists(file_path):
            raise FileStorageError(f"Document file not found: {file_path}")
        
        return self.extract_text_from_file(file_path)
    
    def get_documents(self, skip: int = 0, limit: int = 20) -> List[DocumentResponse]:
        """Get list of documents with pagination"""
        all_docs = list(self.documents.values())
        paginated_docs = all_docs[skip:skip + limit]
        
        return [
            DocumentResponse(**{k: v for k, v in doc.items() if k not in ['file_path']})
            for doc in paginated_docs
        ]
    
    def delete_document(self, document_id: str):
        """Delete document and its file"""
        if document_id not in self.documents:
            raise DocumentNotFoundError(f"Document not found: {document_id}")
        
        doc_data = self.documents[document_id]
        file_path = doc_data.get("file_path")
        
        # Delete file from disk
        if file_path and os.path.exists(file_path):
            try:
                os.remove(file_path)
                logger.info(f"Файл удален с диска: {file_path}")
            except Exception as e:
                logger.error(f"Ошибка при удалении файла {file_path}: {e}")
                raise FileStorageError(f"Failed to delete file {file_path}", str(e))
        
        # Remove from memory
        deleted_doc = self.documents.pop(document_id)
        logger.info(f"Документ удален: {deleted_doc['filename']} (ID: {document_id})")
    
    def update_document_status(self, document_id: str, status: DocumentStatus):
        """Update document processing status"""
        if document_id not in self.documents:
            raise DocumentNotFoundError(f"Document not found: {document_id}")
        
        self.documents[document_id]["status"] = status
        logger.info(f"Статус документа {document_id} обновлен на {status}")
    
    def get_document_file_path(self, document_id: str) -> str:
        """Get file path for document"""
        if document_id not in self.documents:
            raise DocumentNotFoundError(f"Document not found: {document_id}")
        
        file_path = self.documents[document_id].get("file_path")
        if not file_path or not os.path.exists(file_path):
            raise FileStorageError(f"Document file not found: {file_path}")
        
        return file_path
    
    def get_stats(self) -> Dict[str, Any]:
        """Get service statistics"""
        total_docs = len(self.documents)
        status_counts = {}
        format_counts = {}
        total_size = 0
        
        for doc in self.documents.values():
            # Status distribution
            status = doc["status"]
            status_counts[status] = status_counts.get(status, 0) + 1
            
            # Format distribution
            file_extension = Path(doc["filename"]).suffix.lower()
            format_counts[file_extension] = format_counts.get(file_extension, 0) + 1
            
            # Total size
            total_size += doc["file_size"]
        
        return {
            "total_documents": total_docs,
            "status_distribution": status_counts,
            "format_distribution": format_counts,
            "total_size_bytes": total_size,
            "total_size_mb": round(total_size / (1024 * 1024), 2),
            "supported_formats": list(self.supported_extensions),
            "max_file_size_mb": self.max_file_size // (1024 * 1024),
            "storage_path": settings.upload_dir
        }


# Singleton instance
ingestion_service = DocumentIngestionService()
