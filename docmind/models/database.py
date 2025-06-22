"""
Database models for DocMind application
"""
import uuid
import enum
from sqlalchemy import Column, String, Integer, DateTime, Boolean, Text, create_engine, Index, CheckConstraint, Enum, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime, timezone
from typing import Optional

from docmind.config.settings import settings

Base = declarative_base()


class DocumentStatusEnum(enum.Enum):
    """Document processing status enum"""
    UPLOADED = "uploaded"
    PROCESSING = "processing"
    COMPLETED = "completed"
    ERROR = "error"


class ChatSession(Base):
    """Chat session model for grouping documents and conversations"""
    __tablename__ = "chat_sessions"
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    
    # Chat metadata
    name = Column(String(255), nullable=False, default="New Chat")
    description = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False, index=True)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)
    
    # Statistics
    document_count = Column(Integer, default=0, nullable=False)
    
    # Relationships
    documents = relationship("Document", back_populates="chat_session", cascade="all, delete-orphan")
    
    # Table constraints and indexes
    __table_args__ = (
        Index('idx_chat_sessions_created', 'created_at'),
        CheckConstraint('document_count >= 0', name='check_document_count_positive'),
    )


class Document(Base):
    """Document model for database storage"""
    __tablename__ = "documents"
    
    # Primary key with UUID
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    
    # Foreign key to chat session
    chat_id = Column(UUID(as_uuid=True), ForeignKey('chat_sessions.id', ondelete='CASCADE'), nullable=False, index=True)
    
    # Document metadata
    filename = Column(String(255), nullable=False, index=True)
    file_size = Column(Integer, nullable=False)
    content_type = Column(String(100), nullable=False)
    
    # Status with enum
    status = Column(Enum(DocumentStatusEnum, name='document_status_enum'), nullable=False, default=DocumentStatusEnum.UPLOADED, index=True)
    
    # Content
    content_preview = Column(Text, nullable=True)
    file_path = Column(String(500), nullable=False)
    
    # Timestamps with timezone
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False, index=True)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)
    
    # Processing metadata
    chunk_count = Column(Integer, default=0, nullable=False)
    vectorized = Column(Boolean, default=False, nullable=False)
    
    # Relationships
    chat_session = relationship("ChatSession", back_populates="documents")
    
    # Table constraints and indexes
    __table_args__ = (
        Index('idx_documents_chat_status', 'chat_id', 'status'),
        Index('idx_documents_chat_created', 'chat_id', 'created_at'),
        Index('idx_documents_vectorized', 'vectorized'),
        CheckConstraint('file_size > 0', name='check_file_size_positive'),
    )


# Pydantic model for automatic serialization
from pydantic import BaseModel, ConfigDict

class ChatSessionModel(BaseModel):
    """Pydantic model for ChatSession serialization"""
    id: uuid.UUID
    name: str
    description: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    document_count: int
    
    model_config = ConfigDict(from_attributes=True)

class DocumentModel(BaseModel):
    """Pydantic model for Document serialization"""
    id: uuid.UUID
    chat_id: uuid.UUID
    filename: str
    file_size: int
    content_type: str
    status: DocumentStatusEnum
    content_preview: Optional[str] = None
    file_path: str
    created_at: datetime
    updated_at: datetime
    chunk_count: int
    vectorized: bool
    
    model_config = ConfigDict(from_attributes=True)


# Database setup
engine = create_engine(
    settings.database_url,
    echo=settings.database_echo,
    pool_pre_ping=True
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    """Get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def create_tables():
    """Create all tables"""
    Base.metadata.create_all(bind=engine)


def drop_tables():
    """Drop all tables"""
    Base.metadata.drop_all(bind=engine) 