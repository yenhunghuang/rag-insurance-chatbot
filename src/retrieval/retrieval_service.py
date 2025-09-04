"""Document Retrieval Service

Main orchestration service for document indexing, search, and retrieval
operations using embeddings and vector storage.
"""

import logging
from typing import List, Optional, Dict, Any
from pathlib import Path
import json

from ..config import get_config
from ..models import Document, QueryResult
from ..exceptions import RAGSystemError
from ..processing.document_processor import DocumentProcessor
from .embedding_service import EmbeddingService
from .vector_store import PineconeVectorStore


logger = logging.getLogger(__name__)


class RetrievalError(RAGSystemError):
    """Retrieval service errors."""
    pass


class RetrievalService:
    """Main service for document indexing and retrieval operations."""
    
    def __init__(self):
        """Initialize the retrieval service with all components."""
        self.config = get_config()
        
        # Initialize components
        self.document_processor = DocumentProcessor()
        self.embedding_service = EmbeddingService()
        self.vector_store = PineconeVectorStore()
        
        logger.info("RetrievalService initialized successfully")
    
    def index_documents_from_file(self, file_path: str) -> Dict[str, Any]:
        """Process and index documents from a file.
        
        Args:
            file_path: Path to the document file to index.
            
        Returns:
            Dictionary with indexing statistics and results.
            
        Raises:
            RetrievalError: If document indexing fails.
        """
        try:
            logger.info(f"Starting document indexing from file: {file_path}")
            
            # Step 1: Load and process documents into chunks
            content = self.document_processor.load_document(file_path)
            documents = self.document_processor.process_document(content, file_path)
            if not documents:
                raise RetrievalError(f"No documents extracted from file: {file_path}")
            
            logger.info(f"Processed {len(documents)} document chunks")
            
            # Step 2: Generate embeddings
            texts = [doc.content for doc in documents]
            embeddings = self.embedding_service.encode_batch(texts)
            
            # Attach embeddings to documents
            for doc, embedding in zip(documents, embeddings):
                doc.embedding = embedding
            
            logger.info(f"Generated {len(embeddings)} embeddings")
            
            # Step 3: Store in vector database
            indexed_ids = self.vector_store.add_documents(documents)
            
            # Step 4: Save processed chunks locally for reference
            self._save_processed_chunks(documents, file_path)
            
            # Compile results
            results = {
                "source_file": file_path,
                "total_chunks": len(documents),
                "embeddings_generated": len(embeddings),
                "vectors_indexed": len(indexed_ids),
                "embedding_dimension": self.embedding_service.get_dimension(),
                "processing_successful": len(indexed_ids) > 0
            }
            
            logger.info(f"Document indexing completed: {results}")
            return results
            
        except Exception as e:
            logger.error(f"Document indexing failed for {file_path}: {e}")
            raise RetrievalError(f"Failed to index documents from {file_path}: {e}")
    
    def search_documents(self, query: str, top_k: Optional[int] = None) -> List[QueryResult]:
        """Search for documents similar to the query.
        
        Args:
            query: Natural language query string.
            top_k: Number of results to return. Uses config default if None.
            
        Returns:
            List of QueryResult objects ordered by similarity score.
            
        Raises:
            RetrievalError: If search operation fails.
        """
        if not query or not query.strip():
            raise RetrievalError("Query cannot be empty")
        
        try:
            logger.info(f"Searching for query: '{query[:100]}...'")
            
            # Step 1: Generate query embedding
            query_embedding = self.embedding_service.encode_single(query.strip())
            
            # Step 2: Search vector store
            results = self.vector_store.search(query_embedding, top_k)
            
            # Step 3: Enhance results with full content if available
            enhanced_results = self._enhance_search_results(results)
            
            logger.info(f"Search completed, returning {len(enhanced_results)} results")
            return enhanced_results
            
        except Exception as e:
            logger.error(f"Document search failed for query: {query}")
            raise RetrievalError(f"Search failed: {e}")
    
    def get_retrieval_stats(self) -> Dict[str, Any]:
        """Get comprehensive statistics about the retrieval system.
        
        Returns:
            Dictionary with system statistics.
        """
        try:
            vector_stats = self.vector_store.get_stats()
            
            stats = {
                "vector_store": vector_stats,
                "embedding_service": {
                    "model_name": self.embedding_service.model_name,
                    "dimension": self.embedding_service.get_dimension()
                },
                "configuration": {
                    "top_k": self.config.retrieval.top_k,
                    "similarity_threshold": self.config.retrieval.similarity_threshold,
                    "chunk_size": self.config.retrieval.chunk_size,
                    "chunk_overlap": self.config.retrieval.chunk_overlap
                }
            }
            
            return stats
            
        except Exception as e:
            logger.error(f"Failed to get retrieval stats: {e}")
            return {"error": str(e)}
    
    def clear_index(self) -> bool:
        """Clear all indexed documents from the vector store.
        
        Returns:
            True if successful, False otherwise.
        """
        try:
            logger.warning("Clearing all indexed documents")
            success = self.vector_store.clear_namespace()
            
            if success:
                logger.info("Successfully cleared document index")
            else:
                logger.error("Failed to clear document index")
            
            return success
            
        except Exception as e:
            logger.error(f"Failed to clear index: {e}")
            return False
    
    def _save_processed_chunks(self, documents: List[Document], source_file: str):
        """Save processed document chunks for reference.
        
        Args:
            documents: List of processed documents.
            source_file: Original source file path.
        """
        try:
            processed_dir = Path(self.config.data_dir) / "processed"
            processed_dir.mkdir(exist_ok=True)
            
            # Create filename based on source file
            source_name = Path(source_file).stem
            chunks_file = processed_dir / f"{source_name}_chunks.json"
            
            # Prepare data for serialization
            chunks_data = []
            for doc in documents:
                chunk_data = {
                    "content": doc.content,
                    "metadata": doc.metadata,
                    "chunk_id": doc.chunk_id,
                    "embedding_shape": doc.embedding.shape if doc.embedding is not None else None
                }
                chunks_data.append(chunk_data)
            
            # Save to JSON file
            with open(chunks_file, 'w', encoding='utf-8') as f:
                json.dump({
                    "source_file": source_file,
                    "total_chunks": len(chunks_data),
                    "chunks": chunks_data
                }, f, ensure_ascii=False, indent=2)
            
            logger.info(f"Saved {len(chunks_data)} chunks to {chunks_file}")
            
        except Exception as e:
            logger.warning(f"Failed to save processed chunks: {e}")
    
    def _enhance_search_results(self, results: List[QueryResult]) -> List[QueryResult]:
        """Enhance search results with additional context if available.
        
        Args:
            results: Initial search results from vector store.
            
        Returns:
            Enhanced query results with full content.
        """
        # For now, return results as-is
        # In the future, this could load full content from processed chunks
        # or add additional context from neighboring chunks
        return results
    
    def health_check(self) -> Dict[str, Any]:
        """Perform health check on all retrieval components.
        
        Returns:
            Health status of all components.
        """
        health = {
            "status": "healthy",
            "components": {},
            "timestamp": ""
        }
        
        try:
            # Check embedding service
            test_embedding = self.embedding_service.encode_single("健康檢查測試")
            health["components"]["embedding_service"] = {
                "status": "healthy",
                "dimension": len(test_embedding)
            }
        except Exception as e:
            health["components"]["embedding_service"] = {
                "status": "unhealthy",
                "error": str(e)
            }
            health["status"] = "degraded"
        
        try:
            # Check vector store
            stats = self.vector_store.get_stats()
            health["components"]["vector_store"] = {
                "status": "healthy",
                "total_vectors": stats.get("total_vectors", 0)
            }
        except Exception as e:
            health["components"]["vector_store"] = {
                "status": "unhealthy", 
                "error": str(e)
            }
            health["status"] = "degraded"
        
        try:
            # Check document processor
            self.document_processor._validate_security_config()
            health["components"]["document_processor"] = {
                "status": "healthy"
            }
        except Exception as e:
            health["components"]["document_processor"] = {
                "status": "unhealthy",
                "error": str(e)
            }
            health["status"] = "degraded"
        
        return health