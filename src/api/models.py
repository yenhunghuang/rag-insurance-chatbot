"""API Request/Response Models

Pydantic models for API request and response validation
with proper type hints and documentation.
"""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field, validator
from datetime import datetime


class QueryRequest(BaseModel):
    """Request model for chatbot queries."""
    
    query: str = Field(
        ..., 
        min_length=1,
        max_length=1000,
        description="User's question about travel insurance"
    )
    top_k: Optional[int] = Field(
        None,
        ge=1,
        le=20,
        description="Number of relevant documents to retrieve (1-20)"
    )
    include_sources: bool = Field(
        True,
        description="Whether to include source citations in response"
    )
    conversation_history: Optional[List[Dict[str, str]]] = Field(
        None,
        description="Previous conversation messages for context"
    )
    
    @validator('query')
    def validate_query(cls, v):
        """Validate query content."""
        if not v.strip():
            raise ValueError('Query cannot be empty or whitespace only')
        return v.strip()
    
    @validator('conversation_history')
    def validate_conversation_history(cls, v):
        """Validate conversation history format."""
        if v is None:
            return v
        
        for msg in v:
            if not isinstance(msg, dict):
                raise ValueError('Each conversation message must be a dictionary')
            if 'role' not in msg or 'content' not in msg:
                raise ValueError('Each message must have "role" and "content" keys')
            if msg['role'] not in ['user', 'assistant']:
                raise ValueError('Message role must be "user" or "assistant"')
        
        return v


class SourceInfo(BaseModel):
    """Source citation information."""
    
    clause_number: str = Field(description="Insurance clause number")
    source_file: str = Field(description="Source document filename")
    content_snippet: str = Field(description="Relevant content excerpt")
    relevance_score: float = Field(description="Relevance score (0-1)")
    chunk_id: str = Field(description="Unique chunk identifier")


class QueryResponse(BaseModel):
    """Response model for chatbot queries."""
    
    query: str = Field(description="Original user query")
    answer: str = Field(description="Generated response")
    sources: List[SourceInfo] = Field(description="Source citations")
    confidence_score: float = Field(
        ge=0.0, 
        le=1.0, 
        description="Response confidence score"
    )
    metadata: Dict[str, Any] = Field(description="Additional response metadata")


class HealthCheckResponse(BaseModel):
    """Response model for health check endpoints."""
    
    status: str = Field(description="Overall system status")
    timestamp: datetime = Field(description="Health check timestamp")
    components: Dict[str, Any] = Field(description="Component health status")
    system_info: Dict[str, Any] = Field(description="System information")


class SystemStatusResponse(BaseModel):
    """Response model for system status endpoint."""
    
    system_initialized: bool = Field(description="Whether system is initialized")
    overall_status: str = Field(description="Overall system health")
    components: Dict[str, Any] = Field(description="Component status details")
    statistics: Dict[str, Any] = Field(description="System statistics")
    configuration: Dict[str, Any] = Field(description="System configuration")


class InitializationRequest(BaseModel):
    """Request model for system initialization."""
    
    document_file: Optional[str] = Field(
        None,
        description="Path to document file to index (optional)"
    )
    clear_existing: bool = Field(
        False,
        description="Whether to clear existing index before initialization"
    )


class InitializationResponse(BaseModel):
    """Response model for system initialization."""
    
    initialized: bool = Field(description="Whether initialization succeeded")
    indexing_results: Dict[str, Any] = Field(description="Document indexing results")
    system_ready: bool = Field(description="Whether system is ready for queries")
    message: str = Field(description="Status message")


class ErrorResponse(BaseModel):
    """Standard error response model."""
    
    error: str = Field(description="Error type")
    message: str = Field(description="Error message") 
    details: Optional[Dict[str, Any]] = Field(
        None,
        description="Additional error details"
    )
    timestamp: datetime = Field(default_factory=datetime.now)


class ValidationErrorResponse(BaseModel):
    """Validation error response model."""
    
    error: str = Field(default="validation_error")
    message: str = Field(description="Validation error message")
    validation_errors: List[Dict[str, Any]] = Field(description="Field validation errors")
    timestamp: datetime = Field(default_factory=datetime.now)


class StreamingResponse(BaseModel):
    """Model for streaming response metadata."""
    
    query: str = Field(description="Original query")
    total_chunks: int = Field(description="Total number of streamed chunks")
    total_length: int = Field(description="Total response length")
    generation_time: float = Field(description="Total generation time in seconds")
    sources: List[SourceInfo] = Field(description="Source citations")
    confidence_score: float = Field(description="Response confidence score")