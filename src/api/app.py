"""FastAPI Application

Main FastAPI application setup with middleware, error handling,
and API documentation for the RAG insurance chatbot system.
"""

import logging
from contextlib import asynccontextmanager
from typing import Dict, Any

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from fastapi.encoders import jsonable_encoder
from starlette.exceptions import HTTPException as StarletteHTTPException

from ..config import get_config, ConfigurationError
from ..exceptions import RAGSystemError
from .routes import router
from .models import ErrorResponse


logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan context manager."""
    # Startup
    logger.info("Starting RAG Insurance Chatbot API")
    
    try:
        config = get_config()
        logger.info(f"API starting on {config.api.host}:{config.api.port}")
        logger.info(f"Environment: {config.environment}")
    except ConfigurationError as e:
        logger.error(f"Configuration error during startup: {e}")
        raise
    
    yield
    
    # Shutdown
    logger.info("Shutting down RAG Insurance Chatbot API")


def create_app() -> FastAPI:
    """Create and configure FastAPI application."""
    
    # Load configuration
    try:
        config = get_config()
    except ConfigurationError as e:
        logger.error(f"Failed to load configuration: {e}")
        raise
    
    # Create FastAPI instance
    app = FastAPI(
        title="RAG Insurance Chatbot API",
        description="""
        ## RAG Insurance Chatbot API

        A Retrieval-Augmented Generation (RAG) system for answering questions about travel insurance policies.
        
        ### Features
        - **Natural Language Queries**: Ask questions in Chinese about travel insurance
        - **Contextual Responses**: Answers based on actual insurance policy documents
        - **Source Citations**: Every answer includes references to specific policy clauses
        - **Streaming Responses**: Real-time response generation for better user experience
        
        ### Usage
        1. **Initialize System**: POST `/initialize` to index insurance documents
        2. **Query System**: POST `/query` to ask questions about insurance policies
        3. **Health Check**: GET `/health` to check system status
        
        ### Sample Queries
        - 班機延誤超過幾小時可以申請賠償？
        - 行李遺失後應該如何申請理賠？
        - 哪些情況下旅遊不便險不會理賠？
        """,
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=lifespan,
        debug=config.api.debug
    )
    
    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=config.api.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Add request logging middleware
    @app.middleware("http")
    async def log_requests(request: Request, call_next):
        """Log all HTTP requests."""
        start_time = time.time()
        
        # Log request
        logger.info(
            f"Request: {request.method} {request.url.path} "
            f"from {request.client.host if request.client else 'unknown'}"
        )
        
        response = await call_next(request)
        
        # Log response
        process_time = time.time() - start_time
        logger.info(
            f"Response: {response.status_code} "
            f"({process_time:.3f}s)"
        )
        
        return response
    
    # Include API routes
    app.include_router(
        router,
        prefix="/api/v1",
        tags=["RAG Chatbot"]
    )
    
    # Root endpoint
    @app.get(
        "/",
        summary="Root Endpoint",
        description="API information and health status"
    )
    async def root():
        """Root endpoint with API information."""
        return {
            "name": "RAG Insurance Chatbot API",
            "version": "1.0.0",
            "description": "Retrieval-Augmented Generation system for travel insurance queries",
            "docs_url": "/docs",
            "health_check": "/api/v1/health",
            "status": "operational"
        }
    
    # Error handlers
    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(request: Request, exc: StarletteHTTPException):
        """Handle HTTP exceptions."""
        logger.error(f"HTTP {exc.status_code}: {exc.detail}")
        
        error_response = ErrorResponse(
            error="http_error",
            message=exc.detail,
            details={"status_code": exc.status_code}
        )
        
        return JSONResponse(
            status_code=exc.status_code,
            content=jsonable_encoder(error_response)
        )
    
    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        """Handle request validation errors."""
        logger.error(f"Validation error: {exc.errors()}")
        
        error_response = ErrorResponse(
            error="validation_error",
            message="Request validation failed",
            details={"validation_errors": exc.errors()}
        )
        
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content=jsonable_encoder(error_response)
        )
    
    @app.exception_handler(RAGSystemError)
    async def rag_system_exception_handler(request: Request, exc: RAGSystemError):
        """Handle RAG system errors."""
        logger.error(f"RAG system error: {exc}")
        
        error_response = ErrorResponse(
            error="rag_system_error",
            message=str(exc),
            details={"error_type": type(exc).__name__}
        )
        
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=jsonable_encoder(error_response)
        )
    
    @app.exception_handler(ConfigurationError)
    async def config_exception_handler(request: Request, exc: ConfigurationError):
        """Handle configuration errors."""
        logger.error(f"Configuration error: {exc}")
        
        error_response = ErrorResponse(
            error="configuration_error", 
            message="System configuration error",
            details={"error": str(exc)}
        )
        
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=jsonable_encoder(error_response)
        )
    
    @app.exception_handler(Exception)
    async def general_exception_handler(request: Request, exc: Exception):
        """Handle all other exceptions."""
        logger.error(f"Unexpected error: {exc}", exc_info=True)
        
        error_response = ErrorResponse(
            error="internal_server_error",
            message="An unexpected error occurred",
            details={"error_type": type(exc).__name__}
        )
        
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=jsonable_encoder(error_response)
        )
    
    logger.info("FastAPI application created successfully")
    return app


# Create application instance
app = create_app()


# Additional imports for middleware
import time