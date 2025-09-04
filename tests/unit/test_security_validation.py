"""Unit tests for Security Validation module

Tests security validation, PII detection, input sanitization,
and resource protection measures.
"""

import pytest
import tempfile
import hashlib
from pathlib import Path
from unittest.mock import patch, mock_open

from src.security import SecurityValidator, SecurityConfig, SecurityAuditEvent


class TestSecurityValidator:
    """Test suite for SecurityValidator class."""

    def setup_method(self):
        """Set up test environment before each test method."""
        self.config = SecurityConfig()
        self.validator = SecurityValidator(self.config)

    def test_init_with_config(self):
        """Test security validator initialization with configuration."""
        validator = SecurityValidator(self.config)
        assert validator.config == self.config
        assert len(validator.audit_events) == 0

    def test_init_with_default_config(self):
        """Test security validator initialization with default configuration."""
        validator = SecurityValidator()
        assert validator.config is not None
        assert isinstance(validator.config, SecurityConfig)

    def test_validate_file_path_success(self):
        """Test successful file path validation."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create test file
            test_file = Path(temp_dir) / "test.txt"
            test_file.write_text("test content")
            
            is_valid, error_msg = self.validator.validate_file_path(str(test_file), temp_dir)
            
            assert is_valid is True
            assert "Valid" in error_msg

    def test_validate_file_path_traversal_attempt(self):
        """Test detection of path traversal attempts."""
        malicious_path = "../../../etc/passwd"
        
        is_valid, error_msg = self.validator.validate_file_path(malicious_path, "/safe/dir")
        
        assert is_valid is False
        assert "traversal" in error_msg.lower()

    def test_validate_file_path_outside_allowed_directory(self):
        """Test rejection of files outside allowed directory."""
        with tempfile.TemporaryDirectory() as temp_dir:
            with tempfile.TemporaryDirectory() as other_dir:
                # Create file in different directory
                other_file = Path(other_dir) / "test.txt"
                other_file.write_text("test")
                
                is_valid, error_msg = self.validator.validate_file_path(str(other_file), temp_dir)
                
                assert is_valid is False
                assert "outside allowed directory" in error_msg

    def test_validate_file_path_unsupported_extension(self):
        """Test rejection of unsupported file extensions."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create file with unsupported extension
            test_file = Path(temp_dir) / "test.exe"
            test_file.write_text("test")
            
            is_valid, error_msg = self.validator.validate_file_path(str(test_file), temp_dir)
            
            assert is_valid is False
            assert "extension" in error_msg.lower()

    def test_validate_file_size_and_type_success(self):
        """Test successful file size and type validation."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as temp_file:
            temp_file.write("test content")
            temp_path = temp_file.name
        
        try:
            is_valid, error_msg = self.validator.validate_file_size_and_type(temp_path)
            assert is_valid is True
            assert "successful" in error_msg
        finally:
            Path(temp_path).unlink(missing_ok=True)

    def test_validate_file_size_exceeded(self):
        """Test rejection of files exceeding size limit."""
        # Mock file that exceeds size limit
        with patch('pathlib.Path.stat') as mock_stat:
            with patch('pathlib.Path.exists', return_value=True):
                with patch('pathlib.Path.is_file', return_value=True):
                    mock_stat.return_value.st_size = 11 * 1024 * 1024  # 11MB
                    
                    is_valid, error_msg = self.validator.validate_file_size_and_type("large_file.txt")
                    
                    assert is_valid is False
                    assert "exceeds" in error_msg

    def test_validate_file_size_empty_file(self):
        """Test rejection of empty files."""
        with patch('pathlib.Path.stat') as mock_stat:
            with patch('pathlib.Path.exists', return_value=True):
                with patch('pathlib.Path.is_file', return_value=True):
                    mock_stat.return_value.st_size = 0
                    
                    is_valid, error_msg = self.validator.validate_file_size_and_type("empty_file.txt")
                    
                    assert is_valid is False
                    assert "empty" in error_msg

    def test_sanitize_content_script_removal(self):
        """Test removal of script injection attempts."""
        malicious_content = """正常內容
        <script>alert('XSS')</script>
        更多內容
        javascript:malicious_code()
        結束"""
        
        sanitized = self.validator.sanitize_content(malicious_content)
        
        # Script tags should be removed
        assert "<script>" not in sanitized
        assert "alert('XSS')" not in sanitized
        assert "javascript:" not in sanitized
        # Normal content should remain
        assert "正常內容" in sanitized
        assert "更多內容" in sanitized

    def test_sanitize_content_sql_injection_removal(self):
        """Test removal of SQL injection attempts."""
        malicious_content = """正常查詢內容
        UNION SELECT * FROM users
        DROP TABLE important_data
        INSERT INTO malicious VALUES
        正常結束"""
        
        sanitized = self.validator.sanitize_content(malicious_content)
        
        # SQL injection attempts should be removed
        assert "UNION SELECT" not in sanitized
        assert "DROP TABLE" not in sanitized
        assert "INSERT INTO" not in sanitized
        # Normal content should remain
        assert "正常查詢內容" in sanitized
        assert "正常結束" in sanitized

    def test_sanitize_content_null_bytes_removal(self):
        """Test removal of null bytes and control characters."""
        content_with_nulls = "正常內容\x00\x01\x02更多內容\r\n結束"
        
        sanitized = self.validator.sanitize_content(content_with_nulls)
        
        # Null bytes should be removed
        assert "\x00" not in sanitized
        assert "\x01" not in sanitized
        assert "\x02" not in sanitized
        # \r should be converted to \n
        assert "\r" not in sanitized
        # Normal content should remain
        assert "正常內容" in sanitized
        assert "更多內容" in sanitized

    def test_detect_and_mask_pii_taiwan_id(self):
        """Test detection and masking of Taiwan national ID."""
        content_with_id = "身分證字號：A123456789，請妥善保管"
        
        masked_content, pii_types = self.validator.detect_and_mask_pii(content_with_id)
        
        # PII should be detected
        assert "taiwan_id" in pii_types
        # ID should be masked
        assert "A123456789" not in masked_content
        assert "A*******89" in masked_content
        # Other content should remain
        assert "身分證字號" in masked_content
        assert "請妥善保管" in masked_content

    def test_detect_and_mask_pii_credit_card(self):
        """Test detection and masking of credit card numbers."""
        content_with_cc = "信用卡號碼：1234-5678-9012-3456"
        
        masked_content, pii_types = self.validator.detect_and_mask_pii(content_with_cc)
        
        # Credit card should be detected
        assert "credit_card" in pii_types
        # Card number should be masked
        assert "1234-5678-9012-3456" not in masked_content
        assert "*" in masked_content

    def test_detect_and_mask_pii_phone_number(self):
        """Test detection and masking of Taiwan phone numbers."""
        content_with_phone = "聯絡電話：0912345678"
        
        masked_content, pii_types = self.validator.detect_and_mask_pii(content_with_phone)
        
        # Phone number should be detected
        assert "mobile_phone" in pii_types
        # Phone should be masked
        assert "0912345678" not in masked_content
        assert "0*******78" in masked_content

    def test_detect_and_mask_pii_disabled(self):
        """Test PII detection when disabled in configuration."""
        # Disable PII detection
        config = SecurityConfig()
        config.enable_pii_detection = False
        validator = SecurityValidator(config)
        
        content_with_pii = "身分證字號：A123456789，電話：0912345678"
        
        masked_content, pii_types = validator.detect_and_mask_pii(content_with_pii)
        
        # No PII should be detected or masked
        assert len(pii_types) == 0
        assert masked_content == content_with_pii

    def test_check_resource_limits_success(self):
        """Test resource limits check with normal content."""
        normal_content = "正常的保險條款內容" * 100
        
        is_within_limits, error_msg = self.validator.check_resource_limits(normal_content)
        
        assert is_within_limits is True
        assert "passed" in error_msg

    def test_check_resource_limits_memory_exceeded(self):
        """Test resource limits check when memory limit exceeded."""
        # Create content that would exceed memory limit
        large_content = "大量內容" * 100000  # Large enough to exceed limit
        
        # Mock configuration with very low memory limit for testing
        config = SecurityConfig()
        config.max_memory_per_document = 1000  # Very low limit
        validator = SecurityValidator(config)
        
        is_within_limits, error_msg = validator.check_resource_limits(large_content)
        
        assert is_within_limits is False
        assert "memory usage" in error_msg.lower()

    def test_detect_repeated_pattern_attack_character(self):
        """Test detection of repeated character attacks."""
        attack_content = "A" * 10000  # 10,000 'A' characters
        
        is_attack = self.validator._detect_repeated_pattern_attack(attack_content)
        
        assert is_attack is True

    def test_detect_repeated_pattern_attack_pattern(self):
        """Test detection of repeated pattern attacks."""
        attack_content = "AB" * 2000  # Pattern repeated 2000 times
        
        is_attack = self.validator._detect_repeated_pattern_attack(attack_content)
        
        assert is_attack is True

    def test_detect_repeated_pattern_normal_content(self):
        """Test that normal content doesn't trigger attack detection."""
        normal_content = """第1條 旅程延誤保障
被保險人之原定搭乘班機因天候因素延誤達4小時以上時，本公司將給予理賠。
第2條 行李遺失保障
被保險人之隨身行李於旅程中遺失時，本公司將依實際損失給予理賠。"""
        
        is_attack = self.validator._detect_repeated_pattern_attack(normal_content)
        
        assert is_attack is False

    def test_calculate_file_hash(self):
        """Test file hash calculation."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as temp_file:
            temp_file.write("test content for hashing")
            temp_path = temp_file.name
        
        try:
            file_hash = self.validator.calculate_file_hash(temp_path)
            
            # Should return a valid SHA-256 hash
            assert len(file_hash) == 64  # SHA-256 hex string length
            assert all(c in '0123456789abcdef' for c in file_hash)
            
            # Same content should produce same hash
            file_hash2 = self.validator.calculate_file_hash(temp_path)
            assert file_hash == file_hash2
            
        finally:
            Path(temp_path).unlink(missing_ok=True)

    def test_calculate_file_hash_nonexistent_file(self):
        """Test file hash calculation with non-existent file."""
        file_hash = self.validator.calculate_file_hash("nonexistent_file.txt")
        assert file_hash == ""

    def test_security_audit_logging(self):
        """Test security audit event logging."""
        # Trigger a security event
        self.validator._log_security_event(
            "test_event",
            "warning",
            "Test security event",
            "test_file.txt"
        )
        
        # Check that event was logged
        events = self.validator.get_audit_events()
        assert len(events) == 1
        
        event = events[0]
        assert event['event_type'] == "test_event"
        assert event['severity'] == "warning"
        assert event['description'] == "Test security event"
        assert event['file_path'] == "test_file.txt"

    def test_audit_events_filtering(self):
        """Test filtering of audit events by severity."""
        # Add events with different severities
        self.validator._log_security_event("event1", "info", "Info event")
        self.validator._log_security_event("event2", "warning", "Warning event")
        self.validator._log_security_event("event3", "error", "Error event")
        
        # Test filtering
        warning_events = self.validator.get_audit_events("warning")
        assert len(warning_events) == 1
        assert warning_events[0]['severity'] == "warning"
        
        error_events = self.validator.get_audit_events("error")
        assert len(error_events) == 1
        assert error_events[0]['severity'] == "error"
        
        all_events = self.validator.get_audit_events()
        assert len(all_events) == 3

    def test_clear_audit_events(self):
        """Test clearing of audit events."""
        # Add some events
        self.validator._log_security_event("event1", "info", "Test event 1")
        self.validator._log_security_event("event2", "info", "Test event 2")
        
        assert len(self.validator.get_audit_events()) == 2
        
        # Clear events
        self.validator.clear_audit_events()
        
        assert len(self.validator.get_audit_events()) == 0

    def test_security_audit_event_to_dict(self):
        """Test SecurityAuditEvent dictionary conversion."""
        import time
        timestamp = time.time()
        
        event = SecurityAuditEvent(
            event_type="test_event",
            severity="warning", 
            description="Test event",
            file_path="test.txt",
            file_hash="abcd1234",
            user_context="test_user",
            timestamp=timestamp
        )
        
        event_dict = event.to_dict()
        
        assert event_dict['event_type'] == "test_event"
        assert event_dict['severity'] == "warning"
        assert event_dict['description'] == "Test event"
        assert event_dict['file_path'] == "test.txt"
        assert event_dict['file_hash'] == "abcd1234"
        assert event_dict['user_context'] == "test_user"
        assert event_dict['timestamp'] == timestamp

    def test_security_logging_disabled(self):
        """Test behavior when security logging is disabled."""
        # Create validator with logging disabled
        config = SecurityConfig()
        config.enable_security_logging = False
        validator = SecurityValidator(config)
        
        # Try to log an event
        validator._log_security_event("test_event", "info", "Test message")
        
        # No events should be recorded
        events = validator.get_audit_events()
        assert len(events) == 0

    def test_pattern_compilation(self):
        """Test that all security patterns are compiled correctly."""
        patterns = [
            'script_injection_pattern',
            'sql_injection_pattern', 
            'path_traversal_pattern'
        ]
        
        for pattern_name in patterns:
            assert hasattr(self.validator, pattern_name)
            pattern = getattr(self.validator, pattern_name)
            # Test that pattern can be used for matching
            try:
                pattern.search("test string")
            except Exception as e:
                pytest.fail(f"Pattern {pattern_name} is not properly compiled: {e}")

    def test_comprehensive_security_validation_flow(self):
        """Test complete security validation workflow."""
        # Create test file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as temp_file:
            content_with_issues = """正常保險條款內容
            <script>alert('test')</script>
            身分證字號：A123456789
            信用卡：1234-5678-9012-3456
            """ + "A" * 100  # Some repeated content
            
            temp_file.write(content_with_issues)
            temp_path = temp_file.name
        
        try:
            # Test complete validation flow
            base_dir = str(Path(temp_path).parent)
            
            # 1. Path validation
            is_valid, _ = self.validator.validate_file_path(temp_path, base_dir)
            assert is_valid is True
            
            # 2. File size validation  
            is_valid, _ = self.validator.validate_file_size_and_type(temp_path)
            assert is_valid is True
            
            # 3. Content sanitization
            sanitized = self.validator.sanitize_content(content_with_issues)
            assert "<script>" not in sanitized
            
            # 4. PII detection and masking
            masked, pii_types = self.validator.detect_and_mask_pii(sanitized)
            assert len(pii_types) > 0
            assert "A123456789" not in masked
            
            # 5. Resource limits check
            is_within_limits, _ = self.validator.check_resource_limits(masked)
            assert is_within_limits is True
            
            # 6. Verify audit events were logged
            events = self.validator.get_audit_events()
            assert len(events) > 0
            
        finally:
            Path(temp_path).unlink(missing_ok=True)