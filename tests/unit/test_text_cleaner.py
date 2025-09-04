"""Unit tests for TextCleaner class

Tests text cleaning, normalization, and Chinese text processing functionality.
"""

import pytest
from src.processing.text_cleaner import TextCleaner
from src.config import AppConfig


class TestTextCleaner:
    """Test suite for TextCleaner class."""

    def setup_method(self):
        """Set up test environment before each test method."""
        self.config = AppConfig()
        self.cleaner = TextCleaner(self.config)

    def test_init_with_config(self):
        """Test text cleaner initialization with configuration."""
        cleaner = TextCleaner(self.config)
        assert cleaner.config == self.config
        
    def test_init_with_none_config(self):
        """Test text cleaner initialization with None configuration."""
        cleaner = TextCleaner(None)
        assert cleaner.config is None

    def test_clean_text_basic_functionality(self):
        """Test basic text cleaning functionality."""
        dirty_text = "第1條   旅程延誤保障\n\n\n被保險人之原定搭乘班機"
        
        cleaned = self.cleaner.clean_text(dirty_text)
        
        assert cleaned is not None
        assert len(cleaned) > 0
        assert "第1條" in cleaned
        assert "旅程延誤保障" in cleaned

    def test_clean_text_empty_input(self):
        """Test text cleaning with empty input."""
        result = self.cleaner.clean_text("")
        assert result == ""
        
        result = self.cleaner.clean_text("   ")
        assert result == ""

    def test_clean_text_none_input(self):
        """Test text cleaning with None input."""
        result = self.cleaner.clean_text(None)
        assert result == ""

    def test_normalize_unicode(self):
        """Test Unicode normalization for Chinese characters."""
        # Test with mixed Unicode forms
        text_with_unicode = "保險條款ＡＢＣ１２３"
        
        normalized = self.cleaner._normalize_unicode(text_with_unicode)
        
        # Full-width characters should be converted to half-width
        assert "ABC123" in normalized
        assert "保險條款" in normalized

    def test_remove_page_artifacts(self):
        """Test removal of page numbers and headers/footers."""
        text_with_artifacts = """第1條 保險條款
        
第 - 1 - 頁

第2條 理賠程序

- 2 -

第3條 免責條款"""
        
        cleaned = self.cleaner._remove_page_artifacts(text_with_artifacts)
        
        # Page artifacts should be removed
        assert "第 - 1 - 頁" not in cleaned
        assert "- 2 -" not in cleaned
        # Content should be preserved
        assert "第1條 保險條款" in cleaned
        assert "第2條 理賠程序" in cleaned

    def test_clean_formatting_artifacts(self):
        """Test removal of formatting artifacts."""
        text_with_artifacts = """第1條│保險│條款
        ├─────┼─────┤
        • 保障項目
        ▪ 理賠金額
        """
        
        cleaned = self.cleaner._clean_formatting_artifacts(text_with_artifacts)
        
        # Table drawing characters should be removed
        assert "│" not in cleaned
        assert "├" not in cleaned
        assert "┼" not in cleaned
        # List markers should be normalized
        assert "• 保障項目" in cleaned

    def test_normalize_whitespace(self):
        """Test whitespace normalization."""
        text_with_whitespace = """第1條     保險條款



        第2條   理賠程序    
        
        
        第3條 免責條款"""
        
        normalized = self.cleaner._normalize_whitespace(text_with_whitespace)
        
        # Excessive whitespace should be reduced
        assert "     " not in normalized
        assert "\n\n\n\n" not in normalized
        # Content structure should be preserved
        lines = normalized.split('\n')
        content_lines = [line for line in lines if line.strip()]
        assert len(content_lines) >= 3

    def test_normalize_punctuation(self):
        """Test punctuation normalization."""
        text_with_punct = "保險條款，，，理賠程序。。。免責條款！！！"
        
        normalized = self.cleaner._normalize_punctuation(text_with_punct)
        
        # Repeated punctuation should be reduced
        assert "，，，" not in normalized
        assert "。。。" not in normalized
        assert "！！！" not in normalized
        # Single punctuation should remain
        assert "，" in normalized
        assert "。" in normalized

    def test_normalize_clause_numbers(self):
        """Test clause number normalization."""
        text_with_clauses = """第 1 條保障內容
        第2.1條理賠程序
        第 3.2.1 條免責條款"""
        
        normalized = self.cleaner._normalize_clause_numbers(text_with_clauses)
        
        # Clause numbers should be standardized
        assert "第1條" in normalized
        assert "第2.1條" in normalized
        assert "第3.2.1條" in normalized

    def test_final_cleanup(self):
        """Test final cleanup operations."""
        text_with_issues = "第1條  保險條款\r\n\r\n  第2條   理賠程序  \r\n"
        
        cleaned = self.cleaner._final_cleanup(text_with_issues)
        
        # Line endings should be normalized
        assert "\r\n" not in cleaned
        assert "\r" not in cleaned
        # Leading/trailing whitespace should be removed from lines
        lines = cleaned.split('\n')
        for line in lines:
            if line:  # Non-empty lines
                assert line == line.strip()

    def test_clean_text_chinese_traditional_characters(self):
        """Test cleaning with traditional Chinese characters."""
        traditional_text = "第1條 旅遊延誤保障：被保險人之原定搭乘班機因天候因素延誤達4小時以上時，本公司將給予理賠。"
        
        cleaned = self.cleaner.clean_text(traditional_text)
        
        # Traditional characters should be preserved
        assert "旅遊" in cleaned
        assert "給予" in cleaned
        assert "達" in cleaned

    def test_clean_text_chinese_simplified_characters(self):
        """Test cleaning with simplified Chinese characters."""
        simplified_text = "第1条 旅游延误保障：被保险人之原定搭乘班机因天候因素延误达4小时以上时，本公司将给予理赔。"
        
        cleaned = self.cleaner.clean_text(simplified_text)
        
        # Simplified characters should be preserved
        assert "旅游" in cleaned
        assert "给予" in cleaned
        assert "达" in cleaned

    def test_clean_text_mixed_chinese_english_numbers(self):
        """Test cleaning with mixed Chinese, English, and numbers."""
        mixed_text = "第1條 COVID-19相關保障：確診日期為2023年3月15日"
        
        cleaned = self.cleaner.clean_text(mixed_text)
        
        # All content should be preserved properly
        assert "第1條" in cleaned
        assert "COVID-19" in cleaned
        assert "2023年3月15日" in cleaned

    def test_clean_text_insurance_terminology(self):
        """Test cleaning preserves insurance-specific terminology."""
        insurance_text = """第3條 保險金給付
        （一）旅程延誤保險金：每次事故最高新台幣5,000元
        （二）行李遺失保險金：每次事故最高新台幣10,000元
        （三）醫療費用保險金：每次事故最高新台幣100,000元"""
        
        cleaned = self.cleaner.clean_text(insurance_text)
        
        # Insurance terminology should be preserved
        assert "保險金給付" in cleaned
        assert "旅程延誤保險金" in cleaned
        assert "新台幣" in cleaned
        assert "每次事故" in cleaned

    def test_clean_text_preserves_clause_structure(self):
        """Test that cleaning preserves clause structure."""
        structured_text = """第1條 總則
        
        第2條 保障範圍
        2.1 承保項目
        2.2 保障金額
        
        第3條 申請程序
        （一）通知義務
        （二）文件準備"""
        
        cleaned = self.cleaner.clean_text(structured_text)
        
        # Clause structure should be maintained
        assert "第1條" in cleaned
        assert "第2條" in cleaned
        assert "第3條" in cleaned
        assert "2.1" in cleaned
        assert "2.2" in cleaned
        assert "（一）" in cleaned
        assert "（二）" in cleaned

    def test_clean_text_robustness_with_malformed_input(self):
        """Test cleaner robustness with malformed input."""
        malformed_texts = [
            "第1條\x00\x01\x02保險條款",  # Null bytes and control chars
            "第1條" + "\n" * 100 + "保險條款",  # Excessive newlines
            "第1條" + " " * 1000 + "保險條款",  # Excessive spaces
            "第1條\u202e\u202d保險條款",  # Unicode directional marks
        ]
        
        for text in malformed_texts:
            try:
                cleaned = self.cleaner.clean_text(text)
                # Should not crash and should return some cleaned text
                assert isinstance(cleaned, str)
                assert "第1條" in cleaned
                assert "保險條款" in cleaned
            except Exception as e:
                pytest.fail(f"Text cleaner failed on malformed input: {e}")

    def test_get_cleaning_stats(self):
        """Test cleaning statistics generation."""
        original = "第1條   保險條款\n\n\n第2條   理賠程序    "
        cleaned = self.cleaner.clean_text(original)
        
        stats = self.cleaner.get_cleaning_stats(original, cleaned)
        
        # Verify statistics structure
        assert 'original_length' in stats
        assert 'cleaned_length' in stats
        assert 'characters_removed' in stats
        assert 'original_lines' in stats
        assert 'cleaned_lines' in stats
        assert 'compression_ratio' in stats
        
        # Verify values make sense
        assert stats['original_length'] == len(original)
        assert stats['cleaned_length'] == len(cleaned)
        assert stats['characters_removed'] == len(original) - len(cleaned)
        assert 0 <= stats['compression_ratio'] <= 1

    def test_clean_text_error_handling(self):
        """Test error handling during text cleaning."""
        # Mock internal method to raise exception
        with pytest.MonkeyPatch().context() as m:
            def mock_normalize_unicode(self, text):
                raise ValueError("Unicode error")
            
            m.setattr(TextCleaner, '_normalize_unicode', mock_normalize_unicode)
            
            # Should return original text on error
            result = self.cleaner.clean_text("test text")
            assert result == "test text"

    def test_clean_text_performance_with_large_input(self):
        """Test text cleaning performance with large input."""
        # Create a large text input (simulating large insurance document)
        large_text = "第1條 保險條款內容\n" * 1000
        
        import time
        start_time = time.time()
        cleaned = self.cleaner.clean_text(large_text)
        end_time = time.time()
        
        # Should complete in reasonable time (less than 1 second)
        processing_time = end_time - start_time
        assert processing_time < 1.0
        
        # Should still produce valid output
        assert len(cleaned) > 0
        assert "第1條" in cleaned

    def test_pattern_compilation(self):
        """Test that regex patterns are compiled correctly."""
        # Verify patterns are compiled and available
        assert hasattr(self.cleaner, 'excessive_whitespace_pattern')
        assert hasattr(self.cleaner, 'clause_number_pattern')
        assert hasattr(self.cleaner, 'page_artifact_pattern')
        
        # Test pattern matching
        test_text = "第1條 保險條款"
        matches = self.cleaner.clause_number_pattern.findall(test_text)
        assert len(matches) > 0
        assert "1" in matches[0]