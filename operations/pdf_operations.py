from PyPDF2 import PdfMerger, PdfReader, PdfWriter
from PyQt6.QtWidgets import QMessageBox, QApplication
import pytesseract
from pdf2image import convert_from_path
import tempfile
import os

class PDFOperations:
    def __init__(self, parent_window=None):
        self.parent_window = parent_window

    def perform_ocr(self, pdf_path):
        """Perform OCR on a PDF file"""
        try:
            if not os.path.exists(pdf_path):
                raise ValueError("PDF file does not exist")
                
            if not pdf_path.lower().endswith('.pdf'):
                raise ValueError("File must be a PDF")

            if self.parent_window:
                self.parent_window.show_status_message("Starting OCR...")
                self.parent_window.update_status_label("Performing OCR")
                self.parent_window.show_progress(0, 100)

            # Convert PDF to images
            images = convert_from_path(pdf_path)
            total_pages = len(images)
            
            # Create temp directory for OCR output
            with tempfile.TemporaryDirectory() as temp_dir:
                output_pdf = os.path.join(temp_dir, "ocr_output.pdf")
                
                # Perform OCR on each page
                for i, image in enumerate(images):
                    if self.parent_window:
                        progress = int((i + 1) / total_pages * 100)
                        self.parent_window.show_progress(progress)
                        self.parent_window.update_status_label(f"Processing page {i+1}/{total_pages}")
                        QApplication.processEvents()

                    text = pytesseract.image_to_pdf_or_hocr(image, extension='pdf')
                    with open(output_pdf if i == 0 else os.path.join(temp_dir, f"page_{i}.pdf"), 'wb') as f:
                        f.write(text)
                
                # Combine OCR pages
                merger = PdfMerger()
                for i in range(len(images)):
                    page_path = output_pdf if i == 0 else os.path.join(temp_dir, f"page_{i}.pdf")
                    merger.append(page_path)
                
                # Save final output
                output_path = pdf_path.replace('.pdf', '_ocr.pdf')
                merger.write(output_path)
                merger.close()

                if self.parent_window:
                    self.parent_window.show_status_message("OCR completed successfully", 3000)
                    self.parent_window.hide_progress()
                
                return output_path
                
        except Exception as e:
            if self.parent_window:
                self.parent_window.show_status_message(f"OCR error: {str(e)}", 5000)
                self.parent_window.hide_progress()
            raise Exception(f"OCR failed: {str(e)}")
    def combine_pdfs(self, pdf_files, output_file, progress_callback=None):
        merger = PdfMerger()
        
        try:
            for i, pdf in enumerate(pdf_files):
                merger.append(pdf)
                
                # Update progress if callback provided
                if progress_callback:
                    progress_callback(i + 1, len(pdf_files))
                    QApplication.processEvents()  # Ensure the UI updates during the operation

            merger.write(output_file)
            
        except Exception as e:
            raise Exception(f"Failed to combine PDFs: {str(e)}")
        finally:
            merger.close()
