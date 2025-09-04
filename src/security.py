"""Security Validation and Protection Utilities

Provides security validation, PII detection, input sanitization,
and resource protection for document processing operations.
"""

import re
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import hashlib
import time
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class SecurityConfig:
    """Security configuration for document processing operations."""
    
    max_file_size: int = 10_000_000  # 10MB limit per file
    allowed_file_extensions: List[str] = field(default_factory=lambda: ['.txt'])
    enable_pii_detection: bool = True
    pii_masking_patterns: List[str] = field(default_factory=lambda: [
        r'\d{4}-\d{4}-\d{4}-\d{4}',  # Credit card patterns
        r'\d{10,11}',                # Phone numbers
        r'[A-Z]\d{9}'               # National ID patterns
    ])
    max_memory_per_document: int = 500_000_000  # 500MB memory limit
    enable_security_logging: bool = True


@dataclass
class SecurityAuditEvent:
    """Security audit event for logging security-related activities."""
    
    event_type: str
    severity: str  # 'info', 'warning', 'error', 'critical'
    description: str
    file_path: Optional[str] = None
    file_hash: Optional[str] = None
    user_context: Optional[str] = None
    timestamp: float = field(default_factory=time.time)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert audit event to dictionary for logging."""
        return {
            'event_type': self.event_type,
            'severity': self.severity,
            'description': self.description,
            'file_path': self.file_path,
            'file_hash': self.file_hash,
            'user_context': self.user_context,
            'timestamp': self.timestamp
        }


class SecurityValidator:
    """Security validation and protection for document processing.
    
    Provides comprehensive security measures including path validation,
    file size/type checks, PII detection, and resource limits.
    """
    
    def __init__(self, config: Optional[SecurityConfig] = None):
        """Initialize security validator.
        
        Args:
            config: Security configuration. Uses default if None.
        """
        self.config = config or SecurityConfig()
        self._compile_patterns()
        self.audit_events: List[SecurityAuditEvent] = []
        
    def _compile_patterns(self) -> None:
        """Compile regex patterns for security validation."""
        
        # Compile PII detection patterns
        self.pii_patterns = [re.compile(pattern) for pattern in self.config.pii_masking_patterns]
        
        # Pattern for potential script injection attempts
        self.script_injection_pattern = re.compile(
            r'<script[^>]*>.*?</script>|javascript:|vbscript:|onload=|onerror=',
            re.IGNORECASE | re.DOTALL
        )
        
        # Pattern for SQL injection attempts
        self.sql_injection_pattern = re.compile(
            r'(union\s+select|insert\s+into|delete\s+from|drop\s+table|exec\s*\()',
            re.IGNORECASE
        )
        
        # Pattern for path traversal attempts
        self.path_traversal_pattern = re.compile(r'\.\.[\\/]')
        
        # Taiwan-specific PII patterns for insurance documents
        self.taiwan_pii_patterns = [
            re.compile(r'[A-Z]\d{9}'),              # Taiwan National ID
            re.compile(r'\d{4}-\d{4}-\d{4}-\d{4}'), # Credit card
            re.compile(r'09\d{8}'),                  # Taiwan mobile numbers
            re.compile(r'\d{2}-\d{8}'),              # Taiwan landline
            re.compile(r'[A-Z]{2}\d{8}'),            # Taiwan passport
        ]
    
    def validate_file_path(self, file_path: str, allowed_base_dir: str) -> Tuple[bool, str]:
        """Validate file path for security compliance.
        
        Args:
            file_path: File path to validate.
            allowed_base_dir: Base directory that files must be within.
            
        Returns:
            Tuple of (is_valid, error_message).
        """
        try:
            path = Path(file_path)
            base_dir = Path(allowed_base_dir)
            
            # Check for path traversal attempts
            if self.path_traversal_pattern.search(str(path)):
                self._log_security_event(
                    'path_traversal_attempt',
                    'error',
                    f"Path traversal attempt detected: {file_path}",
                    file_path
                )
                return False, "Path traversal attempt detected"
            
            # Resolve paths to absolute form
            try:
                resolved_path = path.resolve()
                resolved_base = base_dir.resolve()
            except (OSError, RuntimeError) as e:
                self._log_security_event(
                    'path_resolution_failed',
                    'warning',
                    f"Path resolution failed: {e}",
                    file_path
                )
                return False, f"Path resolution failed: {e}"
            
            # Check if path is within allowed directory
            try:
                resolved_path.relative_to(resolved_base)
            except ValueError:
                self._log_security_event(
                    'unauthorized_directory_access',
                    'error',
                    f"File outside allowed directory: {resolved_path}",
                    file_path
                )
                return False, "File path outside allowed directory"
            
            # Check file extension
            if path.suffix.lower() not in self.config.allowed_file_extensions:
                self._log_security_event(
                    'unsupported_file_type',
                    'warning',
                    f"Unsupported file extension: {path.suffix}",
                    file_path
                )
                return False, f"Unsupported file extension: {path.suffix}"
            
            self._log_security_event(
                'file_path_validated',
                'info',
                f"File path validation successful: {file_path}",
                file_path
            )
            
            return True, "Valid file path"
            
        except Exception as e:
            self._log_security_event(
                'file_validation_error',
                'error',
                f"File path validation error: {e}",
                file_path
            )
            return False, f"File path validation error: {e}"
    
    def validate_file_size_and_type(self, file_path: str) -> Tuple[bool, str]:
        """Validate file size and type constraints.
        
        Args:
            file_path: Path to file to validate.
            
        Returns:
            Tuple of (is_valid, error_message).
        """
        try:
            path = Path(file_path)
            
            if not path.exists():
                return False, "File does not exist"
            
            if not path.is_file():
                return False, "Path is not a regular file"
            
            # Check file size
            file_size = path.stat().st_size
            if file_size > self.config.max_file_size:
                self._log_security_event(
                    'file_size_exceeded',
                    'error',
                    f"File size {file_size} exceeds limit {self.config.max_file_size}",
                    file_path
                )
                return False, f"File size {file_size} bytes exceeds {self.config.max_file_size} bytes limit"
            
            # Additional security checks for file content type
            if file_size == 0:
                return False, "File is empty"
            
            self._log_security_event(
                'file_size_validated',
                'info',
                f"File size validation successful: {file_size} bytes",
                file_path
            )
            
            return True, "File size and type validation successful"
            
        except Exception as e:
            self._log_security_event(
                'file_size_validation_error',
                'error',
                f"File size validation error: {e}",
                file_path
            )
            return False, f"File size validation error: {e}"
    
    def sanitize_content(self, content: str) -> str:
        """Sanitize document content to remove potential security threats.
        
        Args:
            content: Raw document content to sanitize.
            
        Returns:
            Sanitized content with threats removed.
        """
        try:
            original_length = len(content)
            
            # Remove script injection attempts
            content = self.script_injection_pattern.sub('', content)
            
            # Remove SQL injection attempts
            content = self.sql_injection_pattern.sub('', content)
            
            # Remove null bytes and other control characters that could cause issues
            content = content.replace('\x00', '').replace('\r', '\n')
            
            # Remove excessive consecutive newlines (potential DoS via memory exhaustion)
            content = re.sub(r'\n{10,}', '\n\n\n', content)
            
            sanitized_length = len(content)
            
            if original_length != sanitized_length:
                self._log_security_event(
                    'content_sanitized',
                    'warning',
                    f"Content sanitized: {original_length - sanitized_length} characters removed",
                    None
                )
            
            return content
            
        except Exception as e:
            self._log_security_event(
                'content_sanitization_error',
                'error',
                f"Content sanitization failed: {e}",
                None
            )
            # Return original content if sanitization fails to ensure robustness
            return content
    
    def detect_and_mask_pii(self, content: str) -> Tuple[str, List[str]]:
        """Detect and mask personally identifiable information.
        
        Args:
            content: Content to scan for PII.
            
        Returns:
            Tuple of (masked_content, list_of_pii_types_found).
        """
        if not self.config.enable_pii_detection:
            return content, []
        
        masked_content = content
        pii_types_found = []
        
        try:
            # Check for general PII patterns
            for i, pattern in enumerate(self.pii_patterns):
                matches = pattern.findall(content)
                if matches:
                    pii_types_found.append(f"pii_pattern_{i}")
                    # Mask the PII by replacing with asterisks, keeping first and last chars
                    for match in matches:
                        if len(match) > 2:
                            masked = match[0] + '*' * (len(match) - 2) + match[-1]
                        else:
                            masked = '*' * len(match)
                        masked_content = masked_content.replace(match, masked)
            
            # Check for Taiwan-specific PII
            pii_type_names = ['taiwan_id', 'credit_card', 'mobile_phone', 'landline', 'passport']
            for pattern, pii_type in zip(self.taiwan_pii_patterns, pii_type_names):
                matches = pattern.findall(content)
                if matches:
                    pii_types_found.append(pii_type)
                    for match in matches:
                        if len(match) > 2:
                            masked = match[0] + '*' * (len(match) - 2) + match[-1]
                        else:
                            masked = '*' * len(match)
                        masked_content = masked_content.replace(match, masked)
            
            if pii_types_found:
                self._log_security_event(
                    'pii_detected_and_masked',
                    'warning',
                    f"PII detected and masked: {', '.join(pii_types_found)}",
                    None
                )
            
            return masked_content, pii_types_found
            
        except Exception as e:
            self._log_security_event(
                'pii_detection_error',
                'error',
                f"PII detection failed: {e}",
                None
            )
            return content, []
    
    def check_resource_limits(self, content: str) -> Tuple[bool, str]:
        """Check if content processing would exceed resource limits.
        
        Args:
            content: Content to check resource requirements for.
            
        Returns:
            Tuple of (is_within_limits, error_message).
        """
        try:
            content_size = len(content.encode('utf-8'))
            
            # Estimate memory usage (rough estimate: 5x content size for processing)
            estimated_memory = content_size * 5
            
            if estimated_memory > self.config.max_memory_per_document:
                self._log_security_event(
                    'memory_limit_exceeded',
                    'error',
                    f"Estimated memory {estimated_memory} exceeds limit {self.config.max_memory_per_document}",
                    None
                )
                return False, f"Estimated memory usage {estimated_memory} bytes exceeds limit"
            
            # Check for potential DoS via excessive repeated patterns
            if self._detect_repeated_pattern_attack(content):
                return False, "Potential DoS attack via repeated patterns detected"
            
            return True, "Resource limits check passed"
            
        except Exception as e:
            self._log_security_event(
                'resource_limit_check_error',
                'error',
                f"Resource limit check failed: {e}",
                None
            )
            return False, f"Resource limit check error: {e}"
    
    def _detect_repeated_pattern_attack(self, content: str) -> bool:
        """Detect potential DoS attacks via repeated patterns.
        
        Args:
            content: Content to analyze.
            
        Returns:
            True if suspicious repeated patterns detected.
        """
        # Check for excessive repetition of single characters
        for char in ['A', 'a', '1', '0', ' ', '\n']:
            if content.count(char) > len(content) * 0.8:  # More than 80% is one character
                self._log_security_event(
                    'repeated_character_attack',
                    'warning',
                    f"Excessive repetition of character '{char}' detected",
                    None
                )
                return True
        
        # Check for excessive repetition of short patterns
        for pattern_len in [2, 3, 4, 5]:
            for i in range(min(100, len(content) - pattern_len)):  # Check first 100 positions
                pattern = content[i:i + pattern_len]
                if content.count(pattern) > 1000:  # Pattern appears more than 1000 times
                    self._log_security_event(
                        'repeated_pattern_attack',
                        'warning',
                        f"Excessive repetition of pattern '{pattern[:10]}...' detected",
                        None
                    )
                    return True
        
        return False
    
    def calculate_file_hash(self, file_path: str) -> str:
        """Calculate SHA-256 hash of file for audit logging.
        
        Args:
            file_path: Path to file to hash.
            
        Returns:
            SHA-256 hash as hex string, or empty string on error.
        """
        try:
            hasher = hashlib.sha256()
            with open(file_path, 'rb') as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hasher.update(chunk)
            return hasher.hexdigest()
        except Exception as e:
            logger.error(f"Failed to calculate hash for {file_path}: {e}")
            return ""
    
    def _log_security_event(
        self, 
        event_type: str, 
        severity: str, 
        description: str, 
        file_path: Optional[str] = None
    ) -> None:
        """Log security event for audit purposes.
        
        Args:
            event_type: Type of security event.
            severity: Severity level (info, warning, error, critical).
            description: Description of the event.
            file_path: Optional file path associated with event.
        """
        if not self.config.enable_security_logging:
            return
        
        file_hash = None
        if file_path:
            file_hash = self.calculate_file_hash(file_path)
        
        event = SecurityAuditEvent(
            event_type=event_type,
            severity=severity,
            description=description,
            file_path=file_path,
            file_hash=file_hash
        )
        
        self.audit_events.append(event)
        
        # Log to standard logger as well
        log_level = getattr(logging, severity.upper(), logging.INFO)
        logger.log(log_level, f"Security Event [{event_type}]: {description}")
    
    def get_audit_events(self, severity_filter: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get security audit events, optionally filtered by severity.
        
        Args:
            severity_filter: Optional severity to filter by.
            
        Returns:
            List of audit event dictionaries.
        """
        events = self.audit_events
        
        if severity_filter:
            events = [event for event in events if event.severity == severity_filter]
        
        return [event.to_dict() for event in events]
    
    def clear_audit_events(self) -> None:
        """Clear stored audit events (useful for testing)."""
        self.audit_events.clear()