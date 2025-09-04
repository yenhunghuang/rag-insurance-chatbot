"""OpenAI LLM Client Service

Provides integration with OpenAI's API for response generation
with proper error handling, rate limiting, and streaming support.
"""

import logging
from typing import List, Dict, Any, Optional, Generator
import time
from contextlib import contextmanager

from openai import OpenAI, OpenAIError
from openai.types.chat import ChatCompletion

from ..config import get_config
from ..exceptions import RAGSystemError


logger = logging.getLogger(__name__)


class LLMError(RAGSystemError):
    """LLM client errors."""
    pass


class OpenAIClient:
    """OpenAI API client with enhanced error handling and monitoring."""
    
    def __init__(self):
        """Initialize OpenAI client."""
        self.config = get_config()
        self.generation_config = self.config.generation
        
        self._client: Optional[OpenAI] = None
        self._request_count = 0
        self._last_request_time = 0.0
        
        logger.info("Initializing OpenAI client")
    
    @property
    def client(self) -> OpenAI:
        """Lazy loading of OpenAI client."""
        if self._client is None:
            try:
                self._client = OpenAI(api_key=self.config.openai.api_key)
                logger.info("Successfully initialized OpenAI client")
            except Exception as e:
                raise LLMError(f"Failed to initialize OpenAI client: {e}")
        return self._client
    
    @contextmanager
    def _rate_limit_context(self):
        """Context manager for basic rate limiting."""
        current_time = time.time()
        
        # Simple rate limiting: minimum 100ms between requests
        if current_time - self._last_request_time < 0.1:
            time.sleep(0.1)
        
        try:
            yield
        finally:
            self._request_count += 1
            self._last_request_time = time.time()
    
    def generate_response(
        self,
        messages: List[Dict[str, str]], 
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        model: Optional[str] = None
    ) -> Dict[str, Any]:
        """Generate a response using OpenAI's chat completion API.
        
        Args:
            messages: List of message dictionaries with 'role' and 'content'.
            temperature: Sampling temperature (0-2). Uses config default if None.
            max_tokens: Maximum tokens to generate. Uses config default if None.
            model: Model name to use. Uses config default if None.
            
        Returns:
            Dictionary with response content and metadata.
            
        Raises:
            LLMError: If response generation fails.
        """
        if not messages or not isinstance(messages, list):
            raise LLMError("Messages must be a non-empty list")
        
        # Validate message format
        for msg in messages:
            if not isinstance(msg, dict) or 'role' not in msg or 'content' not in msg:
                raise LLMError("Each message must have 'role' and 'content' keys")
        
        # Use config defaults if parameters not provided
        temp = temperature if temperature is not None else self.generation_config.temperature
        tokens = max_tokens if max_tokens is not None else self.generation_config.max_tokens
        model_name = model or self.generation_config.model_name
        
        try:
            with self._rate_limit_context():
                logger.info(f"Generating response with model {model_name}")
                
                start_time = time.time()
                
                response: ChatCompletion = self.client.chat.completions.create(
                    model=model_name,
                    messages=messages,
                    temperature=temp,
                    max_tokens=tokens
                )
                
                end_time = time.time()
                
                if not response.choices:
                    raise LLMError("No response choices returned from OpenAI")
                
                choice = response.choices[0]
                if not choice.message or not choice.message.content:
                    raise LLMError("Empty response content from OpenAI")
                
                # Compile response data
                result = {
                    "content": choice.message.content.strip(),
                    "model": response.model,
                    "usage": {
                        "prompt_tokens": response.usage.prompt_tokens if response.usage else 0,
                        "completion_tokens": response.usage.completion_tokens if response.usage else 0,
                        "total_tokens": response.usage.total_tokens if response.usage else 0
                    },
                    "finish_reason": choice.finish_reason,
                    "generation_time": round(end_time - start_time, 2),
                    "request_id": getattr(response, 'id', None)
                }
                
                logger.info(
                    f"Response generated successfully: "
                    f"{result['usage']['total_tokens']} tokens, "
                    f"{result['generation_time']}s"
                )
                
                return result
                
        except OpenAIError as e:
            logger.error(f"OpenAI API error: {e}")
            raise LLMError(f"OpenAI API error: {e}")
        except Exception as e:
            logger.error(f"Unexpected error during response generation: {e}")
            raise LLMError(f"Response generation failed: {e}")
    
    def generate_streaming_response(
        self,
        messages: List[Dict[str, str]],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        model: Optional[str] = None
    ) -> Generator[str, None, Dict[str, Any]]:
        """Generate a streaming response using OpenAI's API.
        
        Args:
            messages: List of message dictionaries.
            temperature: Sampling temperature.
            max_tokens: Maximum tokens to generate.
            model: Model name to use.
            
        Yields:
            Partial response content strings.
            
        Returns:
            Final metadata dictionary after streaming completes.
            
        Raises:
            LLMError: If streaming response fails.
        """
        if not messages or not isinstance(messages, list):
            raise LLMError("Messages must be a non-empty list")
        
        # Use config defaults
        temp = temperature if temperature is not None else self.generation_config.temperature
        tokens = max_tokens if max_tokens is not None else self.generation_config.max_tokens
        model_name = model or self.generation_config.model_name
        
        try:
            with self._rate_limit_context():
                logger.info(f"Starting streaming response with model {model_name}")
                
                start_time = time.time()
                full_content = ""
                
                stream = self.client.chat.completions.create(
                    model=model_name,
                    messages=messages,
                    temperature=temp,
                    max_tokens=tokens,
                    timeout=self.generation_config.timeout,
                    stream=True
                )
                
                for chunk in stream:
                    if chunk.choices and chunk.choices[0].delta:
                        delta = chunk.choices[0].delta
                        if delta.content:
                            content = delta.content
                            full_content += content
                            yield content
                
                end_time = time.time()
                
                # Return final metadata
                return {
                    "content": full_content,
                    "model": model_name,
                    "generation_time": round(end_time - start_time, 2),
                    "total_length": len(full_content)
                }
                
        except OpenAIError as e:
            logger.error(f"OpenAI streaming error: {e}")
            raise LLMError(f"OpenAI streaming error: {e}")
        except Exception as e:
            logger.error(f"Unexpected error during streaming: {e}")
            raise LLMError(f"Streaming response failed: {e}")
    
    def validate_messages(self, messages: List[Dict[str, str]]) -> bool:
        """Validate message format for OpenAI API.
        
        Args:
            messages: List of message dictionaries to validate.
            
        Returns:
            True if messages are valid, False otherwise.
        """
        if not messages or not isinstance(messages, list):
            return False
        
        valid_roles = {"system", "user", "assistant", "function"}
        
        for msg in messages:
            if not isinstance(msg, dict):
                return False
            
            if "role" not in msg or "content" not in msg:
                return False
            
            if msg["role"] not in valid_roles:
                return False
            
            if not isinstance(msg["content"], str) or not msg["content"].strip():
                return False
        
        return True
    
    def get_client_stats(self) -> Dict[str, Any]:
        """Get client usage statistics.
        
        Returns:
            Dictionary with client statistics.
        """
        return {
            "total_requests": self._request_count,
            "model": self.generation_config.model_name,
            "temperature": self.generation_config.temperature,
            "max_tokens": self.generation_config.max_tokens,
            "timeout": self.generation_config.timeout
        }
    
    def health_check(self) -> Dict[str, Any]:
        """Perform health check on OpenAI client.
        
        Returns:
            Health status information.
        """
        try:
            # Simple test request
            test_messages = [{"role": "user", "content": "Hello"}]
            response = self.generate_response(test_messages, max_tokens=1)
            
            return {
                "status": "healthy",
                "model": response["model"],
                "response_time": response["generation_time"]
            }
            
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e)
            }