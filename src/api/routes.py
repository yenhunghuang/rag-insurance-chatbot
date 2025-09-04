"""API Routes

FastAPI routes for the RAG insurance chatbot system
with comprehensive error handling and documentation.
"""

import logging
from typing import Dict, Any, Generator
from datetime import datetime
import asyncio
import json

from fastapi import APIRouter, HTTPException, status, Depends
from fastapi.responses import StreamingResponse
from pydantic import ValidationError

from ..config import get_config
from ..generation import RAGSystem, RAGSystemError
from ..exceptions import RAGSystemError as BaseRAGError
from .models import (
    QueryRequest,
    QueryResponse, 
    HealthCheckResponse,
    SystemStatusResponse,
    InitializationRequest,
    InitializationResponse,
    ErrorResponse,
    StreamingResponse as StreamingResponseModel
)


logger = logging.getLogger(__name__)

# Initialize router
router = APIRouter()

# Global RAG system instance
rag_system: RAGSystem = None


def get_rag_system() -> RAGSystem:
    """Dependency to get RAG system instance."""
    global rag_system
    if rag_system is None:
        rag_system = RAGSystem()
    return rag_system


@router.get(
    "/health",
    response_model=HealthCheckResponse,
    summary="Health Check",
    description="Check the health status of all system components"
)
async def health_check():
    """Perform comprehensive health check."""
    try:
        config = get_config()
        
        # Get system status
        system_status = {}
        if rag_system is not None:
            system_status = rag_system.get_system_status()
        
        health_status = "healthy"
        if system_status.get("overall_status") != "healthy":
            health_status = "degraded"
        
        return HealthCheckResponse(
            status=health_status,
            timestamp=datetime.now(),
            components=system_status.get("components", {}),
            system_info={
                "environment": config.environment,
                "log_level": config.log_level,
                "api_version": "1.0.0"
            }
        )
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Health check failed: {str(e)}"
        )


@router.get(
    "/status",
    response_model=SystemStatusResponse,
    summary="System Status", 
    description="Get detailed system status and statistics"
)
async def get_system_status(rag_system: RAGSystem = Depends(get_rag_system)):
    """Get comprehensive system status."""
    try:
        status_info = rag_system.get_system_status()
        
        return SystemStatusResponse(**status_info)
        
    except Exception as e:
        logger.error(f"Failed to get system status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get system status: {str(e)}"
        )


@router.post(
    "/initialize",
    response_model=InitializationResponse,
    summary="Initialize System",
    description="Initialize the RAG system by indexing documents"
)
async def initialize_system(
    request: InitializationRequest,
    rag_system: RAGSystem = Depends(get_rag_system)
):
    """Initialize the RAG system with document indexing."""
    try:
        logger.info("Initializing RAG system via API")
        
        # Clear existing index if requested
        if request.clear_existing:
            rag_system.retrieval_service.clear_index()
        
        # Initialize system
        init_results = rag_system.initialize_system(request.document_file)
        
        message = (
            "System initialized successfully" 
            if init_results["initialized"] 
            else "System initialization failed"
        )
        
        return InitializationResponse(
            **init_results,
            message=message
        )
        
    except RAGSystemError as e:
        logger.error(f"RAG system initialization failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"System initialization failed: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Unexpected error during initialization: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Initialization error: {str(e)}"
        )


@router.post(
    "/query",
    response_model=QueryResponse,
    summary="Process Query",
    description="Process a natural language query about travel insurance"
)
async def process_query(
    request: QueryRequest,
    rag_system: RAGSystem = Depends(get_rag_system)
):
    """Process a query through the RAG system."""
    try:
        logger.info(f"Processing query: '{request.query[:100]}...'")
        
        # Validate query
        validation_result = rag_system.validate_query(request.query)
        if not validation_result["is_valid"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "error": "Invalid query",
                    "issues": validation_result["issues"],
                    "suggestions": validation_result["suggestions"]
                }
            )
        
        # Process query
        response = rag_system.query(
            question=request.query,
            top_k=request.top_k,
            include_sources=request.include_sources,
            conversation_history=request.conversation_history
        )
        
        # Convert to API response model
        return QueryResponse(
            query=response.query,
            answer=response.answer,
            sources=[
                {
                    "clause_number": src["clause_number"],
                    "source_file": src["source_file"],
                    "content_snippet": src["content_snippet"], 
                    "relevance_score": src["relevance_score"],
                    "chunk_id": src["chunk_id"]
                }
                for src in response.sources
            ],
            confidence=response.confidence,
            metadata=response.metadata
        )
        
    except RAGSystemError as e:
        logger.error(f"RAG query processing failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Query processing failed: {str(e)}"
        )
    except ValidationError as e:
        logger.error(f"Query validation failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Query validation failed: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Unexpected error during query processing: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Query processing error: {str(e)}"
        )


@router.post(
    "/query/stream",
    summary="Stream Query Response",
    description="Process a query with streaming response for real-time display"
)
async def stream_query(
    request: QueryRequest,
    rag_system: RAGSystem = Depends(get_rag_system)
):
    """Process a query with streaming response."""
    try:
        logger.info(f"Starting streaming query: '{request.query[:100]}...'")
        
        # Validate query
        validation_result = rag_system.validate_query(request.query)
        if not validation_result["is_valid"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "error": "Invalid query",
                    "issues": validation_result["issues"]
                }
            )
        
        async def generate_streaming_response():
            """Generate streaming response chunks."""
            try:
                chunk_count = 0
                total_content = ""
                final_response = None
                
                # Start streaming
                for chunk in rag_system.stream_query(
                    question=request.query,
                    top_k=request.top_k,
                    conversation_history=request.conversation_history
                ):
                    if isinstance(chunk, str):
                        # Stream content chunk
                        chunk_count += 1
                        total_content += chunk
                        
                        # Send chunk as JSON
                        chunk_data = {
                            "type": "content",
                            "chunk": chunk,
                            "chunk_index": chunk_count
                        }
                        yield f"data: {json.dumps(chunk_data)}\n\n"
                    else:
                        # Final response metadata
                        final_response = chunk
                
                # Send final metadata
                if final_response:
                    final_data = {
                        "type": "completion",
                        "query": final_response.query,
                        "total_chunks": chunk_count,
                        "total_length": len(total_content),
                        "sources": [
                            {
                                "clause_number": src["clause_number"],
                                "source_file": src["source_file"],
                                "content_snippet": src["content_snippet"],
                                "relevance_score": src["relevance_score"],
                                "chunk_id": src["chunk_id"]
                            }
                            for src in final_response.sources
                        ],
                        "confidence": final_response.confidence,
                        "metadata": final_response.metadata
                    }
                    yield f"data: {json.dumps(final_data)}\n\n"
                
            except Exception as e:
                # Send error in stream
                error_data = {
                    "type": "error",
                    "error": str(e)
                }
                yield f"data: {json.dumps(error_data)}\n\n"
        
        return StreamingResponse(
            generate_streaming_response(),
            media_type="text/plain",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
            }
        )
        
    except Exception as e:
        logger.error(f"Streaming query failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Streaming query failed: {str(e)}"
        )


@router.get(
    "/sample-queries",
    response_model=Dict[str, Any],
    summary="Get Sample Queries",
    description="Get sample queries for testing the system"
)
async def get_sample_queries(rag_system: RAGSystem = Depends(get_rag_system)):
    """Get sample queries for system testing."""
    try:
        sample_queries = rag_system.get_sample_queries()
        
        return {
            "sample_queries": sample_queries,
            "total_count": len(sample_queries),
            "description": "Sample queries for testing the travel insurance RAG system"
        }
        
    except Exception as e:
        logger.error(f"Failed to get sample queries: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get sample queries: {str(e)}"
        )


@router.delete(
    "/index",
    summary="Clear Index",
    description="Clear all indexed documents from the vector store"
)
async def clear_index(rag_system: RAGSystem = Depends(get_rag_system)):
    """Clear the document index."""
    try:
        logger.warning("Clearing document index via API")
        
        success = rag_system.retrieval_service.clear_index()
        
        if success:
            return {"message": "Index cleared successfully"}
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to clear index"
            )
            
    except Exception as e:
        logger.error(f"Failed to clear index: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to clear index: {str(e)}"
        )

