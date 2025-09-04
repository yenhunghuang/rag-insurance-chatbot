"""Text Cleaning and Normalization

Handles text preprocessing including formatting artifact removal,
normalization, and Chinese text processing for insurance documents.
"""

import re
import logging
from typing import Dict, Pattern, List
import unicodedata

logger = logging.getLogger(__name__)


class TextCleaner:
    """Text cleaning and normalization for Chinese insurance documents.
    
    Removes formatting artifacts, normalizes content structure, and
    handles Chinese text encoding properly for downstream processing.
    """
    
    def __init__(self, config=None):
        """Initialize text cleaner with configuration.
        
        Args:
            config: Optional configuration override.
        """
        self.config = config
        self._compile_patterns()
    
    def _compile_patterns(self) -> None:
        """Compile regex patterns for text cleaning operations."""
        
        # Pattern for excessive whitespace (multiple spaces, tabs, newlines)
        self.excessive_whitespace_pattern = re.compile(r'\s{2,}')
        
        # Pattern for formatting artifacts commonly found in documents
        self.formatting_artifacts_pattern = re.compile(r'[^\w\s\u4e00-\u9fff，。；：！？「」『』（）［］【】、]', re.UNICODE)
        
        # Pattern for clause numbers (保險條款編號格式)
        self.clause_number_pattern = re.compile(r'第\s*(\d+(?:\.\d+)*)\s*[條章節]', re.UNICODE)
        
        # Pattern for page numbers and headers/footers
        self.page_artifact_pattern = re.compile(r'^[\s\-\d]*第?\s*[\d\-]+\s*頁?[\s\-]*$', re.MULTILINE | re.UNICODE)
        
        # Pattern for bullet points and list markers
        self.list_marker_pattern = re.compile(r'^[\s]*[•·▪▫◦‣⁃\-\*]+[\s]+', re.MULTILINE | re.UNICODE)
        
        # Pattern for table formatting artifacts
        self.table_artifact_pattern = re.compile(r'[|\─┌┐└┘├┤┬┴┼]+', re.UNICODE)
        
        # Pattern for repeated punctuation
        self.repeated_punct_pattern = re.compile(r'([，。；：！？])\1+', re.UNICODE)
        
        # Pattern for English alphanumeric mixed with Chinese (often OCR artifacts)
        self.mixed_alphanumeric_pattern = re.compile(r'(?<=[\u4e00-\u9fff])[a-zA-Z0-9]{1,2}(?=[\u4e00-\u9fff])', re.UNICODE)
    
    def clean_text(self, text: str) -> str:
        """Clean and normalize text content.
        
        Performs comprehensive text cleaning including:
        - Whitespace normalization
        - Formatting artifact removal  
        - Chinese text normalization
        - Structure preservation
        
        Args:
            text: Raw text content to clean.
            
        Returns:
            Cleaned and normalized text content.
        """
        if not text or not text.strip():
            return ""
        
        try:
            # Step 1: Unicode normalization for consistent Chinese character representation
            cleaned_text = self._normalize_unicode(text)
            
            # Step 2: Remove page artifacts and headers/footers
            cleaned_text = self._remove_page_artifacts(cleaned_text)
            
            # Step 3: Clean formatting artifacts while preserving structure
            cleaned_text = self._clean_formatting_artifacts(cleaned_text)
            
            # Step 4: Normalize whitespace and line breaks
            cleaned_text = self._normalize_whitespace(cleaned_text)
            
            # Step 5: Fix punctuation issues
            cleaned_text = self._normalize_punctuation(cleaned_text)
            
            # Step 6: Clean up clause numbering format
            cleaned_text = self._normalize_clause_numbers(cleaned_text)
            
            # Step 7: Final cleanup pass
            cleaned_text = self._final_cleanup(cleaned_text)
            
            logger.debug(f"Text cleaning completed: {len(text)} -> {len(cleaned_text)} characters")
            return cleaned_text.strip()
            
        except Exception as e:
            logger.error(f"Text cleaning failed: {e}")
            # Return original text if cleaning fails to ensure robustness
            return text
    
    def _normalize_unicode(self, text: str) -> str:
        """Normalize Unicode characters for consistent representation.
        
        Args:
            text: Input text with potentially mixed Unicode forms.
            
        Returns:
            Text with normalized Unicode characters.
        """
        # Use NFD normalization to decompose characters, then NFC to recompose
        # This handles traditional/simplified Chinese variants and diacritics
        normalized = unicodedata.normalize('NFD', text)
        normalized = unicodedata.normalize('NFC', normalized)
        
        # Convert full-width characters to half-width where appropriate
        # This helps with English alphanumeric mixed with Chinese
        full_to_half = str.maketrans(
            '０１２３４５６７８９ＡＢＣＤＥＦＧＨＩＪＫＬＭＮＯＰＱＲＳＴＵＶＷＸＹＺａｂｃｄｅｆｇｈｉｊｋｌｍｎｏｐｑｒｓｔｕｖｗｘｙｚ',
            '0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz'
        )
        
        return normalized.translate(full_to_half)
    
    def _remove_page_artifacts(self, text: str) -> str:
        """Remove page numbers, headers, and footers.
        
        Args:
            text: Input text containing page artifacts.
            
        Returns:
            Text with page artifacts removed.
        """
        # Remove standalone page numbers
        text = self.page_artifact_pattern.sub('', text)
        
        # Remove common header/footer patterns
        lines = text.split('\n')
        cleaned_lines = []
        
        for line in lines:
            line = line.strip()
            
            # Skip empty lines and obvious page artifacts
            if not line:
                cleaned_lines.append('')
                continue
                
            # Skip lines that are likely headers/footers (very short, mostly numbers/punctuation)
            if len(line) < 10 and re.match(r'^[\d\s\-\.]+$', line):
                continue
                
            cleaned_lines.append(line)
        
        return '\n'.join(cleaned_lines)
    
    def _clean_formatting_artifacts(self, text: str) -> str:
        """Remove formatting artifacts while preserving document structure.
        
        Args:
            text: Input text containing formatting artifacts.
            
        Returns:
            Text with artifacts removed but structure preserved.
        """
        # Remove table drawing characters
        text = self.table_artifact_pattern.sub(' ', text)
        
        # Clean up bullet points and list markers - normalize to standard format
        text = self.list_marker_pattern.sub('• ', text)
        
        # Remove mixed alphanumeric artifacts (often OCR errors)
        text = self.mixed_alphanumeric_pattern.sub('', text)
        
        # Remove or replace special formatting characters, but preserve Chinese punctuation
        # Keep: Chinese punctuation, parentheses, quotes, basic punctuation
        preserved_chars = r'[\w\s\u4e00-\u9fff，。；：！？「」『』（）［］【】、\.\,\;\:\!\?\"\'\(\)\[\]]'
        text = re.sub(f'[^{preserved_chars[1:-1]}]', ' ', text, flags=re.UNICODE)
        
        return text
    
    def _normalize_whitespace(self, text: str) -> str:
        """Normalize whitespace and line breaks for consistent structure.
        
        Args:
            text: Input text with irregular whitespace.
            
        Returns:
            Text with normalized whitespace.
        """
        # Replace excessive whitespace with single space
        text = self.excessive_whitespace_pattern.sub(' ', text)
        
        # Normalize line breaks - preserve paragraph structure
        lines = text.split('\n')
        normalized_lines = []
        
        for line in lines:
            line = line.strip()
            if line:  # Non-empty line
                normalized_lines.append(line)
            elif normalized_lines and normalized_lines[-1]:  # Empty line after content
                normalized_lines.append('')  # Preserve paragraph break
        
        # Remove trailing empty lines
        while normalized_lines and not normalized_lines[-1]:
            normalized_lines.pop()
        
        return '\n'.join(normalized_lines)
    
    def _normalize_punctuation(self, text: str) -> str:
        """Fix punctuation issues and normalize Chinese punctuation usage.
        
        Args:
            text: Input text with punctuation issues.
            
        Returns:
            Text with normalized punctuation.
        """
        # Fix repeated punctuation
        text = self.repeated_punct_pattern.sub(r'\1', text)
        
        # Ensure proper spacing around punctuation
        # Add space after Chinese punctuation if followed by alphanumeric
        text = re.sub(r'([，。；：！？])(?=[a-zA-Z0-9])', r'\1 ', text, flags=re.UNICODE)
        
        # Remove space before Chinese punctuation
        text = re.sub(r'\s+([，。；：！？])', r'\1', text, flags=re.UNICODE)
        
        return text
    
    def _normalize_clause_numbers(self, text: str) -> str:
        """Normalize insurance clause numbering format.
        
        Args:
            text: Input text with clause numbers.
            
        Returns:
            Text with standardized clause numbering.
        """
        # Standardize clause number format: "第X條" or "第X.Y條"
        def normalize_clause(match):
            clause_num = match.group(1)
            return f"第{clause_num}條"
        
        text = self.clause_number_pattern.sub(normalize_clause, text)
        
        return text
    
    def _final_cleanup(self, text: str) -> str:
        """Final cleanup pass to remove remaining artifacts.
        
        Args:
            text: Input text after previous cleaning steps.
            
        Returns:
            Final cleaned text.
        """
        # Remove any remaining excessive whitespace
        text = self.excessive_whitespace_pattern.sub(' ', text)
        
        # Ensure consistent line ending
        text = re.sub(r'\r\n|\r', '\n', text)
        
        # Remove leading/trailing whitespace from each line
        lines = [line.strip() for line in text.split('\n')]
        
        # Remove empty lines at start and end, but preserve internal paragraph breaks
        while lines and not lines[0]:
            lines.pop(0)
        while lines and not lines[-1]:
            lines.pop()
        
        return '\n'.join(lines)
    
    def get_cleaning_stats(self, original_text: str, cleaned_text: str) -> Dict[str, int]:
        """Generate statistics about the cleaning operation.
        
        Args:
            original_text: Original input text.
            cleaned_text: Cleaned output text.
            
        Returns:
            Dictionary containing cleaning statistics.
        """
        return {
            'original_length': len(original_text),
            'cleaned_length': len(cleaned_text),
            'characters_removed': len(original_text) - len(cleaned_text),
            'original_lines': len(original_text.split('\n')),
            'cleaned_lines': len(cleaned_text.split('\n')),
            'compression_ratio': len(cleaned_text) / len(original_text) if original_text else 0
        }