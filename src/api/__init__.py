"""FastAPI Service Module

Provides HTTP API endpoints, request/response models, and middleware
for the RAG insurance chatbot system with comprehensive documentation.
"""

from .app import app, create_app
from .routes import router
from .models import (
    QueryRequest,
    QueryResponse,
    HealthCheckResponse,
    SystemStatusResponse,
    InitializationRequest,
    InitializationResponse,
    ErrorResponse
)

__all__ = [
    "app",
    "create_app", 
    "router",
    "QueryRequest",
    "QueryResponse",
    "HealthCheckResponse",
    "SystemStatusResponse", 
    "InitializationRequest",
    "InitializationResponse",
    "ErrorResponse"
]