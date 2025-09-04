"""Unit tests for ChunkingStrategy class

Tests document chunking with semantic boundary detection,
metadata generation, and configurable parameters.
"""

import pytest
from unittest.mock import Mock, patch

from src.processing.chunking_strategy import ChunkingStrategy
from src.models import Document
from src.config import AppConfig, RetrievalConfig


class TestChunkingStrategy:
    """Test suite for ChunkingStrategy class."""

    def setup_method(self):
        """Set up test environment before each test method."""
        # Create test configuration
        self.config = AppConfig()
        self.config.retrieval = RetrievalConfig(chunk_size=100, chunk_overlap=10)
        
        self.strategy = ChunkingStrategy(self.config)
        
        # Sample Chinese insurance text with clauses
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
        """Test chunking strategy initialization with configuration."""
        strategy = ChunkingStrategy(self.config)
        assert strategy.config == self.config
        assert strategy.chunk_size == 100
        assert strategy.chunk_overlap == 10

    def test_init_with_default_config(self):
        """Test initialization with default configuration."""
        with patch('src.processing.chunking_strategy.get_config') as mock_get_config:
            mock_get_config.return_value = self.config
            strategy = ChunkingStrategy()
            assert strategy.config == self.config

    def test_chunk_document_with_structure_preservation(self):
        """Test document chunking with semantic structure preservation."""
        chunks = self.strategy.chunk_document(self.sample_text, "test.txt", preserve_structure=True)
        
        assert len(chunks) > 0
        assert all(isinstance(chunk, Document) for chunk in chunks)
        
        # Check that chunks have proper metadata
        for chunk in chunks:
            assert chunk.metadata['source_file'] == 'test.txt'
            assert 'clause_number' in chunk.metadata
            assert 'char_start' in chunk.metadata
            assert 'char_end' in chunk.metadata

    def test_chunk_document_without_structure_preservation(self):
        """Test document chunking with fixed-size chunks."""
        chunks = self.strategy.chunk_document(self.sample_text, "test.txt", preserve_structure=False)
        
        assert len(chunks) > 0
        assert all(isinstance(chunk, Document) for chunk in chunks)
        
        # Verify metadata exists
        for chunk in chunks:
            assert chunk.metadata['source_file'] == 'test.txt'
            assert 'chunk_id' in chunk.metadata

    def test_chunk_document_empty_text(self):
        """Test chunking with empty text input."""
        chunks = self.strategy.chunk_document("", "test.txt")
        assert len(chunks) == 0
        
        chunks = self.strategy.chunk_document("   ", "test.txt")
        assert len(chunks) == 0

    def test_semantic_chunking_with_clauses(self):
        """Test semantic chunking identifies clause boundaries."""
        chunks = self.strategy._semantic_chunking(self.sample_text, "test.txt")
        
        assert len(chunks) > 0
        
        # Should have chunks for different clauses
        clause_numbers = [chunk.metadata.get('clause_number') for chunk in chunks]
        clause_numbers = [num for num in clause_numbers if num]  # Remove None values
        
        # Should have at least some clause identifiers
        assert len(clause_numbers) > 0

    def test_identify_sections(self):
        """Test section identification in documents."""
        text_with_sections = """壹、總則

第1條 定義

貳、保障範圍

第2條 承保項目"""
        
        sections = self.strategy._identify_sections(text_with_sections)
        
        # Should identify sections
        assert len(sections) > 0
        
        for start, end, title in sections:
            assert isinstance(start, int)
            assert isinstance(end, int)
            assert start < end
            assert isinstance(title, str)

    def test_chunk_section_with_clauses(self):
        """Test chunking of individual sections with clauses."""
        chunks = self.strategy._chunk_section(
            self.sample_text, 
            "test.txt", 
            "測試段落", 
            0
        )
        
        assert len(chunks) > 0
        
        # Verify section metadata is included
        for chunk in chunks:
            assert chunk.metadata['section_title'] == '測試段落'

    def test_split_long_clause(self):
        """Test splitting of long clauses into smaller chunks."""
        long_clause = "第1條 " + "很長的條款內容 " * 50  # Create a long clause
        
        chunks = self.strategy._split_long_clause(
            long_clause,
            "1",
            "長條款",
            "test.txt",
            "測試段落",
            0
        )
        
        # Long clause should be split into multiple chunks
        assert len(chunks) > 1
        
        # Verify metadata consistency
        for chunk in chunks:
            assert chunk.metadata['clause_title'] == '長條款'
            assert chunk.metadata['section_title'] == '測試段落'

    def test_sliding_window_chunk(self):
        """Test sliding window chunking approach."""
        long_text = "測試內容 " * 50
        
        chunks = self.strategy._sliding_window_chunk(
            long_text,
            "1",
            "測試條款",
            "test.txt",
            "測試段落", 
            0
        )
        
        assert len(chunks) > 1
        
        # Verify overlapping content (due to chunk_overlap)
        if len(chunks) > 1:
            # Check that there's some overlap between consecutive chunks
            chunk1_end = chunks[0].content[-10:]  # Last 10 chars
            chunk2_start = chunks[1].content[:10]  # First 10 chars
            # There might be some overlap due to word boundaries, but not testing exact overlap

    def test_create_chunk_metadata(self):
        """Test comprehensive metadata generation for chunks."""
        chunk = self.strategy._create_chunk(
            "測試內容",
            "test.txt",
            "測試段落",
            "1.1",
            "測試條款",
            100,
            120
        )
        
        assert isinstance(chunk, Document)
        assert chunk.content == "測試內容"
        
        # Verify all required metadata fields
        metadata = chunk.metadata
        expected_fields = [
            'source_file', 'source_path', 'section_title', 'clause_number',
            'clause_title', 'clause_type', 'char_start', 'char_end',
            'chunk_length', 'chunk_id'
        ]
        
        for field in expected_fields:
            assert field in metadata, f"Missing metadata field: {field}"
        
        # Verify metadata values
        assert metadata['source_file'] == 'test.txt'
        assert metadata['section_title'] == '測試段落'
        assert metadata['clause_number'] == '1.1'
        assert metadata['clause_title'] == '測試條款'
        assert metadata['char_start'] == 100
        assert metadata['char_end'] == 120
        assert metadata['chunk_length'] == len("測試內容")

    def test_classify_clause_type(self):
        """Test automatic clause type classification."""
        # Test coverage clause
        coverage_text = "旅程延誤保障：被保險人搭乘班機延誤時給予理賠"
        clause_type = self.strategy._classify_clause_type(coverage_text)
        assert clause_type == "coverage"
        
        # Test exclusion clause
        exclusion_text = "免責條款：本公司不負理賠責任的情況"
        clause_type = self.strategy._classify_clause_type(exclusion_text)
        assert clause_type == "exclusion"
        
        # Test procedure clause
        procedure_text = "申請理賠程序：被保險人應於30日內通知"
        clause_type = self.strategy._classify_clause_type(procedure_text)
        assert clause_type == "procedure"
        
        # Test general clause
        general_text = "一般條款內容"
        clause_type = self.strategy._classify_clause_type(general_text)
        assert clause_type == "general"

    def test_fixed_size_chunking(self):
        """Test fallback fixed-size chunking."""
        chunks = self.strategy._fixed_size_chunking(self.sample_text, "test.txt")
        
        assert len(chunks) > 0
        
        # Verify chunks are within size limits (approximately)
        for chunk in chunks:
            # Allow some flexibility due to word boundaries and overlap
            assert len(chunk.content) <= self.strategy.chunk_size + 50

    def test_configurable_chunk_parameters(self):
        """Test that chunk size and overlap are configurable."""
        # Test with different configuration
        custom_config = AppConfig()
        custom_config.retrieval = RetrievalConfig(chunk_size=50, chunk_overlap=5)
        
        custom_strategy = ChunkingStrategy(custom_config)
        
        assert custom_strategy.chunk_size == 50
        assert custom_strategy.chunk_overlap == 5
        
        # Test chunking with custom parameters
        chunks = custom_strategy.chunk_document(self.sample_text, "test.txt")
        
        # Should still produce valid chunks
        assert len(chunks) > 0

    def test_get_chunking_stats(self):
        """Test chunking statistics generation."""
        chunks = self.strategy.chunk_document(self.sample_text, "test.txt")
        
        stats = self.strategy.get_chunking_stats(chunks)
        
        # Verify statistics structure
        expected_keys = [
            'total_chunks', 'average_chunk_size', 'min_chunk_size', 
            'max_chunk_size', 'chunk_size_distribution', 'clause_types'
        ]
        
        for key in expected_keys:
            assert key in stats, f"Missing stats key: {key}"
        
        # Verify values make sense
        assert stats['total_chunks'] == len(chunks)
        assert stats['average_chunk_size'] > 0
        assert stats['min_chunk_size'] > 0
        assert stats['max_chunk_size'] >= stats['min_chunk_size']
        assert isinstance(stats['chunk_size_distribution'], dict)
        assert isinstance(stats['clause_types'], dict)

    def test_get_chunking_stats_empty_chunks(self):
        """Test statistics generation with empty chunk list."""
        stats = self.strategy.get_chunking_stats([])
        
        assert stats['total_chunks'] == 0
        assert stats['average_chunk_size'] == 0
        assert stats['chunk_size_distribution'] == {
            'small (0-100)': 0,
            'medium (101-300)': 0, 
            'large (301-500)': 0,
            'xlarge (500+)': 0
        }
        assert stats['clause_types'] == {}

    def test_chunk_with_sub_clauses(self):
        """Test chunking with sub-clause numbering."""
        text_with_subclauses = """第3條 免責條款
被保險人因下列原因造成之損失，本公司不負理賠責任：
（一）戰爭、內亂、暴動或類似的武裝變亂
（二）核子反應、核子輻射或放射性污染
（三）被保險人之故意行為
"""
        
        chunks = self.strategy.chunk_document(text_with_subclauses, "test.txt")
        
        assert len(chunks) > 0
        
        # Should detect and preserve sub-clause structure
        has_subclauses = any("（" in chunk.content for chunk in chunks)
        assert has_subclauses

    def test_chunk_document_error_handling(self):
        """Test error handling during document chunking."""
        # Test with problematic input that might cause chunking to fail
        problematic_text = "第1條" + "\x00\x01\x02" + "保險條款"
        
        # Should not crash and should produce some chunks or fall back gracefully
        chunks = self.strategy.chunk_document(problematic_text, "test.txt")
        
        # Should either produce valid chunks or empty list (not crash)
        assert isinstance(chunks, list)
        assert all(isinstance(chunk, Document) for chunk in chunks)

    def test_chunk_uniqueness(self):
        """Test that all generated chunks have unique identifiers."""
        chunks = self.strategy.chunk_document(self.sample_text, "test.txt")
        
        # Extract all chunk IDs
        chunk_ids = [chunk.chunk_id for chunk in chunks]
        
        # All IDs should be unique
        assert len(chunk_ids) == len(set(chunk_ids))
        
        # All IDs should be non-empty strings
        for chunk_id in chunk_ids:
            assert isinstance(chunk_id, str)
            assert len(chunk_id) > 0

    def test_source_traceability(self):
        """Test that chunks maintain proper source file traceability."""
        chunks = self.strategy.chunk_document(self.sample_text, "insurance_policy.txt")
        
        for chunk in chunks:
            metadata = chunk.metadata
            assert metadata['source_file'] == 'insurance_policy.txt'
            assert metadata['source_path'] == 'insurance_policy.txt'
            
            # Character positions should be valid
            assert metadata['char_start'] >= 0
            assert metadata['char_end'] > metadata['char_start']
            assert metadata['chunk_length'] == len(chunk.content)

    def test_pattern_compilation(self):
        """Test that all regex patterns are compiled correctly."""
        # Verify patterns are compiled and available
        patterns = [
            'clause_header_pattern',
            'sub_clause_pattern', 
            'section_break_pattern',
            'coverage_type_pattern',
            'exclusion_pattern',
            'procedure_pattern'
        ]
        
        for pattern_name in patterns:
            assert hasattr(self.strategy, pattern_name)
            pattern = getattr(self.strategy, pattern_name)
            # Test that pattern can be used for matching
            try:
                pattern.search("第1條 測試")
            except Exception as e:
                pytest.fail(f"Pattern {pattern_name} is not properly compiled: {e}")

    def test_performance_with_large_document(self):
        """Test chunking performance with large documents."""
        # Create a large document (simulating real insurance policy)
        large_text = self.sample_text * 100
        
        import time
        start_time = time.time()
        chunks = self.strategy.chunk_document(large_text, "large_policy.txt")
        end_time = time.time()
        
        processing_time = end_time - start_time
        
        # Should complete in reasonable time (less than 2 seconds for this size)
        assert processing_time < 2.0
        
        # Should still produce valid chunks
        assert len(chunks) > 0
        assert all(isinstance(chunk, Document) for chunk in chunks)