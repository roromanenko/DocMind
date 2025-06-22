"""
Chat repository for database operations
"""
import logging
import uuid
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import desc

from docmind.models.database import ChatSession, Document
from docmind.models.schemas import ChatSessionResponse, ChatSessionWithDocuments
from docmind.core.exceptions import DocumentNotFoundError

logger = logging.getLogger(__name__)


class ChatRepository:
    """Repository for chat session database operations"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create_chat(self, name: str, description: Optional[str] = None) -> ChatSession:
        """Create new chat session in database"""
        try:
            chat = ChatSession(
                name=name,
                description=description
            )
            self.db.add(chat)
            self.db.commit()
            self.db.refresh(chat)
            logger.info(f"Chat session created: {name} (ID: {chat.id})")
            return chat
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to create chat session: {e}")
            raise
    
    def get_chat_by_id(self, chat_id: uuid.UUID) -> Optional[ChatSession]:
        """Get chat session by ID"""
        return self.db.query(ChatSession).filter(ChatSession.id == chat_id).first()
    
    def get_chats(self, skip: int = 0, limit: int = 20) -> List[ChatSession]:
        """Get chat sessions with pagination"""
        return (
            self.db.query(ChatSession)
            .order_by(desc(ChatSession.updated_at))
            .offset(skip)
            .limit(limit)
            .all()
        )
    
    def get_chat_count(self) -> int:
        """Get total number of chat sessions"""
        return self.db.query(ChatSession).count()
    
    def update_chat(self, chat_id: uuid.UUID, name: Optional[str] = None, description: Optional[str] = None) -> bool:
        """Update chat session"""
        try:
            chat = self.get_chat_by_id(chat_id)
            if not chat:
                return False
            
            if name is not None:
                setattr(chat, 'name', name)
            if description is not None:
                setattr(chat, 'description', description)
                
            self.db.commit()
            logger.info(f"Chat session updated: {chat_id}")
            return True
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to update chat session: {e}")
            return False
    
    def update_document_count(self, chat_id: uuid.UUID) -> bool:
        """Update document count for chat session"""
        try:
            chat = self.get_chat_by_id(chat_id)
            if not chat:
                return False
            
            # Count documents in this chat
            document_count = self.db.query(Document).filter(Document.chat_id == chat_id).count()
            setattr(chat, 'document_count', document_count)
            
            self.db.commit()
            return True
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to update document count for chat {chat_id}: {e}")
            return False
    
    def delete_chat(self, chat_id: uuid.UUID) -> bool:
        """Delete chat session from database (cascade deletes documents)"""
        try:
            chat = self.get_chat_by_id(chat_id)
            if not chat:
                return False
            
            self.db.delete(chat)
            self.db.commit()
            logger.info(f"Chat session deleted: {chat_id}")
            return True
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to delete chat session: {e}")
            return False
    
    def get_chat_with_documents(self, chat_id: uuid.UUID) -> Optional[ChatSession]:
        """Get chat session with its documents"""
        return (
            self.db.query(ChatSession)
            .filter(ChatSession.id == chat_id)
            .first()
        )
    
    def get_stats(self) -> Dict[str, Any]:
        """Get chat statistics"""
        total_chats = self.get_chat_count()
        
        # Get chat with most documents
        chat_with_most_docs = (
            self.db.query(ChatSession)
            .order_by(desc(ChatSession.document_count))
            .first()
        )
        
        # Average documents per chat
        avg_docs_per_chat = 0
        if total_chats > 0:
            total_docs = self.db.query(Document).count()
            avg_docs_per_chat = round(total_docs / total_chats, 2)
        
        return {
            "total_chats": total_chats,
            "average_documents_per_chat": avg_docs_per_chat,
            "max_documents_in_chat": chat_with_most_docs.document_count if chat_with_most_docs else 0
        } 