from PyQt6.QtWidgets import QDialog, QVBoxLayout, QLabel, QProgressBar, QPushButton, QHBoxLayout

class ProgressDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Combining PDFs")
        self.setFixedSize(300, 150)
        self.canceled = False
        self.compress = False
        self.compression_level = 2  # Default compression level (0-3)
        self.encrypt = False
        self.password = None
        self.restrict_permissions = False

        layout = QVBoxLayout()

        self.label = QLabel("Combining PDFs...")
        layout.addWidget(self.label)
        self.progress_bar = QProgressBar()
        layout.addWidget(self.progress_bar)

        button_layout = QHBoxLayout()
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.cancel)
        button_layout.addStretch()
        button_layout.addWidget(self.cancel_button)

        layout.addLayout(button_layout)
        self.setLayout(layout)

    def cancel(self):
        self.canceled = True

    def wasCanceled(self):
        return self.canceled
