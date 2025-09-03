# Development Guide

Comprehensive guide for developers working on the RAG Insurance Chatbot project.

## 🏗️ Architecture Overview

### System Components

```
┌─────────────────────────────────────────────────────────────┐
│                    RAG System Architecture                  │
├─────────────────────────────────────────────────────────────┤
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │   FastAPI    │  │  Streamlit   │  │    Docker    │     │
│  │  (API Layer) │  │ (Frontend)   │  │ (Container)  │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
├─────────────────────────────────────────────────────────────┤
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │ Processing   │  │  Retrieval   │  │ Generation   │     │
│  │  Module      │  │   Module     │  │   Module     │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
├─────────────────────────────────────────────────────────────┤
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │    Faiss     │  │    OpenAI    │  │   Logging    │     │
│  │ (Vector DB)  │  │  (LLM API)   │  │   System     │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
└─────────────────────────────────────────────────────────────┘
```

### Module Responsibilities

- **Processing**: Document parsing, text cleaning, chunking
- **Retrieval**: Vector search, embedding generation, ranking
- **Generation**: Prompt templating, LLM integration, response formatting
- **API**: HTTP endpoints, request validation, error handling
- **Evaluation**: Metrics calculation, performance monitoring

## 🚀 Development Workflow

### 1. Environment Setup

```bash
# Clone repository
git clone <repository-url>
cd rag-insurance-chatbot

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\\Scripts\\activate

# Install all dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Install pre-commit hooks
pre-commit install

# Validate setup
python scripts/validate_dependencies.py
python scripts/check_code_quality.py
```

### 2. Configuration Management

#### Environment Files
```bash
# Development
.env                    # Local development settings
.env.example           # Template with all options
.env.production        # Production environment (if needed)
.env.testing           # Test environment settings
```

#### Configuration Loading Priority
1. Environment variables
2. .env file
3. Default values in dataclasses
4. YAML configuration file (optional)

#### Example Configuration Usage
```python
from src.config import ConfigFactory, get_config

# Load configuration
config = ConfigFactory.load_from_env()

# Access nested configuration
print(config.retrieval.top_k)        # 5
print(config.generation.temperature) # 0.1
print(config.api.port)              # 8000

# Global configuration access
from src.config import get_config
config = get_config()
```

### 3. Code Organization

#### Directory Structure
```
src/
├── __init__.py         # Package initialization
├── config.py           # Configuration management
├── models.py           # Data models and types
├── exceptions.py       # Custom exception hierarchy
├── utils.py            # Common utilities
├── main.py             # FastAPI application
├── logging_config.py   # Logging setup
├── processing/         # Document processing
│   ├── __init__.py
│   ├── document_processor.py
│   ├── text_cleaner.py
│   └── chunking_strategy.py
├── retrieval/          # Vector search and retrieval
│   ├── __init__.py
│   ├── retriever.py
│   ├── vector_store.py
│   ├── embedding_engine.py
│   └── ranking_engine.py
├── generation/         # Response generation
│   ├── __init__.py
│   ├── generator.py
│   ├── prompt_templates.py
│   ├── llm_interface.py
│   └── response_processor.py
├── api/               # API routes and middleware
│   ├── __init__.py
│   ├── routes.py
│   ├── middleware.py
│   ├── dependencies.py
│   └── schemas.py
└── evaluation/        # System evaluation
    ├── __init__.py
    ├── evaluator.py
    ├── metrics.py
    └── benchmark.py
```

#### Import Conventions
```python
# Standard library
import os
import logging
from typing import List, Dict, Optional
from pathlib import Path

# Third-party packages  
import numpy as np
import pandas as pd
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

# Local imports
from src.config import get_config
from src.models import Document, QueryResult
from src.exceptions import RAGSystemError
from .utils import timer, ensure_directory
```

### 4. Development Patterns

#### Dependency Injection
```python
# Abstract interface
from abc import ABC, abstractmethod

class RetrieverInterface(ABC):
    @abstractmethod
    def search(self, query: str, top_k: int) -> List[Document]:
        pass

# Concrete implementation
class FaissRetriever(RetrieverInterface):
    def __init__(self, config: RetrievalConfig):
        self.config = config
        
    def search(self, query: str, top_k: int) -> List[Document]:
        # Implementation
        pass

# Usage with dependency injection
class RAGEngine:
    def __init__(self, retriever: RetrieverInterface):
        self.retriever = retriever  # Depends on abstraction
```

#### Error Handling
```python
from src.exceptions import RetrievalError
import logging

logger = logging.getLogger(__name__)

def search_documents(query: str) -> List[Document]:
    try:
        # Search logic
        results = perform_search(query)
        return results
    except ConnectionError as e:
        logger.error(f"Database connection failed: {e}")
        raise RetrievalError("Vector database unavailable") from e
    except ValueError as e:
        logger.error(f"Invalid query: {e}")  
        raise RetrievalError(f"Query validation failed: {e}") from e
```

#### Async Patterns
```python
import asyncio
import aiohttp
from typing import List

class AsyncLLMClient:
    async def generate_response(self, prompt: str) -> str:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=data) as response:
                result = await response.json()
                return result['content']

# Batch processing  
async def process_multiple_queries(queries: List[str]) -> List[str]:
    client = AsyncLLMClient()
    tasks = [client.generate_response(q) for q in queries]
    return await asyncio.gather(*tasks)
```

## 🧪 Testing Strategy

### Test Categories

#### Unit Tests (70% of tests)
```python
# tests/unit/test_document_processor.py
import pytest
from unittest.mock import Mock, patch
from src.processing import DocumentProcessor

class TestDocumentProcessor:
    def setup_method(self):
        self.processor = DocumentProcessor()
        
    def test_chunk_document_valid_input(self):
        # Test single responsibility with mocked dependencies
        text = "Sample insurance clause text..."
        
        result = self.processor.chunk_document(text)
        
        assert len(result) > 0
        assert all(chunk.content for chunk in result)
```

#### Integration Tests (20% of tests)  
```python
# tests/integration/test_rag_pipeline.py
import pytest
from src.config import ConfigFactory
from src.processing import DocumentProcessor
from src.retrieval import FaissRetriever

class TestRAGIntegration:
    @pytest.fixture
    def config(self):
        return ConfigFactory.load_from_dict({
            'openai_api_key': 'test-key',
            'retrieval': {'top_k': 3}
        })
        
    def test_document_to_retrieval_pipeline(self, config):
        # Test component interaction
        processor = DocumentProcessor()
        retriever = FaissRetriever(config.retrieval)
        
        documents = processor.chunk_document("Test content")
        retriever.add_documents(documents)
        results = retriever.search("test query")
        
        assert len(results) <= config.retrieval.top_k
```

#### End-to-End Tests (10% of tests)
```python
# tests/e2e/test_api_endpoints.py
import pytest
from fastapi.testclient import TestClient
from src.main import app

class TestAPIEndpoints:
    def setup_method(self):
        self.client = TestClient(app)
        
    def test_health_endpoint(self):
        response = self.client.get("/health")
        
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"
```

### Test Configuration
```python
# tests/conftest.py
import pytest
from src.config import ConfigFactory

@pytest.fixture(scope="session")
def test_config():
    return ConfigFactory.load_from_dict({
        'openai_api_key': 'test-key',
        'log_level': 'DEBUG',
        'environment': 'testing'
    })

@pytest.fixture
def sample_documents():
    return [
        Document(content="Insurance clause 1", metadata={"type": "coverage"}),
        Document(content="Insurance clause 2", metadata={"type": "exclusion"}),
    ]
```

### Running Tests
```bash
# All tests
pytest

# Specific categories
pytest -m unit
pytest -m integration  
pytest -m e2e

# With coverage
pytest --cov=src --cov-report=html

# Parallel execution
pytest -n auto

# Specific file
pytest tests/unit/test_document_processor.py -v
```

## 📊 Performance Guidelines

### Optimization Strategies

#### 1. Vector Operations
```python
# Efficient batch processing
def generate_embeddings_batch(texts: List[str]) -> np.ndarray:
    # Process in batches to optimize memory usage
    batch_size = 32
    embeddings = []
    
    for i in range(0, len(texts), batch_size):
        batch = texts[i:i + batch_size]
        batch_embeddings = model.encode(batch)
        embeddings.append(batch_embeddings)
        
    return np.vstack(embeddings)
```

#### 2. Caching Strategy
```python
from functools import lru_cache
from typing import Optional

class EmbeddingCache:
    def __init__(self, max_size: int = 1000):
        self._cache = {}
        self.max_size = max_size
    
    @lru_cache(maxsize=1000)
    def get_cached_embedding(self, text: str) -> Optional[np.ndarray]:
        return self._cache.get(text)
```

#### 3. Async Processing
```python
import asyncio
from concurrent.futures import ThreadPoolExecutor

class AsyncDocumentProcessor:
    def __init__(self):
        self.executor = ThreadPoolExecutor(max_workers=4)
    
    async def process_documents_async(self, documents: List[str]) -> List[Document]:
        loop = asyncio.get_event_loop()
        
        tasks = [
            loop.run_in_executor(self.executor, self.process_single, doc)
            for doc in documents
        ]
        
        return await asyncio.gather(*tasks)
```

### Performance Monitoring
```python
import time
from src.utils import timer

@timer
def expensive_operation():
    # Function execution time will be logged
    pass

# Custom metrics
class PerformanceTracker:
    def __init__(self):
        self.metrics = {}
    
    def track_query_time(self, query: str, duration: float):
        self.metrics[f"query_{len(query)}"] = duration
```

## 🔧 Debugging Guidelines

### Logging Best Practices
```python
import logging
from src.logging_config import get_logger

logger = get_logger(__name__)

def process_query(query: str) -> QueryResult:
    logger.info(f"Processing query: {query[:50]}...")
    
    try:
        # Processing logic
        result = perform_processing(query)
        logger.info(f"Query processed successfully, found {len(result.documents)} docs")
        return result
        
    except Exception as e:
        logger.error(f"Query processing failed: {e}", exc_info=True)
        raise
```

### Debug Configuration
```python
# .env for debugging
LOG_LEVEL=DEBUG
ENVIRONMENT=development
DEBUG=true

# Enable detailed logging for specific modules
PYTHONPATH=src python -c "
import logging
logging.basicConfig(level=logging.DEBUG)
from src.retrieval import FaissRetriever
# Your debugging code
"
```

### Common Debug Scenarios

#### 1. Vector Search Issues
```python
def debug_vector_search(query: str, retriever: FaissRetriever):
    logger.debug(f"Query: {query}")
    
    # Check embedding generation
    embedding = retriever.generate_embedding(query)
    logger.debug(f"Query embedding shape: {embedding.shape}")
    
    # Check search results
    results = retriever.search(query, top_k=10)
    for i, (doc, score) in enumerate(results):
        logger.debug(f"Result {i}: score={score:.4f}, content={doc.content[:100]}")
```

#### 2. Configuration Issues
```python
def debug_configuration():
    from src.config import get_config
    config = get_config()
    
    logger.debug(f"Config loaded: {config}")
    logger.debug(f"OpenAI key configured: {'yes' if config.openai_api_key else 'no'}")
    logger.debug(f"Environment: {config.environment}")
```

## 🚀 Deployment

### Docker Development
```bash
# Development with hot reloading
docker-compose -f docker-compose.yml up rag-chatbot-dev

# Production build  
docker-compose up rag-chatbot

# With frontend
docker-compose --profile frontend up
```

### Environment-Specific Builds
```bash
# Production
export ENVIRONMENT=production
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up

# Staging
export ENVIRONMENT=staging  
docker-compose -f docker-compose.yml -f docker-compose.staging.yml up
```

### Health Monitoring
```python
# Custom health checks
from src.config import get_config

async def detailed_health_check():
    config = get_config()
    
    health_status = {
        "api": "healthy",
        "database": check_vector_store(),
        "openai": await check_openai_connection(),
        "memory_usage": get_memory_usage(),
        "response_time": measure_response_time()
    }
    
    return health_status
```

## 📚 Additional Resources

### External Documentation
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Pydantic Models](https://pydantic-docs.helpmanual.io/)
- [Pytest Guide](https://docs.pytest.org/en/stable/)
- [Docker Compose](https://docs.docker.com/compose/)

### Project-Specific Guides
- [Architecture Documentation](../architecture.md)
- [API Specifications](../api/)
- [Coding Standards](../architecture/coding-standards.md)
- [Technology Stack](../architecture/tech-stack.md)

---

**Happy coding! 🚀** This development guide provides the foundation for building robust, maintainable features in the RAG Insurance Chatbot system.