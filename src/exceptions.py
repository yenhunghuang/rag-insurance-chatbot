"""Custom Exception Classes

Defines the exception hierarchy for the RAG insurance chatbot system
following the patterns from coding-standards.md.
"""

import logging
from typing import Optional, Any

logger = logging.getLogger(__name__)


class RAGSystemError(Exception):
    """Base exception class for RAG system errors.
    
    All custom exceptions in the system should inherit from this base class
    to provide consistent error handling and logging.
    """
    
    def __init__(self, message: str, details: Optional[dict] = None):
        """Initialize RAG system error.
        
        Args:
            message: Human-readable error message.
            details: Optional dictionary with additional error context.
        """
        super().__init__(message)
        self.message = message
        self.details = details or {}
        
        # Log the exception when it's created
        logger.error(f"{self.__class__.__name__}: {message}", extra={
            "error_details": self.details,
            "exception_type": self.__class__.__name__
        })


class ConfigurationError(RAGSystemError):
    """Configuration-related errors.
    
    Raised when there are issues with system configuration,
    environment variables, or configuration file parsing.
    """
    pass


class RetrievalError(RAGSystemError):
    """Document retrieval-related errors.
    
    Raised when there are issues with document search, vector database
    operations, or embedding generation.
    """
    pass


class GenerationError(RAGSystemError):
    """Response generation-related errors.
    
    Raised when there are issues with LLM API calls, prompt processing,
    or response generation.
    """
    pass


class ProcessingError(RAGSystemError):
    """Document processing-related errors.
    
    Raised when there are issues with document parsing, text cleaning,
    or chunking operations.
    """
    pass


class ValidationError(RAGSystemError):
    """Data validation-related errors.
    
    Raised when input data fails validation checks or format requirements.
    """
    pass


class APIError(RAGSystemError):
    """API service-related errors.
    
    Raised when there are issues with HTTP requests, response formatting,
    or API middleware operations.
    """
    
    def __init__(self, message: str, status_code: int = 500, details: Optional[dict] = None):
        """Initialize API error.
        
        Args:
            message: Human-readable error message.
            status_code: HTTP status code associated with the error.
            details: Optional dictionary with additional error context.
        """
        super().__init__(message, details)
        self.status_code = status_code


class ExternalServiceError(RAGSystemError):
    """External service integration errors.
    
    Raised when there are issues with external API calls, service timeouts,
    or third-party service failures.
    """
    
    def __init__(self, message: str, service_name: str, details: Optional[dict] = None):
        """Initialize external service error.
        
        Args:
            message: Human-readable error message.
            service_name: Name of the external service that failed.
            details: Optional dictionary with additional error context.
        """
        super().__init__(message, details)
        self.service_name = service_name