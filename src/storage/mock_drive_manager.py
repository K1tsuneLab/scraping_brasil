"""
Mock implementation of Google Drive operations for development and testing.
This allows full development without Google Drive credentials.
"""
import json
import hashlib
import shutil
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional, Union
import asyncio
from loguru import logger

from .drive_interface import DriveInterface, DriveFileInfo
from config.settings import settings

class MockDriveManager(DriveInterface):
    """Mock implementation of Google Drive operations using local filesystem."""
    
    def __init__(self):
        self.storage_path = settings.MOCK_STORAGE_PATH
        self.metadata_file = self.storage_path / "metadata.json"
        self.files_dir = self.storage_path / "files"
        self.stats = {
            'uploads': 0,
            'downloads': 0,
            'deletes': 0,
            'total_size': 0,
            'file_count': 0
        }
        
        # Initialize storage
        self._initialize_storage()
        
        # Load existing metadata
        self.metadata = self._load_metadata()
        
        logger.info(f"MockDriveManager initialized at {self.storage_path}")
    
    def _initialize_storage(self) -> None:
        """Initialize the mock storage structure."""
        self.storage_path.mkdir(parents=True, exist_ok=True)
        self.files_dir.mkdir(exist_ok=True)
        
        # Create standard folder structure
        standard_folders = [
            "documentos_camara",
            "documentos_senado", 
            "processed_data",
            "translations",
            "logs"
        ]
        
        for folder in standard_folders:
            (self.files_dir / folder).mkdir(exist_ok=True)
    
    def _load_metadata(self) -> Dict[str, Any]:
        """Load metadata from file."""
        if self.metadata_file.exists():
            try:
                with open(self.metadata_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"Could not load metadata: {e}")
        
        return {
            'files': {},
            'folders': {
                'root': 'mock_root_id'
            },
            'next_id': 1
        }
    
    def _save_metadata(self) -> None:
        """Save metadata to file."""
        try:
            with open(self.metadata_file, 'w', encoding='utf-8') as f:
                json.dump(self.metadata, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Could not save metadata: {e}")
    
    def _generate_file_id(self) -> str:
        """Generate a unique file ID."""
        file_id = f"mock_file_{self.metadata['next_id']}"
        self.metadata['next_id'] += 1
        return file_id
    
    def _calculate_md5(self, file_path: Path) -> str:
        """Calculate MD5 checksum of a file."""
        hash_md5 = hashlib.md5()
        try:
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_md5.update(chunk)
            return hash_md5.hexdigest()
        except Exception:
            return ""
    
    def _get_file_path(self, file_id: str) -> Path:
        """Get the local file path for a file ID."""
        return self.files_dir / file_id
    
    async def upload_file(self, file_content: Union[bytes, str, Path], 
                         filename: str, folder_id: Optional[str] = None, 
                         mime_type: Optional[str] = None) -> DriveFileInfo:
        """Upload a file to mock storage."""
        file_id = self._generate_file_id()
        file_path = self._get_file_path(file_id)
        
        # Handle different input types
        if isinstance(file_content, Path):
            # Copy from source file
            shutil.copy2(file_content, file_path)
            file_size = file_content.stat().st_size
        elif isinstance(file_content, bytes):
            # Write bytes content
            with open(file_path, 'wb') as f:
                f.write(file_content)
            file_size = len(file_content)
        elif isinstance(file_content, str):
            # Write string content
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(file_content)
            file_size = len(file_content.encode('utf-8'))
        else:
            raise ValueError(f"Unsupported file_content type: {type(file_content)}")
        
        # Calculate checksum
        md5_checksum = self._calculate_md5(file_path)
        
        # Create file info
        now = datetime.now().isoformat()
        file_info = DriveFileInfo(
            file_id=file_id,
            name=filename,
            size=file_size,
            created_time=now,
            modified_time=now,
            mime_type=mime_type or "application/octet-stream",
            md5_checksum=md5_checksum
        )
        
        # Store metadata
        self.metadata['files'][file_id] = {
            **file_info.to_dict(),
            'folder_id': folder_id or 'root',
            'local_path': str(file_path)
        }
        
        # Update stats
        self.stats['uploads'] += 1
        self.stats['total_size'] += file_size
        self.stats['file_count'] += 1
        
        self._save_metadata()
        
        logger.info(f"Uploaded file {filename} ({file_size} bytes) as {file_id}")
        return file_info
    
    async def file_exists(self, filename: str, folder_id: Optional[str] = None) -> Optional[DriveFileInfo]:
        """Check if a file exists."""
        folder_id = folder_id or 'root'
        
        for file_id, file_data in self.metadata['files'].items():
            if (file_data['name'] == filename and 
                file_data['folder_id'] == folder_id):
                return DriveFileInfo(**{k: v for k, v in file_data.items() 
                                      if k != 'folder_id' and k != 'local_path'})
        
        return None
    
    async def list_files(self, folder_id: Optional[str] = None, query: Optional[str] = None) -> List[DriveFileInfo]:
        """List files in a folder."""
        folder_id = folder_id or 'root'
        files = []
        
        for file_id, file_data in self.metadata['files'].items():
            if file_data['folder_id'] == folder_id:
                # Apply query filter if provided
                if query is None or query.lower() in file_data['name'].lower():
                    file_info = DriveFileInfo(**{k: v for k, v in file_data.items() 
                                               if k != 'folder_id' and k != 'local_path'})
                    files.append(file_info)
        
        return files
    
    async def create_folder(self, folder_name: str, parent_folder_id: Optional[str] = None) -> str:
        """Create a new folder."""
        folder_id = self._generate_file_id().replace('file', 'folder')
        folder_path = self.files_dir / folder_name
        folder_path.mkdir(exist_ok=True)
        
        self.metadata['folders'][folder_name] = folder_id
        self._save_metadata()
        
        logger.info(f"Created folder {folder_name} with ID {folder_id}")
        return folder_id
    
    async def setup_folder_structure(self) -> Dict[str, str]:
        """Setup the standard folder structure."""
        folders = {
            'documentos_camara': await self.create_folder('documentos_camara'),
            'documentos_senado': await self.create_folder('documentos_senado'),
            'processed_data': await self.create_folder('processed_data'),
            'translations': await self.create_folder('translations'),
            'logs': await self.create_folder('logs')
        }
        
        logger.info(f"Setup folder structure: {folders}")
        return folders
    
    async def delete_file(self, file_id: str) -> bool:
        """Delete a file."""
        if file_id in self.metadata['files']:
            file_data = self.metadata['files'][file_id]
            local_path = Path(file_data['local_path'])
            
            # Delete local file
            if local_path.exists():
                local_path.unlink()
            
            # Update stats
            self.stats['deletes'] += 1
            self.stats['total_size'] -= file_data['size']
            self.stats['file_count'] -= 1
            
            # Remove from metadata
            del self.metadata['files'][file_id]
            self._save_metadata()
            
            logger.info(f"Deleted file {file_id}")
            return True
        
        return False
    
    async def download_file(self, file_id: str, local_path: Path) -> bool:
        """Download a file to local storage."""
        if file_id in self.metadata['files']:
            file_data = self.metadata['files'][file_id]
            source_path = Path(file_data['local_path'])
            
            if source_path.exists():
                # Ensure target directory exists
                local_path.parent.mkdir(parents=True, exist_ok=True)
                
                # Copy file
                shutil.copy2(source_path, local_path)
                
                self.stats['downloads'] += 1
                
                logger.info(f"Downloaded file {file_id} to {local_path}")
                return True
        
        return False
    
    def get_stats(self) -> Dict[str, Any]:
        """Get statistics about mock Drive usage."""
        return {
            **self.stats,
            'storage_path': str(self.storage_path),
            'metadata_file_size': self.metadata_file.stat().st_size if self.metadata_file.exists() else 0,
            'total_files_tracked': len(self.metadata['files'])
        }
    
    async def validate_file_integrity(self, file_info: DriveFileInfo, 
                                    expected_size: Optional[int] = None, 
                                    expected_checksum: Optional[str] = None) -> bool:
        """Validate file integrity."""
        if file_info.file_id not in self.metadata['files']:
            return False
        
        file_data = self.metadata['files'][file_info.file_id]
        local_path = Path(file_data['local_path'])
        
        if not local_path.exists():
            return False
        
        # Check size
        if expected_size is not None:
            actual_size = local_path.stat().st_size
            if actual_size != expected_size:
                logger.warning(f"Size mismatch for {file_info.file_id}: expected {expected_size}, got {actual_size}")
                return False
        
        # Check checksum
        if expected_checksum is not None:
            actual_checksum = self._calculate_md5(local_path)
            if actual_checksum != expected_checksum:
                logger.warning(f"Checksum mismatch for {file_info.file_id}: expected {expected_checksum}, got {actual_checksum}")
                return False
        
        return True 