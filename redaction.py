import fitz
from PyQt6.QtWidgets import QMessageBox

class Redaction:
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

            # Updated to PyQt6 style
            msg = QMessageBox()
            msg.setWindowTitle("Success")
            msg.setText("PDF redacted successfully!")
            msg.setIcon(QMessageBox.Icon.Information)
            msg.exec()
        except Exception as e:
            # Updated to PyQt6 style
            msg = QMessageBox()
            msg.setWindowTitle("Error")
            msg.setText(f"Could not redact PDF: {str(e)}")
            msg.setIcon(QMessageBox.Icon.Critical)
            msg.exec()
