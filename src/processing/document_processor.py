"""Document Processing System

Main orchestrator for document processing pipeline including loading,
cleaning, and chunking of insurance policy documents.
"""

import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Iterator
import json
from dataclasses import asdict

from ..models import Document, ProcessingStats
from ..exceptions import ProcessingError, ValidationError, SecurityError, DocumentProcessingError
from ..config import get_config
from ..security import SecurityValidator, SecurityConfig
from .text_cleaner import TextCleaner
from .chunking_strategy import ChunkingStrategy

logger = logging.getLogger(__name__)


class DocumentProcessor:
    """Main document processing orchestrator for insurance policy documents.
    
    Coordinates document loading, text cleaning, and chunking operations
    to prepare textual content for vector embedding and retrieval.
    """
    
    def __init__(self, config=None):
        """Initialize document processor.
        
        Args:
            config: Optional configuration override. Uses global config if None.
        """
        self.config = config or get_config()
        self.text_cleaner = TextCleaner(self.config)
        self.chunking_strategy = ChunkingStrategy(self.config)
        self.security_validator = SecurityValidator(SecurityConfig())
        
    def load_document(self, file_path: str) -> str:
        """Load a single document from file path with error handling.
        
        Args:
            file_path: Path to the document file to load.
            
        Returns:
            Raw document content as string.
            
        Raises:
            ProcessingError: If file cannot be loaded or is invalid format.
            ValidationError: If file path is invalid or unsafe.
        """
        try:
            path = Path(file_path)
            
            # Validate file path and ensure it's within allowed directory
            if not self._validate_file_path(path):
                raise ValidationError(f"Invalid or unsafe file path: {file_path}")
            
            # Check file exists and is readable
            if not path.exists():
                raise ProcessingError(f"Document file not found: {file_path}")
                
            if not path.is_file():
                raise ProcessingError(f"Path is not a file: {file_path}")
            
            # Check file size limits (10MB max)
            file_size = path.stat().st_size
            max_size = 10 * 1024 * 1024  # 10MB in bytes
            if file_size > max_size:
                raise ProcessingError(
                    f"Document file too large: {file_size} bytes exceeds {max_size} bytes limit"
                )
            
            # Load file content with proper encoding
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    content = f.read()
            except UnicodeDecodeError:
                # Try alternative encodings for legacy files
                try:
                    with open(path, 'r', encoding='big5') as f:
                        content = f.read()
                    logger.info(f"Loaded document using Big5 encoding: {file_path}")
                except UnicodeDecodeError:
                    raise ProcessingError(
                        f"Unable to decode document with UTF-8 or Big5 encoding: {file_path}"
                    )
            
            if not content.strip():
                raise ProcessingError(f"Document file is empty: {file_path}")
            
            logger.info(f"Successfully loaded document: {file_path} ({len(content)} characters)")
            return content
            
        except (OSError, IOError) as e:
            raise ProcessingError(f"File I/O error loading document {file_path}: {e}") from e
            
    def load_documents_from_directory(self, directory_path: str) -> Iterator[tuple[str, str]]:
        """Load all documents from a directory with batch processing.
        
        Args:
            directory_path: Path to directory containing document files.
            
        Yields:
            Tuples of (file_path, content) for each successfully loaded document.
            
        Raises:
            ProcessingError: If directory is invalid or inaccessible.
        """
        try:
            dir_path = Path(directory_path)
            
            if not dir_path.exists():
                raise ProcessingError(f"Directory not found: {directory_path}")
                
            if not dir_path.is_dir():
                raise ProcessingError(f"Path is not a directory: {directory_path}")
            
            # Find all .txt files in directory
            txt_files = list(dir_path.glob("*.txt"))
            
            if not txt_files:
                logger.warning(f"No .txt files found in directory: {directory_path}")
                return
            
            logger.info(f"Found {len(txt_files)} document files to process")
            
            for file_path in txt_files:
                try:
                    content = self.load_document(str(file_path))
                    yield str(file_path), content
                except (ProcessingError, ValidationError) as e:
                    logger.error(f"Failed to load document {file_path}: {e}")
                    continue
                    
        except Exception as e:
            raise ProcessingError(f"Error accessing directory {directory_path}: {e}") from e
    
    def process_document(
        self, 
        content: str, 
        source_file: str,
        preserve_structure: bool = True
    ) -> List[Document]:
        """Process a single document through the complete pipeline.
        
        Args:
            content: Raw document content.
            source_file: Path to source file for metadata.
            preserve_structure: Whether to preserve clause structure during chunking.
            
        Returns:
            List of processed Document chunks with metadata.
            
        Raises:
            ProcessingError: If processing fails at any stage.
        """
        try:
            # Step 1: Security validation and resource limits check
            is_within_limits, error_msg = self.security_validator.check_resource_limits(content)
            if not is_within_limits:
                raise SecurityError(f"Resource limit exceeded for {source_file}: {error_msg}")
            
            # Step 2: Sanitize content for security
            sanitized_content = self.security_validator.sanitize_content(content)
            
            # Step 3: Detect and mask PII if enabled
            processed_content, pii_found = self.security_validator.detect_and_mask_pii(sanitized_content)
            if pii_found:
                logger.info(f"PII detected and masked in {source_file}: {', '.join(pii_found)}")
            
            # Step 4: Clean the text
            cleaned_content = self.text_cleaner.clean_text(processed_content)
            logger.debug(f"Cleaned text: {len(content)} -> {len(cleaned_content)} characters")
            
            # Step 5: Create chunks using chunking strategy
            chunks = self.chunking_strategy.chunk_document(
                cleaned_content, 
                source_file,
                preserve_structure=preserve_structure
            )
            
            logger.info(
                f"Successfully processed document {source_file}: "
                f"{len(chunks)} chunks generated"
            )
            
            return chunks
            
        except (SecurityError, ValidationError) as e:
            # Re-raise security and validation errors as-is
            raise e
        except Exception as e:
            raise DocumentProcessingError(
                f"Failed to process document {source_file}: {e}", 
                file_path=source_file
            ) from e
    
    def process_documents_batch(
        self, 
        directory_path: str,
        output_path: Optional[str] = None
    ) -> ProcessingStats:
        """Process multiple documents in batch with statistics tracking.
        
        Args:
            directory_path: Directory containing documents to process.
            output_path: Optional path to save processed chunks.
            
        Returns:
            Processing statistics including success/failure counts.
        """
        stats = ProcessingStats(
            total_documents=0,
            processed_documents=0,
            failed_documents=0,
            processing_time=0.0,
            average_chunk_size=0.0,
            errors=[]
        )
        
        all_chunks = []
        total_chunk_size = 0.0
        
        import time
        start_time = time.time()
        
        try:
            # Load and process all documents
            for file_path, content in self.load_documents_from_directory(directory_path):
                stats.total_documents += 1
                
                try:
                    chunks = self.process_document(content, file_path)
                    all_chunks.extend(chunks)
                    stats.processed_documents += 1
                    
                    # Track chunk size statistics
                    for chunk in chunks:
                        total_chunk_size += len(chunk.content)
                    
                    logger.info(f"Processed document {file_path}: {len(chunks)} chunks")
                    
                except (ProcessingError, ValidationError) as e:
                    stats.failed_documents += 1
                    error_msg = f"Failed to process {file_path}: {e}"
                    stats.errors.append(error_msg)
                    logger.error(error_msg)
            
            # Calculate statistics
            stats.processing_time = time.time() - start_time
            
            if all_chunks:
                stats.average_chunk_size = total_chunk_size / len(all_chunks)
            
            # Save processed chunks if output path specified
            if output_path and all_chunks:
                self._save_processed_chunks(all_chunks, output_path)
                logger.info(f"Saved {len(all_chunks)} chunks to {output_path}")
            
            logger.info(
                f"Batch processing completed: {stats.processed_documents}/{stats.total_documents} "
                f"documents processed in {stats.processing_time:.2f}s"
            )
            
            return stats
            
        except Exception as e:
            stats.processing_time = time.time() - start_time
            error_msg = f"Batch processing failed: {e}"
            stats.errors.append(error_msg)
            logger.error(error_msg)
            return stats
    
    def _validate_file_path(self, path: Path) -> bool:
        """Validate file path for security and format compliance.
        
        Args:
            path: Path object to validate.
            
        Returns:
            True if path is valid and safe, False otherwise.
        """
        try:
            # Use security validator for comprehensive path validation
            allowed_dir = Path(self.config.data_dir) / "raw"
            is_valid, error_msg = self.security_validator.validate_file_path(str(path), str(allowed_dir))
            
            if not is_valid:
                logger.warning(f"Security validation failed for {path}: {error_msg}")
                return False
            
            # Additional file size and type validation
            is_valid, error_msg = self.security_validator.validate_file_size_and_type(str(path))
            
            if not is_valid:
                logger.warning(f"File size/type validation failed for {path}: {error_msg}")
                return False
            
            return True
            
        except Exception as e:
            logger.warning(f"Path validation failed for {path}: {e}")
            return False
    
    def _save_processed_chunks(self, chunks: List[Document], output_path: str) -> None:
        """Save processed chunks to JSON file.
        
        Args:
            chunks: List of processed Document chunks.
            output_path: Path where to save the chunks.
        """
        try:
            output_file = Path(output_path)
            output_file.parent.mkdir(parents=True, exist_ok=True)
            
            # Convert chunks to serializable format
            chunks_data = []
            for chunk in chunks:
                chunk_dict = asdict(chunk)
                # Convert datetime to ISO string for JSON serialization
                if 'created_at' in chunk_dict:
                    chunk_dict['created_at'] = chunk.created_at.isoformat()
                chunks_data.append(chunk_dict)
            
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(chunks_data, f, ensure_ascii=False, indent=2)
                
        except Exception as e:
            raise ProcessingError(f"Failed to save processed chunks: {e}") from e