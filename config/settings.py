"""
Centralized configuration management for the Brazil Scraping project.
Provides validated, type-safe configuration with environment variable support.
"""
import os
from pathlib import Path
from datetime import datetime, date
from typing import Optional, List, Dict, Any, Callable
from dataclasses import dataclass
from dotenv import load_dotenv

# Configuration validation utilities
class ConfigurationError(Exception):
    """Raised when configuration validation fails."""
    pass

def raise_configuration_error(message: str, setting: Optional[str] = None, value: Any = None):
    """Raise a configuration error with details."""
    details = f" (setting: {setting}, value: {value})" if setting else ""
    raise ConfigurationError(f"{message}{details}")

# Load environment variables from .env file
load_dotenv()

@dataclass
class ValidationRule:
    """Represents a configuration validation rule."""
    name: str
    validator: Callable[[Any], bool]
    error_message: str


class Settings:
    """Centralized settings management with validation."""
    
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
    
    @classmethod
    def validate_configuration(cls) -> List[str]:
        """Validate all configuration settings and return list of errors."""
        errors = []
        
        # Define validation rules
        validation_rules = [
            ValidationRule(
                name="APP_MODE",
                validator=lambda x: x.lower() in ['mock', 'real', 'auto'],
                error_message="APP_MODE must be one of: mock, real, auto"
            ),
            ValidationRule(
                name="LOG_LEVEL",
                validator=lambda x: x.upper() in ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
                error_message="LOG_LEVEL must be one of: DEBUG, INFO, WARNING, ERROR, CRITICAL"
            ),
            ValidationRule(
                name="MAX_CONCURRENT_DOWNLOADS",
                validator=lambda x: 1 <= x <= 20,
                error_message="MAX_CONCURRENT_DOWNLOADS must be between 1 and 20"
            ),
            ValidationRule(
                name="RETRY_ATTEMPTS",
                validator=lambda x: 0 <= x <= 10,
                error_message="RETRY_ATTEMPTS must be between 0 and 10"
            ),
            ValidationRule(
                name="API_TIMEOUT",
                validator=lambda x: 5 <= x <= 300,
                error_message="API_TIMEOUT must be between 5 and 300 seconds"
            ),
            ValidationRule(
                name="DEFAULT_START_DATE",
                validator=cls._validate_date_format,
                error_message="DEFAULT_START_DATE must be in YYYY-MM-DD format"
            )
        ]
        
        # Validate each rule
        for rule in validation_rules:
            try:
                value = getattr(cls, rule.name)
                if not rule.validator(value):
                    errors.append(f"{rule.error_message} (current: {value})")
            except Exception as e:
                errors.append(f"Error validating {rule.name}: {str(e)}")
        
        # Validate directory permissions
        try:
            cls.ensure_directories_exist()
        except Exception as e:
            errors.append(f"Directory creation failed: {str(e)}")
        
        # Validate date range
        try:
            start_date = datetime.strptime(cls.DEFAULT_START_DATE, '%Y-%m-%d').date()
            end_date = datetime.strptime(cls.get_end_date(), '%Y-%m-%d').date()
            if start_date >= end_date:
                errors.append(f"Start date ({start_date}) must be before end date ({end_date})")
        except Exception as e:
            errors.append(f"Date range validation failed: {str(e)}")
        
        # Validate Google Drive settings if in real mode
        if cls.is_real_mode():
            if not cls.GOOGLE_DRIVE_FOLDER_ID:
                errors.append("GOOGLE_DRIVE_FOLDER_ID is required in real mode")
            if not Path(cls.GOOGLE_CREDENTIALS_PATH).exists():
                errors.append(f"Google credentials file not found: {cls.GOOGLE_CREDENTIALS_PATH}")
        
        return errors
    
    @staticmethod
    def _validate_date_format(date_str: str) -> bool:
        """Validate date string format."""
        try:
            datetime.strptime(date_str, '%Y-%m-%d')
            return True
        except ValueError:
            return False
    
    @classmethod
    def validate_and_raise(cls) -> None:
        """Validate configuration and raise error if invalid."""
        errors = cls.validate_configuration()
        if errors:
            error_message = "Configuration validation failed:\n" + "\n".join(f"- {error}" for error in errors)
            raise_configuration_error(error_message)
    
    @classmethod
    def get_configuration_summary(cls) -> Dict[str, Any]:
        """Get a summary of current configuration."""
        return {
            'mode': cls.APP_MODE,
            'log_level': cls.LOG_LEVEL,
            'date_range': {
                'start': cls.DEFAULT_START_DATE,
                'end': cls.get_end_date()
            },
            'paths': {
                'project_root': str(cls.PROJECT_ROOT),
                'data_raw': str(cls.DATA_RAW_PATH),
                'data_processed': str(cls.DATA_PROCESSED_PATH),
                'mock_storage': str(cls.MOCK_STORAGE_PATH),
                'logs': str(cls.LOG_PATH)
            },
            'api_settings': {
                'timeout': cls.API_TIMEOUT,
                'rate_limit_delay': cls.API_RATE_LIMIT_DELAY,
                'max_concurrent_downloads': cls.MAX_CONCURRENT_DOWNLOADS
            },
            'google_drive': {
                'folder_id': cls.GOOGLE_DRIVE_FOLDER_ID or 'Not configured',
                'credentials_path': cls.GOOGLE_CREDENTIALS_PATH,
                'token_path': cls.GOOGLE_TOKEN_PATH
            }
        }

# Create global settings instance
settings = Settings()

# Ensure directories exist when module is imported
settings.ensure_directories_exist() 