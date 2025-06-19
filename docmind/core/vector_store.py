"""
Vector storage functionality using Qdrant
"""
import logging
from typing import List, Dict, Any, Optional
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct, Filter, FieldCondition, MatchValue
import numpy as np

from docmind.config.settings import settings
from docmind.core.text_processing.embedding import get_embeddings
from docmind.core.exceptions import VectorStoreError

logger = logging.getLogger(__name__)


class VectorStore:
    """
    Vector storage service using Qdrant
    """
    
    def __init__(self):
        try:
            self.client = QdrantClient(
                url=settings.qdrant_url,
                api_key=settings.qdrant_api_key
            )
            self.collection_name = settings.qdrant_collection_name
            self.vector_size = settings.qdrant_vector_size
            
            # Ensure collection exists
            self._ensure_collection()
        except Exception as e:
            logger.error(f"Failed to initialize Qdrant client: {e}")
            raise VectorStoreError("Failed to initialize vector store", str(e))
    
    def _ensure_collection(self):
        """Ensure Qdrant collection exists"""
        try:
            collections = self.client.get_collections()
            collection_names = [c.name for c in collections.collections]
            
            if self.collection_name not in collection_names:
                self.client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=VectorParams(
                        size=self.vector_size,
                        distance=Distance.COSINE
                    )
                )
                logger.info(f"Создана коллекция Qdrant: {self.collection_name}")
            else:
                logger.info(f"Коллекция Qdrant уже существует: {self.collection_name}")
                
        except Exception as e:
            logger.error(f"Ошибка при инициализации Qdrant: {e}")
            raise VectorStoreError("Failed to ensure collection exists", str(e))
    
    def add_chunks(self, chunks: List[Dict[str, Any]]) -> bool:
        """
        Add text chunks to vector store
        
        Args:
            chunks: List of chunk dictionaries with text and metadata
            
        Returns:
            Success status
        """
        if not chunks:
            return True
        
        try:
            # Generate embeddings for all chunks
            texts = [chunk["text"] for chunk in chunks]
            embeddings = get_embeddings(texts)
            
            # Prepare points for Qdrant
            points = []
            for i, chunk in enumerate(chunks):
                point = PointStruct(
                    id=chunk["id"],
                    vector=embeddings[i].tolist(),
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
            
            # Insert points into Qdrant
            self.client.upsert(
                collection_name=self.collection_name,
                points=points
            )
            
            logger.info(f"Добавлено {len(chunks)} чанков в векторное хранилище")
            return True
            
        except Exception as e:
            logger.error(f"Ошибка при добавлении чанков в векторное хранилище: {e}")
            raise VectorStoreError("Failed to add chunks to vector store", str(e))
    
    def search(self, query: str, limit: int = 10, score_threshold: float = 0.7) -> List[Dict[str, Any]]:
        """
        Search for similar chunks
        
        Args:
            query: Search query
            limit: Maximum number of results
            score_threshold: Minimum similarity score
            
        Returns:
            List of search results
        """
        try:
            # Generate embedding for query
            query_embedding = get_embeddings([query])[0]
            
            # Search in Qdrant
            search_result = self.client.search(
                collection_name=self.collection_name,
                query_vector=query_embedding.tolist(),
                limit=limit,
                score_threshold=score_threshold
            )
            
            # Format results
            results = []
            for hit in search_result:
                if hit.payload:  # Check if payload exists
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
            logger.error(f"Ошибка при поиске в векторном хранилище: {e}")
            raise VectorStoreError("Failed to search vector store", str(e))
    
    def delete_document_chunks(self, document_id: str) -> bool:
        """
        Delete all chunks for a specific document
        
        Args:
            document_id: ID of the document to delete
            
        Returns:
            Success status
        """
        try:
            # Delete points by document_id filter
            self.client.delete(
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
            
            logger.info(f"Удалены чанки для документа: {document_id}")
            return True
            
        except Exception as e:
            logger.error(f"Ошибка при удалении чанков документа {document_id}: {e}")
            raise VectorStoreError(f"Failed to delete chunks for document {document_id}", str(e))
    
    def get_stats(self) -> Dict[str, Any]:
        """Get vector store statistics"""
        try:
            collection_info = self.client.get_collection(self.collection_name)
            return {
                "collection_name": self.collection_name,
                "vector_size": self.vector_size,
                "points_count": collection_info.points_count,
                "segments_count": collection_info.segments_count,
                "status": collection_info.status
            }
        except Exception as e:
            logger.error(f"Ошибка при получении статистики векторного хранилища: {e}")
            raise VectorStoreError("Failed to get vector store statistics", str(e))


# Global vector store instance
vector_store = VectorStore()
