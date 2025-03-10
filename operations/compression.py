from PyPDF2 import PdfReader, PdfWriter
from PyQt6.QtWidgets import QMessageBox
import os

class PDFCompressor:
    def __init__(self, parent_window=None):
        self.parent_window = parent_window
        
    def compress_pdf(self, pdf_path, quality_level):
        """
        Compress a PDF file with specified quality level
        
        Args:
            pdf_path: Path to input PDF file
            quality_level: Compression level (1-3)
                          1: Fast (lower quality)
                          2: Balanced
                          3: Best (higher quality)
        """
        try:
            # Validate input
            if not os.path.exists(pdf_path):
                raise ValueError("PDF file does not exist")
                
            if not pdf_path.lower().endswith('.pdf'):
                raise ValueError("File must be a PDF")
                
            if quality_level not in (1, 2, 3):
                raise ValueError("Quality level must be 1, 2, or 3")

            # Get original size before compression
            original_size = os.path.getsize(pdf_path)
            
            # Create PDF reader and writer
            reader = PdfReader(pdf_path)
            writer = PdfWriter()

            # Set compression parameters based on quality level
            compression_params = {
                1: {'compress_content_streams': True, 'compress_images': True},
                2: {'compress_content_streams': True, 'compress_images': True, 'image_quality': 75},
                3: {'compress_content_streams': True, 'compress_images': True, 'image_quality': 90}
            }

            # Add pages with compression
            for page in reader.pages:
                writer.add_page(page)
                writer.add_metadata(reader.metadata)

            # Apply compression settings
            writer.compress_content_streams = compression_params[quality_level]['compress_content_streams']
            if 'image_quality' in compression_params[quality_level]:
                for page in writer.pages:
                    for img in page.images:
                        img.compress(compression_params[quality_level]['image_quality'])

            # Write to temporary file
            temp_file = pdf_path + '.tmp'
            with open(temp_file, 'wb') as f:
                writer.write(f)

            # Replace original file
            os.replace(temp_file, pdf_path)

            # Update status
            self.parent_window.show_status_message(
                f"PDF compressed: {os.path.getsize(pdf_path) / 1024:.1f} KB (was {original_size / 1024:.1f} KB)",
                5000
            )

        except Exception as e:
            self.parent_window.show_status_message(f"Compression error: {str(e)}", 5000)
