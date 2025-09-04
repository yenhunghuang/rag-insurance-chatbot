"""Vector Store Service

Provides vector storage and retrieval using Pinecone with optimized
indexing and search capabilities for insurance document chunks.
"""

import logging
from typing import List, Dict, Any, Optional, Tuple
import time
import uuid
import numpy as np

import pinecone
from pinecone import Pinecone, Index

from ..config import get_config
from ..models import Document, DocumentMatch
from ..exceptions import RAGSystemError


logger = logging.getLogger(__name__)


class VectorStoreError(RAGSystemError):
    """Vector store operation errors."""
    pass


class PineconeVectorStore:
    """Pinecone-based vector storage and retrieval service."""
    
    def __init__(self):
        """Initialize Pinecone vector store."""
        self.config = get_config()
        self.pinecone_config = self.config.pinecone
        
        self._client: Optional[Pinecone] = None
        self._index: Optional[Index] = None
        
        logger.info(f"Initializing PineconeVectorStore for index: {self.pinecone_config.index_name}")
    
    @property
    def client(self) -> Pinecone:
        """Lazy loading of Pinecone client."""
        if self._client is None:
            try:
                self._client = Pinecone(api_key=self.pinecone_config.api_key)
                logger.info("Successfully connected to Pinecone")
            except Exception as e:
                raise VectorStoreError(f"Failed to connect to Pinecone: {e}")
        return self._client
    
    @property
    def index(self) -> Index:
        """Get or create the Pinecone index."""
        if self._index is None:
            try:
                # Check if index exists
                existing_indexes = self.client.list_indexes()
                index_names = [idx.name for idx in existing_indexes]
                
                if self.pinecone_config.index_name not in index_names:
                    logger.info(f"Creating new index: {self.pinecone_config.index_name}")
                    self._create_index()
                else:
                    logger.info(f"Using existing index: {self.pinecone_config.index_name}")
                
                self._index = self.client.Index(self.pinecone_config.index_name)
                
                # Wait for index to be ready
                self._wait_for_index_ready()
                
            except Exception as e:
                raise VectorStoreError(f"Failed to initialize index: {e}")
        
        return self._index
    
    def _create_index(self):
        """Create a new Pinecone index with specified configuration."""
        try:
            self.client.create_index(
                name=self.pinecone_config.index_name,
                dimension=self.pinecone_config.dimension,
                metric=self.pinecone_config.metric,
                spec=pinecone.ServerlessSpec(
                    cloud="aws",
                    region=self.pinecone_config.environment
                )
            )
            logger.info(f"Successfully created index: {self.pinecone_config.index_name}")
            
        except Exception as e:
            raise VectorStoreError(f"Failed to create index: {e}")
    
    def _wait_for_index_ready(self, max_wait: int = 60):
        """Wait for index to be ready for operations."""
        start_time = time.time()
        
        while time.time() - start_time < max_wait:
            try:
                stats = self.index.describe_index_stats()
                if stats:  # Index is responsive
                    logger.info("Index is ready for operations")
                    return
            except Exception:
                pass
            
            time.sleep(2)
        
        logger.warning("Index may not be fully ready, proceeding anyway")
    
    def add_documents(self, documents: List[Document]) -> List[str]:
        """Add documents to the vector store.
        
        Args:
            documents: List of Document objects with embeddings.
            
        Returns:
            List of document IDs that were successfully added.
            
        Raises:
            VectorStoreError: If document addition fails.
        """
        if not documents:
            return []
        
        try:
            vectors_to_upsert = []
            document_ids = []
            
            for doc in documents:
                if doc.embedding is None:
                    logger.warning(f"Skipping document without embedding: {doc.chunk_id}")
                    continue
                
                # Generate unique ID if not provided
                doc_id = doc.chunk_id or str(uuid.uuid4())
                document_ids.append(doc_id)
                
                # Prepare metadata (Pinecone has size limits)
                metadata = {
                    "content": doc.content[:1000],  # Truncate content for metadata
                    "source_file": doc.metadata.get("source_file", ""),
                    "clause_number": doc.metadata.get("clause_number", ""),
                    "clause_type": doc.metadata.get("clause_type", ""),
                    "chunk_index": doc.metadata.get("chunk_index", 0),
                    "char_start": doc.metadata.get("char_start", 0),
                    "char_end": doc.metadata.get("char_end", 0)
                }
                
                vector_data = {
                    "id": doc_id,
                    "values": doc.embedding.tolist(),
                    "metadata": metadata
                }
                
                vectors_to_upsert.append(vector_data)
            
            if not vectors_to_upsert:
                logger.warning("No valid documents with embeddings to add")
                return []
            
            # Upsert vectors in batches
            batch_size = 100  # Pinecone batch limit
            added_ids = []
            
            for i in range(0, len(vectors_to_upsert), batch_size):
                batch = vectors_to_upsert[i:i + batch_size]
                
                response = self.index.upsert(
                    vectors=batch,
                    namespace=self.pinecone_config.namespace
                )
                
                if response.get("upserted_count", 0) > 0:
                    batch_ids = [v["id"] for v in batch]
                    added_ids.extend(batch_ids)
                    logger.info(f"Successfully added {len(batch)} vectors to Pinecone")
            
            logger.info(f"Total documents added: {len(added_ids)}")
            return added_ids
            
        except Exception as e:
            logger.error(f"Failed to add documents to vector store: {e}")
            raise VectorStoreError(f"Document addition failed: {e}")
    
    def search(self, query_embedding: np.ndarray, top_k: Optional[int] = None) -> List[DocumentMatch]:
        """Search for similar vectors in the store.
        
        Args:
            query_embedding: Query vector for similarity search.
            top_k: Number of results to return. Uses config default if None.
            
        Returns:
            List of QueryResult objects ordered by similarity score (highest first).
            
        Raises:
            VectorStoreError: If search operation fails.
        """
        if query_embedding is None or len(query_embedding) == 0:
            raise VectorStoreError("Invalid query embedding")
        
        k = top_k or self.config.retrieval.top_k
        
        try:
            response = self.index.query(
                vector=query_embedding.tolist(),
                top_k=k,
                namespace=self.pinecone_config.namespace,
                include_metadata=True,
                include_values=False  # We don't need the vectors back
            )
            
            results = []
            for match in response.get("matches", []):
                # Extract metadata
                metadata = match.get("metadata", {})
                
                # Reconstruct document
                document = Document(
                    content=metadata.get("content", ""),
                    metadata={
                        "source_file": metadata.get("source_file", ""),
                        "clause_number": metadata.get("clause_number", ""),
                        "clause_type": metadata.get("clause_type", ""),
                        "chunk_index": metadata.get("chunk_index", 0),
                        "char_start": metadata.get("char_start", 0),
                        "char_end": metadata.get("char_end", 0)
                    },
                    chunk_id=match.get("id", ""),
                    embedding=None  # Don't return embeddings in search results
                )
                
                query_result = DocumentMatch(
                    document=document,
                    score=match.get("score", 0.0),
                    rank=len(results) + 1
                )
                
                results.append(query_result)
            
            # Filter by similarity threshold
            threshold = self.config.retrieval.similarity_threshold
            filtered_results = [r for r in results if r.score >= threshold]
            
            logger.info(f"Search returned {len(results)} results, {len(filtered_results)} above threshold {threshold}")
            return filtered_results
            
        except Exception as e:
            logger.error(f"Vector search failed: {e}")
            raise VectorStoreError(f"Search operation failed: {e}")
    
    def delete_documents(self, document_ids: List[str]) -> int:
        """Delete documents from the vector store.
        
        Args:
            document_ids: List of document IDs to delete.
            
        Returns:
            Number of documents successfully deleted.
            
        Raises:
            VectorStoreError: If deletion fails.
        """
        if not document_ids:
            return 0
        
        try:
            # Delete in batches
            batch_size = 1000  # Pinecone delete batch limit
            total_deleted = 0
            
            for i in range(0, len(document_ids), batch_size):
                batch = document_ids[i:i + batch_size]
                
                self.index.delete(
                    ids=batch,
                    namespace=self.pinecone_config.namespace
                )
                
                total_deleted += len(batch)
                logger.info(f"Deleted {len(batch)} documents from vector store")
            
            logger.info(f"Total documents deleted: {total_deleted}")
            return total_deleted
            
        except Exception as e:
            logger.error(f"Failed to delete documents: {e}")
            raise VectorStoreError(f"Document deletion failed: {e}")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get vector store statistics.
        
        Returns:
            Dictionary containing index statistics.
        """
        try:
            stats = self.index.describe_index_stats()
            
            namespace_stats = stats.get("namespaces", {}).get(self.pinecone_config.namespace, {})
            
            return {
                "total_vectors": stats.get("total_vector_count", 0),
                "namespace_vectors": namespace_stats.get("vector_count", 0),
                "dimension": stats.get("dimension", 0),
                "index_fullness": stats.get("index_fullness", 0.0),
                "namespace": self.pinecone_config.namespace,
                "index_name": self.pinecone_config.index_name
            }
            
        except Exception as e:
            logger.error(f"Failed to get vector store stats: {e}")
            return {}
    
    def clear_namespace(self) -> bool:
        """Clear all vectors in the configured namespace.
        
        Returns:
            True if successful, False otherwise.
        """
        try:
            self.index.delete(delete_all=True, namespace=self.pinecone_config.namespace)
            logger.info(f"Cleared all vectors from namespace: {self.pinecone_config.namespace}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to clear namespace: {e}")
            return False