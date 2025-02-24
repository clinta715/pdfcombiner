import fitz
from PyQt6.QtWidgets import QMessageBox

class Redaction:
    def __init__(self, parent_window=None):
        self.parent_window = parent_window
    def redact_pdf(self, pdf_path, redactions):
        try:
            doc = fitz.open(pdf_path)
            for page_num, rect in redactions:
                page = doc.load_page(page_num)
                page.add_redact_annot(rect)
                page.apply_redactions()

            temp_file = pdf_path + '.tmp'
            doc.save(temp_file)
            doc.close()

            import os
            os.replace(temp_file, pdf_path)

            self.parent_window.show_status_message("PDF redacted successfully!", 3000)
        except Exception as e:
            self.parent_window.show_status_message(f"Redaction error: {str(e)}", 5000)
