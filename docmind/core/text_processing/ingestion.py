"""
Document ingestion and processing functionality
Handles file upload, validation, text extraction, and document management
"""
import logging
import os
import shutil
import uuid
from typing import Dict, Any, Optional, List, Tuple, Union
from datetime import datetime, timezone
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

from sqlalchemy.orm import Session
from docmind.models.database import DocumentStatusEnum, DocumentModel
from docmind.models.schemas import DocumentResponse
from docmind.config.settings import settings
from docmind.core.exceptions import (
    DocumentValidationError, 
    DocumentNotFoundError, 
    TextExtractionError,
    FileStorageError
)
from docmind.core.repositories.document_repository import DocumentRepository
from docmind.core.text_processing.chunking import TextChunker
from docmind.core.text_processing.cleaning import TextCleaner

logger = logging.getLogger(__name__)


class DocumentIngestionService:
    """
    Service for document ingestion, processing, and management
    Handles file validation, text extraction, and document storage
    """
    
    def __init__(self, db: Session):
        self.db = db
        self.supported_extensions = {'.pdf', '.docx', '.txt', '.md'}
        self.max_file_size = settings.max_file_size
        
        # MIME type mapping
        self.mime_types = {
            '.pdf': 'application/pdf',
            '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            '.txt': 'text/plain',
            '.md': 'text/markdown'
        }
        
        # Initialize services
        self.repository = DocumentRepository(db)
        self.text_cleaner = TextCleaner()
        self.chunker = TextChunker(text_cleaner=self.text_cleaner)
        
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
    
    def _get_file_path(self, document_id: uuid.UUID, filename: str) -> str:
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
            Extracted text content (raw, not cleaned)
            
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
        
        document_id = uuid.uuid4()
        
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
        
        # Extract raw text content (no cleaning at this stage)
        raw_text_content = self.extract_text_from_file(file_path)
        
        # Clean text content
        cleaned_text_content = self.text_cleaner.clean_text(raw_text_content)
        
        if not cleaned_text_content.strip():
            logger.warning(f"No content after cleaning for file {filename}")
            # Still create document but with empty content
            cleaned_text_content = ""
        
        # Generate chunks from cleaned text
        chunks = self.chunker.split_text(cleaned_text_content, document_id, {
            "filename": filename,
            "content_type": content_type,
            "file_size": len(content)
        })
        
        # Create content preview from cleaned text
        content_preview = cleaned_text_content[:200] + "..." if len(cleaned_text_content) > 200 else cleaned_text_content
        
        # Create document metadata record
        document_data = {
            "id": document_id,
            "filename": filename,
            "file_size": len(content),
            "content_type": content_type,
            "status": DocumentStatusEnum.UPLOADED,
            "content_preview": content_preview,
            "file_path": file_path,
            "created_at": datetime.now(timezone.utc),
            "chunk_count": len(chunks),
            "vectorized": False
        }
        
        # Save to database
        try:
            db_document = self.repository.create_document(document_data)
            
            # Log processing statistics
            cleaning_stats = self.text_cleaner.get_cleaning_stats(raw_text_content, cleaned_text_content)
            logger.info(f"Документ обработан: {filename} (ID: {document_id}, "
                       f"размер: {len(content)} байт, чанков: {len(chunks)}, "
                       f"очистка: {cleaning_stats['reduction_percent']}% сокращение)")
            
            return DocumentResponse(**DocumentModel.from_orm(db_document).dict())
        except Exception as e:
            logger.error(f"Ошибка при сохранении документа в БД: {e}")
            raise
    
    def get_document(self, document_id: uuid.UUID) -> DocumentResponse:
        """Get document metadata by ID"""
        try:
            document = self.repository.get_document_by_id(document_id)
            if not document:
                raise DocumentNotFoundError(f"Document not found: {document_id}")
            
            return DocumentResponse(**DocumentModel.from_orm(document).dict())
        except Exception as e:
            logger.error(f"Ошибка при получении документа {document_id}: {e}")
            raise
    
    def get_document_text(self, document_id: uuid.UUID, cleaned: bool = True) -> str:
        """
        Get extracted text content of document
        
        Args:
            document_id: UUID of the document
            cleaned: Whether to return cleaned text (True) or raw text (False)
            
        Returns:
            Text content of the document
        """
        try:
            document = self.repository.get_document_by_id(document_id)
            if not document:
                raise DocumentNotFoundError(f"Document not found: {document_id}")
            
            file_path = str(document.file_path)
            if not file_path or not os.path.exists(file_path):
                raise FileStorageError(f"Document file not found: {file_path}")
            
            raw_text = self.extract_text_from_file(file_path)
            
            if cleaned:
                return self.text_cleaner.clean_text(raw_text)
            else:
                return raw_text
                
        except Exception as e:
            logger.error(f"Ошибка при получении текста документа {document_id}: {e}")
            raise
    
    def get_documents(self, skip: int = 0, limit: int = 20) -> List[DocumentResponse]:
        """Get list of documents with pagination"""
        try:
            documents = self.repository.get_documents(skip=skip, limit=limit)
            return [DocumentResponse(**DocumentModel.from_orm(doc).dict()) for doc in documents]
        except Exception as e:
            logger.error(f"Ошибка при получении списка документов: {e}")
            raise
    
    def delete_document(self, document_id: uuid.UUID):
        """Delete document and its file"""
        try:
            document = self.repository.get_document_by_id(document_id)
            if not document:
                raise DocumentNotFoundError(f"Document not found: {document_id}")
            
            file_path = str(document.file_path)
            
            # Delete file from disk
            if file_path and os.path.exists(file_path):
                try:
                    os.remove(file_path)
                    logger.info(f"Файл удален с диска: {file_path}")
                except Exception as e:
                    logger.error(f"Ошибка при удалении файла {file_path}: {e}")
                    raise FileStorageError(f"Failed to delete file {file_path}", str(e))
            
            # Delete from database
            self.repository.delete_document(document_id)
            logger.info(f"Документ удален: {document.filename} (ID: {document_id})")
        except Exception as e:
            logger.error(f"Ошибка при удалении документа {document_id}: {e}")
            raise
    
    def update_document_status(self, document_id: uuid.UUID, status: DocumentStatusEnum):
        """Update document processing status"""
        try:
            success = self.repository.update_document_status(document_id, status)
            if not success:
                raise DocumentNotFoundError(f"Document not found: {document_id}")
            
            logger.info(f"Статус документа {document_id} обновлен на {status}")
        except Exception as e:
            logger.error(f"Ошибка при обновлении статуса документа {document_id}: {e}")
            raise
    
    def get_document_file_path(self, document_id: uuid.UUID) -> str:
        """Get file path for document"""
        try:
            document = self.repository.get_document_by_id(document_id)
            if not document:
                raise DocumentNotFoundError(f"Document not found: {document_id}")
            
            file_path = str(document.file_path)
            if not file_path or not os.path.exists(file_path):
                raise FileStorageError(f"Document file not found: {file_path}")
            
            return file_path
        except Exception as e:
            logger.error(f"Ошибка при получении пути файла документа {document_id}: {e}")
            raise
    
    def get_stats(self) -> Dict[str, Any]:
        """Get service statistics"""
        try:
            stats = self.repository.get_stats()
            stats.update({
                "supported_formats": list(self.supported_extensions),
                "max_file_size_mb": self.max_file_size // (1024 * 1024),
                "storage_path": settings.upload_dir
            })
            return stats
        except Exception as e:
            logger.error(f"Ошибка при получении статистики: {e}")
            raise

    def get_document_chunks(self, document_id: uuid.UUID) -> List[Dict[str, Any]]:
        """
        Get chunks for a specific document
        
        Args:
            document_id: UUID of the document
            
        Returns:
            List of chunk dictionaries
            
        Raises:
            DocumentNotFoundError: If document not found
        """
        try:
            document = self.repository.get_document_by_id(document_id)
            if not document:
                raise DocumentNotFoundError(f"Document not found: {document_id}")
            
            # Extract text and generate chunks on the fly
            text_content = self.get_document_text(document_id)
            chunks = self.chunker.split_text(text_content, document_id, {
                "filename": document.filename,
                "content_type": document.content_type,
                "file_size": document.file_size
            })
            
            return chunks
        except Exception as e:
            logger.error(f"Ошибка при получении чанков документа {document_id}: {e}")
            raise
