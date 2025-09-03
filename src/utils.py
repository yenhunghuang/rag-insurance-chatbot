"""Utility Functions

Common utility functions used across the RAG insurance chatbot system.
"""

import time
import logging
from functools import wraps
from typing import Any, Callable, TypeVar, Dict
from pathlib import Path
import hashlib

F = TypeVar('F', bound=Callable[..., Any])

logger = logging.getLogger(__name__)


def timer(func: F) -> F:
    """Decorator to measure function execution time."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        logger.debug(f"{func.__name__} executed in {end_time - start_time:.4f} seconds")
        return result
    return wrapper


def ensure_directory(path: str) -> Path:
    """Ensure directory exists, create if it doesn't.
    
    Args:
        path: Directory path to ensure exists.
        
    Returns:
        Path object for the directory.
    """
    dir_path = Path(path)
    dir_path.mkdir(parents=True, exist_ok=True)
    return dir_path


def calculate_text_hash(text: str) -> str:
    """Calculate SHA-256 hash of text for caching/deduplication.
    
    Args:
        text: Text to hash.
        
    Returns:
        Hexadecimal hash string.
    """
    return hashlib.sha256(text.encode('utf-8')).hexdigest()


def sanitize_filename(filename: str) -> str:
    """Sanitize filename for safe filesystem usage.
    
    Args:
        filename: Original filename.
        
    Returns:
        Sanitized filename safe for filesystem.
    """
    # Remove or replace unsafe characters
    unsafe_chars = '<>:"/\\|?*'
    for char in unsafe_chars:
        filename = filename.replace(char, '_')
    
    # Remove leading/trailing periods and spaces
    filename = filename.strip('. ')
    
    # Ensure filename is not empty
    if not filename:
        filename = "unnamed_file"
    
    return filename


def format_file_size(size_bytes: int) -> str:
    """Format file size in human-readable format.
    
    Args:
        size_bytes: Size in bytes.
        
    Returns:
        Formatted size string (e.g., "1.5 MB").
    """
    if size_bytes == 0:
        return "0 B"
    
    size_names = ["B", "KB", "MB", "GB", "TB"]
    i = 0
    while size_bytes >= 1024 and i < len(size_names) - 1:
        size_bytes /= 1024.0
        i += 1
    
    return f"{size_bytes:.1f} {size_names[i]}"


def truncate_text(text: str, max_length: int = 100) -> str:
    """Truncate text to maximum length with ellipsis.
    
    Args:
        text: Text to truncate.
        max_length: Maximum length including ellipsis.
        
    Returns:
        Truncated text with ellipsis if needed.
    """
    if len(text) <= max_length:
        return text
    
    return text[:max_length - 3] + "..."


def safe_divide(numerator: float, denominator: float, default: float = 0.0) -> float:
    """Safely divide two numbers, returning default if denominator is zero.
    
    Args:
        numerator: Number to divide.
        denominator: Number to divide by.
        default: Default value if division by zero.
        
    Returns:
        Division result or default value.
    """
    if denominator == 0:
        return default
    return numerator / denominator