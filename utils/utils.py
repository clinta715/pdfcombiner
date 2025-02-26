import os
from typing import List, Optional, Tuple
from PyQt6.QtWidgets import QMessageBox

class PageRangeError(Exception):
    """Custom exception for page range validation errors"""
    pass

def validate_page_range(page_range: str, max_pages: Optional[int] = None) -> Optional[List[int]]:
    """
    Validate and parse a page range string into a list of page numbers.

    Args:
        page_range: String containing page ranges (e.g., "1-3,5,7-9")
        max_pages: Optional maximum number of pages to validate against

    Returns:
        List of zero-based page numbers, or None if validation fails

    Examples:
        >>> validate_page_range("1-3,5")
        [0, 1, 2, 4]
        >>> validate_page_range("1-3,5", max_pages=4)
        None  # Because 5 exceeds max_pages
    """
    try:
        if not page_range.strip():
            raise PageRangeError("Page range cannot be empty")

        pages = set()  # Use set to avoid duplicates
        parts = [p.strip() for p in page_range.split(',')]

        for part in parts:
            if not part:
                raise PageRangeError("Empty range specified")

            if '-' in part:
                try:
                    start, end = map(int, part.split('-'))
                except ValueError:
                    raise PageRangeError(f"Invalid range format: {part}")

                if start < 1:
                    raise PageRangeError(f"Page numbers must be positive: {start}")
                if end < start:
                    raise PageRangeError(f"End page must be greater than start page: {part}")
                if max_pages and end > max_pages:
                    raise PageRangeError(f"Page number {end} exceeds document length ({max_pages})")

                pages.update(range(start - 1, end))
            else:
                try:
                    page = int(part)
                except ValueError:
                    raise PageRangeError(f"Invalid page number: {part}")

                if page < 1:
                    raise PageRangeError(f"Page numbers must be positive: {page}")
                if max_pages and page > max_pages:
                    raise PageRangeError(f"Page number {page} exceeds document length ({max_pages})")

                pages.add(page - 1)

        return sorted(list(pages))

    except PageRangeError as e:
        msg = QMessageBox()
        msg.setWindowTitle("Invalid Page Range")
        msg.setText(str(e))
        msg.setIcon(QMessageBox.Icon.Warning)
        msg.exec()
        return None

    except Exception as e:
        msg = QMessageBox()
        msg.setWindowTitle("Error")
        msg.setText(f"Error processing page range: {str(e)}")
        msg.setIcon(QMessageBox.Icon.Critical)
        msg.exec()
        return None

def validate_output_directory(directory: str) -> Tuple[bool, str]:
    """
    Validate and create output directory if it doesn't exist.

    Args:
        directory: Path to the output directory

    Returns:
        Tuple of (success: bool, error_message: str)
    """
    try:
        if not directory:
            return False, "Output directory cannot be empty"

        # Expand user directory and environment variables
        directory = os.path.expanduser(os.path.expandvars(directory))

        # Create directory if it doesn't exist
        if not os.path.exists(directory):
            os.makedirs(directory)
        elif not os.path.isdir(directory):
            return False, f"Path exists but is not a directory: {directory}"

        # Check if directory is writable
        if not os.access(directory, os.W_OK):
            return False, f"Directory is not writable: {directory}"

        return True, ""

    except Exception as e:
        return False, f"Error validating directory: {str(e)}"

import random
import string

def generate_password() -> str:
    """Generate a random password that meets complexity requirements"""
    # Define character sets
    uppercase = string.ascii_uppercase
    lowercase = string.ascii_lowercase
    digits = string.digits
    
    # Ensure we have at least one of each required character type
    password = [
        random.choice(uppercase),
        random.choice(lowercase),
        random.choice(digits)
    ]
    
    # Add random characters to reach minimum length
    all_chars = uppercase + lowercase + digits
    password.extend(random.choice(all_chars) for _ in range(5))  # Total length 8
    
    # Shuffle to avoid predictable patterns
    random.shuffle(password)
    
    return ''.join(password)

def get_safe_filename(filename: str) -> str:
    """
    Convert a filename to a safe version that can be used on all operating systems.

    Args:
        filename: Original filename

    Returns:
        Safe version of the filename
    """
    # Replace unsafe characters
    unsafe_chars = '<>:"/\\|?*'
    for char in unsafe_chars:
        filename = filename.replace(char, '_')

    # Remove leading/trailing spaces and dots
    filename = filename.strip('. ')

    # Ensure filename is not empty
    if not filename:
        filename = 'unnamed'

    return filename
