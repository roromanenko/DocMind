"""
Migration script to add chat sessions support to DocMind.

This script:
1. Creates the new chat_sessions table
2. Adds chat_id column to documents table
3. Creates a default chat session for existing documents
4. Updates all existing documents to belong to the default chat

Usage:
    poetry run python scripts/migrate_to_chat_sessions.py
"""
import os
import sys
import uuid

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from sqlalchemy.orm import Session
from docmind.models.database import SessionLocal, create_tables, ChatSession, Document
from docmind.core.services.chat_service import ChatService

def migrate_to_chat_sessions():
    """Perform the migration to add chat sessions support"""
    print("Starting migration to chat sessions...")
    
    # Create new tables
    print("Creating new database tables...")
    create_tables()
    print("✅ Database tables created/updated")
    
    # Get database session
    db = SessionLocal()
    chat_service = ChatService(db)
    
    try:
        # Check if we already have chat sessions
        existing_chats = db.query(ChatSession).count()
        if existing_chats > 0:
            print(f"Found {existing_chats} existing chat sessions. Migration may have already been run.")
            return
        
        # Check for documents without chat_id
        orphaned_docs = db.query(Document).filter(Document.chat_id.is_(None)).all()
        
        if orphaned_docs:
            print(f"Found {len(orphaned_docs)} documents without chat sessions.")
            
            # Create a default chat session
            from docmind.models.schemas import ChatSessionCreate
            default_chat_data = ChatSessionCreate(
                name="Default Chat",
                description="Default chat session for migrated documents"
            )
            
            default_chat = chat_service.create_chat(default_chat_data)
            print(f"✅ Created default chat session: {default_chat.id}")
            
            # Assign all orphaned documents to the default chat
            for doc in orphaned_docs:
                setattr(doc, 'chat_id', default_chat.id)
            
            # Update document count for the default chat
            chat_service.update_document_count(default_chat.id)
            
            db.commit()
            print(f"✅ Assigned {len(orphaned_docs)} documents to default chat session")
        else:
            print("No orphaned documents found.")
        
        print("✅ Migration completed successfully!")
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        db.rollback()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    migrate_to_chat_sessions() 