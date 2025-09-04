"""Embedding Generation Service

Provides text embedding generation using OpenAI's text-embedding-3-small
with optimized Chinese language support for insurance documents.
"""

import logging
from typing import List, Union, Optional
import numpy as np
import openai
from openai import OpenAI

from ..config import get_config
from ..exceptions import RAGSystemError


logger = logging.getLogger(__name__)


class EmbeddingError(RAGSystemError):
    """Embedding generation errors."""
    pass


class EmbeddingService:
    """Service for generating text embeddings using OpenAI's embedding API."""
    
    def __init__(self, model_name: Optional[str] = None):
        """Initialize the embedding service.
        
        Args:
            model_name: Name of the OpenAI embedding model to use.
                       If None, uses configuration default.
        """
        self.config = get_config()
        self.model_name = model_name or self.config.embedding.model_name
        self._client: Optional[OpenAI] = None
        
        logger.info(f"Initializing EmbeddingService with model: {self.model_name}")
    
    @property
    def client(self) -> OpenAI:
        """Lazy loading of the OpenAI client."""
        if self._client is None:
            try:
                self._client = OpenAI(
                    api_key=self.config.openai.api_key
                )
                logger.info(f"Successfully initialized OpenAI client")
            except Exception as e:
                raise EmbeddingError(f"Failed to initialize OpenAI client: {e}")
        return self._client
    
    def get_dimension(self) -> int:
        """Get the dimension of the embedding vectors.
        
        Returns:
            The dimension of embedding vectors produced by this model.
        """
        # text-embedding-3-small produces 1536-dimensional vectors
        if self.model_name == "text-embedding-3-small":
            return 1536
        elif self.model_name == "text-embedding-3-large":
            return 3072
        else:
            return self.config.embedding.vector_dimension
    
    def encode_single(self, text: str) -> np.ndarray:
        """Generate embedding for a single text using OpenAI API.
        
        Args:
            text: Input text to embed.
            
        Returns:
            Embedding vector as numpy array.
            
        Raises:
            EmbeddingError: If embedding generation fails.
        """
        if not text or not text.strip():
            raise EmbeddingError("Cannot generate embedding for empty text")
        
        try:
            response = self.client.embeddings.create(
                input=text.strip(),
                model=self.model_name
            )
            
            embedding_data = response.data[0].embedding
            embedding = np.array(embedding_data, dtype=np.float32)
            
            # Normalize for cosine similarity (OpenAI embeddings are already normalized)
            norm = np.linalg.norm(embedding)
            if norm > 0:
                embedding = embedding / norm
            
            if embedding is None or len(embedding) == 0:
                raise EmbeddingError("API returned empty embedding")
                
            return embedding
            
        except Exception as e:
            logger.error(f"Failed to generate embedding for text: {text[:100]}...")
            raise EmbeddingError(f"Embedding generation failed: {e}")
    
    def encode_batch(self, texts: List[str]) -> List[np.ndarray]:
        """Generate embeddings for a batch of texts using OpenAI API.
        
        Args:
            texts: List of input texts to embed.
            
        Returns:
            List of embedding vectors as numpy arrays.
            
        Raises:
            EmbeddingError: If batch embedding generation fails.
        """
        if not texts:
            return []
        
        # Filter out empty texts and track indices
        non_empty_texts = []
        original_indices = []
        
        for i, text in enumerate(texts):
            if text and text.strip():
                non_empty_texts.append(text.strip())
                original_indices.append(i)
        
        if not non_empty_texts:
            raise EmbeddingError("Cannot generate embeddings for all empty texts")
        
        try:
            # OpenAI supports batch processing up to 2048 inputs per request
            batch_size = min(self.config.embedding.batch_size, 2048)
            all_embeddings = []
            
            for i in range(0, len(non_empty_texts), batch_size):
                batch = non_empty_texts[i:i + batch_size]
                
                response = self.client.embeddings.create(
                    input=batch,
                    model=self.model_name
                )
                
                batch_embeddings = []
                for embedding_obj in response.data:
                    embedding = np.array(embedding_obj.embedding, dtype=np.float32)
                    # Normalize for cosine similarity
                    norm = np.linalg.norm(embedding)
                    if norm > 0:
                        embedding = embedding / norm
                    batch_embeddings.append(embedding)
                
                all_embeddings.extend(batch_embeddings)
            
            # Create result array matching original input length
            result_embeddings = []
            embedding_idx = 0
            
            for i in range(len(texts)):
                if i in original_indices:
                    result_embeddings.append(all_embeddings[embedding_idx])
                    embedding_idx += 1
                else:
                    # Create zero embedding for empty texts
                    zero_embedding = np.zeros(self.get_dimension())
                    result_embeddings.append(zero_embedding)
            
            logger.info(f"Generated {len(result_embeddings)} embeddings in batch")
            return result_embeddings
            
        except Exception as e:
            logger.error(f"Failed to generate batch embeddings for {len(texts)} texts")
            raise EmbeddingError(f"Batch embedding generation failed: {e}")
    
    def encode(self, texts: Union[str, List[str]]) -> Union[np.ndarray, List[np.ndarray]]:
        """Generate embeddings for single text or batch of texts.
        
        Args:
            texts: Single text string or list of text strings.
            
        Returns:
            Single embedding array or list of embedding arrays.
        """
        if isinstance(texts, str):
            return self.encode_single(texts)
        else:
            return self.encode_batch(texts)
    
    def similarity(self, embedding1: np.ndarray, embedding2: np.ndarray) -> float:
        """Calculate cosine similarity between two embeddings.
        
        Args:
            embedding1: First embedding vector.
            embedding2: Second embedding vector.
            
        Returns:
            Cosine similarity score between 0 and 1.
            
        Raises:
            EmbeddingError: If embeddings have incompatible dimensions.
        """
        if embedding1.shape != embedding2.shape:
            raise EmbeddingError(
                f"Embedding dimensions mismatch: {embedding1.shape} vs {embedding2.shape}"
            )
        
        try:
            # Since embeddings are normalized, dot product equals cosine similarity
            similarity_score = float(np.dot(embedding1, embedding2))
            
            # Ensure score is in valid range [0, 1]
            similarity_score = max(0.0, min(1.0, similarity_score))
            
            return similarity_score
            
        except Exception as e:
            raise EmbeddingError(f"Similarity calculation failed: {e}")