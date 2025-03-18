"""Preview PDF in a separate window"""
from PyQt6.QtWidgets import QDialog, QVBoxLayout, QScrollArea
from PyQt6.QtGui import QPixmap
from PyQt6.QtCore import Qt
import fitz

class PDFPreviewDialog(QDialog):
    def __init__(self, pdf_path, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"Preview - {os.path.basename(pdf_path)}")
        self.setMinimumSize(800, 600)

        layout = QVBoxLayout()
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        layout.addWidget(self.scroll)

        # Create container for pages
        self.pages_container = QWidget()
        self.pages_layout = QVBoxLayout()
        self.pages_container.setLayout(self.pages_layout)
        self.scroll.setWidget(self.pages_container)

        self.setLayout(layout)
        self.load_pdf(pdf_path)

    def load_pdf(self, pdf_path):
        """Load and display PDF pages"""
        try:
            doc = fitz.open(pdf_path)
            for page_num in range(len(doc)):
                page = doc.load_page(page_num)
                pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))  # Higher resolution for preview

                # Create QLabel for the page
                label = QLabel()
                pixmap = QPixmap()
                pixmap.loadFromData(pix.tobytes())
                label.setPixmap(pixmap)
                label.setAlignment(Qt.AlignmentFlag.AlignCenter)

                # Add page number label
                page_label = QLabel(f"Page {page_num + 1}")
                page_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

                # Add to layout
                self.pages_layout.addWidget(page_label)
                self.pages_layout.addWidget(label)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Could not load PDF: {str(e)}")
