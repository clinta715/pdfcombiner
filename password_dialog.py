from PyQt6.QtWidgets import QDialog, QVBoxLayout, QLineEdit, QPushButton, QHBoxLayout, QLabel, QDialogButtonBox

class PasswordDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Encrypt PDF")
        self.setMinimumWidth(400)

        layout = QVBoxLayout()

        # Password requirements label
        requirements = QLabel(
            "Password must be at least 8 characters with:\n"
            "- One uppercase letter\n"
            "- One lowercase letter\n"
            "- One digit"
        )
        layout.addWidget(requirements)

        # Password input field with real-time validation
        self.password_edit = QLineEdit()
        self.password_edit.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_edit.textChanged.connect(self.validate_password)
        layout.addWidget(self.password_edit)

        # Validation status label
        self.validation_label = QLabel()
        self.validation_label.setStyleSheet("color: red; font-size: 10px;")
        layout.addWidget(self.validation_label)

        # Generate password button
        generate_btn = QPushButton("Generate Password")
        generate_btn.clicked.connect(self.generate_password)
        layout.addWidget(generate_btn)

        # Buttons
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok |
            QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

        self.setLayout(layout)

    def validate_password(self, password):
        """Validate password and update status"""
        from operations.security import Security
        try:
            Security.validate_password(None, password)
            self.validation_label.setText("✓ Password meets requirements")
            self.validation_label.setStyleSheet("color: green; font-size: 10px;")
            return True
        except ValueError as e:
            self.validation_label.setText(str(e))
            self.validation_label.setStyleSheet("color: red; font-size: 10px;")
            return False

    def generate_password(self):
        """Generate and set a random password"""
        from utils.utils import generate_password
        password = generate_password()
        self.password_edit.setText(password)
        self.validate_password(password)

    def get_password(self):
        return self.password_edit.text()
