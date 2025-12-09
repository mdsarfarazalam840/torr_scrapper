"""
Helper utilities for the Torrent Automation System.
"""

import os
import yaml
from typing import Dict, Any

def format_bytes(bytes_value: int) -> str:
    """
    Format bytes to human-readable string.
    
    Args:
        bytes_value: Size in bytes
        
    Returns:
        str: Formatted string (e.g., "1.5 GB")
    """
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if bytes_value < 1024.0:
            return f"{bytes_value:.2f} {unit}"
        bytes_value /= 1024.0
    return f"{bytes_value:.2f} PB"

def format_speed(bytes_per_sec: int) -> str:
    """
    Format speed to human-readable string.
    
    Args:
        bytes_per_sec: Speed in bytes per second
        
    Returns:
        str: Formatted string (e.g., "1.5 MB/s")
    """
    return f"{format_bytes(bytes_per_sec)}/s"

def format_time(seconds: int) -> str:
    """
    Format seconds to human-readable time string.
    
    Args:
        seconds: Time in seconds
        
    Returns:
        str: Formatted string (e.g., "1h 23m 45s")
    """
    if seconds < 0:
        return "Unknown"
    
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    secs = seconds % 60
    
    if hours > 0:
        return f"{hours}h {minutes}m {secs}s"
    elif minutes > 0:
        return f"{minutes}m {secs}s"
    else:
        return f"{secs}s"

def validate_path(path: str, create_if_missing: bool = False) -> bool:
    """
    Validate if a path exists, optionally create it.
    
    Args:
        path: Path to validate
        create_if_missing: Create directory if it doesn't exist
        
    Returns:
        bool: True if path exists or was created
    """
    if os.path.exists(path):
        return True
    
    if create_if_missing:
        try:
            os.makedirs(path, exist_ok=True)
            return True
        except Exception:
            return False
    
    return False

def load_config(config_path: str = 'config/config.yaml') -> Dict[str, Any]:
    """
    Load configuration from YAML file.
    
    Args:
        config_path: Path to config file
        
    Returns:
        dict: Configuration dictionary
    """
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    except FileNotFoundError:
        raise FileNotFoundError(f"Configuration file not found: {config_path}")
    except yaml.YAMLError as e:
        raise ValueError(f"Invalid YAML configuration: {e}")

def sanitize_filename(filename: str) -> str:
    """
    Remove invalid characters from filename.
    
    Args:
        filename: Original filename
        
    Returns:
        str: Sanitized filename
    """
    invalid_chars = '<>:"/\\|?*'
    for char in invalid_chars:
        filename = filename.replace(char, '_')
    return filename.strip()

def truncate_string(text: str, max_length: int = 50) -> str:
    """
    Truncate string to max length with ellipsis.
    
    Args:
        text: Input text
        max_length: Maximum length
        
    Returns:
        str: Truncated string
    """
    if len(text) <= max_length:
        return text
    return text[:max_length-3] + "..."
