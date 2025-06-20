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


class AsyncVectorStore:
    """
    Async vector storage service using Qdrant
    """
    
    def __init__(self, embedding_service: Optional[EmbeddingService] = None):
        try:
            self.client = AsyncQdrantClient(
                url=settings.qdrant_url,
                api_key=settings.qdrant_api_key
            )
            self.collection_name = settings.qdrant_collection_name
            self.vector_size = settings.qdrant_vector_size
            self.embedding_service = embedding_service or EmbeddingService()
            
            # Ensure collection exists
            self._ensure_collection_task = None
        except Exception as e:
            logger.error(f"Failed to initialize async Qdrant client: {e}")
            raise VectorStoreError("Failed to initialize vector store", str(e))
    
    async def _ensure_collection(self):
        """Ensure Qdrant collection exists with correct dimensions"""
        try:
            collections = await self.client.get_collections()
            collection_names = [c.name for c in collections.collections]
            
            if self.collection_name in collection_names:
                # Check if existing collection has correct dimensions
                collection_info = await self.client.get_collection(self.collection_name)
                vectors_config = collection_info.config.params.vectors
                
                # Normalize vectors config to handle all cases
                if vectors_config is None:
                    existing_size = None
                elif isinstance(vectors_config, dict):
                    # Named vectors case - get first vector config
                    vparams = next(iter(vectors_config.values()))
                    existing_size = vparams.size
                else:
                    # Single VectorParams case
                    existing_size = vectors_config.size
                
                if existing_size != self.vector_size:
                    logger.warning(f"Collection {self.collection_name} has wrong dimensions: "
                                 f"expected {self.vector_size}, got {existing_size}")
                    logger.info(f"Recreating collection with correct dimensions...")
                    
                    # Delete old collection
                    await self.client.delete_collection(self.collection_name)
                    
                    # Create new collection with correct dimensions
                    await self.client.create_collection(
                        collection_name=self.collection_name,
                        vectors_config=VectorParams(
                            size=self.vector_size,
                            distance=Distance.COSINE
                        )
                    )
                    logger.info(f"Collection {self.collection_name} recreated with dimensions {self.vector_size}")
                else:
                    logger.info(f"Collection {self.collection_name} already exists with correct dimensions")
            else:
                # Create new collection
                await self.client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=VectorParams(
                        size=self.vector_size,
                        distance=Distance.COSINE
                    )
                )
                logger.info(f"Created new collection {self.collection_name} with dimensions {self.vector_size}")
                
        except Exception as e:
            logger.error(f"Error ensuring collection exists: {e}")
            raise VectorStoreError("Failed to ensure collection exists", str(e))
    
    async def add_chunks_async(self, chunks: List[Dict[str, Any]]) -> bool:
        """
        Add text chunks to vector store asynchronously
        
        Args:
            chunks: List of chunk dictionaries with text and metadata
            
        Returns:
            Success status
        """
        if not chunks:
            return True
        
        try:
            # Ensure collection exists
            await self._ensure_collection()
            
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
                        "document_id": chunk["document_id"],
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
            
            logger.info(f"Added {len(chunks)} chunks to vector store asynchronously")
            return True
            
        except Exception as e:
            logger.error(f"Error adding chunks to vector store: {e}")
            raise VectorStoreError("Failed to add chunks to vector store", str(e))
    
    async def search_async(self, query: str, limit: int = 10, score_threshold: float = 0.7) -> List[Dict[str, Any]]:
        """
        Search for similar chunks asynchronously
        
        Args:
            query: Search query
            limit: Maximum number of results
            score_threshold: Minimum similarity score
            
        Returns:
            List of search results
        """
        try:
            # Generate embedding for query asynchronously
            query_embedding = await self.embedding_service.get_embedding_async(query)
            
            # Search in Qdrant asynchronously
            search_result = await self.client.search(
                collection_name=self.collection_name,
                query_vector=query_embedding,
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
                        "metadata": {k: v for k, v in hit.payload.items() 
                                   if k not in ["text", "document_id"]}
                    })
            
            return results
            
        except Exception as e:
            logger.error(f"Error searching vector store: {e}")
            raise VectorStoreError("Failed to search vector store", str(e))
    
    async def delete_document_chunks_async(self, document_id: str) -> bool:
        """
        Delete all chunks for a specific document asynchronously
        
        Args:
            document_id: ID of the document to delete
            
        Returns:
            Success status
        """
        try:
            # Delete points by document_id filter asynchronously
            await self.client.delete(
                collection_name=self.collection_name,
                points_selector=Filter(
                    must=[
                        FieldCondition(
                            key="document_id",
                            match=MatchValue(value=document_id)
                        )
                    ]
                )
            )
            
            logger.info(f"Deleted chunks for document {document_id} from vector store")
            return True
            
        except Exception as e:
            logger.error(f"Error deleting document chunks from vector store: {e}")
            raise VectorStoreError("Failed to delete document chunks", str(e))
    
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


# Global instance
async_vector_store = AsyncVectorStore()
