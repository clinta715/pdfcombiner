import pytesseract
from pdf2image import convert_from_path
from PyQt6.QtWidgets import QMessageBox  # Updated import

class OCRProcessor:
    def __init__(self):
        self.ocr_language = 'eng'
        self.ocr_quality = 2
        self.ocr_page_range = None

    def perform_ocr(self, pdf_path):
        try:
            pages = convert_from_path(pdf_path, dpi=self.get_ocr_dpi())
            total_pages = len(pages)

            if self.ocr_page_range:
                pages = [pages[i] for i in self.ocr_page_range if i < total_pages]
                total_pages = len(pages)

            ocr_text = ""
            for i, page in enumerate(pages):
                config = self.get_ocr_config()
                text = pytesseract.image_to_string(page, lang=self.ocr_language, config=config)
                ocr_text += f"--- Page {i+1} ---\n{text}\n\n"

            return ocr_text
        except Exception as e:
            QMessageBox.critical(None, "OCR Error", f"Could not perform OCR: {str(e)}")
            return ""

    def get_ocr_dpi(self):
        return {
            1: 200,  # Fast
            2: 300,  # Balanced
            3: 400   # Best
        }.get(self.ocr_quality, 300)

    def get_ocr_config(self):
        if self.ocr_quality == 1:  # Fast
            return '--oem 1 --psm 3'  # LSTM OCR, auto page segmentation
        elif self.ocr_quality == 3:  # Best
            return '--oem 1 --psm 6'  # LSTM OCR, assume uniform block of text
        else:  # Balanced
            return '--oem 1 --psm 4'  # LSTM OCR, assume single column of text
