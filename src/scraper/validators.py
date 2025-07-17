"""
Document validation system for the Brazil scraping project.
Handles duplicate detection, file integrity validation, and document filtering.
"""
import hashlib
import json
from datetime import datetime, date
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple, Any
from dataclasses import dataclass
from loguru import logger

from ..storage.drive_interface import DriveInterface, DriveFileInfo
from config.settings import settings

@dataclass
class DocumentMetadata:
    """Metadata for a scraped document."""
    id: str
    title: str
    date: str  # YYYY-MM-DD format
    source: str  # 'camara' or 'senado'
    document_type: str
    url: str
    file_size: Optional[int] = None
    md5_checksum: Optional[str] = None
    scraped_at: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            'id': self.id,
            'title': self.title,
            'date': self.date,
            'source': self.source,
            'document_type': self.document_type,
            'url': self.url,
            'file_size': self.file_size,
            'md5_checksum': self.md5_checksum,
            'scraped_at': self.scraped_at
        }

class DocumentValidator:
    """Validates documents for duplicates and integrity."""
    
    def __init__(self, drive_manager: DriveInterface):
        self.drive_manager = drive_manager
        self.existing_documents: Dict[str, DocumentMetadata] = {}
        self.metadata_cache_path = settings.DATA_PROCESSED_PATH / "document_metadata_cache.json"
        
        # Load existing metadata
        self._load_metadata_cache()
    
    def _load_metadata_cache(self) -> None:
        """Load existing document metadata from cache."""
        if self.metadata_cache_path.exists():
            try:
                with open(self.metadata_cache_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    
                for doc_id, doc_data in data.items():
                    self.existing_documents[doc_id] = DocumentMetadata(**doc_data)
                    
                logger.info(f"Loaded {len(self.existing_documents)} documents from metadata cache")
            except Exception as e:
                logger.warning(f"Could not load metadata cache: {e}")
        
        logger.info(f"Document validator initialized with {len(self.existing_documents)} existing documents")
    
    def _save_metadata_cache(self) -> None:
        """Save current metadata cache to file."""
        try:
            self.metadata_cache_path.parent.mkdir(parents=True, exist_ok=True)
            
            data = {doc_id: doc.to_dict() for doc_id, doc in self.existing_documents.items()}
            
            with open(self.metadata_cache_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
                
            logger.debug("Metadata cache saved successfully")
        except Exception as e:
            logger.error(f"Could not save metadata cache: {e}")
    
    def calculate_document_hash(self, content: bytes) -> str:
        """Calculate MD5 hash of document content."""
        return hashlib.md5(content).hexdigest()
    
    def is_duplicate(self, document: DocumentMetadata) -> Tuple[bool, Optional[DocumentMetadata]]:
        """
        Check if a document is a duplicate of an existing one.
        
        Args:
            document: Document to check
            
        Returns:
            Tuple of (is_duplicate, existing_document if duplicate)
        """
        # Check by ID first (exact match)
        if document.id in self.existing_documents:
            existing = self.existing_documents[document.id]
            logger.debug(f"Found exact ID match for {document.id}")
            return True, existing
        
        # Check by content hash if available
        if document.md5_checksum:
            for existing_doc in self.existing_documents.values():
                if (existing_doc.md5_checksum == document.md5_checksum and
                    existing_doc.source == document.source):
                    logger.debug(f"Found content hash match for {document.id}")
                    return True, existing_doc
        
        # Check by title and date (fuzzy match)
        for existing_doc in self.existing_documents.values():
            if (existing_doc.title == document.title and
                existing_doc.date == document.date and
                existing_doc.source == document.source):
                logger.debug(f"Found title/date match for {document.id}")
                return True, existing_doc
        
        return False, None
    
    def is_date_in_range(self, document_date: str, start_date: str, end_date: str) -> bool:
        """
        Check if document date is within the specified range.
        
        Args:
            document_date: Document date in YYYY-MM-DD format
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format
            
        Returns:
            True if date is in range, False otherwise
        """
        try:
            doc_date = datetime.strptime(document_date, '%Y-%m-%d').date()
            start = datetime.strptime(start_date, '%Y-%m-%d').date()
            end = datetime.strptime(end_date, '%Y-%m-%d').date()
            
            return start <= doc_date <= end
        except ValueError as e:
            logger.warning(f"Invalid date format: {e}")
            return False
    
    def validate_document_content(self, content: bytes, expected_size: Optional[int] = None) -> bool:
        """
        Validate document content integrity.
        
        Args:
            content: Document content as bytes
            expected_size: Expected file size in bytes
            
        Returns:
            True if content is valid, False otherwise
        """
        # Check if content is not empty
        if not content:
            logger.warning("Document content is empty")
            return False
        
        # Check file size if expected size is provided
        if expected_size is not None:
            actual_size = len(content)
            if actual_size != expected_size:
                logger.warning(f"File size mismatch: expected {expected_size}, got {actual_size}")
                return False
        
        # Basic content validation for PDFs
        if content.startswith(b'%PDF-'):
            # PDF header validation
            if b'%%EOF' not in content[-1024:]:  # EOF marker should be near end
                logger.warning("PDF file appears to be truncated")
                return False
        
        # Basic content validation for JSON
        elif content.strip().startswith(b'{') or content.strip().startswith(b'['):
            try:
                json.loads(content.decode('utf-8'))
            except (json.JSONDecodeError, UnicodeDecodeError):
                logger.warning("JSON content appears to be invalid")
                return False
        
        return True
    
    def add_document(self, document: DocumentMetadata) -> None:
        """Add a new document to the tracking system."""
        document.scraped_at = datetime.now().isoformat()
        self.existing_documents[document.id] = document
        self._save_metadata_cache()
        logger.info(f"Added new document: {document.id} ({document.source})")
    
    def update_document(self, document: DocumentMetadata) -> None:
        """Update an existing document's metadata."""
        if document.id in self.existing_documents:
            document.scraped_at = datetime.now().isoformat()
            self.existing_documents[document.id] = document
            self._save_metadata_cache()
            logger.info(f"Updated document: {document.id}")
        else:
            logger.warning(f"Attempted to update non-existent document: {document.id}")
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get validation statistics."""
        camara_docs = sum(1 for doc in self.existing_documents.values() if doc.source == 'camara')
        senado_docs = sum(1 for doc in self.existing_documents.values() if doc.source == 'senado')
        
        return {
            'total_documents': len(self.existing_documents),
            'camara_documents': camara_docs,
            'senado_documents': senado_docs,
            'cache_file_size': self.metadata_cache_path.stat().st_size if self.metadata_cache_path.exists() else 0,
            'last_updated': datetime.now().isoformat()
        }
    
    def filter_new_documents(self, documents: List[DocumentMetadata], 
                           start_date: str, end_date: str) -> List[DocumentMetadata]:
        """
        Filter documents to only include new ones within the date range.
        
        Args:
            documents: List of documents to filter
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format
            
        Returns:
            List of new documents within the date range
        """
        new_documents = []
        
        for doc in documents:
            # Check date range
            if not self.is_date_in_range(doc.date, start_date, end_date):
                logger.debug(f"Document {doc.id} outside date range: {doc.date}")
                continue
            
            # Check for duplicates
            is_dup, existing_doc = self.is_duplicate(doc)
            if is_dup and existing_doc:
                logger.debug(f"Document {doc.id} is duplicate of {existing_doc.id}")
                continue
            
            new_documents.append(doc)
        
        logger.info(f"Filtered {len(documents)} documents to {len(new_documents)} new documents")
        return new_documents

class ContentValidator:
    """Validates specific content types (PDFs, JSON, etc.)."""
    
    @staticmethod
    def validate_pdf(content: bytes) -> bool:
        """Validate PDF file content."""
        if not content.startswith(b'%PDF-'):
            return False
        
        # Check for PDF version
        version_line = content[:20]
        if not any(version in version_line for version in [b'1.0', b'1.1', b'1.2', b'1.3', b'1.4', b'1.5', b'1.6', b'1.7', b'2.0']):
            logger.warning("Unknown PDF version")
        
        # Check for EOF marker
        if b'%%EOF' not in content[-1024:]:
            logger.warning("PDF missing EOF marker")
            return False
        
        return True
    
    @staticmethod
    def validate_json(content: bytes) -> bool:
        """Validate JSON file content."""
        try:
            json.loads(content.decode('utf-8'))
            return True
        except (json.JSONDecodeError, UnicodeDecodeError) as e:
            logger.warning(f"Invalid JSON content: {e}")
            return False
    
    @staticmethod
    def validate_file_size(content: bytes, min_size: int = 100, max_size: int = 100 * 1024 * 1024) -> bool:
        """
        Validate file size is within reasonable bounds.
        
        Args:
            content: File content
            min_size: Minimum expected size in bytes (default: 100 bytes)
            max_size: Maximum expected size in bytes (default: 100MB)
            
        Returns:
            True if size is valid, False otherwise
        """
        size = len(content)
        
        if size < min_size:
            logger.warning(f"File too small: {size} bytes (minimum: {min_size})")
            return False
        
        if size > max_size:
            logger.warning(f"File too large: {size} bytes (maximum: {max_size})")
            return False
        
        return True 