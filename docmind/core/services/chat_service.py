"""
Chat service for managing chat sessions and their documents
"""
import logging
import uuid
import shutil
import os
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session

from docmind.config.settings import settings
from docmind.core.repositories.chat_repository import ChatRepository
from docmind.core.repositories.document_repository import DocumentRepository
from docmind.core.vector_store.qdrant_store import async_vector_store
from docmind.models.schemas import ChatSessionResponse, ChatSessionCreate, ChatSessionUpdate, ChatSessionWithDocuments, DocumentResponse
from docmind.models.database import ChatSessionModel
from docmind.core.exceptions import DocumentNotFoundError

logger = logging.getLogger(__name__)


class ChatService:
    """Service for chat session management"""
    
    def __init__(self, db: Session):
        self.db = db
        self.chat_repository = ChatRepository(db)
        self.document_repository = DocumentRepository(db)
    
    def create_chat(self, chat_data: ChatSessionCreate) -> ChatSessionResponse:
        """Create a new chat session"""
        try:
            chat = self.chat_repository.create_chat(
                name=chat_data.name,
                description=chat_data.description
            )
            
            # Create directory for this chat's documents
            chat_dir = self._get_chat_directory(str(chat.id))
            os.makedirs(chat_dir, exist_ok=True)
            
            logger.info(f"Created chat session: {chat.id} with directory: {chat_dir}")
            return ChatSessionResponse(**ChatSessionModel.from_orm(chat).dict())
            
        except Exception as e:
            logger.error(f"Failed to create chat session: {e}")
            raise
    
    def get_chat(self, chat_id: uuid.UUID) -> ChatSessionResponse:
        """Get chat session by ID"""
        chat = self.chat_repository.get_chat_by_id(chat_id)
        if not chat:
            raise DocumentNotFoundError(f"Chat session not found: {chat_id}")
        
        return ChatSessionResponse(**ChatSessionModel.from_orm(chat).dict())
    
    def get_chats(self, skip: int = 0, limit: int = 20) -> List[ChatSessionResponse]:
        """Get list of chat sessions with pagination"""
        chats = self.chat_repository.get_chats(skip=skip, limit=limit)
        return [ChatSessionResponse(**ChatSessionModel.from_orm(chat).dict()) for chat in chats]
    
    def update_chat(self, chat_id: uuid.UUID, chat_data: ChatSessionUpdate) -> ChatSessionResponse:
        """Update chat session"""
        # Check if chat exists
        existing_chat = self.chat_repository.get_chat_by_id(chat_id)
        if not existing_chat:
            raise DocumentNotFoundError(f"Chat session not found: {chat_id}")
        
        # Update chat
        success = self.chat_repository.update_chat(
            chat_id=chat_id,
            name=chat_data.name,
            description=chat_data.description
        )
        
        if not success:
            raise Exception("Failed to update chat session")
        
        # Return updated chat
        return self.get_chat(chat_id)
    
    async def delete_chat(self, chat_id: uuid.UUID) -> bool:
        """Delete chat session and all associated data"""
        try:
            # Check if chat exists
            chat = self.chat_repository.get_chat_by_id(chat_id)
            if not chat:
                raise DocumentNotFoundError(f"Chat session not found: {chat_id}")
            
            # 1. Delete all vector embeddings for this chat
            try:
                await async_vector_store.delete_chat_chunks_async(str(chat_id))
                logger.info(f"Deleted vector embeddings for chat {chat_id}")
            except Exception as e:
                logger.error(f"Failed to delete vector embeddings for chat {chat_id}: {e}")
                # Continue with deletion even if vector cleanup fails
            
            # 2. Delete chat directory and all files
            chat_dir = self._get_chat_directory(str(chat_id))
            if os.path.exists(chat_dir):
                try:
                    shutil.rmtree(chat_dir)
                    logger.info(f"Deleted chat directory: {chat_dir}")
                except Exception as e:
                    logger.error(f"Failed to delete chat directory {chat_dir}: {e}")
            
            # 3. Delete chat from database (cascade deletes documents)
            success = self.chat_repository.delete_chat(chat_id)
            if not success:
                raise Exception("Failed to delete chat from database")
            
            logger.info(f"Successfully deleted chat session: {chat_id}")
            return True
            
        except DocumentNotFoundError:
            raise
        except Exception as e:
            logger.error(f"Failed to delete chat session {chat_id}: {e}")
            raise
    
    def get_chat_with_documents(self, chat_id: uuid.UUID) -> ChatSessionWithDocuments:
        """Get chat session with its documents"""
        chat = self.chat_repository.get_chat_with_documents(chat_id)
        if not chat:
            raise DocumentNotFoundError(f"Chat session not found: {chat_id}")
        
        # Convert to response model
        chat_response = ChatSessionResponse(**ChatSessionModel.from_orm(chat).dict())
        documents = [DocumentResponse(**doc.__dict__) for doc in chat.documents]
        
        return ChatSessionWithDocuments(
            **chat_response.dict(),
            documents=documents
        )
    
    def update_document_count(self, chat_id: uuid.UUID) -> bool:
        """Update document count for chat session"""
        return self.chat_repository.update_document_count(chat_id)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get chat service statistics"""
        return self.chat_repository.get_stats()
    
    def _get_chat_directory(self, chat_id: str) -> str:
        """Get directory path for chat's documents"""
        return os.path.join(settings.upload_dir, chat_id) 