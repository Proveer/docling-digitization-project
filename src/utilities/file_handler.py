"""File handling utilities."""

import os
import shutil
from pathlib import Path
from typing import BinaryIO
import logging

logger = logging.getLogger(__name__)


async def save_uploaded_file(
    file_content: bytes,
    filename: str,
    upload_dir: Path
) -> Path:
    """
    Save uploaded file to disk.
    
    Args:
        file_content: File content bytes
        filename: Original filename
        upload_dir: Directory to save file
        
    Returns:
        Path to saved file
    """
    upload_dir.mkdir(parents=True, exist_ok=True)
    file_path = upload_dir / filename
    
    try:
        with file_path.open("wb") as f:
            f.write(file_content)
        logger.info(f"File saved: {file_path}")
        return file_path
    except Exception as e:
        logger.error(f"Failed to save file {filename}: {e}")
        raise


def cleanup_file(file_path: Path) -> None:
    """
    Delete a file from disk.
    
    Args:
        file_path: Path to file to delete
    """
    try:
        if file_path.exists():
            file_path.unlink()
            logger.info(f"File deleted: {file_path}")
    except Exception as e:
        logger.error(f"Failed to delete file {file_path}: {e}")


def validate_file_extension(filename: str, allowed_extensions: set) -> bool:
    """
    Validate file extension.
    
    Args:
        filename: Filename to validate
        allowed_extensions: Set of allowed extensions (e.g., {'.pdf', '.docx'})
        
    Returns:
        True if valid, False otherwise
    """
    file_ext = Path(filename).suffix.lower()
    return file_ext in allowed_extensions


def get_file_size_mb(file_path: Path) -> float:
    """
    Get file size in megabytes.
    
    Args:
        file_path: Path to file
        
    Returns:
        File size in MB
    """
    size_bytes = file_path.stat().st_size
    return size_bytes / (1024 * 1024)
