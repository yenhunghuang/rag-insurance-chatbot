"""RAG System Orchestrator

Main orchestration service that combines document retrieval and response generation
to provide end-to-end RAG (Retrieval-Augmented Generation) capabilities.
"""

import logging
from typing import List, Dict, Any, Optional, Union

from ..config import get_config
from ..models import ChatbotResponse, QueryResult
from ..exceptions import RAGSystemError
from ..retrieval import RetrievalService
from .response_generator import ResponseGenerator


logger = logging.getLogger(__name__)


class RAGSystemError(RAGSystemError):
    """RAG system orchestration errors."""
    pass


class RAGSystem:
    """Complete RAG system combining retrieval and generation."""
    
    def __init__(self):
        """Initialize the RAG system with all components."""
        self.config = get_config()
        
        # Initialize components
        self.retrieval_service = RetrievalService()
        self.response_generator = ResponseGenerator()
        
        # System state
        self._is_initialized = False
        self._index_stats = {}
        
        logger.info("RAGSystem initialized successfully")
    
    def initialize_system(self, document_file: Optional[str] = None) -> Dict[str, Any]:
        """Initialize the RAG system by indexing documents.
        
        Args:
            document_file: Path to document file to index. 
                          If None, looks for default insurance document.
            
        Returns:
            Dictionary with initialization results.
            
        Raises:
            RAGSystemError: If system initialization fails.
        """
        try:
            logger.info("Initializing RAG system...")
            
            # Default to processed insurance document if no file specified
            if document_file is None:
                document_file = f"{self.config.data_dir}/raw/海外旅行不便險條款.txt"
            
            # Index documents
            indexing_results = self.retrieval_service.index_documents_from_file(document_file)
            
            # Update system state
            self._is_initialized = indexing_results["processing_successful"]
            self._index_stats = indexing_results
            
            if self._is_initialized:
                logger.info("RAG system initialization completed successfully")
            else:
                logger.error("RAG system initialization failed")
            
            return {
                "initialized": self._is_initialized,
                "indexing_results": indexing_results,
                "system_ready": self._is_initialized
            }
            
        except Exception as e:
            logger.error(f"RAG system initialization failed: {e}")
            self._is_initialized = False
            raise RAGSystemError(f"System initialization failed: {e}")
    
    def query(
        self,
        question: str,
        top_k: Optional[int] = None,
        include_sources: bool = True,
        conversation_history: Optional[List[Dict[str, str]]] = None
    ) -> ChatbotResponse:
        """Process a query through the complete RAG pipeline.
        
        Args:
            question: User's question.
            top_k: Number of documents to retrieve. Uses config default if None.
            include_sources: Whether to include source citations in response.
            conversation_history: Previous conversation context.
            
        Returns:
            ChatbotResponse with generated answer and sources.
            
        Raises:
            RAGSystemError: If query processing fails.
        """
        if not self._is_initialized:
            raise RAGSystemError(
                "RAG system not initialized. Call initialize_system() first."
            )
        
        if not question or not question.strip():
            raise RAGSystemError("Question cannot be empty")
        
        try:
            logger.info(f"Processing RAG query: '{question[:100]}...'")
            
            # Step 1: Retrieve relevant documents
            retrieved_docs = self.retrieval_service.search_documents(
                query=question.strip(),
                top_k=top_k
            )
            
            logger.info(f"Retrieved {len(retrieved_docs)} relevant documents")
            
            # Step 2: Generate contextual response
            response = self.response_generator.generate_response(
                query=question.strip(),
                retrieved_documents=retrieved_docs,
                conversation_history=conversation_history
            )
            
            # Step 3: Filter sources if requested
            if not include_sources:
                response.sources = []
            
            logger.info("RAG query processed successfully")
            return response
            
        except Exception as e:
            logger.error(f"RAG query processing failed: {e}")
            raise RAGSystemError(f"Query processing failed: {e}")
    
    def stream_query(
        self,
        question: str,
        top_k: Optional[int] = None,
        conversation_history: Optional[List[Dict[str, str]]] = None
    ):
        """Process a query with streaming response.
        
        Args:
            question: User's question.
            top_k: Number of documents to retrieve.
            conversation_history: Previous conversation context.
            
        Yields:
            Partial response chunks.
            
        Returns:
            Final ChatbotResponse object.
            
        Raises:
            RAGSystemError: If streaming query fails.
        """
        if not self._is_initialized:
            raise RAGSystemError(
                "RAG system not initialized. Call initialize_system() first."
            )
        
        try:
            logger.info(f"Starting streaming RAG query: '{question[:100]}...'")
            
            # Retrieve documents
            retrieved_docs = self.retrieval_service.search_documents(
                query=question.strip(),
                top_k=top_k
            )
            
            # Stream response generation
            final_response = None
            for chunk in self.response_generator.generate_streaming_response(
                query=question.strip(),
                retrieved_documents=retrieved_docs,
                conversation_history=conversation_history
            ):
                if isinstance(chunk, str):
                    yield chunk
                else:
                    final_response = chunk
            
            return final_response
            
        except Exception as e:
            logger.error(f"Streaming RAG query failed: {e}")
            raise RAGSystemError(f"Streaming query failed: {e}")
    
    def get_system_status(self) -> Dict[str, Any]:
        """Get comprehensive system status and statistics.
        
        Returns:
            Dictionary with system status information.
        """
        try:
            # Get component health
            retrieval_health = self.retrieval_service.health_check()
            generation_health = self.response_generator.health_check()
            
            # Get system stats
            retrieval_stats = self.retrieval_service.get_retrieval_stats()
            
            return {
                "system_initialized": self._is_initialized,
                "overall_status": (
                    "healthy" if self._is_initialized and 
                    retrieval_health.get("status") == "healthy" and
                    generation_health.get("status") == "healthy"
                    else "degraded"
                ),
                "components": {
                    "retrieval_service": retrieval_health,
                    "response_generator": generation_health
                },
                "statistics": {
                    "indexing": self._index_stats,
                    "retrieval": retrieval_stats
                },
                "configuration": {
                    "retrieval": {
                        "top_k": self.config.retrieval.top_k,
                        "similarity_threshold": self.config.retrieval.similarity_threshold,
                        "index_type": self.config.retrieval.index_type
                    },
                    "generation": {
                        "model": self.config.generation.model_name,
                        "temperature": self.config.generation.temperature,
                        "max_tokens": self.config.generation.max_tokens
                    }
                }
            }
            
        except Exception as e:
            logger.error(f"Failed to get system status: {e}")
            return {
                "system_initialized": self._is_initialized,
                "overall_status": "error",
                "error": str(e)
            }
    
    def reindex_documents(self, document_file: str) -> Dict[str, Any]:
        """Reindex documents with a new file.
        
        Args:
            document_file: Path to new document file.
            
        Returns:
            Dictionary with reindexing results.
            
        Raises:
            RAGSystemError: If reindexing fails.
        """
        try:
            logger.info(f"Reindexing documents from: {document_file}")
            
            # Clear existing index
            clear_success = self.retrieval_service.clear_index()
            if not clear_success:
                logger.warning("Failed to clear existing index, proceeding anyway")
            
            # Index new documents
            indexing_results = self.retrieval_service.index_documents_from_file(document_file)
            
            # Update system state
            self._is_initialized = indexing_results["processing_successful"]
            self._index_stats = indexing_results
            
            return {
                "reindexing_successful": self._is_initialized,
                "indexing_results": indexing_results
            }
            
        except Exception as e:
            logger.error(f"Document reindexing failed: {e}")
            raise RAGSystemError(f"Reindexing failed: {e}")
    
    def get_sample_queries(self) -> List[str]:
        """Get sample queries for testing the system.
        
        Returns:
            List of sample question strings.
        """
        return [
            "班機延誤超過幾小時可以申請賠償？",
            "行李遺失後應該如何申請理賠？",
            "哪些情況下旅遊不便險不會理賠？",
            "旅程取消保險的承保範圍有哪些？",
            "信用卡被盜刷在海外旅行期間如何處理？",
            "行李延誤達到多久才能申請理賠？",
            "海外就醫的醫療轉送費用保險如何申請？",
            "租車發生事故時保險理賠條件是什麼？"
        ]
    
    def validate_query(self, question: str) -> Dict[str, Any]:
        """Validate a query before processing.
        
        Args:
            question: Question to validate.
            
        Returns:
            Dictionary with validation results.
        """
        validation_result = {
            "is_valid": True,
            "issues": [],
            "suggestions": []
        }
        
        if not question or not question.strip():
            validation_result["is_valid"] = False
            validation_result["issues"].append("Question is empty")
            return validation_result
        
        question = question.strip()
        
        # Length checks
        if len(question) < 3:
            validation_result["is_valid"] = False
            validation_result["issues"].append("Question is too short")
        
        if len(question) > 1000:
            validation_result["issues"].append("Question is very long, may be truncated")
            validation_result["suggestions"].append("Consider breaking into multiple questions")
        
        # Content checks
        insurance_keywords = [
            "保險", "理賠", "條款", "賠償", "承保", "申請", "證明", 
            "班機", "行李", "旅程", "延誤", "取消", "遺失", "醫療"
        ]
        
        has_insurance_context = any(keyword in question for keyword in insurance_keywords)
        if not has_insurance_context:
            validation_result["suggestions"].append(
                "Question doesn't seem insurance-related. This system specializes in travel insurance queries."
            )
        
        return validation_result