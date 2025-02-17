from PyPDF2 import PdfWriter, PdfReader
from PyQt6.QtWidgets import QMessageBox

class Security:
    def validate_password(self, password):
        """Validate password strength"""
        if len(password) < 8:
            raise ValueError("Password must be at least 8 characters")
        if not any(c.isupper() for c in password):
            raise ValueError("Password must contain at least one uppercase letter")
        if not any(c.islower() for c in password):
            raise ValueError("Password must contain at least one lowercase letter")
        if not any(c.isdigit() for c in password):
            raise ValueError("Password must contain at least one digit")

    def encrypt_pdf(self, pdf_path, password, permissions):
        try:
            # Validate password first
            self.validate_password(password)
            
            writer = PdfWriter()
            reader = PdfReader(pdf_path)
            writer.append_pages_from_reader(reader)

            # Use different owner password
            writer.encrypt(
                user_password=password,
                owner_password=password + "_owner",  # Different owner password
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
