"""Unit tests for configuration management system.

Tests the configuration loading, validation, and factory patterns
following the testing standards from coding-standards.md.
"""

import os
import pytest
import tempfile
import yaml
from pathlib import Path
from unittest.mock import patch, mock_open

from src.config import (
    AppConfig,
    EmbeddingConfig,
    RetrievalConfig,
    GenerationConfig,
    APIConfig,
    ConfigFactory,
    ConfigurationError,
    get_config,
    set_config,
)


class TestEmbeddingConfig:
    """Test EmbeddingConfig dataclass."""

    def test_default_values(self):
        """Test default configuration values."""
        config = EmbeddingConfig()

        assert config.model_name == "paraphrase-multilingual-MiniLM-L12-v2"
        assert config.batch_size == 32
        assert config.max_length == 512

    def test_custom_values(self):
        """Test custom configuration values."""
        config = EmbeddingConfig(
            model_name="custom-model", batch_size=64, max_length=1024
        )

        assert config.model_name == "custom-model"
        assert config.batch_size == 64
        assert config.max_length == 1024


class TestRetrievalConfig:
    """Test RetrievalConfig dataclass."""

    def test_default_values(self):
        """Test default configuration values."""
        config = RetrievalConfig()

        assert config.top_k == 5
        assert config.similarity_threshold == 0.8
        assert config.index_type == "faiss"
        assert config.chunk_size == 256
        assert config.chunk_overlap == 26


class TestGenerationConfig:
    """Test GenerationConfig dataclass."""

    def test_default_values(self):
        """Test default configuration values."""
        config = GenerationConfig()

        assert config.model_name == "gpt-3.5-turbo"
        assert config.temperature == 0.1
        assert config.max_tokens == 500
        assert config.timeout == 30


class TestAPIConfig:
    """Test APIConfig dataclass."""

    def test_default_values(self):
        """Test default configuration values."""
        config = APIConfig()

        assert config.host == "localhost"
        assert config.port == 8000
        assert config.cors_origins == ["*"]
        assert config.debug is False


class TestAppConfig:
    """Test main AppConfig class."""

    def setup_method(self):
        """Setup for each test method."""
        # Clear global config
        import src.config

        src.config.config = None

        # Clean environment variables
        self.original_env = {}
        for key in ["OPENAI_API_KEY", "LOG_LEVEL", "ENVIRONMENT", "VECTOR_STORE_PATH"]:
            if key in os.environ:
                self.original_env[key] = os.environ[key]
                del os.environ[key]

    def teardown_method(self):
        """Cleanup after each test method."""
        # Restore original environment
        for key, value in self.original_env.items():
            os.environ[key] = value

    def test_valid_config_with_api_key(self):
        """Test valid configuration with required API key."""
        os.environ["OPENAI_API_KEY"] = "test-api-key"

        config = AppConfig()

        assert config.openai_api_key == "test-api-key"
        assert config.log_level == "INFO"
        assert config.environment == "development"
        assert isinstance(config.embedding, EmbeddingConfig)
        assert isinstance(config.retrieval, RetrievalConfig)
        assert isinstance(config.generation, GenerationConfig)
        assert isinstance(config.api, APIConfig)

    def test_missing_api_key_raises_error(self):
        """Test that missing API key raises ConfigurationError."""
        with pytest.raises(
            ConfigurationError, match="OPENAI_API_KEY environment variable is required"
        ):
            AppConfig()

    def test_invalid_retrieval_top_k(self):
        """Test validation of retrieval.top_k parameter."""
        os.environ["OPENAI_API_KEY"] = "test-api-key"

        config = AppConfig()
        config.retrieval.top_k = -1

        with pytest.raises(
            ConfigurationError, match="retrieval.top_k must be positive"
        ):
            config._validate_config()

    def test_invalid_similarity_threshold(self):
        """Test validation of similarity threshold range."""
        os.environ["OPENAI_API_KEY"] = "test-api-key"

        config = AppConfig()
        config.retrieval.similarity_threshold = 1.5

        with pytest.raises(
            ConfigurationError,
            match="retrieval.similarity_threshold must be between 0.0 and 1.0",
        ):
            config._validate_config()

    def test_invalid_temperature(self):
        """Test validation of generation temperature range."""
        os.environ["OPENAI_API_KEY"] = "test-api-key"

        config = AppConfig()
        config.generation.temperature = 3.0

        with pytest.raises(
            ConfigurationError,
            match="generation.temperature must be between 0.0 and 2.0",
        ):
            config._validate_config()

    def test_invalid_max_tokens(self):
        """Test validation of max tokens parameter."""
        os.environ["OPENAI_API_KEY"] = "test-api-key"

        config = AppConfig()
        config.generation.max_tokens = -100

        with pytest.raises(
            ConfigurationError, match="generation.max_tokens must be positive"
        ):
            config._validate_config()

    def test_invalid_api_port(self):
        """Test validation of API port range."""
        os.environ["OPENAI_API_KEY"] = "test-api-key"

        config = AppConfig()
        config.api.port = 70000

        with pytest.raises(
            ConfigurationError, match="api.port must be between 1 and 65535"
        ):
            config._validate_config()

    @patch("pathlib.Path.mkdir")
    def test_setup_paths_creates_directories(self, mock_mkdir):
        """Test that setup_paths creates required directories."""
        os.environ["OPENAI_API_KEY"] = "test-api-key"

        config = AppConfig()

        # Verify mkdir was called for each required directory
        assert mock_mkdir.call_count >= 4  # data, raw, processed, indices, test

    def test_custom_environment_variables(self):
        """Test loading custom environment variables."""
        os.environ["OPENAI_API_KEY"] = "custom-key"
        os.environ["LOG_LEVEL"] = "DEBUG"
        os.environ["ENVIRONMENT"] = "production"
        os.environ["VECTOR_STORE_PATH"] = "custom/path/index.bin"

        config = AppConfig()

        assert config.openai_api_key == "custom-key"
        assert config.log_level == "DEBUG"
        assert config.environment == "production"
        assert config.vector_store_path == "custom/path/index.bin"


class TestConfigFactory:
    """Test ConfigFactory methods."""

    def setup_method(self):
        """Setup for each test method."""
        # Clear global config
        import src.config

        src.config.config = None

        # Clean environment variables
        self.original_env = {}
        for key in ["OPENAI_API_KEY", "LOG_LEVEL", "ENVIRONMENT"]:
            if key in os.environ:
                self.original_env[key] = os.environ[key]
                del os.environ[key]

    def teardown_method(self):
        """Cleanup after each test method."""
        # Restore original environment
        for key, value in self.original_env.items():
            os.environ[key] = value

    def test_load_from_env_with_api_key(self):
        """Test loading configuration from environment."""
        os.environ["OPENAI_API_KEY"] = "env-api-key"

        config = ConfigFactory.load_from_env()

        assert isinstance(config, AppConfig)
        assert config.openai_api_key == "env-api-key"

    @patch(
        "builtins.open",
        new_callable=mock_open,
        read_data="""
openai_api_key: file-api-key
log_level: ERROR
embedding:
  model_name: custom-embedding-model
retrieval:
  top_k: 10
  similarity_threshold: 0.9
generation:
  temperature: 0.5
api:
  port: 9000
""",
    )
    @patch("pathlib.Path.exists", return_value=True)
    def test_load_from_file(self, mock_exists, mock_file):
        """Test loading configuration from YAML file."""
        config = ConfigFactory.load_from_file("test_config.yaml")

        assert isinstance(config, AppConfig)
        assert config.embedding.model_name == "custom-embedding-model"
        assert config.retrieval.top_k == 10
        assert config.retrieval.similarity_threshold == 0.9
        assert config.generation.temperature == 0.5
        assert config.api.port == 9000

    @patch("pathlib.Path.exists", return_value=False)
    def test_load_from_file_not_found(self, mock_exists):
        """Test loading from non-existent file raises error."""
        with pytest.raises(ConfigurationError, match="Configuration file not found"):
            ConfigFactory.load_from_file("nonexistent.yaml")

    def test_load_from_dict(self):
        """Test loading configuration from dictionary."""
        config_dict = {
            "openai_api_key": "dict-api-key",
            "log_level": "WARNING",
            "embedding": {"model_name": "dict-embedding-model", "batch_size": 16},
            "retrieval": {"top_k": 3, "similarity_threshold": 0.7},
        }

        config = ConfigFactory.load_from_dict(config_dict)

        assert isinstance(config, AppConfig)
        assert config.openai_api_key == "dict-api-key"
        assert config.log_level == "WARNING"
        assert config.embedding.model_name == "dict-embedding-model"
        assert config.embedding.batch_size == 16
        assert config.retrieval.top_k == 3
        assert config.retrieval.similarity_threshold == 0.7


class TestGlobalConfigManagement:
    """Test global configuration management functions."""

    def setup_method(self):
        """Setup for each test method."""
        # Clear global config
        import src.config

        src.config.config = None

    def test_get_config_not_initialized(self):
        """Test get_config raises error when not initialized."""
        with pytest.raises(ConfigurationError, match="Configuration not initialized"):
            get_config()

    def test_set_and_get_config(self):
        """Test setting and getting global configuration."""
        os.environ["OPENAI_API_KEY"] = "global-test-key"
        test_config = AppConfig()

        set_config(test_config)
        retrieved_config = get_config()

        assert retrieved_config is test_config
        assert retrieved_config.openai_api_key == "global-test-key"
