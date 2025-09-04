"""Pytest configuration and shared fixtures.

Provides common test fixtures and configuration for the RAG insurance chatbot
testing suite following testing standards from coding-standards.md.
"""

import pytest
import os
import tempfile
import json
from pathlib import Path
from typing import Dict, Any, List
from unittest.mock import MagicMock


@pytest.fixture(scope="session")
def test_data_dir():
    """Test data directory fixture."""
    return Path(__file__).parent / "data"


@pytest.fixture(scope="session")
def sample_insurance_clauses():
    """Sample insurance clauses for testing."""
    return [
        {
            "id": "3.1",
            "title": "旅程延誤保障",
            "content": "被保險人之原定搭乘班機因天候因素延誤達4小時以上時，本公司按下列標準給付旅程延誤費用保險金。",
            "type": "coverage",
        },
        {
            "id": "3.2",
            "title": "行李延誤保障",
            "content": "被保險人搭乘班機抵達目的地後，託運行李延誤達6小時以上仍未送達時，本公司給付行李延誤費用保險金。",
            "type": "coverage",
        },
        {
            "id": "4.1",
            "title": "戰爭行為除外",
            "content": "本保險不承保因戰爭、類似戰爭行為、敵人行為、武裝叛亂、革命、內亂所致之損失。",
            "type": "exclusion",
        },
    ]


@pytest.fixture(scope="function")
def mock_openai_response():
    """Mock OpenAI API response fixture."""
    return {
        "choices": [
            {
                "message": {
                    "content": "根據第3.1條規定，當班機延誤達4小時以上時，可申請旅程延誤保障。需提供航空公司延誤證明文件。",
                    "role": "assistant",
                }
            }
        ],
        "usage": {"prompt_tokens": 100, "completion_tokens": 50, "total_tokens": 150},
    }


@pytest.fixture(scope="function")
def temp_config_file():
    """Temporary configuration file fixture."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        config_data = {
            "openai_api_key": "test-key",
            "log_level": "DEBUG",
            "embedding": {"model_name": "test-embedding-model", "batch_size": 16},
            "retrieval": {"top_k": 3, "similarity_threshold": 0.7},
        }
        import yaml

        yaml.dump(config_data, f)
        temp_file_path = f.name

    yield temp_file_path

    # Cleanup
    os.unlink(temp_file_path)


@pytest.fixture(scope="function")
def clean_environment():
    """Clean environment variables fixture."""
    original_env = {}
    test_env_vars = [
        "OPENAI_API_KEY",
        "LOG_LEVEL",
        "ENVIRONMENT",
        "VECTOR_STORE_PATH",
        "DATA_DIR",
    ]

    # Save original values
    for var in test_env_vars:
        if var in os.environ:
            original_env[var] = os.environ[var]
            del os.environ[var]

    yield

    # Restore original values
    for var, value in original_env.items():
        os.environ[var] = value


@pytest.fixture(scope="function")
def mock_vector_embeddings():
    """Mock vector embeddings fixture."""
    import numpy as np

    # Create realistic looking embeddings (384 dimensions for sentence-transformers)
    return np.random.rand(3, 384).astype(np.float32)


@pytest.fixture(scope="function")
def sample_documents():
    """Sample Document objects for testing."""
    from src.models import Document

    return [
        Document(
            content="第3.1條 旅程延誤保障：被保險人之原定搭乘班機因天候因素延誤達4小時以上時...",
            metadata={"clause_id": "3.1", "type": "coverage", "article": "3"},
            chunk_id="chunk_001",
        ),
        Document(
            content="第3.2條 行李延誤保障：被保險人搭乘班機抵達目的地後，託運行李延誤達6小時以上...",
            metadata={"clause_id": "3.2", "type": "coverage", "article": "3"},
            chunk_id="chunk_002",
        ),
    ]


@pytest.fixture(scope="function")
def mock_faiss_index():
    """Mock Faiss index fixture."""
    mock_index = MagicMock()
    mock_index.ntotal = 100
    mock_index.d = 384

    # Mock search results
    import numpy as np

    mock_index.search.return_value = (
        np.array([[0.8, 0.7, 0.6]]),  # distances
        np.array([[0, 1, 2]]),  # indices
    )

    return mock_index


# Pytest configuration
pytest_plugins = []


def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line("markers", "unit: mark test as a unit test")
    config.addinivalue_line("markers", "integration: mark test as an integration test")
    config.addinivalue_line("markers", "e2e: mark test as an end-to-end test")
    config.addinivalue_line("markers", "slow: mark test as slow running")


def pytest_collection_modifyitems(config, items):
    """Modify test collection to add markers."""
    for item in items:
        # Auto-mark tests based on file path
        if "unit" in str(item.fspath):
            item.add_marker(pytest.mark.unit)
        elif "integration" in str(item.fspath):
            item.add_marker(pytest.mark.integration)
        elif "e2e" in str(item.fspath):
            item.add_marker(pytest.mark.e2e)

        # Mark slow tests
        if "docker" in str(item.fspath) or "slow" in item.name:
            item.add_marker(pytest.mark.slow)
