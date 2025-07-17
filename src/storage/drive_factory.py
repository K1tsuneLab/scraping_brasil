"""
Factory for creating appropriate Drive manager instances.
Handles automatic selection between mock and real implementations.
"""
from typing import Optional
from loguru import logger

from src.storage.drive_interface import DriveInterface
from src.storage.mock_drive_manager import MockDriveManager
from config.settings import settings

class DriveFactory:
    """Factory for creating Drive manager instances."""
    
    @staticmethod
    def create_drive_manager(mode: Optional[str] = None) -> DriveInterface:
        """
        Create a Drive manager instance based on the specified mode.
        
        Args:
            mode: Operation mode ('mock', 'real', 'auto', or None for settings default)
            
        Returns:
            DriveInterface implementation
        """
        if mode is None:
            mode = settings.APP_MODE
        
        mode = mode.lower() if mode else 'mock'
        
        if mode == 'mock':
            logger.info("Creating MockDriveManager (development mode)")
            return MockDriveManager()
        
        elif mode == 'real':
            logger.info("Creating RealDriveManager (production mode)")
            return DriveFactory._create_real_drive_manager()
        
        elif mode == 'auto':
            logger.info("Auto mode: attempting real Drive, falling back to mock if needed")
            try:
                return DriveFactory._create_real_drive_manager()
            except Exception as e:
                logger.warning(f"Failed to create real Drive manager: {e}")
                logger.info("Falling back to MockDriveManager")
                return MockDriveManager()
        
        else:
            raise ValueError(f"Invalid mode: {mode}. Must be 'mock', 'real', or 'auto'")
    
    @staticmethod
    def _create_real_drive_manager() -> DriveInterface:
        """
        Create a real Google Drive manager instance.
        
        Returns:
            RealDriveManager instance
            
        Raises:
            ImportError: If Google Drive dependencies are not available
            Exception: If credentials are not properly configured
        """
        try:
            # TODO: Implement RealDriveManager for Google Drive integration
            # from src.storage.drive_manager import RealDriveManager
            
            # Validate that credentials are available
            DriveFactory._validate_drive_credentials()
            
            # For now, raise ImportError to trigger auto mode fallback
            raise ImportError("RealDriveManager not yet implemented - this is expected in Phase 1")
            
        except ImportError as e:
            logger.error("Real Drive manager not yet implemented (Phase 2 feature)")
            raise ImportError(f"Real Drive manager not available: {e}")
        
        except Exception as e:
            logger.error(f"Failed to create real Drive manager: {e}")
            raise
    
    @staticmethod
    def _validate_drive_credentials() -> None:
        """
        Validate that Google Drive credentials are properly configured.
        
        Raises:
            Exception: If credentials are not properly configured
        """
        from pathlib import Path
        
        # Check for credentials file
        credentials_path = Path(settings.GOOGLE_CREDENTIALS_PATH)
        if not credentials_path.exists():
            raise Exception(f"Google Drive credentials file not found: {credentials_path}")
        
        # Check for required settings
        if not settings.GOOGLE_DRIVE_FOLDER_ID:
            logger.warning("GOOGLE_DRIVE_FOLDER_ID not set. Will use root folder.")
        
        logger.info("Google Drive credentials validation passed")
    
    @staticmethod
    def get_recommended_mode() -> str:
        """
        Get the recommended mode based on current environment.
        
        Returns:
            Recommended mode string
        """
        from pathlib import Path
        
        # Check if we have Google Drive credentials
        credentials_path = Path(settings.GOOGLE_CREDENTIALS_PATH)
        has_credentials = credentials_path.exists()
        
        # Check if we have folder ID configured
        has_folder_id = bool(settings.GOOGLE_DRIVE_FOLDER_ID)
        
        if has_credentials and has_folder_id:
            return 'auto'  # Try real, fallback to mock
        elif has_credentials:
            return 'auto'  # Try real but might fail without folder ID
        else:
            return 'mock'  # No credentials, use mock only
    
    @staticmethod
    def get_mode_info() -> dict:
        """
        Get information about available modes and current configuration.
        
        Returns:
            Dictionary with mode information
        """
        from pathlib import Path
        
        credentials_path = Path(settings.GOOGLE_CREDENTIALS_PATH)
        
        return {
            'current_mode': settings.APP_MODE,
            'recommended_mode': DriveFactory.get_recommended_mode(),
            'has_credentials': credentials_path.exists(),
            'has_folder_id': bool(settings.GOOGLE_DRIVE_FOLDER_ID),
            'credentials_path': str(credentials_path),
            'folder_id': settings.GOOGLE_DRIVE_FOLDER_ID or 'Not set',
            'available_modes': ['mock', 'real', 'auto'],
            'mock_storage_path': str(settings.MOCK_STORAGE_PATH)
        } 