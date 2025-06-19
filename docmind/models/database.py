"""
Database models for DocMind application
"""
from sqlalchemy import Column, String, Integer, DateTime, Boolean, Text, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
from typing import Optional

from docmind.config.settings import settings

Base = declarative_base()


class Document(Base):
    """Document model for database storage"""
    __tablename__ = "documents"
    
    id = Column(String(36), primary_key=True, index=True)
    filename = Column(String(255), nullable=False, index=True)
    file_size = Column(Integer, nullable=False)
    content_type = Column(String(100), nullable=False)
    status = Column(String(20), nullable=False, default="uploaded")
    content_preview = Column(Text, nullable=True)
    file_path = Column(String(500), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    chunk_count = Column(Integer, default=0, nullable=False)
    vectorized = Column(Boolean, default=False, nullable=False)
    
    def to_dict(self) -> dict:
        """Convert model to dictionary"""
        return {
            "id": self.id,
            "filename": self.filename,
            "file_size": self.file_size,
            "content_type": self.content_type,
            "status": self.status,
            "content_preview": self.content_preview,
            "created_at": getattr(self, 'created_at').isoformat() if getattr(self, 'created_at') else None,
            "chunk_count": self.chunk_count,
            "vectorized": self.vectorized
        }


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