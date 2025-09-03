"""Data Models and Type Definitions

Defines core data structures used throughout the RAG insurance chatbot system.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from datetime import datetime
import uuid


@dataclass
class Document:
    """Represents a document chunk with metadata and optional embedding."""
    
    content: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    embedding: Optional[List[float]] = None
    chunk_id: Optional[str] = field(default_factory=lambda: str(uuid.uuid4()))
    created_at: datetime = field(default_factory=datetime.now)
    
    def __post_init__(self):
        """Validate document after initialization."""
        if not self.content.strip():
            raise ValueError("Document content cannot be empty")


@dataclass
class QueryResult:
    """Represents the result of a document query."""
    
    query: str
    documents: List[Document]
    similarity_scores: List[float]
    total_found: int
    processing_time: float
    
    def __post_init__(self):
        """Validate query result consistency."""
        if len(self.documents) != len(self.similarity_scores):
            raise ValueError("Documents and similarity_scores must have the same length")


@dataclass
class ChatbotResponse:
    """Represents a complete chatbot response."""
    
    query: str
    answer: str
    sources: List[Document]
    confidence: float
    response_time: float
    model_used: str
    timestamp: datetime = field(default_factory=datetime.now)
    
    def __post_init__(self):
        """Validate response data."""
        if not (0.0 <= self.confidence <= 1.0):
            raise ValueError("Confidence must be between 0.0 and 1.0")
        if self.response_time < 0:
            raise ValueError("Response time cannot be negative")


@dataclass
class ProcessingStats:
    """Statistics for document processing operations."""
    
    total_documents: int
    processed_documents: int
    failed_documents: int
    processing_time: float
    average_chunk_size: float
    errors: List[str] = field(default_factory=list)
    
    @property
    def success_rate(self) -> float:
        """Calculate processing success rate."""
        if self.total_documents == 0:
            return 0.0
        return self.processed_documents / self.total_documents