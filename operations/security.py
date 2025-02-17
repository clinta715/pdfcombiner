from PyPDF2 import PdfWriter, PdfReader
from PyQt6.QtWidgets import QMessageBox

class Security:
    def encrypt_pdf(self, pdf_path, password, permissions):
        try:
            writer = PdfWriter()
            reader = PdfReader(pdf_path)
            writer.append_pages_from_reader(reader)

            writer.encrypt(
                user_password=password,
                owner_password=password,
                permissions=permissions
            )

            temp_file = pdf_path + '.tmp'
            with open(temp_file, 'wb') as f:
                writer.write(f)

            import os
            os.replace(temp_file, pdf_path)

            # Updated to PyQt6 style
            msg = QMessageBox()
            msg.setWindowTitle("Success")
            msg.setText("PDF encrypted successfully!")
            msg.setIcon(QMessageBox.Icon.Information)
            msg.exec()
        except Exception as e:
            # Updated to PyQt6 style
            msg = QMessageBox()
            msg.setWindowTitle("Error")
            msg.setText(f"Could not encrypt PDF: {str(e)}")
            msg.setIcon(QMessageBox.Icon.Critical)
            msg.exec()
