"""Document Chunking Strategy

Implements semantic boundary detection and chunking for insurance policy documents
with configurable parameters and metadata preservation.
"""

import re
import logging
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path
import uuid

from ..models import Document
from ..config import get_config

logger = logging.getLogger(__name__)


class ChunkingStrategy:
    """Semantic chunking strategy for insurance policy documents.
    
    Implements intelligent chunking that preserves clause boundaries,
    maintains context information, and generates structured metadata.
    """
    
    def __init__(self, config=None):
        """Initialize chunking strategy with configuration.
        
        Args:
            config: Optional configuration override.
        """
        self.config = config or get_config()
        self.chunk_size = self.config.retrieval.chunk_size
        self.chunk_overlap = self.config.retrieval.chunk_overlap
        self._compile_patterns()
    
    def _compile_patterns(self) -> None:
        """Compile regex patterns for semantic boundary detection."""
        
        # Pattern for insurance clause headers (第X條, 第X.Y條, etc.)
        self.clause_header_pattern = re.compile(
            r'第\s*(\d+(?:\.\d+)*)\s*條\s*([^\n]*)', 
            re.UNICODE | re.MULTILINE
        )
        
        # Pattern for sub-clause numbering (（一）, （二）, 1., 2., etc.)
        self.sub_clause_pattern = re.compile(
            r'^[\s]*(?:（[一二三四五六七八九十]+）|\([一二三四五六七八九十]+\)|\d+[\.\)、])',
            re.UNICODE | re.MULTILINE
        )
        
        # Pattern for section breaks and major divisions
        self.section_break_pattern = re.compile(
            r'(?:^|\n)[\s]*(?:第[一二三四五六七八九十]+[章節部]|[壹貳參肆伍陸柒捌玖拾]+[\s]*、)',
            re.UNICODE | re.MULTILINE
        )
        
        # Pattern for coverage types (保障項目識別)
        self.coverage_type_pattern = re.compile(
            r'(旅[程遊]延[誤遲]|行李[遺損失毀]|醫療費用|意外傷[害亡]|取消行程|緊急救援)',
            re.UNICODE
        )
        
        # Pattern for exclusion clauses (免責條款識別)
        self.exclusion_pattern = re.compile(
            r'(不[負承]?保[障險]|免責|排除|例外|但[不非]包括)',
            re.UNICODE
        )
        
        # Pattern for procedure clauses (申請程序識別)
        self.procedure_pattern = re.compile(
            r'(申請|理賠|通知|證明|文件|程序|手續|期限|時間)',
            re.UNICODE
        )
    
    def chunk_document(
        self, 
        text: str, 
        source_file: str,
        preserve_structure: bool = True
    ) -> List[Document]:
        """Chunk document into semantic pieces with metadata.
        
        Args:
            text: Cleaned document text to chunk.
            source_file: Source file path for traceability.
            preserve_structure: Whether to preserve clause structure.
            
        Returns:
            List of Document chunks with structured metadata.
        """
        if not text or not text.strip():
            return []
        
        try:
            if preserve_structure:
                chunks = self._semantic_chunking(text, source_file)
            else:
                chunks = self._fixed_size_chunking(text, source_file)
            
            logger.info(
                f"Generated {len(chunks)} chunks from {source_file} "
                f"(avg size: {sum(len(c.content) for c in chunks) / len(chunks):.1f} chars)"
            )
            
            return chunks
            
        except Exception as e:
            logger.error(f"Chunking failed for {source_file}: {e}")
            # Fallback to basic chunking if semantic chunking fails
            return self._fixed_size_chunking(text, source_file)
    
    def _semantic_chunking(self, text: str, source_file: str) -> List[Document]:
        """Perform semantic chunking preserving clause boundaries.
        
        Args:
            text: Input text to chunk semantically.
            source_file: Source file for metadata.
            
        Returns:
            List of semantically chunked Documents.
        """
        chunks = []
        
        # Step 1: Identify major section boundaries
        sections = self._identify_sections(text)
        
        # Step 2: Process each section for clause boundaries
        for section_start, section_end, section_title in sections:
            section_text = text[section_start:section_end]
            section_chunks = self._chunk_section(
                section_text, 
                source_file, 
                section_title,
                section_start
            )
            chunks.extend(section_chunks)
        
        # If no sections found, process entire text as one section
        if not chunks:
            chunks = self._chunk_section(text, source_file, "文件內容", 0)
        
        return chunks
    
    def _identify_sections(self, text: str) -> List[Tuple[int, int, str]]:
        """Identify major document sections and their boundaries.
        
        Args:
            text: Full document text.
            
        Returns:
            List of tuples (start_pos, end_pos, section_title).
        """
        sections = []
        
        # Find section headers
        section_matches = list(self.section_break_pattern.finditer(text))
        
        if not section_matches:
            # No explicit sections found, treat entire document as one section
            return [(0, len(text), "全文")]
        
        # Process each section
        for i, match in enumerate(section_matches):
            start_pos = match.start()
            end_pos = section_matches[i + 1].start() if i + 1 < len(section_matches) else len(text)
            section_title = match.group().strip()
            
            sections.append((start_pos, end_pos, section_title))
        
        return sections
    
    def _chunk_section(
        self, 
        section_text: str, 
        source_file: str, 
        section_title: str,
        section_start: int
    ) -> List[Document]:
        """Chunk a document section preserving clause structure.
        
        Args:
            section_text: Text of the section to chunk.
            source_file: Source file for metadata.
            section_title: Title of the section.
            section_start: Character position where section starts in full document.
            
        Returns:
            List of Document chunks for this section.
        """
        chunks = []
        
        # Find all clause headers in this section
        clause_matches = list(self.clause_header_pattern.finditer(section_text))
        
        if not clause_matches:
            # No explicit clauses, use fixed-size chunking with overlap
            return self._fixed_size_chunking_with_metadata(
                section_text, 
                source_file, 
                section_title,
                section_start
            )
        
        # Process each clause
        for i, match in enumerate(clause_matches):
            clause_start = match.start()
            clause_end = clause_matches[i + 1].start() if i + 1 < len(clause_matches) else len(section_text)
            clause_text = section_text[clause_start:clause_end].strip()
            
            if not clause_text:
                continue
            
            # Extract clause metadata
            clause_number = match.group(1)
            clause_title = match.group(2).strip() if match.group(2) else ""
            
            # If clause is too long, split it while preserving context
            if len(clause_text) > self.chunk_size:
                sub_chunks = self._split_long_clause(
                    clause_text,
                    clause_number,
                    clause_title,
                    source_file,
                    section_title,
                    section_start + clause_start
                )
                chunks.extend(sub_chunks)
            else:
                # Create single chunk for this clause
                chunk = self._create_chunk(
                    clause_text,
                    source_file,
                    section_title,
                    clause_number,
                    clause_title,
                    section_start + clause_start,
                    section_start + clause_end
                )
                chunks.append(chunk)
        
        return chunks
    
    def _split_long_clause(
        self,
        clause_text: str,
        clause_number: str,
        clause_title: str,
        source_file: str,
        section_title: str,
        clause_start: int
    ) -> List[Document]:
        """Split a long clause into smaller chunks while preserving context.
        
        Args:
            clause_text: Text of the long clause.
            clause_number: Number of the clause (e.g., "3.1").
            clause_title: Title of the clause.
            source_file: Source file path.
            section_title: Title of the parent section.
            clause_start: Starting position in full document.
            
        Returns:
            List of Document chunks from the split clause.
        """
        chunks = []
        
        # Try to split on sub-clause boundaries first
        sub_clause_matches = list(self.sub_clause_pattern.finditer(clause_text))
        
        if sub_clause_matches and len(sub_clause_matches) > 1:
            # Split on sub-clause boundaries
            for i, match in enumerate(sub_clause_matches):
                sub_start = match.start()
                sub_end = sub_clause_matches[i + 1].start() if i + 1 < len(sub_clause_matches) else len(clause_text)
                sub_text = clause_text[sub_start:sub_end].strip()
                
                if sub_text and len(sub_text) > 10:  # Skip very short fragments
                    chunk = self._create_chunk(
                        sub_text,
                        source_file,
                        section_title,
                        f"{clause_number}.{i+1}",
                        clause_title,
                        clause_start + sub_start,
                        clause_start + sub_end
                    )
                    chunks.append(chunk)
        else:
            # No sub-clauses, use sliding window with overlap
            chunks = self._sliding_window_chunk(
                clause_text,
                clause_number,
                clause_title,
                source_file,
                section_title,
                clause_start
            )
        
        return chunks
    
    def _sliding_window_chunk(
        self,
        text: str,
        clause_number: str,
        clause_title: str,
        source_file: str,
        section_title: str,
        start_pos: int
    ) -> List[Document]:
        """Create overlapping chunks using sliding window approach.
        
        Args:
            text: Text to chunk.
            clause_number: Clause number for metadata.
            clause_title: Clause title for metadata.
            source_file: Source file path.
            section_title: Section title for metadata.
            start_pos: Starting position in full document.
            
        Returns:
            List of overlapping Document chunks.
        """
        chunks = []
        text_length = len(text)
        chunk_index = 0
        
        position = 0
        while position < text_length:
            end_pos = min(position + self.chunk_size, text_length)
            chunk_text = text[position:end_pos].strip()
            
            if chunk_text:
                chunk = self._create_chunk(
                    chunk_text,
                    source_file,
                    section_title,
                    f"{clause_number}_{chunk_index}",
                    clause_title,
                    start_pos + position,
                    start_pos + end_pos
                )
                chunks.append(chunk)
                chunk_index += 1
            
            # Move position forward by chunk_size minus overlap
            position += self.chunk_size - self.chunk_overlap
        
        return chunks
    
    def _fixed_size_chunking(self, text: str, source_file: str) -> List[Document]:
        """Fallback fixed-size chunking when semantic chunking is not applicable.
        
        Args:
            text: Text to chunk with fixed sizes.
            source_file: Source file for metadata.
            
        Returns:
            List of fixed-size Document chunks.
        """
        return self._fixed_size_chunking_with_metadata(text, source_file, "固定大小分塊", 0)
    
    def _fixed_size_chunking_with_metadata(
        self,
        text: str,
        source_file: str,
        section_title: str,
        section_start: int
    ) -> List[Document]:
        """Fixed-size chunking with metadata generation.
        
        Args:
            text: Text to chunk.
            source_file: Source file path.
            section_title: Section title for metadata.
            section_start: Starting position in full document.
            
        Returns:
            List of fixed-size Document chunks with metadata.
        """
        chunks = []
        text_length = len(text)
        chunk_index = 0
        
        position = 0
        while position < text_length:
            end_pos = min(position + self.chunk_size, text_length)
            chunk_text = text[position:end_pos].strip()
            
            if chunk_text:
                chunk = self._create_chunk(
                    chunk_text,
                    source_file,
                    section_title,
                    f"chunk_{chunk_index}",
                    "",
                    section_start + position,
                    section_start + end_pos
                )
                chunks.append(chunk)
                chunk_index += 1
            
            position += self.chunk_size - self.chunk_overlap
        
        return chunks
    
    def _create_chunk(
        self,
        content: str,
        source_file: str,
        section_title: str,
        clause_number: str,
        clause_title: str,
        char_start: int,
        char_end: int
    ) -> Document:
        """Create a Document chunk with comprehensive metadata.
        
        Args:
            content: Text content of the chunk.
            source_file: Source file path.
            section_title: Title of the parent section.
            clause_number: Clause identifier.
            clause_title: Title of the clause.
            char_start: Start character position in full document.
            char_end: End character position in full document.
            
        Returns:
            Document instance with structured metadata.
        """
        # Generate unique chunk ID
        chunk_id = str(uuid.uuid4())
        
        # Classify clause type based on content
        clause_type = self._classify_clause_type(content)
        
        # Build comprehensive metadata
        metadata = {
            'source_file': Path(source_file).name,
            'source_path': source_file,
            'section_title': section_title,
            'clause_number': clause_number,
            'clause_title': clause_title,
            'clause_type': clause_type,
            'char_start': char_start,
            'char_end': char_end,
            'chunk_length': len(content),
            'chunk_id': chunk_id
        }
        
        return Document(
            content=content,
            metadata=metadata,
            embedding=None,
            chunk_id=chunk_id
        )
    
    def _classify_clause_type(self, content: str) -> str:
        """Classify the type of insurance clause based on content.
        
        Args:
            content: Text content to classify.
            
        Returns:
            Clause type classification string.
        """
        content_lower = content.lower()
        
        # Check for exclusion clauses
        if self.exclusion_pattern.search(content):
            return "exclusion"
        
        # Check for procedure clauses
        if self.procedure_pattern.search(content):
            return "procedure"
        
        # Check for coverage clauses
        if self.coverage_type_pattern.search(content):
            return "coverage"
        
        # Default to general clause
        return "general"
    
    def get_chunking_stats(self, chunks: List[Document]) -> Dict[str, Any]:
        """Generate statistics about the chunking operation.
        
        Args:
            chunks: List of generated chunks.
            
        Returns:
            Dictionary containing chunking statistics.
        """
        if not chunks:
            return {
                'total_chunks': 0,
                'average_chunk_size': 0,
                'chunk_size_distribution': {},
                'clause_types': {}
            }
        
        chunk_sizes = [len(chunk.content) for chunk in chunks]
        clause_types = [chunk.metadata.get('clause_type', 'unknown') for chunk in chunks]
        
        # Calculate size distribution
        size_ranges = {
            'small (0-100)': len([s for s in chunk_sizes if s <= 100]),
            'medium (101-300)': len([s for s in chunk_sizes if 101 <= s <= 300]),
            'large (301-500)': len([s for s in chunk_sizes if 301 <= s <= 500]),
            'xlarge (500+)': len([s for s in chunk_sizes if s > 500])
        }
        
        # Count clause types
        type_counts = {}
        for clause_type in clause_types:
            type_counts[clause_type] = type_counts.get(clause_type, 0) + 1
        
        return {
            'total_chunks': len(chunks),
            'average_chunk_size': sum(chunk_sizes) / len(chunk_sizes),
            'min_chunk_size': min(chunk_sizes),
            'max_chunk_size': max(chunk_sizes),
            'chunk_size_distribution': size_ranges,
            'clause_types': type_counts
        }