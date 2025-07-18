"""
Centralized logging system for Brazil scraping project.
"""

import logging
import logging.handlers
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional
import json


class ConsoleFormatter(logging.Formatter):
    """Human-readable formatter for console output."""
    
    COLORS = {
        'DEBUG': '\033[36m',     # Cyan
        'INFO': '\033[32m',      # Green  
        'WARNING': '\033[33m',   # Yellow
        'ERROR': '\033[31m',     # Red
        'CRITICAL': '\033[35m',  # Magenta
        'RESET': '\033[0m'       # Reset
    }
    
    def format(self, record: logging.LogRecord) -> str:
        color = self.COLORS.get(record.levelname, '')
        reset = self.COLORS['RESET'] if color else ''
        
        component = getattr(record, 'component', 'general')
        operation = getattr(record, 'operation', '')
        
        timestamp = datetime.fromtimestamp(record.created).strftime('%H:%M:%S')
        
        operation_part = f":{operation}" if operation else ""
        component_part = f"[{component}{operation_part}]"
        
        formatted = f"[{timestamp}] {color}{record.levelname:<8}{reset} {component_part:<20} {record.getMessage()}"
        
        if record.exc_info:
            formatted += f"\n{self.formatException(record.exc_info)}"
            
        return formatted


class BrazilScrapingLogger:
    """Centralized logger for the Brazil scraping system."""
    
    _instance = None
    _initialized = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
            
        self.logger = logging.getLogger('brazil_scraping')
        self.logger.setLevel(logging.DEBUG)
        
        # Clear any existing handlers
        self.logger.handlers.clear()
        
        # Setup handlers
        self._setup_console_handler()
        self._setup_file_handler()
        
        # Prevent propagation to root logger
        self.logger.propagate = False
        
        self._initialized = True
    
    def _setup_console_handler(self):
        """Setup console handler with human-readable format."""
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(ConsoleFormatter())
        self.logger.addHandler(console_handler)
    
    def _setup_file_handler(self):
        """Setup rotating file handler with structured format."""
        logs_dir = Path('logs')
        logs_dir.mkdir(exist_ok=True)
        
        log_file = logs_dir / 'scraping.log'
        file_handler = logging.handlers.RotatingFileHandler(
            log_file,
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=5,
            encoding='utf-8'
        )
        file_handler.setLevel(logging.DEBUG)
        self.logger.addHandler(file_handler)
    
    def get_logger(self, component: str = 'general'):
        """Get a logger instance for a specific component."""
        return ComponentLogger(self.logger, component)


class ComponentLogger:
    """Logger wrapper that adds component context."""
    
    def __init__(self, logger: logging.Logger, component: str):
        self.logger = logger
        self.component = component
    
    def _log(self, level: int, message: str, operation: str = '', extra_data: Optional[dict] = None, **kwargs):
        """Internal logging method that adds component context."""
        extra = {
            'component': self.component,
            'operation': operation
        }
        
        if extra_data:
            extra.update(extra_data)
            
        self.logger.log(level, message, extra=extra, **kwargs)
    
    def debug(self, message: str, operation: str = '', extra_data: Optional[dict] = None, **kwargs):
        self._log(logging.DEBUG, message, operation, extra_data, **kwargs)
    
    def info(self, message: str, operation: str = '', extra_data: Optional[dict] = None, **kwargs):
        self._log(logging.INFO, message, operation, extra_data, **kwargs)
    
    def warning(self, message: str, operation: str = '', extra_data: Optional[dict] = None, **kwargs):
        self._log(logging.WARNING, message, operation, extra_data, **kwargs)
    
    def error(self, message: str, operation: str = '', extra_data: Optional[dict] = None, **kwargs):
        self._log(logging.ERROR, message, operation, extra_data, **kwargs)
    
    def critical(self, message: str, operation: str = '', extra_data: Optional[dict] = None, **kwargs):
        self._log(logging.CRITICAL, message, operation, extra_data, **kwargs)
    
    def exception(self, message: str, operation: str = '', extra_data: Optional[dict] = None, **kwargs):
        kwargs['exc_info'] = True
        self.error(message, operation, extra_data, **kwargs)


# Global logger instance
_global_logger = BrazilScrapingLogger()


def get_logger(component: str = 'general'):
    """Get a logger instance for a specific component."""
    return _global_logger.get_logger(component)


def log_operation_start(component: str, operation: str, details: Optional[dict] = None):
    """Log the start of an operation."""
    logger = get_logger(component)
    logger.info(f"Starting {operation}", operation, details)


def log_operation_success(component: str, operation: str, details: Optional[dict] = None):
    """Log successful completion of an operation."""
    logger = get_logger(component)
    logger.info(f"Completed {operation}", operation, details)


def log_operation_error(component: str, operation: str, error: Exception, details: Optional[dict] = None):
    """Log an operation error with exception details."""
    logger = get_logger(component)
    error_details = details or {}
    error_details.update({
        'error_type': type(error).__name__,
        'error_message': str(error)
    })
    logger.exception(f"Failed {operation}", operation, error_details) 