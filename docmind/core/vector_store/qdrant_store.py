"""
Async vector storage functionality using Qdrant
"""
import logging
from typing import List, Dict, Any, Optional
from qdrant_client import AsyncQdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct, Filter, FieldCondition, MatchValue

from docmind.config.settings import settings
from docmind.core.services.embedding_service import EmbeddingService
from docmind.core.exceptions import VectorStoreError

logger = logging.getLogger(__name__)


class AsyncQdrantVectorStore:
    """
    Improved Async vector storage service using Qdrant with proper index handling
    """
    
    def __init__(self, url: str, api_key: str, collection_name: str, vector_size: int):
        try:
            self.client = AsyncQdrantClient(url=url, api_key=api_key)
            self.collection_name = collection_name
            self.vector_size = vector_size
            self.embedding_service = EmbeddingService()
            logger.info(f"Initialized AsyncQdrantVectorStore for collection: {collection_name}")
        except Exception as e:
            logger.error(f"Failed to initialize Qdrant client: {e}")
            raise VectorStoreError("Failed to initialize vector store", str(e))
    
    async def initialize(self):
        """Initialize collection with proper configuration"""
        try:
            # Delete existing collection if it exists
            try:
                await self.client.delete_collection(self.collection_name)
                logger.info(f"Deleted existing collection: {self.collection_name}")
            except:
                logger.info(f"No existing collection to delete: {self.collection_name}")
            
            # Create new collection
            await self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config=VectorParams(
                    size=self.vector_size,
                    distance=Distance.COSINE
                )
            )
            logger.info(f"Created collection: {self.collection_name}")
            
            # Wait a moment for collection to be ready
            import asyncio
            await asyncio.sleep(1)
            
            # Create payload indexes - we'll create them when first data is added
            logger.info("Collection initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize collection: {e}")
            raise VectorStoreError("Failed to initialize collection", str(e))
    
    async def _ensure_indexes(self):
        """Ensure indexes exist for filtering - only called after data is added"""
        try:
            # Try to create chat_id index - this will only work after data exists
            try:
                await self.client.create_payload_index(
                    collection_name=self.collection_name,
                    field_name="chat_id"
                )
                logger.info("Created chat_id index")
            except Exception as e:
                # Index might already exist or not needed yet
                logger.debug(f"chat_id index creation: {e}")
            
            try:
                await self.client.create_payload_index(
                    collection_name=self.collection_name,
                    field_name="document_id"
                )
                logger.info("Created document_id index")
            except Exception as e:
                # Index might already exist or not needed yet
                logger.debug(f"document_id index creation: {e}")
                
        except Exception as e:
            logger.warning(f"Index creation warning: {e}")
    
    async def add_chunks_async(self, chunks: List[Dict[str, Any]]) -> bool:
        """Add text chunks to vector store asynchronously"""
        if not chunks:
            return True
        
        try:
            # Generate embeddings for all chunks asynchronously
            texts = [chunk["text"] for chunk in chunks]
            embeddings = await self.embedding_service.get_embeddings_async(texts)
            
            # Prepare points for Qdrant
            points = []
            for i, chunk in enumerate(chunks):
                point = PointStruct(
                    id=chunk["id"],
                    vector=embeddings[i],
                    payload={
                        "text": chunk["text"],
                        "document_id": str(chunk["document_id"]),  # Ensure string
                        "chat_id": str(chunk.get("chat_id", "")),  # Ensure string
                        "start_position": chunk["start_position"],
                        "end_position": chunk["end_position"],
                        "length": chunk["length"],
                        **chunk.get("metadata", {})
                    }
                )
                points.append(point)
            
            # Insert points into Qdrant asynchronously
            await self.client.upsert(
                collection_name=self.collection_name,
                points=points
            )
            
            # Try to ensure indexes after adding data
            await self._ensure_indexes()
            
            logger.info(f"Added {len(chunks)} chunks to vector store")
            return True
            
        except Exception as e:
            logger.error(f"Error adding chunks to vector store: {e}")
            raise VectorStoreError("Failed to add chunks to vector store", str(e))
    
    async def search_async(self, query: str, chat_id: Optional[str] = None, limit: int = 10, score_threshold: float = 0.7) -> List[Dict[str, Any]]:
        """Search for similar chunks asynchronously"""
        try:
            # Generate embedding for query asynchronously
            query_embedding = await self.embedding_service.get_embedding_async(query)
            
            # Prepare filter for chat_id if provided
            query_filter = None
            if chat_id:
                query_filter = Filter(
                    must=[
                        FieldCondition(
                            key="chat_id",
                            match=MatchValue(value=str(chat_id))  # Ensure string
                        )
                    ]
                )
            
            # Search in Qdrant asynchronously
            search_result = await self.client.search(
                collection_name=self.collection_name,
                query_vector=query_embedding,
                query_filter=query_filter,
                limit=limit,
                score_threshold=score_threshold
            )
            
            # Format results
            results = []
            for hit in search_result:
                if hit.payload:
                    results.append({
                        "id": hit.id,
                        "score": hit.score,
                        "text": hit.payload.get("text", ""),
                        "document_id": hit.payload.get("document_id", ""),
                        "chat_id": hit.payload.get("chat_id", ""),
                        "metadata": {k: v for k, v in hit.payload.items() 
                                   if k not in ["text", "document_id", "chat_id"]}
                    })
            
            return results
            
        except Exception as e:
            logger.error(f"Error searching vector store: {e}")
            # If search fails due to index issues, try without filter
            if chat_id and "index" in str(e).lower():
                logger.warning("Retrying search without chat_id filter due to index issue")
                return await self.search_async(query, chat_id=None, limit=limit, score_threshold=score_threshold)
            raise VectorStoreError("Failed to search vector store", str(e))
    
    async def delete_document_chunks_async(self, document_id: str) -> bool:
        """Delete all chunks for a specific document asynchronously"""
        try:
            # Use the correct filter-based deletion approach
            from qdrant_client.models import FilterSelector
            
            filter_selector = FilterSelector(
                filter=Filter(
                    must=[
                        FieldCondition(
                            key="document_id",
                            match=MatchValue(value=str(document_id))
                        )
                    ]
                )
            )
            
            # Delete points using filter
            result = await self.client.delete(
                collection_name=self.collection_name,
                points_selector=filter_selector
            )
            
            logger.info(f"Deleted chunks for document {document_id} from vector store. Operation ID: {result.operation_id if result else 'N/A'}")
            return True
            
        except Exception as e:
            logger.error(f"Error deleting document chunks from vector store: {e}")
            raise VectorStoreError("Failed to delete document chunks", str(e))
    
    async def delete_chat_chunks_async(self, chat_id: str) -> bool:
        """Delete all chunks for a specific chat asynchronously"""
        try:
            # Use the correct filter-based deletion approach
            from qdrant_client.models import FilterSelector
            
            filter_selector = FilterSelector(
                filter=Filter(
                    must=[
                        FieldCondition(
                            key="chat_id",
                            match=MatchValue(value=str(chat_id))
                        )
                    ]
                )
            )
            
            # Delete points using filter
            result = await self.client.delete(
                collection_name=self.collection_name,
                points_selector=filter_selector
            )
            
            logger.info(f"Deleted chunks for chat {chat_id} from vector store. Operation ID: {result.operation_id if result else 'N/A'}")
            return True
            
        except Exception as e:
            logger.error(f"Error deleting chat chunks from vector store: {e}")
            raise VectorStoreError("Failed to delete chat chunks", str(e))
    
    async def get_stats_async(self) -> Dict[str, Any]:
        """Get vector store statistics asynchronously"""
        try:
            collection_info = await self.client.get_collection(self.collection_name)
            return {
                "status": "connected",
                "collection_name": self.collection_name,
                "vector_size": self.vector_size,
                "points_count": collection_info.points_count,
                "segments_count": collection_info.segments_count
            }
        except Exception as e:
            logger.error(f"Error getting vector store stats: {e}")
            return {
                "status": "error",
                "error": str(e)
            }
    
    async def close(self):
        """Close the client connection"""
        try:
            await self.client.close()
        except:
            pass


# Legacy class for backward compatibility
class AsyncVectorStore(AsyncQdrantVectorStore):
    """Legacy class - use AsyncQdrantVectorStore instead"""
    
    def __init__(self, embedding_service: Optional[EmbeddingService] = None):
        super().__init__(
            url=settings.qdrant_url,
            api_key=settings.qdrant_api_key,
            collection_name=settings.qdrant_collection_name,
            vector_size=settings.qdrant_vector_size
        )
        if embedding_service:
            self.embedding_service = embedding_service


# Global instance
async_vector_store = AsyncVectorStore()
