"""
Custom exceptions for the Brazil scraping system.
Provides a hierarchy of exceptions for better error handling and debugging.
"""

from typing import Optional, Dict, Any


class BrazilScrapingError(Exception):
    """Base exception for all Brazil scraping related errors."""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None, operation: Optional[str] = None):
        self.message = message
        self.details = details or {}
        self.operation = operation
        super().__init__(self.message)
    
    def __str__(self) -> str:
        base_msg = self.message
        if self.operation:
            base_msg = f"[{self.operation}] {base_msg}"
        
        if self.details:
            details_str = ", ".join(f"{k}={v}" for k, v in self.details.items())
            base_msg += f" (Details: {details_str})"
        
        return base_msg


class ConfigurationError(BrazilScrapingError):
    """Raised when there are configuration-related issues."""
    pass


class ValidationError(BrazilScrapingError):
    """Raised when data validation fails."""
    
    def __init__(self, message: str, field: Optional[str] = None, value: Any = None, **kwargs):
        details = kwargs.get('details', {})
        if field:
            details['field'] = field
        if value is not None:
            details['value'] = str(value)
        super().__init__(message, details, kwargs.get('operation'))


class ScrapingError(BrazilScrapingError):
    """Raised when web scraping operations fail."""
    
    def __init__(self, message: str, url: Optional[str] = None, status_code: Optional[int] = None, **kwargs):
        details = kwargs.get('details', {})
        if url:
            details['url'] = url
        if status_code:
            details['status_code'] = status_code
        super().__init__(message, details, kwargs.get('operation'))


class APIError(ScrapingError):
    """Raised when API calls fail."""
    
    def __init__(self, message: str, endpoint: Optional[str] = None, response_data: Optional[Dict] = None, **kwargs):
        details = kwargs.get('details', {})
        if endpoint:
            details['endpoint'] = endpoint
        if response_data:
            details['response_data'] = response_data
        super().__init__(message, **kwargs)


class DataProcessingError(BrazilScrapingError):
    """Raised when data processing operations fail."""
    
    def __init__(self, message: str, document_id: Optional[str] = None, processor: Optional[str] = None, **kwargs):
        details = kwargs.get('details', {})
        if document_id:
            details['document_id'] = document_id
        if processor:
            details['processor'] = processor
        super().__init__(message, details, kwargs.get('operation'))


class StorageError(BrazilScrapingError):
    """Raised when storage operations fail."""
    
    def __init__(self, message: str, file_path: Optional[str] = None, storage_type: Optional[str] = None, **kwargs):
        details = kwargs.get('details', {})
        if file_path:
            details['file_path'] = file_path
        if storage_type:
            details['storage_type'] = storage_type
        super().__init__(message, details, kwargs.get('operation'))


class DriveError(StorageError):
    """Raised when Google Drive operations fail."""
    
    def __init__(self, message: str, drive_operation: Optional[str] = None, file_id: Optional[str] = None, **kwargs):
        details = kwargs.get('details', {})
        if drive_operation:
            details['drive_operation'] = drive_operation
        if file_id:
            details['file_id'] = file_id
        super().__init__(message, storage_type='google_drive', **kwargs)


class DocumentError(BrazilScrapingError):
    """Raised when document-related operations fail."""
    
    def __init__(self, message: str, document_type: Optional[str] = None, document_source: Optional[str] = None, **kwargs):
        details = kwargs.get('details', {})
        if document_type:
            details['document_type'] = document_type
        if document_source:
            details['document_source'] = document_source
        super().__init__(message, details, kwargs.get('operation'))


class DuplicateDocumentError(DocumentError):
    """Raised when a duplicate document is detected."""
    
    def __init__(self, message: str, duplicate_type: str, original_id: Optional[str] = None, **kwargs):
        details = kwargs.get('details', {})
        details['duplicate_type'] = duplicate_type
        if original_id:
            details['original_id'] = original_id
        super().__init__(message, **kwargs)


class TranslationError(BrazilScrapingError):
    """Raised when translation operations fail."""
    
    def __init__(self, message: str, source_lang: Optional[str] = None, target_lang: Optional[str] = None, **kwargs):
        details = kwargs.get('details', {})
        if source_lang:
            details['source_lang'] = source_lang
        if target_lang:
            details['target_lang'] = target_lang
        super().__init__(message, details, kwargs.get('operation'))


class RateLimitError(APIError):
    """Raised when API rate limits are exceeded."""
    
    def __init__(self, message: str, retry_after: Optional[int] = None, **kwargs):
        details = kwargs.get('details', {})
        if retry_after:
            details['retry_after_seconds'] = retry_after
        super().__init__(message, **kwargs)


class AuthenticationError(BrazilScrapingError):
    """Raised when authentication fails."""
    
    def __init__(self, message: str, service: Optional[str] = None, **kwargs):
        details = kwargs.get('details', {})
        if service:
            details['service'] = service
        super().__init__(message, details, kwargs.get('operation'))


class TimeoutError(BrazilScrapingError):
    """Raised when operations timeout."""
    
    def __init__(self, message: str, timeout_seconds: Optional[float] = None, **kwargs):
        details = kwargs.get('details', {})
        if timeout_seconds:
            details['timeout_seconds'] = timeout_seconds
        super().__init__(message, details, kwargs.get('operation'))


class RetryableError(BrazilScrapingError):
    """Base class for errors that can be retried."""
    
    def __init__(self, message: str, max_retries: int = 3, **kwargs):
        details = kwargs.get('details', {})
        details['max_retries'] = max_retries
        super().__init__(message, details, kwargs.get('operation'))


class NetworkError(RetryableError):
    """Raised when network operations fail."""
    pass


class ServiceUnavailableError(RetryableError):
    """Raised when external services are unavailable."""
    
    def __init__(self, message: str, service_name: Optional[str] = None, **kwargs):
        details = kwargs.get('details', {})
        if service_name:
            details['service_name'] = service_name
        super().__init__(message, **kwargs)


# Convenience functions for common error scenarios
def raise_configuration_error(message: str, setting: Optional[str] = None, value: Any = None):
    """Raise a configuration error with standardized details."""
    details = {}
    if setting:
        details['setting'] = setting
    if value is not None:
        details['value'] = str(value)
    raise ConfigurationError(message, details=details)


def raise_validation_error(message: str, field: str, value: Any, operation: Optional[str] = None):
    """Raise a validation error with standardized details."""
    raise ValidationError(message, field=field, value=value, operation=operation)


def raise_api_error(message: str, endpoint: str, status_code: Optional[int] = None, operation: Optional[str] = None):
    """Raise an API error with standardized details."""
    raise APIError(message, endpoint=endpoint, status_code=status_code, operation=operation)


def raise_storage_error(message: str, file_path: str, operation: Optional[str] = None):
    """Raise a storage error with standardized details."""
    raise StorageError(message, file_path=file_path, operation=operation)


def raise_duplicate_error(message: str, duplicate_type: str, document_id: str, original_id: Optional[str] = None):
    """Raise a duplicate document error with standardized details."""
    raise DuplicateDocumentError(
        message, 
        duplicate_type=duplicate_type, 
        original_id=original_id,
        details={'document_id': document_id}
    ) 