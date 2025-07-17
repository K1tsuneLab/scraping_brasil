"""
Abstract interface for Google Drive operations.
This allows seamless switching between mock and real implementations.
"""
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, Union
from pathlib import Path
import asyncio

class DriveFileInfo:
    """Represents information about a file in Drive."""
    
    def __init__(self, file_id: str, name: str, size: int = 0, 
                 created_time: str = "", modified_time: str = "", 
                 mime_type: str = "", md5_checksum: str = ""):
        self.file_id = file_id
        self.name = name
        self.size = size
        self.created_time = created_time
        self.modified_time = modified_time
        self.mime_type = mime_type
        self.md5_checksum = md5_checksum
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            'file_id': self.file_id,
            'name': self.name,
            'size': self.size,
            'created_time': self.created_time,
            'modified_time': self.modified_time,
            'mime_type': self.mime_type,
            'md5_checksum': self.md5_checksum
        }

class DriveInterface(ABC):
    """Abstract interface for Drive operations."""
    
    @abstractmethod
    async def upload_file(self, file_content: Union[bytes, str, Path], 
                         filename: str, folder_id: str = None, 
                         mime_type: str = None) -> DriveFileInfo:
        """
        Upload a file to Drive.
        
        Args:
            file_content: File content as bytes, string, or Path to file
            filename: Name for the file in Drive
            folder_id: ID of the folder to upload to (None for root)
            mime_type: MIME type of the file (auto-detected if None)
            
        Returns:
            DriveFileInfo object with file details
        """
        pass
    
    @abstractmethod
    async def file_exists(self, filename: str, folder_id: str = None) -> Optional[DriveFileInfo]:
        """
        Check if a file exists in the specified folder.
        
        Args:
            filename: Name of the file to check
            folder_id: ID of the folder to check (None for root)
            
        Returns:
            DriveFileInfo if file exists, None otherwise
        """
        pass
    
    @abstractmethod
    async def list_files(self, folder_id: str = None, query: str = None) -> List[DriveFileInfo]:
        """
        List files in a folder.
        
        Args:
            folder_id: ID of the folder to list (None for root)
            query: Optional query to filter files
            
        Returns:
            List of DriveFileInfo objects
        """
        pass
    
    @abstractmethod
    async def create_folder(self, folder_name: str, parent_folder_id: str = None) -> str:
        """
        Create a new folder.
        
        Args:
            folder_name: Name of the folder to create
            parent_folder_id: ID of the parent folder (None for root)
            
        Returns:
            ID of the created folder
        """
        pass
    
    @abstractmethod
    async def setup_folder_structure(self) -> Dict[str, str]:
        """
        Setup the standard folder structure for the project.
        
        Returns:
            Dictionary mapping folder names to their IDs
        """
        pass
    
    @abstractmethod
    async def delete_file(self, file_id: str) -> bool:
        """
        Delete a file from Drive.
        
        Args:
            file_id: ID of the file to delete
            
        Returns:
            True if successful, False otherwise
        """
        pass
    
    @abstractmethod
    async def download_file(self, file_id: str, local_path: Path) -> bool:
        """
        Download a file from Drive to local storage.
        
        Args:
            file_id: ID of the file to download
            local_path: Local path to save the file
            
        Returns:
            True if successful, False otherwise
        """
        pass
    
    @abstractmethod
    def get_stats(self) -> Dict[str, Any]:
        """
        Get statistics about Drive usage.
        
        Returns:
            Dictionary with statistics
        """
        pass
    
    @abstractmethod
    async def validate_file_integrity(self, file_info: DriveFileInfo, 
                                    expected_size: int = None, 
                                    expected_checksum: str = None) -> bool:
        """
        Validate file integrity using size and/or checksum.
        
        Args:
            file_info: DriveFileInfo object to validate
            expected_size: Expected file size in bytes
            expected_checksum: Expected MD5 checksum
            
        Returns:
            True if file is valid, False otherwise
        """
        pass 