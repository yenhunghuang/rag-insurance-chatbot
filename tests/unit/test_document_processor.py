"""Unit tests for DocumentProcessor class

Tests document loading, processing pipeline, error handling,
and security validation according to acceptance criteria.
"""

import pytest
import tempfile
import json
from pathlib import Path
from unittest.mock import Mock, patch, mock_open
from dataclasses import asdict

from src.processing.document_processor import DocumentProcessor
from src.models import Document, ProcessingStats
from src.exceptions import ProcessingError, ValidationError, SecurityError, DocumentProcessingError
from src.config import AppConfig, RetrievalConfig


class TestDocumentProcessor:
    """Test suite for DocumentProcessor class."""

    def setup_method(self):
        """Set up test environment before each test method."""
        # Create test configuration
        self.config = AppConfig()
        self.config.retrieval = RetrievalConfig(chunk_size=100, chunk_overlap=10)
        self.config.data_dir = "test_data"
        
        # Create processor instance
        self.processor = DocumentProcessor(self.config)
        
        # Sample Chinese insurance text
        self.sample_text = """第1條 旅程延誤保障
被保險人之原定搭乘班機因天候因素延誤達4小時以上時，本公司將給予理賠。

第2條 行李遺失保障  
被保險人之隨身行李於旅程中遺失時，本公司將依實際損失給予理賠。

第3條 免責條款
被保險人因下列原因造成之損失，本公司不負理賠責任：
（一）戰爭、暴動
（二）核子反應
"""
        
    def test_init_with_config(self):
        """Test processor initialization with custom configuration."""
        processor = DocumentProcessor(self.config)
        assert processor.config == self.config
        assert processor.text_cleaner is not None
        assert processor.chunking_strategy is not None
        assert processor.security_validator is not None
        
    def test_init_with_default_config(self):
        """Test processor initialization with default configuration."""
        with patch('src.processing.document_processor.get_config') as mock_get_config:
            mock_get_config.return_value = self.config
            processor = DocumentProcessor()
            assert processor.config == self.config

    @patch('builtins.open', mock_open(read_data="Test content"))
    @patch('pathlib.Path.exists', return_value=True)
    @patch('pathlib.Path.is_file', return_value=True)
    @patch('pathlib.Path.stat')
    def test_load_document_success(self, mock_stat):
        """Test successful document loading."""
        # Mock file size within limits
        mock_stat.return_value.st_size = 1024
        
        with patch.object(self.processor, '_validate_file_path', return_value=True):
            content = self.processor.load_document("test_data/raw/test.txt")
            assert content == "Test content"

    @patch('pathlib.Path.exists', return_value=False)
    def test_load_document_file_not_found(self):
        """Test document loading when file doesn't exist."""
        with pytest.raises(ProcessingError, match="Document file not found"):
            self.processor.load_document("nonexistent.txt")

    @patch('pathlib.Path.exists', return_value=True)
    @patch('pathlib.Path.is_file', return_value=False)
    def test_load_document_not_a_file(self):
        """Test document loading when path is not a file."""
        with pytest.raises(ProcessingError, match="Path is not a file"):
            self.processor.load_document("test_directory")

    @patch('pathlib.Path.exists', return_value=True)
    @patch('pathlib.Path.is_file', return_value=True)  
    @patch('pathlib.Path.stat')
    def test_load_document_file_too_large(self, mock_stat):
        """Test document loading when file exceeds size limit."""
        # Mock file size exceeding 10MB limit
        mock_stat.return_value.st_size = 11 * 1024 * 1024
        
        with patch.object(self.processor, '_validate_file_path', return_value=True):
            with pytest.raises(ProcessingError, match="Document file too large"):
                self.processor.load_document("large_file.txt")

    def test_load_document_invalid_path(self):
        """Test document loading with invalid file path."""
        with patch.object(self.processor, '_validate_file_path', return_value=False):
            with pytest.raises(ValidationError, match="Invalid or unsafe file path"):
                self.processor.load_document("../../../etc/passwd")

    @patch('builtins.open', mock_open(read_data=""))
    @patch('pathlib.Path.exists', return_value=True)
    @patch('pathlib.Path.is_file', return_value=True)
    @patch('pathlib.Path.stat')
    def test_load_document_empty_file(self, mock_stat):
        """Test document loading when file is empty."""
        mock_stat.return_value.st_size = 0
        
        with patch.object(self.processor, '_validate_file_path', return_value=True):
            with pytest.raises(ProcessingError, match="Document file is empty"):
                self.processor.load_document("empty.txt")

    @patch('builtins.open', side_effect=UnicodeDecodeError('utf-8', b'', 0, 1, 'invalid start byte'))
    @patch('pathlib.Path.exists', return_value=True)
    @patch('pathlib.Path.is_file', return_value=True)
    @patch('pathlib.Path.stat')
    def test_load_document_encoding_fallback(self, mock_stat):
        """Test document loading with encoding fallback to Big5."""
        mock_stat.return_value.st_size = 1024
        
        with patch.object(self.processor, '_validate_file_path', return_value=True):
            # Mock Big5 encoding success
            with patch('builtins.open', mock_open(read_data="Big5 content")):
                content = self.processor.load_document("big5_file.txt")
                assert content == "Big5 content"

    def test_process_document_success(self):
        """Test successful document processing pipeline."""
        # Mock the security validator
        self.processor.security_validator.check_resource_limits = Mock(return_value=(True, "OK"))
        self.processor.security_validator.sanitize_content = Mock(return_value=self.sample_text)
        self.processor.security_validator.detect_and_mask_pii = Mock(return_value=(self.sample_text, []))
        
        chunks = self.processor.process_document(self.sample_text, "test.txt")
        
        assert len(chunks) > 0
        assert all(isinstance(chunk, Document) for chunk in chunks)
        assert all(chunk.content.strip() for chunk in chunks)
        assert all(chunk.metadata.get('source_file') == 'test.txt' for chunk in chunks)

    def test_process_document_security_validation_failure(self):
        """Test document processing when security validation fails."""
        # Mock security validation failure
        self.processor.security_validator.check_resource_limits = Mock(
            return_value=(False, "Memory limit exceeded")
        )
        
        with pytest.raises(SecurityError, match="Resource limit exceeded"):
            self.processor.process_document(self.sample_text, "test.txt")

    def test_process_document_with_pii_detection(self):
        """Test document processing with PII detection and masking."""
        text_with_pii = "聯絡電話：0912345678，身分證字號：A123456789"
        
        # Mock security validator responses
        self.processor.security_validator.check_resource_limits = Mock(return_value=(True, "OK"))
        self.processor.security_validator.sanitize_content = Mock(return_value=text_with_pii)
        self.processor.security_validator.detect_and_mask_pii = Mock(
            return_value=("聯絡電話：0*********8，身分證字號：A*******89", ["mobile_phone", "taiwan_id"])
        )
        
        chunks = self.processor.process_document(text_with_pii, "pii_test.txt")
        
        assert len(chunks) > 0
        # Verify PII was detected (check that masking was called)
        self.processor.security_validator.detect_and_mask_pii.assert_called_once()

    def test_process_document_empty_content(self):
        """Test document processing with empty content."""
        chunks = self.processor.process_document("", "empty.txt")
        assert len(chunks) == 0

    def test_process_document_preserve_structure_flag(self):
        """Test document processing with structure preservation flag."""
        # Mock security validator
        self.processor.security_validator.check_resource_limits = Mock(return_value=(True, "OK"))
        self.processor.security_validator.sanitize_content = Mock(return_value=self.sample_text)
        self.processor.security_validator.detect_and_mask_pii = Mock(return_value=(self.sample_text, []))
        
        # Test with preserve_structure=True (default)
        chunks_structured = self.processor.process_document(self.sample_text, "test.txt", preserve_structure=True)
        
        # Test with preserve_structure=False
        chunks_fixed = self.processor.process_document(self.sample_text, "test.txt", preserve_structure=False)
        
        # Both should produce chunks, but potentially different structures
        assert len(chunks_structured) > 0
        assert len(chunks_fixed) > 0

    @patch('pathlib.Path.glob')
    @patch('pathlib.Path.exists', return_value=True)
    @patch('pathlib.Path.is_dir', return_value=True)
    def test_load_documents_from_directory_success(self, mock_is_dir, mock_exists, mock_glob):
        """Test loading multiple documents from directory."""
        # Mock directory containing txt files
        mock_files = [Path("test1.txt"), Path("test2.txt")]
        mock_glob.return_value = mock_files
        
        # Mock successful document loading
        with patch.object(self.processor, 'load_document', side_effect=["Content 1", "Content 2"]):
            documents = list(self.processor.load_documents_from_directory("test_dir"))
            
            assert len(documents) == 2
            assert documents[0] == (str(mock_files[0]), "Content 1")
            assert documents[1] == (str(mock_files[1]), "Content 2")

    @patch('pathlib.Path.exists', return_value=False)
    def test_load_documents_from_directory_not_found(self):
        """Test loading documents when directory doesn't exist."""
        with pytest.raises(ProcessingError, match="Directory not found"):
            list(self.processor.load_documents_from_directory("nonexistent_dir"))

    @patch('pathlib.Path.exists', return_value=True)
    @patch('pathlib.Path.is_dir', return_value=False)
    def test_load_documents_from_directory_not_a_dir(self):
        """Test loading documents when path is not a directory."""
        with pytest.raises(ProcessingError, match="Path is not a directory"):
            list(self.processor.load_documents_from_directory("file.txt"))

    def test_process_documents_batch_success(self):
        """Test batch processing of multiple documents."""
        # Mock directory loading returning sample documents
        sample_docs = [("doc1.txt", self.sample_text), ("doc2.txt", self.sample_text)]
        
        with patch.object(self.processor, 'load_documents_from_directory', return_value=sample_docs):
            with patch.object(self.processor, 'process_document', side_effect=[
                [Document("chunk1", {"source_file": "doc1.txt"})],
                [Document("chunk2", {"source_file": "doc2.txt"})]
            ]):
                stats = self.processor.process_documents_batch("test_dir")
                
                assert stats.total_documents == 2
                assert stats.processed_documents == 2
                assert stats.failed_documents == 0
                assert stats.processing_time > 0
                assert stats.success_rate == 1.0

    def test_process_documents_batch_with_failures(self):
        """Test batch processing with some document failures."""
        sample_docs = [("doc1.txt", self.sample_text), ("doc2.txt", self.sample_text)]
        
        with patch.object(self.processor, 'load_documents_from_directory', return_value=sample_docs):
            with patch.object(self.processor, 'process_document', side_effect=[
                [Document("chunk1", {"source_file": "doc1.txt"})],
                ProcessingError("Processing failed")
            ]):
                stats = self.processor.process_documents_batch("test_dir")
                
                assert stats.total_documents == 2
                assert stats.processed_documents == 1
                assert stats.failed_documents == 1
                assert len(stats.errors) == 1
                assert stats.success_rate == 0.5

    def test_save_processed_chunks(self):
        """Test saving processed chunks to JSON file."""
        chunks = [
            Document("Content 1", {"source_file": "test.txt"}, chunk_id="chunk1"),
            Document("Content 2", {"source_file": "test.txt"}, chunk_id="chunk2")
        ]
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as temp_file:
            temp_path = temp_file.name
        
        try:
            self.processor._save_processed_chunks(chunks, temp_path)
            
            # Verify file was created and contains correct data
            with open(temp_path, 'r', encoding='utf-8') as f:
                saved_data = json.load(f)
            
            assert len(saved_data) == 2
            assert saved_data[0]['content'] == "Content 1"
            assert saved_data[1]['content'] == "Content 2"
            assert saved_data[0]['chunk_id'] == "chunk1"
            
        finally:
            Path(temp_path).unlink(missing_ok=True)

    def test_validate_file_path_security_integration(self):
        """Test file path validation using security validator."""
        # Mock security validator responses
        self.processor.security_validator.validate_file_path = Mock(return_value=(True, "Valid"))
        self.processor.security_validator.validate_file_size_and_type = Mock(return_value=(True, "Valid"))
        
        result = self.processor._validate_file_path(Path("test.txt"))
        assert result is True
        
        # Verify security validator was called
        self.processor.security_validator.validate_file_path.assert_called_once()
        self.processor.security_validator.validate_file_size_and_type.assert_called_once()

    def test_validate_file_path_security_failure(self):
        """Test file path validation when security check fails."""
        # Mock security validation failure
        self.processor.security_validator.validate_file_path = Mock(
            return_value=(False, "Path traversal detected")
        )
        
        result = self.processor._validate_file_path(Path("../../../etc/passwd"))
        assert result is False

    # Acceptance Criteria Validation Tests

    def test_ac1_document_loading_from_raw_directory(self):
        """AC1: Verify document loading from data/raw/ directory works correctly."""
        test_file = Path("test_data/raw/test.txt")
        
        # Mock file system operations
        with patch('pathlib.Path.exists', return_value=True), \
             patch('pathlib.Path.is_file', return_value=True), \
             patch('pathlib.Path.stat') as mock_stat, \
             patch('builtins.open', mock_open(read_data=self.sample_text)):
            
            mock_stat.return_value.st_size = 1024
            
            # Mock security validation success
            self.processor.security_validator.validate_file_path = Mock(return_value=(True, "Valid"))
            self.processor.security_validator.validate_file_size_and_type = Mock(return_value=(True, "Valid"))
            
            content = self.processor.load_document(str(test_file))
            assert content == self.sample_text
            
            # Verify security validation was called with correct base directory
            expected_base = str(Path("test_data/raw"))
            self.processor.security_validator.validate_file_path.assert_called_once_with(
                str(test_file), expected_base
            )

    def test_ac2_text_cleaning_normalizes_structure(self):
        """AC2: Verify text cleaning removes artifacts and normalizes structure."""
        dirty_text = """第1條   旅程延誤保障


被保險人之原定搭乘班機因天候因素延誤達4小時以上時，本公司將給予理賠。



        第2條行李遺失保障"""
        
        # Mock security validator
        self.processor.security_validator.check_resource_limits = Mock(return_value=(True, "OK"))
        self.processor.security_validator.sanitize_content = Mock(return_value=dirty_text)
        self.processor.security_validator.detect_and_mask_pii = Mock(return_value=(dirty_text, []))
        
        chunks = self.processor.process_document(dirty_text, "test.txt")
        
        # Verify text was processed and cleaned
        assert len(chunks) > 0
        for chunk in chunks:
            # Check that excessive whitespace was normalized
            assert '   ' not in chunk.content  # No triple spaces
            assert '\n\n\n' not in chunk.content  # No triple newlines

    def test_ac3_chunking_preserves_semantic_boundaries(self):
        """AC3: Confirm chunking preserves semantic boundaries and clause context."""
        # Mock security validator
        self.processor.security_validator.check_resource_limits = Mock(return_value=(True, "OK"))
        self.processor.security_validator.sanitize_content = Mock(return_value=self.sample_text)
        self.processor.security_validator.detect_and_mask_pii = Mock(return_value=(self.sample_text, []))
        
        chunks = self.processor.process_document(self.sample_text, "test.txt", preserve_structure=True)
        
        # Verify clause structure is preserved
        assert len(chunks) > 0
        
        # Check that chunks contain clause information in metadata
        clause_chunks = [c for c in chunks if c.metadata.get('clause_number')]
        assert len(clause_chunks) > 0
        
        # Verify clause numbers are preserved
        clause_numbers = [c.metadata.get('clause_number') for c in clause_chunks]
        assert any('1' in str(num) for num in clause_numbers)

    def test_ac4_structured_storage_with_metadata(self):
        """AC4: Verify structured storage with proper metadata format."""
        # Mock security validator
        self.processor.security_validator.check_resource_limits = Mock(return_value=(True, "OK"))
        self.processor.security_validator.sanitize_content = Mock(return_value=self.sample_text)
        self.processor.security_validator.detect_and_mask_pii = Mock(return_value=(self.sample_text, []))
        
        chunks = self.processor.process_document(self.sample_text, "test.txt")
        
        # Verify chunks have required metadata structure
        for chunk in chunks:
            metadata = chunk.metadata
            assert 'source_file' in metadata
            assert 'source_path' in metadata
            assert 'char_start' in metadata
            assert 'char_end' in metadata
            assert 'chunk_length' in metadata
            assert 'chunk_id' in metadata
            
            # Verify metadata values are correct
            assert metadata['source_file'] == 'test.txt'
            assert isinstance(metadata['char_start'], int)
            assert isinstance(metadata['char_end'], int)
            assert metadata['char_start'] < metadata['char_end']

    def test_ac5_configurable_chunk_parameters(self):
        """AC5: Test chunk size and overlap configuration via AppConfig."""
        # Test with custom chunk configuration
        custom_config = AppConfig()
        custom_config.retrieval = RetrievalConfig(chunk_size=50, chunk_overlap=5)
        custom_config.data_dir = "test_data"
        
        processor_custom = DocumentProcessor(custom_config)
        
        # Verify configuration is applied
        assert processor_custom.chunking_strategy.chunk_size == 50
        assert processor_custom.chunking_strategy.chunk_overlap == 5
        
        # Mock security validator for custom processor
        processor_custom.security_validator.check_resource_limits = Mock(return_value=(True, "OK"))
        processor_custom.security_validator.sanitize_content = Mock(return_value=self.sample_text)
        processor_custom.security_validator.detect_and_mask_pii = Mock(return_value=(self.sample_text, []))
        
        chunks = processor_custom.process_document(self.sample_text, "test.txt")
        
        # Verify chunks were created with custom parameters
        # (Smaller chunk size should create more chunks)
        assert len(chunks) > 0

    def test_ac6_unique_identifiers_and_traceability(self):
        """AC6: Validate unique identifiers and source traceability."""
        # Mock security validator
        self.processor.security_validator.check_resource_limits = Mock(return_value=(True, "OK"))
        self.processor.security_validator.sanitize_content = Mock(return_value=self.sample_text)
        self.processor.security_validator.detect_and_mask_pii = Mock(return_value=(self.sample_text, []))
        
        chunks = self.processor.process_document(self.sample_text, "test.txt")
        
        # Verify unique chunk IDs
        chunk_ids = [chunk.chunk_id for chunk in chunks]
        assert len(chunk_ids) == len(set(chunk_ids))  # All IDs unique
        
        # Verify source traceability
        for chunk in chunks:
            assert chunk.metadata['source_file'] == 'test.txt'
            assert chunk.metadata['source_path'] == 'test.txt'
            assert chunk.chunk_id is not None
            assert len(chunk.chunk_id) > 0

    def test_ac7_chinese_text_processing_accuracy(self):
        """AC7: Test Chinese text processing with traditional and simplified characters."""
        traditional_text = "第1條 旅遊延誤保障：被保險人之原定搭乘班機"
        simplified_text = "第1条 旅游延误保障：被保险人之原定搭乘班机"
        
        # Mock security validator for both texts
        self.processor.security_validator.check_resource_limits = Mock(return_value=(True, "OK"))
        self.processor.security_validator.sanitize_content = Mock(side_effect=lambda x: x)
        self.processor.security_validator.detect_and_mask_pii = Mock(side_effect=lambda x: (x, []))
        
        # Test traditional Chinese
        chunks_traditional = self.processor.process_document(traditional_text, "traditional.txt")
        
        # Test simplified Chinese
        chunks_simplified = self.processor.process_document(simplified_text, "simplified.txt")
        
        # Verify both processed successfully
        assert len(chunks_traditional) > 0
        assert len(chunks_simplified) > 0
        
        # Verify Chinese characters are preserved
        traditional_chunk = chunks_traditional[0]
        simplified_chunk = chunks_simplified[0]
        
        assert "旅遊" in traditional_chunk.content
        assert "旅游" in simplified_chunk.content

    def test_ac8_comprehensive_error_handling(self):
        """AC8: Confirm comprehensive error handling for all failure scenarios."""
        # Test various error scenarios
        
        # 1. File not found
        with pytest.raises(ProcessingError, match="Document file not found"):
            self.processor.load_document("nonexistent.txt")
        
        # 2. Security validation failure
        self.processor.security_validator.check_resource_limits = Mock(
            return_value=(False, "Memory limit exceeded")
        )
        
        with pytest.raises(SecurityError, match="Resource limit exceeded"):
            self.processor.process_document(self.sample_text, "test.txt")
        
        # 3. Invalid file path
        with patch.object(self.processor, '_validate_file_path', return_value=False):
            with pytest.raises(ValidationError, match="Invalid or unsafe file path"):
                self.processor.load_document("invalid_path")
        
        # 4. Processing pipeline failure
        with patch.object(self.processor.text_cleaner, 'clean_text', side_effect=Exception("Cleaning failed")):
            self.processor.security_validator.check_resource_limits = Mock(return_value=(True, "OK"))
            self.processor.security_validator.sanitize_content = Mock(return_value=self.sample_text)
            self.processor.security_validator.detect_and_mask_pii = Mock(return_value=(self.sample_text, []))
            
            with pytest.raises(DocumentProcessingError, match="Failed to process document"):
                self.processor.process_document(self.sample_text, "test.txt")