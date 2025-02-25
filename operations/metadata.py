from PyPDF2 import PdfReader, PdfWriter
from PyQt6.QtWidgets import QMessageBox
from typing import Dict, Any
import os
from datetime import datetime

class MetadataError(Exception):
    """Custom exception for metadata-related errors"""
    pass

class Metadata:
    def __init__(self, parent_window=None):
        self.parent_window = parent_window
        
    # Standard PDF metadata keys (must start with / according to PDF spec)
    VALID_KEYS = {
        '/Title', '/Author', '/Subject', '/Keywords', '/Creator', '/Producer',
        '/CreationDate', '/ModDate', '/Trapped'
    }

    def validate_metadata(self, metadata: Dict[str, Any]) -> None:
        """
        Validate metadata before applying it to the PDF.

        Args:
            metadata: Dictionary of metadata key-value pairs

        Raises:
            MetadataError: If metadata validation fails
        """
        if not isinstance(metadata, dict):
            raise MetadataError("Metadata must be a dictionary")

        # Check for invalid keys
        invalid_keys = set(metadata.keys()) - self.VALID_KEYS
        if invalid_keys:
            raise MetadataError(f"Invalid metadata keys: {', '.join(invalid_keys)}")

        # Validate data types and formats
        for key, value in metadata.items():
            if not isinstance(value, str):
                raise MetadataError(f"Metadata value for '{key}' must be a string")

            # Validate date formats if present
            if key in ('CreationDate', 'ModDate') and value:
                try:
                    # Check if date string is in PDF format (D:YYYYMMDDHHmmSS)
                    if not value.startswith('D:'):
                        # Try to convert datetime to PDF format
                        try:
                            dt = datetime.fromisoformat(value)
                            metadata[key] = f"D:{dt.strftime('%Y%m%d%H%M%S')}"
                        except ValueError:
                            raise MetadataError(f"Invalid date format for {key}")
                except ValueError:
                    raise MetadataError(f"Invalid date format for {key}")

    def backup_pdf(self, pdf_path: str) -> str:
        """
        Create a backup of the original PDF file.

        Args:
            pdf_path: Path to the PDF file

        Returns:
            str: Path to the backup file

        Raises:
            MetadataError: If backup creation fails
        """
        backup_path = f"{pdf_path}.backup.{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        try:
            import shutil
            shutil.copy2(pdf_path, backup_path)
            return backup_path
        except Exception as e:
            raise MetadataError(f"Failed to create backup: {str(e)}")

    def edit_metadata(self, pdf_path: str, new_metadata: Dict[str, Any]) -> None:
        """
        Edit PDF metadata with validation and backup.

        Args:
            pdf_path: Path to the PDF file
            new_metadata: Dictionary of new metadata key-value pairs

        Raises:
            MetadataError: If metadata editing fails
        """
        backup_path = None
        temp_file = None

        try:
            # Validate the PDF path
            if not os.path.exists(pdf_path):
                raise MetadataError("PDF file does not exist")

            if not pdf_path.lower().endswith('.pdf'):
                raise MetadataError("File must be a PDF")

            # Validate metadata
            self.validate_metadata(new_metadata)

            # Create backup
            backup_path = self.backup_pdf(pdf_path)

            # Read and process PDF
            reader = PdfReader(pdf_path)
            writer = PdfWriter()
            writer.append_pages_from_reader(reader)

            # Add modification date if not specified
            if '/ModDate' not in new_metadata:
                new_metadata['/ModDate'] = f"D:{datetime.now().strftime('%Y%m%d%H%M%S')}"

            writer.add_metadata(new_metadata)

            # Save to temporary file
            temp_file = f"{pdf_path}.tmp"
            with open(temp_file, 'wb') as f:
                writer.write(f)

            # Replace original file
            os.replace(temp_file, pdf_path)

            # Update status
            self.parent_window.show_status_message(
                f"Metadata updated successfully! Backup created at: {backup_path}", 
                5000
            )

        except MetadataError as me:
            self.parent_window.show_status_message(
                f"Metadata validation error: {str(me)}",
                5000
            )

        except Exception as e:
            self.parent_window.show_status_message(
                f"Metadata error: {str(e)}. Backup at: {backup_path}",
                5000
            )

        finally:
            # Clean up temporary file if it exists
            if temp_file and os.path.exists(temp_file):
                try:
                    os.remove(temp_file)
                except:
                    pass

    def get_current_metadata(self, pdf_path: str) -> Dict[str, str]:
        """
        Get current metadata from PDF file.

        Args:
            pdf_path: Path to the PDF file

        Returns:
            Dict[str, str]: Current metadata key-value pairs

        Raises:
            MetadataError: If metadata reading fails
        """
        try:
            reader = PdfReader(pdf_path)
            return reader.metadata
        except Exception as e:
            raise MetadataError(f"Could not read metadata: {str(e)}")
