"""
Document ingestion and processing functionality
Handles file upload, validation, text extraction, and document management
"""
import logging
import os
import uuid
from typing import Dict, Any, Optional, List
from datetime import datetime, timezone
import io
from pathlib import Path
import asyncio

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
    FileStorageError,
    VectorStoreError
)
from docmind.core.repositories.document_repository import DocumentRepository
from docmind.core.text_processing.chunking import TextChunker
from docmind.core.text_processing.cleaning import TextCleaner
from docmind.core.vector_store.qdrant_store import async_vector_store

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
    
    def _get_file_path_with_chat(self, chat_id: uuid.UUID, document_id: uuid.UUID, filename: str) -> str:
        """Generate file path for storage organized by chat"""
        file_extension = Path(filename).suffix.lower()
        return os.path.join(settings.upload_dir, str(chat_id), f"{document_id}{file_extension}")
    
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
    
    async def process_and_vectorize_document(self, document_id: uuid.UUID):
        """
        Asynchronous background task to process and vectorize a document.
        
        Args:
            document_id: The ID of the document to process.
        """
        logger.info(f"Starting background processing for document {document_id}")
        doc = None
        try:
            # 1. Get document and update status to PROCESSING
            doc = self.repository.get_document_by_id(document_id)
            if not doc:
                raise DocumentNotFoundError(f"Document {document_id} not found for background processing.")
                
            self.repository.update_document_status(document_id, DocumentStatusEnum.PROCESSING)
            
            # 2. Extract and clean text
            logger.info(f"Extracting text from {str(doc.file_path)} for doc {document_id}")
            raw_text = self.extract_text_from_file(str(doc.file_path))
            cleaned_text = self.text_cleaner.clean_text(raw_text)
            
            if not cleaned_text.strip():
                logger.warning(f"No content after cleaning for doc {document_id}")
                self.repository.update_document_status(document_id, DocumentStatusEnum.ERROR)
                return

            # Update text content in the document record (assuming a method exists)
            # This part needs a new method in the repository
            # setattr(doc, 'raw_text_content', raw_text)
            # setattr(doc, 'cleaned_text_content', cleaned_text)
            
            # 3. Chunk the text
            logger.info(f"Chunking text for doc {document_id}")
            chunks = self.chunker.split_text(cleaned_text, document_id, chat_id=getattr(doc, 'chat_id', None), metadata={"filename": doc.filename})
            self.repository.update_document_chunk_count(document_id, len(chunks))
            logger.info(f"Created {len(chunks)} chunks for doc {document_id}")

            if not chunks:
                self.repository.update_document_status(document_id, DocumentStatusEnum.COMPLETED)
                logger.info(f"Document {document_id} has no chunks, marking as complete.")
                return

            # 4. Initialize vector store collection if needed
            try:
                # Check if collection exists, if not initialize it
                await async_vector_store.get_stats_async()
            except:
                logger.info("Initializing vector store collection...")
                await async_vector_store.initialize()
            
            # 5. Vectorize and upsert to Qdrant
            logger.info(f"Vectorizing chunks for doc {document_id}")
            try:
                await async_vector_store.add_chunks_async(chunks)
                self.repository.update_document_vectorized(document_id, True)
                logger.info(f"Successfully vectorized and stored chunks for doc {document_id}")
            except VectorStoreError as e:
                logger.error(f"Vector store error for doc {document_id}: {e}")
                self.repository.update_document_status(document_id, DocumentStatusEnum.ERROR)
                return
            
            # 6. Mark as COMPLETED
            self.repository.update_document_status(document_id, DocumentStatusEnum.COMPLETED)
            logger.info(f"Successfully processed document {document_id}")

        except Exception as e:
            logger.error(f"Unhandled error processing document {document_id}: {e}", exc_info=True)
            if document_id:
                try:
                    self.repository.update_document_status(document_id, DocumentStatusEnum.ERROR)
                except Exception as db_e:
                    logger.error(f"Failed to even update status to ERROR for doc {document_id}: {db_e}")
    
    def create_upload_record(self, chat_id: uuid.UUID, filename: str, content: bytes, content_type: Optional[str] = None) -> DocumentResponse:
        """
        Validates, saves file, and creates initial document record in DB.
        This is the first, synchronous part of the upload process.
        """
        # Validate file
        self.validate_file(filename, len(content))
        
        # Verify chat exists
        from docmind.core.repositories.chat_repository import ChatRepository
        chat_repo = ChatRepository(self.db)
        if not chat_repo.get_chat_by_id(chat_id):
            raise DocumentValidationError(f"Chat session {chat_id} not found")
        
        document_id = uuid.uuid4()
        
        # Determine content type if not provided
        if not content_type:
            file_extension = Path(filename).suffix.lower()
            content_type = self.mime_types.get(file_extension, 'application/octet-stream')
        
        # Save file to disk with chat organization
        file_path = self._get_file_path_with_chat(chat_id, document_id, filename)
        try:
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            with open(file_path, 'wb') as f:
                f.write(content)
        except Exception as e:
            logger.error(f"Ошибка при сохранении файла {filename}: {e}")
            raise FileStorageError(f"Failed to save file {filename}", str(e))
        
        # Create document record in the database with UPLOADED status
        document_data = {
            "id": document_id,
            "chat_id": chat_id,
            "filename": filename,
            "file_path": file_path,
            "file_size": len(content),
            "content_type": content_type or 'application/octet-stream',
            "status": DocumentStatusEnum.UPLOADED
        }
        db_document = self.repository.create_document(document_data)
        
        logger.info(f"Created initial record for document {db_document.id} with status UPLOADED")
        return DocumentResponse.from_orm(db_document)
    
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
    
    def get_documents(self, chat_id: Optional[uuid.UUID] = None, skip: int = 0, limit: int = 20) -> List[DocumentResponse]:
        """Get list of documents with pagination, optionally filtered by chat_id"""
        try:
            documents = self.repository.get_documents(chat_id=chat_id, skip=skip, limit=limit)
            return [DocumentResponse(**DocumentModel.from_orm(doc).dict()) for doc in documents]
        except Exception as e:
            logger.error(f"Ошибка при получении списка документов: {e}")
            raise
    
    async def delete_document(self, document_id: uuid.UUID):
        """Delete document, its file, and its vector chunks."""
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
                    # Non-critical error, log and continue
            
            # Delete chunks from vector store
            try:
                await async_vector_store.delete_document_chunks_async(str(document_id))
                logger.info(f"Chunks deleted from vector store for document: {document_id}")
            except Exception as e:
                logger.error(f"Error deleting chunks from vector store, continuing deletion: {e}")
            
            # Delete from database
            self.repository.delete_document(document_id)
            logger.info(f"Документ удален из БД: {document_id}")
            
        except DocumentNotFoundError:
            raise  # Re-raise to be caught by caller
        except Exception as e:
            logger.error(f"Ошибка при удалении документа {document_id}: {e}")
            raise
    
    def update_document_status(self, document_id: uuid.UUID, status: DocumentStatusEnum):
        """Update document processing status"""
        try:
            self.repository.update_document_status(document_id, status)
            logger.info(f"Статус документа обновлен: {document_id} -> {status}")
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
            logger.error(f"Ошибка при получении пути к файлу документа {document_id}: {e}")
            raise
    
    def get_stats(self) -> Dict[str, Any]:
        """Get service statistics"""
        try:
            stats = self.repository.get_stats()
            stats.update({
                "supported_formats": list(self.supported_extensions),
                "max_file_size_mb": self.max_file_size / (1024 * 1024)
            })
            return stats
        except Exception as e:
            logger.error(f"Ошибка при получении статистики: {e}")
            return {"error": str(e)}
    
    def get_document_chunks(self, document_id: uuid.UUID) -> List[Dict[str, Any]]:
        """Get chunks for a specific document"""
        try:
            # This would typically query the vector store for chunks
            # For now, return empty list as chunks are stored in vector store
            return []
        except Exception as e:
            logger.error(f"Ошибка при получении чанков документа {document_id}: {e}")
            return []
