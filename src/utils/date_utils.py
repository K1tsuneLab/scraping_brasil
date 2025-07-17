"""
Date utility functions for the Brazil scraping project.
Handles date parsing, formatting, and range calculations.
"""
from datetime import datetime, date, timedelta
from typing import List, Optional, Tuple
from loguru import logger

def parse_date(date_str: str, formats: Optional[List[str]] = None) -> Optional[date]:
    """
    Parse a date string using multiple possible formats.
    
    Args:
        date_str: Date string to parse
        formats: List of date formats to try (uses common formats if None)
        
    Returns:
        Parsed date object or None if parsing fails
    """
    if formats is None:
        formats = [
            '%Y-%m-%d',           # 2024-01-15
            '%d/%m/%Y',           # 15/01/2024
            '%Y-%m-%dT%H:%M:%S',  # 2024-01-15T10:30:00
            '%Y-%m-%dT%H:%M:%SZ', # 2024-01-15T10:30:00Z
            '%Y-%m-%d %H:%M:%S',  # 2024-01-15 10:30:00
            '%d-%m-%Y',           # 15-01-2024
            '%m/%d/%Y',           # 01/15/2024
        ]
    
    for fmt in formats:
        try:
            parsed = datetime.strptime(date_str, fmt)
            return parsed.date()
        except ValueError:
            continue
    
    logger.warning(f"Could not parse date: {date_str}")
    return None

def format_date(date_obj: date, format_str: str = '%Y-%m-%d') -> str:
    """
    Format a date object to string.
    
    Args:
        date_obj: Date object to format
        format_str: Format string (default: YYYY-MM-DD)
        
    Returns:
        Formatted date string
    """
    return date_obj.strftime(format_str)

def get_date_range_since_2024() -> Tuple[str, str]:
    """
    Get date range from 2024-01-01 to today.
    
    Returns:
        Tuple of (start_date, end_date) in YYYY-MM-DD format
    """
    start_date = '2024-01-01'
    end_date = date.today().strftime('%Y-%m-%d')
    return start_date, end_date

def get_custom_date_range(start_date: str, end_date: Optional[str] = None) -> Tuple[str, str]:
    """
    Get a custom date range, validating the dates.
    
    Args:
        start_date: Start date in YYYY-MM-DD format
        end_date: End date in YYYY-MM-DD format (defaults to today)
        
    Returns:
        Tuple of (start_date, end_date) in YYYY-MM-DD format
        
    Raises:
        ValueError: If dates are invalid or start_date > end_date
    """
    # Parse and validate start date
    parsed_start = parse_date(start_date)
    if parsed_start is None:
        raise ValueError(f"Invalid start date: {start_date}")
    
    # Parse and validate end date
    if end_date is None:
        parsed_end = date.today()
        end_date = format_date(parsed_end)
    else:
        parsed_end = parse_date(end_date)
        if parsed_end is None:
            raise ValueError(f"Invalid end date: {end_date}")
    
    # Validate date range
    if parsed_start > parsed_end:
        raise ValueError(f"Start date {start_date} is after end date {end_date}")
    
    return format_date(parsed_start), format_date(parsed_end)

def is_date_in_range(check_date: str, start_date: str, end_date: str) -> bool:
    """
    Check if a date is within a specified range.
    
    Args:
        check_date: Date to check in YYYY-MM-DD format
        start_date: Start date in YYYY-MM-DD format
        end_date: End date in YYYY-MM-DD format
        
    Returns:
        True if date is in range, False otherwise
    """
    parsed_check = parse_date(check_date)
    parsed_start = parse_date(start_date)
    parsed_end = parse_date(end_date)
    
    if any(d is None for d in [parsed_check, parsed_start, parsed_end]):
        return False
    
    # Type checking assurance - we know these are not None due to check above
    assert parsed_check is not None and parsed_start is not None and parsed_end is not None
    return parsed_start <= parsed_check <= parsed_end

def get_months_in_range(start_date: str, end_date: str) -> List[Tuple[str, str]]:
    """
    Get list of month ranges within the specified date range.
    Useful for processing large date ranges in smaller chunks.
    
    Args:
        start_date: Start date in YYYY-MM-DD format
        end_date: End date in YYYY-MM-DD format
        
    Returns:
        List of (month_start, month_end) tuples in YYYY-MM-DD format
    """
    parsed_start = parse_date(start_date)
    parsed_end = parse_date(end_date)
    
    if parsed_start is None or parsed_end is None:
        raise ValueError("Invalid date format")
    
    months = []
    current = parsed_start.replace(day=1)  # Start of month
    
    while current <= parsed_end:
        # Calculate end of current month
        if current.month == 12:
            next_month = current.replace(year=current.year + 1, month=1)
        else:
            next_month = current.replace(month=current.month + 1)
        
        month_end = next_month - timedelta(days=1)
        
        # Adjust for actual range
        range_start = max(current, parsed_start)
        range_end = min(month_end, parsed_end)
        
        months.append((format_date(range_start), format_date(range_end)))
        
        current = next_month
    
    return months

def days_between_dates(start_date: str, end_date: str) -> int:
    """
    Calculate number of days between two dates.
    
    Args:
        start_date: Start date in YYYY-MM-DD format
        end_date: End date in YYYY-MM-DD format
        
    Returns:
        Number of days between dates
    """
    parsed_start = parse_date(start_date)
    parsed_end = parse_date(end_date)
    
    if parsed_start is None or parsed_end is None:
        raise ValueError("Invalid date format")
    
    return (parsed_end - parsed_start).days

def is_recent_date(check_date: str, days_threshold: int = 7) -> bool:
    """
    Check if a date is recent (within specified days from today).
    
    Args:
        check_date: Date to check in YYYY-MM-DD format
        days_threshold: Number of days to consider as "recent"
        
    Returns:
        True if date is recent, False otherwise
    """
    parsed_date = parse_date(check_date)
    if parsed_date is None:
        return False
    
    today = date.today()
    threshold_date = today - timedelta(days=days_threshold)
    
    return parsed_date >= threshold_date

def get_year_from_date(date_str: str) -> Optional[int]:
    """
    Extract year from a date string.
    
    Args:
        date_str: Date string to parse
        
    Returns:
        Year as integer or None if parsing fails
    """
    parsed_date = parse_date(date_str)
    return parsed_date.year if parsed_date else None

def normalize_date_format(date_str: str, target_format: str = '%Y-%m-%d') -> Optional[str]:
    """
    Normalize a date string to a specific format.
    
    Args:
        date_str: Date string to normalize
        target_format: Target format (default: YYYY-MM-DD)
        
    Returns:
        Normalized date string or None if parsing fails
    """
    parsed_date = parse_date(date_str)
    return format_date(parsed_date, target_format) if parsed_date else None 