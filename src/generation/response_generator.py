"""RAG Response Generator

Generates contextual responses by combining retrieved documents
with LLM capabilities for insurance-related queries.
"""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime

from ..config import get_config
from ..models import Document, QueryResult, ChatbotResponse
from ..exceptions import RAGSystemError
from .llm_client import OpenAIClient


logger = logging.getLogger(__name__)


class ResponseGenerationError(RAGSystemError):
    """Response generation errors."""
    pass


class ResponseGenerator:
    """Generates contextual responses using retrieved documents and LLM."""
    
    def __init__(self):
        """Initialize the response generator."""
        self.config = get_config()
        self.llm_client = OpenAIClient()
        
        logger.info("ResponseGenerator initialized successfully")
    
    def generate_response(
        self,
        query: str,
        retrieved_documents: List[QueryResult],
        conversation_history: Optional[List[Dict[str, str]]] = None
    ) -> ChatbotResponse:
        """Generate a contextual response based on query and retrieved documents.
        
        Args:
            query: User's question.
            retrieved_documents: List of relevant documents from retrieval.
            conversation_history: Previous conversation messages (optional).
            
        Returns:
            ChatbotResponse with generated answer and source citations.
            
        Raises:
            ResponseGenerationError: If response generation fails.
        """
        if not query or not query.strip():
            raise ResponseGenerationError("Query cannot be empty")
        
        try:
            logger.info(f"Generating response for query: '{query[:100]}...'")
            
            # Step 1: Prepare context from retrieved documents
            context = self._prepare_context(retrieved_documents)
            
            # Step 2: Build prompt messages
            messages = self._build_prompt_messages(query, context, conversation_history)
            
            # Step 3: Generate response with LLM
            llm_response = self.llm_client.generate_response(messages)
            
            # Step 4: Create structured response with citations
            response = self._create_structured_response(
                query, llm_response, retrieved_documents
            )
            
            logger.info(
                f"Response generated successfully: "
                f"{len(response.answer)} chars, "
                f"{len(response.sources)} sources"
            )
            
            return response
            
        except Exception as e:
            logger.error(f"Response generation failed for query: {query}")
            raise ResponseGenerationError(f"Failed to generate response: {e}")
    
    def _prepare_context(self, retrieved_documents: List[QueryResult]) -> str:
        """Prepare context string from retrieved documents.
        
        Args:
            retrieved_documents: List of retrieved documents with scores.
            
        Returns:
            Formatted context string for the prompt.
        """
        if not retrieved_documents:
            return "沒有找到相關的保險條款資料。"
        
        context_parts = []
        
        for i, result in enumerate(retrieved_documents, 1):
            doc = result.document
            score = result.score
            
            # Extract clause information
            clause_info = doc.metadata.get("clause_number", f"條款 {i}")
            source_file = doc.metadata.get("source_file", "保險條款")
            
            # Format document content with metadata
            context_part = (
                f"【{clause_info}】(相關度: {score:.2f})\n"
                f"來源: {source_file}\n"
                f"內容: {doc.content}\n"
            )
            
            context_parts.append(context_part)
        
        context = "\n" + "="*50 + "\n".join(context_parts) + "="*50 + "\n"
        
        logger.info(f"Prepared context from {len(retrieved_documents)} documents")
        return context
    
    def _build_prompt_messages(
        self,
        query: str,
        context: str,
        conversation_history: Optional[List[Dict[str, str]]] = None
    ) -> List[Dict[str, str]]:
        """Build prompt messages for the LLM.
        
        Args:
            query: User's question.
            context: Context from retrieved documents.
            conversation_history: Previous conversation (optional).
            
        Returns:
            List of message dictionaries for OpenAI API.
        """
        # System prompt for insurance domain
        system_prompt = """你是一個專業的旅遊不便險諮詢助手，專門協助客戶理解保險條款和理賠相關問題。

**你的職責:**
1. 根據提供的保險條款準確回答客戶問題
2. 提供清楚、易懂的解釋
3. 指出相關的條款編號和具體規定
4. 如果需要其他文件或程序，要明確說明

**回答格式要求:**
1. 直接回答客戶問題
2. 引用相關條款編號和內容
3. 如果有多個相關條款，要分點說明
4. 最後提供注意事項或建議

**重要原則:**
- 只根據提供的條款內容回答，不要編造資訊
- 如果條款中沒有明確規定，要誠實說明
- 用繁體中文回答
- 保持專業、友善的語氣

請根據以下保險條款資料回答客戶問題。"""
        
        messages = [{"role": "system", "content": system_prompt}]
        
        # Add conversation history if provided
        if conversation_history:
            for msg in conversation_history[-6:]:  # Keep last 6 messages for context
                if msg.get("role") in ["user", "assistant"]:
                    messages.append(msg)
        
        # Add current query with context
        user_message = f"""保險條款資料:
{context}

客戶問題: {query}

請根據上述條款資料，提供專業、準確的回答。請記得引用相關條款編號。"""
        
        messages.append({"role": "user", "content": user_message})
        
        return messages
    
    def _create_structured_response(
        self,
        query: str,
        llm_response: Dict[str, Any],
        retrieved_documents: List[QueryResult]
    ) -> ChatbotResponse:
        """Create structured chatbot response with citations.
        
        Args:
            query: Original user query.
            llm_response: Response from LLM client.
            retrieved_documents: Documents used for context.
            
        Returns:
            Structured ChatbotResponse object.
        """
        # Extract source information
        sources = []
        for result in retrieved_documents:
            doc = result.document
            
            source_info = {
                "clause_number": doc.metadata.get("clause_number", ""),
                "source_file": doc.metadata.get("source_file", ""),
                "content_snippet": doc.content[:200] + "..." if len(doc.content) > 200 else doc.content,
                "relevance_score": result.score,
                "chunk_id": doc.chunk_id or ""
            }
            sources.append(source_info)
        
        # Create response metadata
        metadata = {
            "model_used": llm_response.get("model", ""),
            "generation_time": llm_response.get("generation_time", 0),
            "token_usage": llm_response.get("usage", {}),
            "finish_reason": llm_response.get("finish_reason", ""),
            "retrieved_documents_count": len(retrieved_documents),
            "average_relevance_score": (
                sum(r.score for r in retrieved_documents) / len(retrieved_documents)
                if retrieved_documents else 0.0
            ),
            "timestamp": datetime.now().isoformat()
        }
        
        response = ChatbotResponse(
            query=query,
            answer=llm_response["content"],
            sources=sources,
            confidence=self._calculate_confidence_score(retrieved_documents, llm_response),
            response_time=llm_response.get("response_time", 0.0),
            model_used=llm_response.get("model", "gpt-3.5-turbo")
        )
        
        return response
    
    def _calculate_confidence_score(
        self,
        retrieved_documents: List[QueryResult],
        llm_response: Dict[str, Any]
    ) -> float:
        """Calculate confidence score for the response.
        
        Args:
            retrieved_documents: Documents used for context.
            llm_response: LLM response data.
            
        Returns:
            Confidence score between 0.0 and 1.0.
        """
        if not retrieved_documents:
            return 0.1  # Low confidence without context
        
        # Base confidence from document relevance
        avg_relevance = sum(r.score for r in retrieved_documents) / len(retrieved_documents)
        
        # Adjust based on number of relevant documents
        doc_count_factor = min(1.0, len(retrieved_documents) / 3)  # Optimal around 3 docs
        
        # Adjust based on LLM finish reason
        finish_reason_factor = 1.0
        if llm_response.get("finish_reason") == "length":
            finish_reason_factor = 0.8  # Slightly lower confidence for truncated responses
        elif llm_response.get("finish_reason") == "stop":
            finish_reason_factor = 1.0  # Normal completion
        
        # Combine factors
        confidence = avg_relevance * 0.6 + doc_count_factor * 0.3 + finish_reason_factor * 0.1
        
        return min(1.0, max(0.0, confidence))
    
    def generate_streaming_response(
        self,
        query: str,
        retrieved_documents: List[QueryResult],
        conversation_history: Optional[List[Dict[str, str]]] = None
    ):
        """Generate a streaming response for real-time display.
        
        Args:
            query: User's question.
            retrieved_documents: List of relevant documents.
            conversation_history: Previous conversation (optional).
            
        Yields:
            Partial response chunks.
            
        Returns:
            Final ChatbotResponse object.
        """
        try:
            logger.info(f"Starting streaming response for query: '{query[:100]}...'")
            
            # Prepare context and messages
            context = self._prepare_context(retrieved_documents)
            messages = self._build_prompt_messages(query, context, conversation_history)
            
            # Generate streaming response
            full_content = ""
            metadata = {}
            
            for chunk in self.llm_client.generate_streaming_response(messages):
                if isinstance(chunk, str):
                    full_content += chunk
                    yield chunk
                else:
                    # Final metadata
                    metadata = chunk
            
            # Create final structured response
            llm_response = {
                "content": full_content,
                "model": metadata.get("model", ""),
                "generation_time": metadata.get("generation_time", 0),
                "usage": {"total_tokens": len(full_content)},  # Approximate
                "finish_reason": "stop"
            }
            
            response = self._create_structured_response(query, llm_response, retrieved_documents)
            
            return response
            
        except Exception as e:
            logger.error(f"Streaming response failed: {e}")
            raise ResponseGenerationError(f"Streaming response failed: {e}")
    
    def health_check(self) -> Dict[str, Any]:
        """Perform health check on response generator.
        
        Returns:
            Health status information.
        """
        try:
            # Test LLM client
            llm_health = self.llm_client.health_check()
            
            return {
                "status": "healthy" if llm_health["status"] == "healthy" else "degraded",
                "llm_client": llm_health,
                "configuration": {
                    "model": self.config.generation.model_name,
                    "temperature": self.config.generation.temperature,
                    "max_tokens": self.config.generation.max_tokens
                }
            }
            
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e)
            }