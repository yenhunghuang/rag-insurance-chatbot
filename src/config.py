"""Configuration Management System

Provides dataclass-based configuration with environment variable support,
validation, and multiple loading strategies for the RAG insurance chatbot.
"""

import os
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from pathlib import Path
import logging

from dotenv import load_dotenv
import yaml


class ConfigurationError(Exception):
    """Configuration-related errors."""

    pass


@dataclass
class EmbeddingConfig:
    """Configuration for text embedding generation."""

    model_name: str = field(default_factory=lambda: os.getenv("EMBEDDING_MODEL", "text-embedding-3-small"))
    batch_size: int = 32
    max_length: int = 512
    vector_dimension: int = field(default_factory=lambda: int(os.getenv("VECTOR_DIMENSION", "1536")))


@dataclass
class OpenAIConfig:
    """Configuration for OpenAI API."""
    
    api_key: str = field(default_factory=lambda: os.getenv("OPENAI_API_KEY", ""))
    timeout: int = 30


@dataclass
class PineconeConfig:
    """Configuration for Pinecone vector database."""

    api_key: str = field(default_factory=lambda: os.getenv("PINECONE_API_KEY", ""))
    environment: str = field(default_factory=lambda: os.getenv("PINECONE_ENVIRONMENT", ""))
    index_name: str = field(default_factory=lambda: os.getenv("PINECONE_INDEX_NAME", "insurance-rag-index"))
    namespace: str = field(default_factory=lambda: os.getenv("PINECONE_NAMESPACE", "travel-insurance"))
    dimension: int = field(default_factory=lambda: int(os.getenv("VECTOR_DIMENSION", "384")))
    metric: str = "cosine"


@dataclass
class RetrievalConfig:
    """Configuration for document retrieval system."""

    top_k: int = 5
    similarity_threshold: float = 0.8
    index_type: str = "pinecone"  # Changed default to pinecone
    chunk_size: int = 256
    chunk_overlap: int = 26


@dataclass
class GenerationConfig:
    """Configuration for LLM response generation."""

    model_name: str = "gpt-3.5-turbo"
    temperature: float = 0.1
    max_tokens: int = 500
    timeout: int = 30


@dataclass
class APIConfig:
    """Configuration for API service."""

    host: str = "localhost"
    port: int = 8000
    cors_origins: List[str] = field(default_factory=lambda: ["*"])
    debug: bool = False


@dataclass
class AppConfig:
    """Main application configuration."""

    # Environment variables with defaults
    log_level: str = field(default_factory=lambda: os.getenv("LOG_LEVEL", "INFO"))
    environment: str = field(
        default_factory=lambda: os.getenv("ENVIRONMENT", "development")
    )

    # File paths
    vector_store_path: str = field(
        default_factory=lambda: os.getenv(
            "VECTOR_STORE_PATH", "data/indices/faiss_index.bin"
        )
    )
    data_dir: str = "data"

    # Sub-configurations
    openai: OpenAIConfig = field(default_factory=OpenAIConfig)
    embedding: EmbeddingConfig = field(default_factory=EmbeddingConfig)
    pinecone: PineconeConfig = field(default_factory=PineconeConfig)
    retrieval: RetrievalConfig = field(default_factory=RetrievalConfig)
    generation: GenerationConfig = field(default_factory=GenerationConfig)
    api: APIConfig = field(default_factory=APIConfig)

    def __post_init__(self):
        """Validate configuration after initialization."""
        self._validate_config()
        self._setup_paths()

    def _validate_config(self):
        """Validate configuration values."""
        if not self.openai.api_key:
            raise ConfigurationError(
                "OPENAI_API_KEY environment variable is required. "
                "Please set it in your .env file or environment."
            )

        if self.retrieval.index_type == "pinecone":
            if not self.pinecone.api_key:
                raise ConfigurationError(
                    "PINECONE_API_KEY environment variable is required when using Pinecone. "
                    "Please set it in your .env file or environment."
                )
            if not self.pinecone.environment:
                raise ConfigurationError(
                    "PINECONE_ENVIRONMENT environment variable is required when using Pinecone. "
                    "Please set it in your .env file or environment."
                )

        if self.retrieval.top_k <= 0:
            raise ConfigurationError("retrieval.top_k must be positive")

        if not (0.0 <= self.retrieval.similarity_threshold <= 1.0):
            raise ConfigurationError(
                "retrieval.similarity_threshold must be between 0.0 and 1.0"
            )

        if not (0.0 <= self.generation.temperature <= 2.0):
            raise ConfigurationError(
                "generation.temperature must be between 0.0 and 2.0"
            )

        if self.generation.max_tokens <= 0:
            raise ConfigurationError("generation.max_tokens must be positive")

        if self.api.port <= 0 or self.api.port > 65535:
            raise ConfigurationError("api.port must be between 1 and 65535")

    def _setup_paths(self):
        """Ensure required directories exist."""
        data_path = Path(self.data_dir)
        data_path.mkdir(exist_ok=True)
        (data_path / "raw").mkdir(exist_ok=True)
        (data_path / "processed").mkdir(exist_ok=True)
        (data_path / "indices").mkdir(exist_ok=True)
        (data_path / "test").mkdir(exist_ok=True)


class ConfigFactory:
    """Factory for creating configuration instances with different loading strategies."""

    @staticmethod
    def load_from_env(env_file: Optional[str] = None) -> AppConfig:
        """Load configuration from environment variables.

        Args:
            env_file: Optional path to .env file to load first.

        Returns:
            Configured AppConfig instance.
        """
        if env_file:
            load_dotenv(env_file)
        else:
            # Try to load from default locations
            for env_path in [".env", "../.env"]:
                if Path(env_path).exists():
                    load_dotenv(env_path)
                    break

        return AppConfig()

    @staticmethod
    def load_from_file(config_path: str) -> AppConfig:
        """Load configuration from YAML file.

        Args:
            config_path: Path to configuration YAML file.

        Returns:
            Configured AppConfig instance.
        """
        config_file = Path(config_path)
        if not config_file.exists():
            raise ConfigurationError(f"Configuration file not found: {config_path}")

        try:
            with open(config_file, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)

            # Override environment variables with file values
            for key, value in data.items():
                if isinstance(value, dict):
                    continue
                os.environ[key.upper()] = str(value)

            config = AppConfig()

            # Apply nested configuration
            if "openai" in data:
                config.openai = OpenAIConfig(**data["openai"])
            if "embedding" in data:
                config.embedding = EmbeddingConfig(**data["embedding"])
            if "pinecone" in data:
                config.pinecone = PineconeConfig(**data["pinecone"])
            if "retrieval" in data:
                config.retrieval = RetrievalConfig(**data["retrieval"])
            if "generation" in data:
                config.generation = GenerationConfig(**data["generation"])
            if "api" in data:
                config.api = APIConfig(**data["api"])

            return config

        except yaml.YAMLError as e:
            raise ConfigurationError(f"Invalid YAML in config file: {e}")
        except Exception as e:
            raise ConfigurationError(f"Error loading config file: {e}")

    @staticmethod
    def load_from_dict(config_dict: Dict[str, Any]) -> AppConfig:
        """Load configuration from dictionary.

        Args:
            config_dict: Configuration dictionary.

        Returns:
            Configured AppConfig instance.
        """
        # Set environment variables from dictionary
        for key, value in config_dict.items():
            if not isinstance(value, dict):
                os.environ[key.upper()] = str(value)

        config = AppConfig()

        # Apply nested configuration
        if "openai" in config_dict:
            config.openai = OpenAIConfig(**config_dict["openai"])
        if "embedding" in config_dict:
            config.embedding = EmbeddingConfig(**config_dict["embedding"])
        if "pinecone" in config_dict:
            config.pinecone = PineconeConfig(**config_dict["pinecone"])
        if "retrieval" in config_dict:
            config.retrieval = RetrievalConfig(**config_dict["retrieval"])
        if "generation" in config_dict:
            config.generation = GenerationConfig(**config_dict["generation"])
        if "api" in config_dict:
            config.api = APIConfig(**config_dict["api"])

        return config


# Global configuration instance
config: Optional[AppConfig] = None


def get_config() -> AppConfig:
    """Get the global configuration instance.

    Returns:
        The global AppConfig instance.

    Raises:
        ConfigurationError: If configuration has not been initialized.
    """
    global config
    if config is None:
        raise ConfigurationError(
            "Configuration not initialized. Call ConfigFactory.load_from_env() first."
        )
    return config


def set_config(new_config: AppConfig) -> None:
    """Set the global configuration instance.

    Args:
        new_config: The new configuration to set globally.
    """
    global config
    config = new_config


# Auto-initialize with environment variables if available
try:
    config = ConfigFactory.load_from_env()
    logging.getLogger(__name__).info("Configuration loaded from environment")
except ConfigurationError:
    # Configuration will be loaded explicitly by the application
    logging.getLogger(__name__).debug(
        "Configuration not auto-loaded, waiting for explicit initialization"
    )
