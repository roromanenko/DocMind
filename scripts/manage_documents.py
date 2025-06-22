"""
A command-line script to manage documents in the DocMind system.

Usage:
    - List all documents:
        poetry run python scripts/manage_documents.py --action list

    - Delete a document:
        poetry run python scripts/manage_documents.py --action delete --id <DOCUMENT_ID>

    - Delete a document interactively:
        poetry run python scripts/manage_documents.py --action delete
"""
import os
import sys
import argparse
import uuid
import asyncio
from datetime import datetime, timezone

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from sqlalchemy.orm import Session
from docmind.models.database import SessionLocal
from docmind.core.services.document_service import DocumentIngestionService
from docmind.core.exceptions import DocumentNotFoundError

def get_document_service(db: Session) -> DocumentIngestionService:
    """Initializes and returns the document service."""
    return DocumentIngestionService(db)

async def list_documents(service: DocumentIngestionService):
    """Lists all documents in the database."""
    print("Fetching documents...")
    documents = service.get_documents(limit=1000)  # Get up to 1000 documents
    if not documents:
        print("No documents found.")
        return

    print(f"{'ID':<38}{'Filename':<50}{'Status':<12}{'Created At':<28}")
    print("-" * 130)
    
    # Sort documents, handling potential None in created_at
    sorted_docs = sorted(
        documents, 
        key=lambda d: d.created_at or datetime.min.replace(tzinfo=timezone.utc), 
        reverse=True
    )
    
    for doc in sorted_docs:
        created_at_str = doc.created_at.strftime('%Y-%m-%d %H:%M:%S') if doc.created_at else "N/A"
        print(f"{doc.id!s:<38}{doc.filename:<50}{doc.status.value:<12}{created_at_str:<28}")

async def delete_document(service: DocumentIngestionService, document_id: uuid.UUID):
    """Deletes a specific document."""
    try:
        print(f"Attempting to delete document {document_id}...")
        await service.delete_document(document_id)
        print(f"✅ Document {document_id} and its associated data have been successfully deleted.")
    except DocumentNotFoundError:
        print(f"❌ Error: Document with ID {document_id} not found.")
    except Exception as e:
        print(f"❌ An unexpected error occurred: {e}")

async def main():
    """Main function to parse arguments and execute actions."""
    parser = argparse.ArgumentParser(description="Manage DocMind documents.")
    parser.add_argument(
        '--action',
        type=str,
        choices=['list', 'delete'],
        required=True,
        help="The action to perform: 'list' or 'delete'."
    )
    parser.add_argument(
        '--id',
        type=uuid.UUID,
        help="The UUID of the document to delete."
    )

    args = parser.parse_args()
    db = SessionLocal()
    service = get_document_service(db)

    try:
        if args.action == 'list':
            await list_documents(service)
        elif args.action == 'delete':
            doc_id = args.id
            if not doc_id:
                await list_documents(service)
                try:
                    doc_id_str = input("\nEnter the ID of the document to delete: ")
                    doc_id = uuid.UUID(doc_id_str)
                except (ValueError, TypeError):
                    print("❌ Invalid UUID format. Aborting.")
                    return
            
            await delete_document(service, doc_id)

    finally:
        db.close()

if __name__ == "__main__":
    asyncio.run(main()) 