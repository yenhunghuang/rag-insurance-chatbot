"""Unit tests for custom exception classes.

Tests the exception hierarchy and error handling patterns
following the testing standards from coding-standards.md.
"""

import pytest
import logging
from unittest.mock import patch, MagicMock

from src.exceptions import (
    RAGSystemError,
    ConfigurationError,
    RetrievalError,
    GenerationError,
    ProcessingError,
    ValidationError,
    APIError,
    ExternalServiceError,
)


class TestRAGSystemError:
    """Test base RAGSystemError exception class."""

    @patch("src.exceptions.logger")
    def test_basic_error_creation(self, mock_logger):
        """Test basic error creation with message."""
        error = RAGSystemError("Test error message")

        assert str(error) == "Test error message"
        assert error.message == "Test error message"
        assert error.details == {}

        # Verify error was logged
        mock_logger.error.assert_called_once()
        args, kwargs = mock_logger.error.call_args
        assert "RAGSystemError: Test error message" in args[0]
        assert kwargs["extra"]["exception_type"] == "RAGSystemError"

    @patch("src.exceptions.logger")
    def test_error_with_details(self, mock_logger):
        """Test error creation with additional details."""
        details = {"component": "test", "operation": "validation"}
        error = RAGSystemError("Test error with details", details)

        assert error.message == "Test error with details"
        assert error.details == details

        # Verify error was logged with details
        mock_logger.error.assert_called_once()
        args, kwargs = mock_logger.error.call_args
        assert kwargs["extra"]["error_details"] == details


class TestConfigurationError:
    """Test ConfigurationError exception."""

    @patch("src.exceptions.logger")
    def test_configuration_error_inheritance(self, mock_logger):
        """Test ConfigurationError inherits from RAGSystemError."""
        error = ConfigurationError("Config validation failed")

        assert isinstance(error, RAGSystemError)
        assert isinstance(error, ConfigurationError)
        assert str(error) == "Config validation failed"

        # Verify logging with correct exception type
        mock_logger.error.assert_called_once()
        args, kwargs = mock_logger.error.call_args
        assert "ConfigurationError: Config validation failed" in args[0]
        assert kwargs["extra"]["exception_type"] == "ConfigurationError"


class TestRetrievalError:
    """Test RetrievalError exception."""

    @patch("src.exceptions.logger")
    def test_retrieval_error_inheritance(self, mock_logger):
        """Test RetrievalError inherits from RAGSystemError."""
        error = RetrievalError("Vector search failed")

        assert isinstance(error, RAGSystemError)
        assert isinstance(error, RetrievalError)
        assert str(error) == "Vector search failed"

        # Verify logging with correct exception type
        mock_logger.error.assert_called_once()
        args, kwargs = mock_logger.error.call_args
        assert "RetrievalError: Vector search failed" in args[0]


class TestGenerationError:
    """Test GenerationError exception."""

    @patch("src.exceptions.logger")
    def test_generation_error_inheritance(self, mock_logger):
        """Test GenerationError inherits from RAGSystemError."""
        error = GenerationError("LLM API call failed")

        assert isinstance(error, RAGSystemError)
        assert isinstance(error, GenerationError)
        assert str(error) == "LLM API call failed"


class TestProcessingError:
    """Test ProcessingError exception."""

    @patch("src.exceptions.logger")
    def test_processing_error_inheritance(self, mock_logger):
        """Test ProcessingError inherits from RAGSystemError."""
        error = ProcessingError("Document parsing failed")

        assert isinstance(error, RAGSystemError)
        assert isinstance(error, ProcessingError)
        assert str(error) == "Document parsing failed"


class TestValidationError:
    """Test ValidationError exception."""

    @patch("src.exceptions.logger")
    def test_validation_error_inheritance(self, mock_logger):
        """Test ValidationError inherits from RAGSystemError."""
        error = ValidationError("Input validation failed")

        assert isinstance(error, RAGSystemError)
        assert isinstance(error, ValidationError)
        assert str(error) == "Input validation failed"


class TestAPIError:
    """Test APIError exception with status code."""

    @patch("src.exceptions.logger")
    def test_api_error_default_status_code(self, mock_logger):
        """Test APIError with default status code."""
        error = APIError("API request failed")

        assert isinstance(error, RAGSystemError)
        assert isinstance(error, APIError)
        assert str(error) == "API request failed"
        assert error.status_code == 500

        # Verify logging
        mock_logger.error.assert_called_once()
        args, kwargs = mock_logger.error.call_args
        assert "APIError: API request failed" in args[0]

    @patch("src.exceptions.logger")
    def test_api_error_custom_status_code(self, mock_logger):
        """Test APIError with custom status code."""
        error = APIError("Bad request", status_code=400)

        assert error.status_code == 400
        assert str(error) == "Bad request"

    @patch("src.exceptions.logger")
    def test_api_error_with_details(self, mock_logger):
        """Test APIError with details and status code."""
        details = {"endpoint": "/api/chat", "method": "POST"}
        error = APIError("Validation failed", status_code=422, details=details)

        assert error.status_code == 422
        assert error.details == details
        assert str(error) == "Validation failed"


class TestExternalServiceError:
    """Test ExternalServiceError exception."""

    @patch("src.exceptions.logger")
    def test_external_service_error_basic(self, mock_logger):
        """Test ExternalServiceError with service name."""
        error = ExternalServiceError("Service unavailable", "OpenAI API")

        assert isinstance(error, RAGSystemError)
        assert isinstance(error, ExternalServiceError)
        assert str(error) == "Service unavailable"
        assert error.service_name == "OpenAI API"

        # Verify logging
        mock_logger.error.assert_called_once()
        args, kwargs = mock_logger.error.call_args
        assert "ExternalServiceError: Service unavailable" in args[0]

    @patch("src.exceptions.logger")
    def test_external_service_error_with_details(self, mock_logger):
        """Test ExternalServiceError with details."""
        details = {"timeout": 30, "retries": 3}
        error = ExternalServiceError(
            "Connection timeout", "Vector Database", details=details
        )

        assert error.service_name == "Vector Database"
        assert error.details == details
        assert str(error) == "Connection timeout"


class TestExceptionChaining:
    """Test exception chaining and context preservation."""

    @patch("src.exceptions.logger")
    def test_exception_chaining_with_context(self, mock_logger):
        """Test proper exception chaining preserves context."""
        try:
            # Simulate original error
            raise ConnectionError("Network connection failed")
        except ConnectionError as original_error:
            # Chain with our custom exception
            custom_error = RetrievalError("Vector database unavailable")
            custom_error.__cause__ = original_error

            # Verify chaining
            assert custom_error.__cause__ is original_error
            assert isinstance(custom_error.__cause__, ConnectionError)

    def test_exception_hierarchy_catch_patterns(self):
        """Test that specific exceptions can be caught by base class."""
        # Test catching specific exception
        with pytest.raises(ConfigurationError):
            raise ConfigurationError("Config error")

        # Test catching by base class
        with pytest.raises(RAGSystemError):
            raise ConfigurationError("Config error")

        # Test catching multiple exception types
        with pytest.raises((RetrievalError, GenerationError)):
            raise RetrievalError("Retrieval failed")

    def test_exception_details_serialization(self):
        """Test that exception details are properly serializable."""
        details = {
            "query": "什麼情況下可以申請旅遊延誤賠償？",
            "threshold": 0.8,
            "results_count": 0,
            "model_name": "gpt-3.5-turbo",
        }

        error = RetrievalError("No relevant documents found", details)

        # Verify all details are preserved
        assert error.details["query"] == "什麼情況下可以申請旅遊延誤賠償？"
        assert error.details["threshold"] == 0.8
        assert error.details["results_count"] == 0
        assert error.details["model_name"] == "gpt-3.5-turbo"


class TestErrorHandlingPatterns:
    """Test common error handling patterns."""

    @patch("src.exceptions.logger")
    def test_error_creation_logs_immediately(self, mock_logger):
        """Test that errors are logged immediately when created."""
        # Create various error types
        errors = [
            ConfigurationError("Config issue"),
            RetrievalError("Search issue"),
            GenerationError("LLM issue"),
            APIError("API issue", 400),
            ExternalServiceError("Service issue", "TestService"),
        ]

        # Verify each error was logged
        assert mock_logger.error.call_count == len(errors)

        # Verify each call includes the error type
        for call, error in zip(mock_logger.error.call_args_list, errors):
            args, kwargs = call
            assert error.__class__.__name__ in args[0]
            assert kwargs["extra"]["exception_type"] == error.__class__.__name__

    def test_error_message_accessibility(self):
        """Test that error messages are accessible for user display."""
        errors = [
            ("設定檔案格式錯誤", ConfigurationError),
            ("無法找到相關的保險條款", RetrievalError),
            ("AI 回答生成失敗", GenerationError),
            ("API 請求格式不正確", APIError),
            ("外部服務暫時無法使用", ExternalServiceError),
        ]

        for message, error_class in errors:
            if error_class == ExternalServiceError:
                error = error_class(message, "TestService")
            else:
                error = error_class(message)

            # Verify message is accessible and contains Chinese text
            assert str(error) == message
            assert error.message == message
            # Verify Chinese characters are properly handled
            assert len(message.encode("utf-8")) > len(message)  # UTF-8 encoding check
