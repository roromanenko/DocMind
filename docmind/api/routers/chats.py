"""
Chat sessions API router
"""
import logging
import uuid
from typing import List

from fastapi import APIRouter, Depends, status
from pydantic import BaseModel

from docmind.core.services.chat_service import ChatService
from docmind.api.dependencies import get_chat_service
from docmind.models.schemas import (
    ChatSessionCreate,
    ChatSessionUpdate,
    ChatSessionResponse,
    ChatSessionWithDocuments
)
from docmind.api.exceptions import handle_errors

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/chats", tags=["chats"])


@router.post(
    "/",
    response_model=ChatSessionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new chat session"
)
@handle_errors
async def create_chat(
    chat_data: ChatSessionCreate,
    service: ChatService = Depends(get_chat_service),
):
    """Create a new chat session for organizing documents and conversations."""
    return service.create_chat(chat_data)


@router.get(
    "/",
    response_model=List[ChatSessionResponse],
    summary="Get all chat sessions"
)
@handle_errors
async def get_chats(
    skip: int = 0,
    limit: int = 20,
    service: ChatService = Depends(get_chat_service),
):
    """Retrieve a paginated list of all chat sessions."""
    return service.get_chats(skip=skip, limit=limit)


@router.get(
    "/{chat_id}",
    response_model=ChatSessionResponse,
    summary="Get a specific chat session"
)
@handle_errors
async def get_chat(
    chat_id: uuid.UUID,
    service: ChatService = Depends(get_chat_service),
):
    """Retrieve detailed information about a specific chat session."""
    return service.get_chat(chat_id)


@router.get(
    "/{chat_id}/documents",
    response_model=ChatSessionWithDocuments,
    summary="Get chat session with its documents"
)
@handle_errors
async def get_chat_with_documents(
    chat_id: uuid.UUID,
    service: ChatService = Depends(get_chat_service),
):
    """Retrieve a chat session along with all its associated documents."""
    return service.get_chat_with_documents(chat_id)


@router.put(
    "/{chat_id}",
    response_model=ChatSessionResponse,
    summary="Update a chat session"
)
@handle_errors
async def update_chat(
    chat_id: uuid.UUID,
    chat_data: ChatSessionUpdate,
    service: ChatService = Depends(get_chat_service),
):
    """Update the name or description of an existing chat session."""
    return service.update_chat(chat_id, chat_data)


@router.delete(
    "/{chat_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a chat session"
)
@handle_errors
async def delete_chat(
    chat_id: uuid.UUID,
    service: ChatService = Depends(get_chat_service),
):
    """
    Delete a chat session and all its associated data.
    
    This will remove:
    - The chat session record
    - All documents in the chat
    - All files on disk
    - All vector embeddings
    """
    await service.delete_chat(chat_id) 