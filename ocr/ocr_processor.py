import pytesseract
from pdf2image import convert_from_path
from PyQt6.QtWidgets import QMessageBox  # Updated import

class OCRProcessor:
    def __init__(self, parent_window=None):
        self.parent_window = parent_window
        # OCR Settings
        self.ocr_language = 'eng'  # Default language
        self.ocr_quality = 2       # 1=Fast, 2=Balanced, 3=Best
        self.ocr_page_range = None # Specific pages to process
        self.ocr_deskew = True     # Auto deskew images
        self.ocr_clean = True      # Clean up images before OCR
        self.ocr_psm = 3           # Page segmentation mode
        self.ocr_oem = 1           # OCR Engine mode (1=LSTM only)
        self.ocr_dpi = 300         # Default DPI
        self.ocr_contrast = 1.0    # Contrast adjustment
        self.ocr_brightness = 1.0  # Brightness adjustment
        self.ocr_threshold = 0     # Binarization threshold (0=auto)

    def perform_ocr(self, pdf_path):
        try:
            if not os.path.exists(pdf_path):
                raise ValueError("PDF file does not exist")
                
            if not pdf_path.lower().endswith('.pdf'):
                raise ValueError("File must be a PDF")

            pages = convert_from_path(pdf_path, dpi=self.get_ocr_dpi())
            total_pages = len(pages)

            if self.ocr_page_range:
                pages = [pages[i] for i in self.ocr_page_range if i < total_pages]
                total_pages = len(pages)

            ocr_text = ""
            for i, page in enumerate(pages):
                if self.parent_window:
                    self.parent_window.show_progress(i + 1, total_pages)
                    self.parent_window.update_status_label(f"Processing page {i+1}/{total_pages}")
                    QApplication.processEvents()

                # Preprocess image
                page = self.preprocess_image(page)
                
                # Get OCR config
                config = self.get_ocr_config()
                
                # Perform OCR
                text = pytesseract.image_to_string(
                    page, 
                    lang=self.ocr_language, 
                    config=config
                )
                ocr_text += f"--- Page {i+1} ---\n{text}\n\n"

            if self.parent_window:
                self.parent_window.show_status_message("OCR completed successfully", 3000)
                self.parent_window.hide_progress()
                
            return ocr_text
        except Exception as e:
            if self.parent_window:
                self.parent_window.show_status_message(f"OCR error: {str(e)}", 5000)
                self.parent_window.hide_progress()
            return ""

    def get_ocr_dpi(self):
        """Get DPI based on quality setting"""
        return {
            1: 200,  # Fast
            2: 300,  # Balanced
            3: 400   # Best
        }.get(self.ocr_quality, self.ocr_dpi)

    def get_ocr_config(self):
        """Generate Tesseract config string based on settings"""
        config = []
        
        # OCR Engine Mode
        config.append(f'--oem {self.ocr_oem}')
        
        # Page Segmentation Mode
        config.append(f'--psm {self.ocr_psm}')
        
        # Image processing options
        if self.ocr_deskew:
            config.append('--deskew 1')
        if self.ocr_clean:
            config.append('--clean 1')
        if self.ocr_threshold > 0:
            config.append(f'--threshold {self.ocr_threshold}')
            
        return ' '.join(config)

    def preprocess_image(self, image):
        """Apply preprocessing to image before OCR"""
        from PIL import ImageEnhance, ImageFilter
        
        # Adjust contrast
        if self.ocr_contrast != 1.0:
            enhancer = ImageEnhance.Contrast(image)
            image = enhancer.enhance(self.ocr_contrast)
            
        # Adjust brightness
        if self.ocr_brightness != 1.0:
            enhancer = ImageEnhance.Brightness(image)
            image = enhancer.enhance(self.ocr_brightness)
            
        # Apply threshold if specified
        if self.ocr_threshold > 0:
            image = image.convert('L').point(
                lambda x: 0 if x < self.ocr_threshold else 255, '1')
            
        return image
