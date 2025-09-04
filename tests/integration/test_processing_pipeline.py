"""Integration tests for Document Processing Pipeline

Tests end-to-end document processing workflow, Chinese text handling,
and performance with realistic insurance documents.
"""

import pytest
import tempfile
import json
import time
from pathlib import Path
from unittest.mock import patch

from src.processing import DocumentProcessor
from src.models import Document, ProcessingStats
from src.config import AppConfig, RetrievalConfig
from src.exceptions import ProcessingError, SecurityError


class TestProcessingPipelineIntegration:
    """Integration test suite for complete document processing pipeline."""

    def setup_method(self):
        """Set up test environment with realistic configuration."""
        self.config = AppConfig()
        self.config.retrieval = RetrievalConfig(
            chunk_size=200,
            chunk_overlap=20
        )
        
        # Create temporary data directory structure
        self.temp_dir = tempfile.mkdtemp()
        self.config.data_dir = self.temp_dir
        
        # Create required subdirectories
        (Path(self.temp_dir) / "raw").mkdir()
        (Path(self.temp_dir) / "processed").mkdir()
        
        self.processor = DocumentProcessor(self.config)
        
        # Realistic Chinese insurance document content
        self.realistic_insurance_text = """國泰人壽保險股份有限公司
旅行平安保險條款

第壹章 總則

第一條 契約構成
本保險契約（以下簡稱本契約）由保險單條款、要保書、批註及其他約定書面構成。

第二條 名詞定義
本契約所稱之名詞定義如下：
一、要保人：指對保險標的具有保險利益，向本公司申請訂立保險契約，並負有交付保險費義務之人。
二、被保險人：指其生命或身體為保險標的之人。
三、受益人：指被保險人或要保人約定享有保險金請求權之人，要保人或被保險人均得為受益人。

第貳章 保障內容

第三條 旅程延誤保障
被保險人預定搭乘之公共交通工具因下列原因延誤四小時（含）以上者，本公司按下列約定給付旅程延誤保險金：
（一）天候因素：包括颱風、暴雨、暴雪、濃霧等自然災害。
（二）機械故障：公共交通工具本身之機械或電子設備故障。
（三）罷工或勞資糾紛：交通運輸業從業人員之合法罷工行為。

第四條 行李遺失保障
被保險人於旅程期間，其隨身攜帶之行李物品因下列原因而遺失或毀損時，本公司依實際損失給付行李遺失保險金：
（一）竊盜或搶奪：第三人之故意犯罪行為所致。
（二）運輸業者疏失：公共交通工具承運人之作業疏失。
（三）自然災害：地震、火災、水災等不可抗力因素。

第參章 免責條款

第五條 除外責任
被保險人因下列原因所致之損失，本公司不負給付保險金責任：
（一）要保人、被保險人之故意行為。
（二）被保險人犯罪行為。
（三）被保險人酒醉駕車。
（四）戰爭（不論宣戰與否）、內亂及其類似之武裝變亂。
（五）核子反應、核子輻射或放射性污染。

第肆章 理賠程序

第六條 保險事故通知
被保險人發生保險事故時，要保人、被保險人或受益人應於知悉後十日內通知本公司，並儘速檢具下列文件：
（一）保險金給付申請書。
（二）保險單或其謄本。
（三）相關證明文件：包括但不限於醫療診斷書、警察報案證明、航空公司延誤證明等。

第七條 保險金給付
本公司應於收齊前條文件後十五日內給付保險金。但因可歸責於本公司之事由致未在前述約定期限內為給付者，應按年利一分加計利息給付。

第八條 時效
由保險契約所生之權利，自得為請求之日起，經過兩年不行使而消滅。

第伍章 其他約定

第九條 管轄法院
因本契約涉訟時，同意以本公司總公司所在地之法院為第一審管轄法院。

第十條 契約解釋
本契約條款如有疑義，以有利於被保險人之解釋為準。"""

    def teardown_method(self):
        """Clean up test environment."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_end_to_end_document_processing_workflow(self):
        """Test complete document processing from file to chunks."""
        # Create test document file
        test_file = Path(self.temp_dir) / "raw" / "insurance_policy.txt"
        test_file.write_text(self.realistic_insurance_text, encoding='utf-8')
        
        # Process the document
        content = self.processor.load_document(str(test_file))
        chunks = self.processor.process_document(content, str(test_file))
        
        # Verify processing results
        assert len(chunks) > 0
        assert all(isinstance(chunk, Document) for chunk in chunks)
        
        # Verify chunk metadata
        for chunk in chunks:
            assert chunk.metadata['source_file'] == 'insurance_policy.txt'
            assert 'clause_number' in chunk.metadata
            assert 'clause_type' in chunk.metadata
            assert chunk.metadata['char_start'] >= 0
            assert chunk.metadata['char_end'] > chunk.metadata['char_start']
        
        # Verify Chinese text preservation
        combined_content = " ".join(chunk.content for chunk in chunks)
        assert "保險條款" in combined_content
        assert "被保險人" in combined_content
        assert "理賠程序" in combined_content

    def test_batch_processing_multiple_documents(self):
        """Test batch processing of multiple insurance documents."""
        # Create multiple test documents
        documents = {
            "travel_policy.txt": self.realistic_insurance_text,
            "health_policy.txt": """第一條 健康保險保障
被保險人因疾病或意外傷害需要醫療時，本公司依約定給付醫療保險金。

第二條 住院醫療給付
被保險人因疾病或意外傷害必須住院治療時，本公司按住院日數給付住院醫療保險金。""",
            "accident_policy.txt": """第一條 意外傷害保險
被保險人因意外傷害事故致死亡或殘廢時，本公司依約定給付保險金。

第二條 意外醫療給付  
被保險人因意外傷害需要門診或住院治療時，本公司給付意外醫療保險金。"""
        }
        
        # Write documents to test directory
        for filename, content in documents.items():
            file_path = Path(self.temp_dir) / "raw" / filename
            file_path.write_text(content, encoding='utf-8')
        
        # Process documents in batch
        output_path = Path(self.temp_dir) / "processed" / "batch_chunks.json"
        stats = self.processor.process_documents_batch(
            str(Path(self.temp_dir) / "raw"),
            str(output_path)
        )
        
        # Verify batch processing statistics
        assert stats.total_documents == 3
        assert stats.processed_documents == 3
        assert stats.failed_documents == 0
        assert stats.success_rate == 1.0
        assert stats.processing_time > 0
        assert stats.average_chunk_size > 0
        
        # Verify output file was created
        assert output_path.exists()
        
        # Verify output file contains valid JSON
        with open(output_path, 'r', encoding='utf-8') as f:
            saved_chunks = json.load(f)
        
        assert len(saved_chunks) > 0
        assert all('content' in chunk for chunk in saved_chunks)
        assert all('metadata' in chunk for chunk in saved_chunks)

    def test_chinese_text_processing_traditional_simplified(self):
        """Test processing of both traditional and simplified Chinese text."""
        traditional_text = """第一條 旅遊保險條款
被保險人於旅遊期間發生意外事故時，本公司將依約給付保險金。
保險範圍包括醫療費用、住院津貼及緊急救援服務。"""
        
        simplified_text = """第一条 旅游保险条款
被保险人于旅游期间发生意外事故时，本公司将依约给付保险金。
保险范围包括医疗费用、住院津贴及紧急救援服务。"""
        
        # Process traditional Chinese
        traditional_chunks = self.processor.process_document(traditional_text, "traditional.txt")
        
        # Process simplified Chinese
        simplified_chunks = self.processor.process_document(simplified_text, "simplified.txt")
        
        # Both should process successfully
        assert len(traditional_chunks) > 0
        assert len(simplified_chunks) > 0
        
        # Verify character preservation
        traditional_content = " ".join(chunk.content for chunk in traditional_chunks)
        simplified_content = " ".join(chunk.content for chunk in simplified_chunks)
        
        # Traditional characters should be preserved
        assert "旅遊" in traditional_content
        assert "於" in traditional_content
        assert "範圍" in traditional_content
        
        # Simplified characters should be preserved
        assert "旅游" in simplified_content
        assert "于" in simplified_content
        assert "范围" in simplified_content

    def test_insurance_terminology_preservation(self):
        """Test that insurance-specific terminology is correctly preserved."""
        terminology_text = """第一條 保險術語定義
要保人：向保險公司申請保險契約之人
被保險人：保險標的之人
受益人：保險金請求權人
保險費：要保人應繳納之費用
保險金：保險公司應給付之金額
免賠額：被保險人自負之金額
承保範圍：保險公司承擔責任之範圍
除外責任：保險公司不承擔責任之情況"""
        
        chunks = self.processor.process_document(terminology_text, "terminology.txt")
        
        # Verify terminology preservation
        combined_content = " ".join(chunk.content for chunk in chunks)
        
        insurance_terms = [
            "要保人", "被保險人", "受益人", "保險費", "保險金",
            "免賠額", "承保範圍", "除外責任"
        ]
        
        for term in insurance_terms:
            assert term in combined_content

    def test_clause_structure_preservation(self):
        """Test that clause numbering and structure is preserved."""
        structured_text = """第壹章 總則

第一條 契約構成
本契約由保險單及條款構成。

第二條 名詞定義
2.1 要保人定義
2.2 被保險人定義

第貳章 保障內容

第三條 保障範圍
（一）醫療費用給付
（二）住院津貼給付
（三）手術費用給付

第四條 給付條件
4.1 通知義務
4.2 證明文件
4.3 給付期限"""
        
        chunks = self.processor.process_document(structured_text, "structured.txt")
        
        # Verify clause structure is preserved
        clause_patterns = ["第壹章", "第貳章", "第一條", "第二條", "第三條", "第四條"]
        sub_patterns = ["2.1", "2.2", "4.1", "4.2", "4.3"]
        list_patterns = ["（一）", "（二）", "（三）"]
        
        combined_content = " ".join(chunk.content for chunk in chunks)
        
        for pattern in clause_patterns + sub_patterns + list_patterns:
            assert pattern in combined_content
        
        # Verify chunk metadata contains clause information
        clause_chunks = [c for c in chunks if c.metadata.get('clause_number')]
        assert len(clause_chunks) > 0

    def test_performance_with_large_document(self):
        """Test processing performance with large insurance documents."""
        # Create a large document by repeating the realistic text
        large_text = self.realistic_insurance_text * 5  # Simulate 5x larger document
        
        start_time = time.time()
        chunks = self.processor.process_document(large_text, "large_policy.txt")
        end_time = time.time()
        
        processing_time = end_time - start_time
        
        # Should complete within reasonable time (less than 3 seconds)
        assert processing_time < 3.0
        
        # Should produce reasonable number of chunks
        assert len(chunks) > 10
        
        # All chunks should be valid
        for chunk in chunks:
            assert len(chunk.content.strip()) > 0
            assert chunk.metadata['source_file'] == 'large_policy.txt'

    def test_security_measures_in_pipeline(self):
        """Test that security measures are properly integrated in the pipeline."""
        # Create content with security issues
        content_with_issues = """第一條 正常保險條款
<script>alert('xss')</script>
身分證字號：A123456789
信用卡號：1234-5678-9012-3456
UNION SELECT * FROM users
javascript:malicious_code()

第二條 更多正常內容
被保險人權利義務說明"""
        
        # Process through pipeline
        chunks = self.processor.process_document(content_with_issues, "security_test.txt")
        
        # Verify security measures were applied
        combined_content = " ".join(chunk.content for chunk in chunks)
        
        # Script tags should be removed
        assert "<script>" not in combined_content
        assert "alert(" not in combined_content
        assert "javascript:" not in combined_content
        
        # SQL injection attempts should be removed
        assert "UNION SELECT" not in combined_content
        
        # PII should be masked (if PII detection is enabled)
        if self.processor.security_validator.config.enable_pii_detection:
            assert "A123456789" not in combined_content
            assert "1234-5678-9012-3456" not in combined_content
        
        # Normal content should be preserved
        assert "正常保險條款" in combined_content
        assert "被保險人" in combined_content

    def test_error_handling_in_pipeline(self):
        """Test error handling throughout the processing pipeline."""
        # Test with various problematic inputs
        
        # 1. Empty content
        chunks = self.processor.process_document("", "empty.txt")
        assert len(chunks) == 0
        
        # 2. Only whitespace
        chunks = self.processor.process_document("   \n\n   ", "whitespace.txt")
        assert len(chunks) == 0
        
        # 3. Content with encoding issues
        problematic_content = "第一條\x00\x01\x02保險條款"
        chunks = self.processor.process_document(problematic_content, "encoding_issues.txt")
        # Should handle gracefully without crashing
        assert isinstance(chunks, list)

    def test_batch_processing_with_failures(self):
        """Test batch processing resilience when some documents fail."""
        # Create mix of valid and problematic documents
        documents = {
            "valid1.txt": "第一條 正常保險條款",
            "valid2.txt": "第二條 另一個正常條款",
            "invalid.exe": "應該被拒絕的檔案",  # Invalid extension
        }
        
        # Write documents (including invalid one that should be rejected)
        raw_dir = Path(self.temp_dir) / "raw"
        for filename, content in documents.items():
            file_path = raw_dir / filename
            file_path.write_text(content, encoding='utf-8')
        
        # Process batch (should handle mixed success/failure)
        stats = self.processor.process_documents_batch(str(raw_dir))
        
        # Should process valid documents and track failures
        assert stats.total_documents >= 2  # At least the .txt files
        assert stats.processed_documents >= 2
        assert stats.success_rate > 0

    def test_chunking_configuration_integration(self):
        """Test that chunking configuration is properly applied in integration."""
        # Test with small chunk size
        small_config = AppConfig()
        small_config.retrieval = RetrievalConfig(chunk_size=50, chunk_overlap=5)
        small_config.data_dir = self.temp_dir
        
        small_processor = DocumentProcessor(small_config)
        
        # Process same text with different configurations
        standard_chunks = self.processor.process_document(self.realistic_insurance_text, "standard.txt")
        small_chunks = small_processor.process_document(self.realistic_insurance_text, "small.txt")
        
        # Small chunk size should generally produce more chunks
        assert len(small_chunks) >= len(standard_chunks)
        
        # Verify chunk sizes are generally smaller
        avg_standard_size = sum(len(c.content) for c in standard_chunks) / len(standard_chunks)
        avg_small_size = sum(len(c.content) for c in small_chunks) / len(small_chunks)
        
        # Small chunks should be smaller on average
        assert avg_small_size <= avg_standard_size

    def test_metadata_consistency_across_pipeline(self):
        """Test that metadata remains consistent throughout processing pipeline."""
        # Create test document
        test_file = Path(self.temp_dir) / "raw" / "metadata_test.txt"
        test_file.write_text(self.realistic_insurance_text, encoding='utf-8')
        
        # Process through complete pipeline
        content = self.processor.load_document(str(test_file))
        chunks = self.processor.process_document(content, str(test_file))
        
        # Save and reload to test serialization
        output_path = Path(self.temp_dir) / "processed" / "metadata_test.json"
        self.processor._save_processed_chunks(chunks, str(output_path))
        
        # Reload and verify metadata consistency
        with open(output_path, 'r', encoding='utf-8') as f:
            saved_data = json.load(f)
        
        assert len(saved_data) == len(chunks)
        
        for original_chunk, saved_chunk in zip(chunks, saved_data):
            assert saved_chunk['content'] == original_chunk.content
            assert saved_chunk['chunk_id'] == original_chunk.chunk_id
            assert saved_chunk['metadata']['source_file'] == original_chunk.metadata['source_file']
            assert saved_chunk['metadata']['char_start'] == original_chunk.metadata['char_start']
            assert saved_chunk['metadata']['char_end'] == original_chunk.metadata['char_end']

    def test_pipeline_robustness_edge_cases(self):
        """Test pipeline handling of various edge cases."""
        edge_cases = [
            # Very short content
            "第一條",
            # Only punctuation and numbers
            "1.2.3.4 ，。；：",
            # Mixed scripts
            "第1條 Article 1 條款 Clause",
            # Repeated content
            "第一條 " * 100,
            # Special Unicode characters
            "第一條\u202e\u202d保險條款\u200b\u200c",
        ]
        
        for i, content in enumerate(edge_cases):
            try:
                chunks = self.processor.process_document(content, f"edge_case_{i}.txt")
                # Should not crash and should return valid chunks or empty list
                assert isinstance(chunks, list)
                assert all(isinstance(chunk, Document) for chunk in chunks)
            except Exception as e:
                pytest.fail(f"Pipeline failed on edge case {i}: {content[:50]}... - Error: {e}")

    def test_memory_efficiency_large_batch(self):
        """Test memory efficiency with large batch processing."""
        import psutil
        import os
        
        # Get initial memory usage
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # Create multiple medium-sized documents
        document_content = self.realistic_insurance_text * 2  # 2x size each
        
        for i in range(10):  # 10 documents
            file_path = Path(self.temp_dir) / "raw" / f"doc_{i}.txt"
            file_path.write_text(document_content, encoding='utf-8')
        
        # Process batch
        stats = self.processor.process_documents_batch(str(Path(self.temp_dir) / "raw"))
        
        # Get final memory usage
        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = final_memory - initial_memory
        
        # Should process all documents successfully
        assert stats.total_documents == 10
        assert stats.processed_documents == 10
        
        # Memory increase should be reasonable (less than 100MB for this test)
        assert memory_increase < 100, f"Memory usage increased by {memory_increase:.1f}MB"