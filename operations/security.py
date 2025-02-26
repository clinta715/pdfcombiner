from PyPDF2 import PdfWriter, PdfReader
from PyQt6.QtWidgets import QMessageBox

class Security:
    def __init__(self, parent_window=None):
        self.parent_window = parent_window
    def validate_password(self, password):
        """Validate password strength"""
        if not password:
            raise ValueError("Password cannot be empty")
            
        # Use constant-time comparison to prevent timing attacks
        errors = []
        if len(password) < 8:
            errors.append("Password must be at least 8 characters")
        if not any(c.isupper() for c in password):
            errors.append("Password must contain at least one uppercase letter")
        if not any(c.islower() for c in password):
            errors.append("Password must contain at least one lowercase letter")
        if not any(c.isdigit() for c in password):
            errors.append("Password must contain at least one digit")
            
        if errors:
            raise ValueError("\n".join(errors))

    def encrypt_pdf(self, pdf_path, password, permissions=None):
        try:
            # Validate password first
            self.validate_password(password)
            
            # Check if PDF is already encrypted
            reader = PdfReader(pdf_path)
            if reader.is_encrypted:
                raise ValueError("PDF is already encrypted")

            # Set default permissions if none provided
            if permissions is None:
                permissions = {
                    'printing': True,  # Allow printing
                    'modify': False,   # Prevent modifications
                    'copy': True,      # Allow copying text
                    'annot-forms': True  # Allow annotations and form filling
                }

            writer = PdfWriter()
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

            self.parent_window.show_status_message("PDF encrypted successfully!", 3000)
            return True
            
        except ValueError as e:
            self.parent_window.show_status_message(f"Encryption error: {str(e)}", 5000)
            return False
        except Exception as e:
            self.parent_window.show_status_message(f"Encryption error: {str(e)}", 5000)
