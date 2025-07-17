"""
Centralized configuration management for the Brazil Scraping project.
"""
import os
from pathlib import Path
from datetime import datetime, date
from typing import Optional
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Settings:
    """Centralized settings management."""
    
    # Project paths
    PROJECT_ROOT = Path(__file__).parent.parent
    
    # Database settings
    DB_HOST: str = os.getenv('DB_HOST', 'localhost')
    DB_PORT: str = os.getenv('DB_PORT', '5432')
    DB_NAME: str = os.getenv('DB_NAME', 'brasil_scraping')
    DB_USER: str = os.getenv('DB_USER', 'postgres')
    DB_PASSWORD: str = os.getenv('DB_PASSWORD', '')
    
    # Google Drive settings
    GOOGLE_DRIVE_FOLDER_ID: str = os.getenv('GOOGLE_DRIVE_FOLDER_ID', '')
    GOOGLE_CREDENTIALS_PATH: str = os.getenv('GOOGLE_CREDENTIALS_PATH', 'credentials.json')
    GOOGLE_TOKEN_PATH: str = os.getenv('GOOGLE_TOKEN_PATH', 'token.json')
    
    # Application settings
    APP_MODE: str = os.getenv('APP_MODE', 'mock')  # mock, real, auto
    LOG_LEVEL: str = os.getenv('LOG_LEVEL', 'INFO')
    MAX_CONCURRENT_DOWNLOADS: int = int(os.getenv('MAX_CONCURRENT_DOWNLOADS', '5'))
    RETRY_ATTEMPTS: int = int(os.getenv('RETRY_ATTEMPTS', '3'))
    RETRY_DELAY: int = int(os.getenv('RETRY_DELAY', '1'))
    
    # Storage paths
    DATA_RAW_PATH: Path = PROJECT_ROOT / os.getenv('DATA_RAW_PATH', 'data/raw')
    DATA_PROCESSED_PATH: Path = PROJECT_ROOT / os.getenv('DATA_PROCESSED_PATH', 'data/processed')
    MOCK_STORAGE_PATH: Path = PROJECT_ROOT / os.getenv('MOCK_STORAGE_PATH', 'mock_storage')
    LOG_PATH: Path = PROJECT_ROOT / os.getenv('LOG_PATH', 'logs')
    CONFIG_MOCK_DATA_PATH: Path = PROJECT_ROOT / 'config' / 'mock_data'
    
    # API settings
    API_RATE_LIMIT_DELAY: float = float(os.getenv('API_RATE_LIMIT_DELAY', '1'))
    API_TIMEOUT: int = int(os.getenv('API_TIMEOUT', '30'))
    
    # Date range settings
    DEFAULT_START_DATE: str = os.getenv('DEFAULT_START_DATE', '2024-01-01')
    DEFAULT_END_DATE: Optional[str] = os.getenv('DEFAULT_END_DATE')  # None means today
    
    @classmethod
    def get_end_date(cls) -> str:
        """Get end date, defaulting to today if not specified."""
        if cls.DEFAULT_END_DATE:
            return cls.DEFAULT_END_DATE
        return date.today().strftime('%Y-%m-%d')
    
    @classmethod
    def ensure_directories_exist(cls) -> None:
        """Create all necessary directories if they don't exist."""
        directories = [
            cls.DATA_RAW_PATH,
            cls.DATA_PROCESSED_PATH,
            cls.MOCK_STORAGE_PATH,
            cls.LOG_PATH,
            cls.CONFIG_MOCK_DATA_PATH
        ]
        
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
    
    @classmethod
    def get_database_url(cls) -> str:
        """Get database connection URL."""
        return f"postgresql://{cls.DB_USER}:{cls.DB_PASSWORD}@{cls.DB_HOST}:{cls.DB_PORT}/{cls.DB_NAME}"
    
    @classmethod
    def is_mock_mode(cls) -> bool:
        """Check if running in mock mode."""
        return cls.APP_MODE.lower() in ['mock', 'auto']
    
    @classmethod
    def is_real_mode(cls) -> bool:
        """Check if running in real mode."""
        return cls.APP_MODE.lower() == 'real'
    
    @classmethod
    def is_auto_mode(cls) -> bool:
        """Check if running in auto mode."""
        return cls.APP_MODE.lower() == 'auto'

# Create global settings instance
settings = Settings()

# Ensure directories exist when module is imported
settings.ensure_directories_exist() 