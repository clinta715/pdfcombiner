from PyPDF2 import PdfMerger, PdfReader, PdfWriter
from PyQt6.QtWidgets import QMessageBox, QApplication
import pytesseract
from pdf2image import convert_from_path
import tempfile
import os

class PDFOperations:
    def perform_ocr(self, pdf_path):
        """Perform OCR on a PDF file"""
        try:
            # Convert PDF to images
            images = convert_from_path(pdf_path)
            
            # Create temp directory for OCR output
            with tempfile.TemporaryDirectory() as temp_dir:
                output_pdf = os.path.join(temp_dir, "ocr_output.pdf")
                
                # Perform OCR on each page
                for i, image in enumerate(images):
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
                
                return output_path
                
        except Exception as e:
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
