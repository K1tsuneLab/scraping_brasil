"""
Integration tests for the Brazil Scraping project.
Tests the complete pipeline from scraping to storage.
"""
import pytest
import asyncio
import tempfile
import json
from pathlib import Path
from datetime import datetime, date
from unittest.mock import Mock, patch

# Import project modules
import sys
sys.path.append(str(Path(__file__).parent.parent))

from src.storage.drive_factory import DriveFactory
from src.storage.mock_drive_manager import MockDriveManager
from src.scraper.validators import DocumentValidator, DocumentMetadata
from src.utils.date_utils import get_date_range_since_2024, parse_date
from config.settings import settings

class TestDriveSystem:
    """Test the Drive storage system."""
    
    @pytest.mark.asyncio
    async def test_mock_drive_manager_creation(self):
        """Test MockDriveManager creation and basic operations."""
        drive = DriveFactory.create_drive_manager(mode='mock')
        assert isinstance(drive, MockDriveManager)
        
        # Test basic operations
        stats = drive.get_stats()
        assert 'uploads' in stats
        assert 'total_size' in stats
    
    @pytest.mark.asyncio
    async def test_file_upload_and_exists(self):
        """Test file upload and existence checking."""
        drive = DriveFactory.create_drive_manager(mode='mock')
        
        # Upload a test file
        test_content = "Test document content"
        file_info = await drive.upload_file(
            file_content=test_content,
            filename="test_document.txt"
        )
        
        assert file_info.name == "test_document.txt"
        assert file_info.size > 0
        
        # Check if file exists
        existing_file = await drive.file_exists("test_document.txt")
        assert existing_file is not None
        assert existing_file.name == "test_document.txt"
        
        # Check non-existent file
        non_existing = await drive.file_exists("non_existent.txt")
        assert non_existing is None
    
    @pytest.mark.asyncio
    async def test_folder_operations(self):
        """Test folder creation and structure setup."""
        drive = DriveFactory.create_drive_manager(mode='mock')
        
        # Create a single folder
        folder_id = await drive.create_folder("test_folder")
        assert folder_id is not None
        
        # Setup complete folder structure
        folders = await drive.setup_folder_structure()
        expected_folders = ['documentos_camara', 'documentos_senado', 'processed_data', 'translations', 'logs']
        
        for folder_name in expected_folders:
            assert folder_name in folders
            assert folders[folder_name] is not None

class TestDocumentValidator:
    """Test the document validation system."""
    
    def setup_method(self):
        """Setup test environment."""
        self.drive = DriveFactory.create_drive_manager(mode='mock')
        self.validator = DocumentValidator(self.drive)
    
    def test_document_metadata_creation(self):
        """Test DocumentMetadata creation and conversion."""
        doc = DocumentMetadata(
            id="test_001",
            title="Test Document",
            date="2024-01-15",
            source="camara",
            document_type="PL",
            url="https://example.com/doc1"
        )
        
        assert doc.id == "test_001"
        assert doc.source == "camara"
        
        # Test dictionary conversion
        doc_dict = doc.to_dict()
        assert doc_dict['id'] == "test_001"
        assert doc_dict['title'] == "Test Document"
    
    def test_duplicate_detection(self):
        """Test duplicate document detection."""
        # Add a document
        doc1 = DocumentMetadata(
            id="test_001",
            title="Test Document",
            date="2024-01-15",
            source="camara",
            document_type="PL",
            url="https://example.com/doc1"
        )
        
        self.validator.add_document(doc1)
        
        # Test exact ID match
        doc2 = DocumentMetadata(
            id="test_001",
            title="Different Title",
            date="2024-01-16",
            source="camara",
            document_type="PL",
            url="https://example.com/doc2"
        )
        
        is_dup, existing = self.validator.is_duplicate(doc2)
        assert is_dup is True
        assert existing is not None
        assert existing.id == "test_001"
        
        # Test non-duplicate
        doc3 = DocumentMetadata(
            id="test_002",
            title="Different Document",
            date="2024-01-15",
            source="camara",
            document_type="PL",
            url="https://example.com/doc3"
        )
        
        is_dup, existing = self.validator.is_duplicate(doc3)
        assert is_dup is False
        assert existing is None
    
    def test_date_range_filtering(self):
        """Test date range filtering functionality."""
        documents = [
            DocumentMetadata("1", "Doc 1", "2024-01-15", "camara", "PL", "url1"),
            DocumentMetadata("2", "Doc 2", "2023-12-31", "camara", "PL", "url2"),  # Outside range
            DocumentMetadata("3", "Doc 3", "2024-06-15", "senado", "PLS", "url3"),
            DocumentMetadata("4", "Doc 4", "2025-01-01", "camara", "PL", "url4"),   # Future date
        ]
        
        # Filter for 2024 documents
        filtered = self.validator.filter_new_documents(documents, "2024-01-01", "2024-12-31")
        
        # Should include docs 1 and 3, exclude 2 and 4
        assert len(filtered) == 2
        assert any(doc.id == "1" for doc in filtered)
        assert any(doc.id == "3" for doc in filtered)
    
    def test_content_validation(self):
        """Test document content validation."""
        # Valid content
        valid_content = b"Valid document content"
        assert self.validator.validate_document_content(valid_content) is True
        
        # Empty content
        empty_content = b""
        assert self.validator.validate_document_content(empty_content) is False
        
        # Size validation
        large_content = b"x" * 1000
        assert self.validator.validate_document_content(large_content, expected_size=1000) is True
        assert self.validator.validate_document_content(large_content, expected_size=500) is False

class TestDateUtils:
    """Test date utility functions."""
    
    def test_date_parsing(self):
        """Test various date format parsing."""
        from src.utils.date_utils import parse_date, format_date
        
        # Test valid formats
        date1 = parse_date("2024-01-15")
        assert date1 is not None
        assert date1.year == 2024
        assert date1.month == 1
        assert date1.day == 15
        
        date2 = parse_date("15/01/2024")
        assert date2 is not None
        assert date2.year == 2024
        
        # Test invalid format
        invalid_date = parse_date("invalid-date")
        assert invalid_date is None
    
    def test_date_range_generation(self):
        """Test date range generation."""
        from src.utils.date_utils import get_date_range_since_2024, get_custom_date_range
        
        # Test 2024 to today range
        start, end = get_date_range_since_2024()
        assert start == "2024-01-01"
        assert end >= "2024-01-01"  # Should be today or later
        
        # Test custom range
        custom_start, custom_end = get_custom_date_range("2024-01-01", "2024-12-31")
        assert custom_start == "2024-01-01"
        assert custom_end == "2024-12-31"
    
    def test_date_range_validation(self):
        """Test date range validation."""
        from src.utils.date_utils import is_date_in_range
        
        # Test valid range
        assert is_date_in_range("2024-06-15", "2024-01-01", "2024-12-31") is True
        
        # Test outside range
        assert is_date_in_range("2023-12-31", "2024-01-01", "2024-12-31") is False
        assert is_date_in_range("2025-01-01", "2024-01-01", "2024-12-31") is False

class TestConfiguration:
    """Test configuration system."""
    
    def test_settings_loading(self):
        """Test that settings are loaded correctly."""
        from config.settings import settings
        
        # Test default values
        assert settings.APP_MODE in ['mock', 'real', 'auto']
        assert settings.DEFAULT_START_DATE == '2024-01-01'
        assert settings.PROJECT_ROOT.exists()
    
    def test_directory_creation(self):
        """Test that required directories are created."""
        from config.settings import settings
        
        # These should be created automatically
        assert settings.DATA_RAW_PATH.exists()
        assert settings.DATA_PROCESSED_PATH.exists()
        assert settings.MOCK_STORAGE_PATH.exists()
        assert settings.LOG_PATH.exists()

class TestPipelineIntegration:
    """Test the complete pipeline integration."""
    
    @pytest.mark.asyncio
    async def test_mock_pipeline_execution(self):
        """Test a simplified version of the complete pipeline."""
        # Create test documents
        test_documents = [
            DocumentMetadata("test_1", "Test Doc 1", "2024-01-15", "camara", "PL", "url1"),
            DocumentMetadata("test_2", "Test Doc 2", "2024-02-15", "senado", "PLS", "url2"),
        ]
        
        # Initialize components
        drive = DriveFactory.create_drive_manager(mode='mock')
        validator = DocumentValidator(drive)
        
        # Test validation and filtering
        start_date, end_date = get_date_range_since_2024()
        new_documents = validator.filter_new_documents(test_documents, start_date, end_date)
        
        # Should have all documents since they're new
        assert len(new_documents) == 2
        
        # Test storage
        folders = await drive.setup_folder_structure()
        assert len(folders) > 0
        
        # Test file upload for each document
        for doc in new_documents:
            filename = f"{doc.source}_{doc.id}_{doc.date}.json"
            file_info = await drive.upload_file(
                file_content=json.dumps(doc.to_dict()),
                filename=filename
            )
            assert file_info.name == filename
            
            # Add to validator
            validator.add_document(doc)
        
        # Test that documents are now tracked
        stats = validator.get_statistics()
        assert stats['total_documents'] == 2
        assert stats['camara_documents'] == 1
        assert stats['senado_documents'] == 1
    
    @pytest.mark.asyncio 
    async def test_duplicate_handling_in_pipeline(self):
        """Test that the pipeline correctly handles duplicates."""
        drive = DriveFactory.create_drive_manager(mode='mock')
        validator = DocumentValidator(drive)
        
        # First batch of documents
        batch1 = [
            DocumentMetadata("dup_1", "Duplicate Doc", "2024-01-15", "camara", "PL", "url1"),
            DocumentMetadata("unique_1", "Unique Doc", "2024-01-15", "camara", "PL", "url2"),
        ]
        
        # Add first batch
        start_date, end_date = get_date_range_since_2024()
        new_docs1 = validator.filter_new_documents(batch1, start_date, end_date)
        assert len(new_docs1) == 2
        
        for doc in new_docs1:
            validator.add_document(doc)
        
        # Second batch with one duplicate
        batch2 = [
            DocumentMetadata("dup_1", "Duplicate Doc", "2024-01-15", "camara", "PL", "url1"),  # Duplicate
            DocumentMetadata("unique_2", "Another Unique Doc", "2024-01-15", "camara", "PL", "url3"),  # New
        ]
        
        # Filter second batch
        new_docs2 = validator.filter_new_documents(batch2, start_date, end_date)
        
        # Should only have 1 new document (the duplicate should be filtered out)
        assert len(new_docs2) == 1
        assert new_docs2[0].id == "unique_2"

# Pytest configuration
@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

if __name__ == "__main__":
    # Run tests directly
    pytest.main([__file__, "-v"]) 