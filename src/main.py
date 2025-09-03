"""FastAPI Application Entry Point

Main application entry point for the RAG insurance chatbot system.
Initializes configuration, logging, and FastAPI application.
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import logging

from .config import ConfigFactory, get_config, ConfigurationError
from .logging_config import setup_logging
from .exceptions import RAGSystemError

# Initialize configuration and logging
try:
    config = ConfigFactory.load_from_env()
    setup_logging(config.log_level, config.environment)
    logger = logging.getLogger(__name__)
    logger.info("RAG Insurance Chatbot starting up...")
except ConfigurationError as e:
    print(f"Configuration error: {e}")
    raise

# Create FastAPI application
app = FastAPI(
    title="RAG Insurance Chatbot API",
    description="Retrieval-Augmented Generation system for insurance clause queries",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=config.api.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    """Root endpoint for health check."""
    return {
        "message": "RAG Insurance Chatbot API", 
        "version": "1.0.0",
        "status": "running"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    try:
        config = get_config()
        return {
            "status": "healthy",
            "environment": config.environment,
            "version": "1.0.0"
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=503, detail="Service unhealthy")


@app.exception_handler(RAGSystemError)
async def rag_system_error_handler(request, exc: RAGSystemError):
    """Handle RAG system errors."""
    logger.error(f"RAG system error: {exc.message}", extra=exc.details)
    return HTTPException(
        status_code=500,
        detail={
            "error": exc.__class__.__name__,
            "message": exc.message,
            "details": exc.details
        }
    )


if __name__ == "__main__":
    import uvicorn
    config = get_config()
    uvicorn.run(
        "src.main:app",
        host=config.api.host,
        port=config.api.port,
        log_level=config.log_level.lower(),
        reload=config.api.debug
    )