# main.py
import sys
import logging
import os
from PyQt6.QtWidgets import (QApplication, QMainWindow, QMenuBar, QMenu, QVBoxLayout, 
                            QWidget, QTabWidget, QListWidget, QListWidgetItem, QMessageBox,
                            QLineEdit, QLabel, QScrollArea, QGridLayout)
from PyQt6.QtCore import Qt, QMimeData
from PyQt6.QtGui import QPixmap
import fitz  # PyMuPDF
import tempfile

class PDFCombiner(QMainWindow):
    def open_files(self):
        """Handle open files action"""
        from PyQt6.QtWidgets import QFileDialog
        files, _ = QFileDialog.getOpenFileNames(
            self,
            "Select PDF Files",
            "",
            "PDF Files (*.pdf)"
        )
        if files:
            for file_path in files:
                self.generate_thumbnail(file_path)

    def save_files(self):
        """Handle save files action"""
        from PyQt6.QtWidgets import QFileDialog
        file, _ = QFileDialog.getSaveFileName(
            self,
            "Save Combined PDF",
            "",
            "PDF Files (*.pdf)"
        )
        if file:
            # TODO: Implement save logic
            pass

    def undo_action(self):
        """Handle undo action"""
        # TODO: Implement undo logic
        pass

    def redo_action(self):
        """Handle redo action"""
        # TODO: Implement redo logic
        pass
        
    def add_watermark(self):
        """Handle watermark operation"""
        from operations.watermark import Watermark
        from PyQt6.QtWidgets import QInputDialog, QColorDialog
        
        if not self.file_list.count():
            QMessageBox.warning(self, "No Files", "Please add PDF files first")
            return
            
        text, ok = QInputDialog.getText(self, "Watermark Text", "Enter watermark text:")
        if not ok or not text:
            return
            
        color = QColorDialog.getColor()
        if not color.isValid():
            return
            
        watermark = Watermark()
        for i in range(self.file_list.count()):
            file_path = self.file_list.item(i).text()
            watermark.add_text_watermark(file_path, text, 48, 0.5, 45, color, "Center")

    def perform_ocr(self):
        """Handle OCR operation"""
        from ocr.ocr_processor import OCRProcessor
        from PyQt6.QtWidgets import QFileDialog
        
        if not self.file_list.count():
            QMessageBox.warning(self, "No Files", "Please add PDF files first")
            return
            
        processor = OCRProcessor()
        for i in range(self.file_list.count()):
            file_path = self.file_list.item(i).text()
            output_path = file_path.replace('.pdf', '_ocr.pdf')
            try:
                processor.perform_ocr(file_path)
                QMessageBox.information(self, "OCR Complete", f"OCR completed. Output saved to {output_path}")
            except Exception as e:
                QMessageBox.critical(self, "OCR Error", str(e))

    def edit_metadata(self):
        """Handle metadata editing"""
        from operations.metadata import Metadata
        from PyQt6.QtWidgets import QInputDialog
        
        if not self.file_list.count():
            QMessageBox.warning(self, "No Files", "Please add PDF files first")
            return
            
        metadata = {
            'Title': '',
            'Author': '',
            'Subject': '',
            'Keywords': '',
            'Creator': 'PDF Combiner'
        }
        
        for field in ['Title', 'Author', 'Subject', 'Keywords']:
            value, ok = QInputDialog.getText(self, f"Enter {field}", f"{field}:")
            if ok:
                metadata[field] = value
                
        meta = Metadata()
        for i in range(self.file_list.count()):
            file_path = self.file_list.item(i).text()
            meta.edit_metadata(file_path, metadata)

    def encrypt_pdf(self):
        """Handle PDF encryption"""
        from operations.security import Security
        from PyQt6.QtWidgets import QInputDialog
        
        if not self.file_list.count():
            QMessageBox.warning(self, "No Files", "Please add PDF files first")
            return
            
        password, ok = QInputDialog.getText(self, "Encrypt PDF", "Enter password:", echo=QLineEdit.Password)
        if not ok or not password:
            return
            
        security = Security()
        for i in range(self.file_list.count()):
            file_path = self.file_list.item(i).text()
            security.encrypt_pdf(file_path, password, permissions={})

    def decrypt_pdf(self):
        """Handle PDF decryption"""
        from operations.security import Security
        from PyQt6.QtWidgets import QInputDialog
        
        if not self.file_list.count():
            QMessageBox.warning(self, "No Files", "Please add PDF files first")
            return
            
        password, ok = QInputDialog.getText(self, "Decrypt PDF", "Enter password:", echo=QLineEdit.Password)
        if not ok or not password:
            return
            
        security = Security()
        for i in range(self.file_list.count()):
            file_path = self.file_list.item(i).text()
            security.decrypt_pdf(file_path, password)

    def redact_pdf(self):
        """Handle PDF redaction"""
        from operations.redaction import Redaction
        from PyQt6.QtWidgets import QInputDialog
        
        if not self.file_list.count():
            QMessageBox.warning(self, "No Files", "Please add PDF files first")
            return
            
        redaction = Redaction()
        for i in range(self.file_list.count()):
            file_path = self.file_list.item(i).text()
            # TODO: Implement redaction UI
            QMessageBox.information(self, "Redaction", "Redaction feature coming soon")
    def generate_thumbnail(self, pdf_path):
        """Generate and display a thumbnail for the PDF"""
        try:
            # Open the PDF and get the first page
            doc = fitz.open(pdf_path)
            page = doc.load_page(0)
            
            # Render the page to an image
            pix = page.get_pixmap(matrix=fitz.Matrix(0.2, 0.2))
            
            # Save to a temporary file
            with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp:
                pix.save(tmp.name)
                thumbnail_path = tmp.name
            
            # Create container widget for thumbnail and filename
            container = QWidget()
            container_layout = QVBoxLayout()
            container.setLayout(container_layout)
            
            # Create QLabel with the thumbnail
            label = QLabel()
            pixmap = QPixmap(thumbnail_path)
            label.setPixmap(pixmap.scaled(200, 200, Qt.AspectRatioMode.KeepAspectRatio))
            label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            
            # Add filename label
            filename = QLabel(os.path.basename(pdf_path))
            filename.setAlignment(Qt.AlignmentFlag.AlignCenter)
            
            # Add widgets to container
            container_layout.addWidget(label)
            container_layout.addWidget(filename)
            
            # Add container to thumbnail layout in a 3-column grid
            item_count = self.thumbnail_layout.count()
            row = item_count // 3
            col = item_count % 3
            self.thumbnail_layout.addWidget(container, row, col)
            
            # Adjust container size
            container.setFixedSize(220, 250)  # Fixed size for consistency
            
            # Store PDF path in container
            container.pdf_path = pdf_path
            
        except Exception as e:
            print(f"Error generating thumbnail: {e}")

    def __init__(self):
        super().__init__()
        
        # Create menu bar first
        self.create_menu_bar()
        
        # Then set up main layout
        self.setCentralWidget(self.create_main_layout())
        
    def create_menu_bar(self):
        """Create and configure the menu bar"""
        menu_bar = self.menuBar()
        
        # File menu
        file_menu = menu_bar.addMenu("File")
        open_action = file_menu.addAction("Open")
        save_action = file_menu.addAction("Save")
        file_menu.addSeparator()
        exit_action = file_menu.addAction("Exit")
        
        # Connect actions
        open_action.triggered.connect(self.open_files)
        save_action.triggered.connect(self.save_files)
        exit_action.triggered.connect(self.close)
        
        # Edit menu
        edit_menu = menu_bar.addMenu("Edit")
        undo_action = edit_menu.addAction("Undo")
        redo_action = edit_menu.addAction("Redo")
        
        # Connect actions
        undo_action.triggered.connect(self.undo_action)
        redo_action.triggered.connect(self.redo_action)
        
        # Operations menu
        operations_menu = menu_bar.addMenu("Operations")
        
        # Watermark
        watermark_action = operations_menu.addAction("Add Watermark")
        watermark_action.triggered.connect(self.add_watermark)
        
        # OCR
        ocr_action = operations_menu.addAction("Perform OCR")
        ocr_action.triggered.connect(self.perform_ocr)
        
        # Metadata
        metadata_action = operations_menu.addAction("Edit Metadata")
        metadata_action.triggered.connect(self.edit_metadata)
        
        # Security
        security_menu = operations_menu.addMenu("Security")
        encrypt_action = security_menu.addAction("Encrypt PDF")
        encrypt_action.triggered.connect(self.encrypt_pdf)
        decrypt_action = security_menu.addAction("Decrypt PDF")
        decrypt_action.triggered.connect(self.decrypt_pdf)
        
        # Redaction
        redaction_action = operations_menu.addAction("Redact PDF")
        redaction_action.triggered.connect(self.redact_pdf)
        
    def create_main_layout(self):
        main_layout = QVBoxLayout()
        
        # Main Thumbnail View
        self.thumbnail_scroll = QScrollArea()
        self.thumbnail_scroll.setWidgetResizable(True)
        self.thumbnail_container = QWidget()
        self.thumbnail_layout = QGridLayout(self.thumbnail_container)
        self.thumbnail_layout.setSpacing(20)  # Add spacing between thumbnails
        self.thumbnail_layout.setContentsMargins(20, 20, 20, 20)  # Add margins
        self.thumbnail_scroll.setWidget(self.thumbnail_container)
        
        main_layout.addWidget(self.thumbnail_scroll)
        
        central_widget = QWidget()
        central_widget.setLayout(main_layout)
        
        return central_widget
    
    def dragEnterEvent(self, event):
        """Handle drag enter event"""
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            event.ignore()
    
    def dropEvent(self, event):
        """Handle drop event"""
        if event.mimeData().hasUrls():
            event.setDropAction(Qt.DropAction.CopyAction)
            event.accept()
            
            # Get the list of dropped files
            for url in event.mimeData().urls():
                file_path = url.toLocalFile()
                if file_path.lower().endswith('.pdf'):
                    # Generate and display thumbnail
                    self.generate_thumbnail(file_path)
        else:
            event.ignore()
            
    def update_thumbnails(self):
        """Update all thumbnails based on current file list order"""
        # Clear existing thumbnails
        while self.thumbnail_layout.count():
            item = self.thumbnail_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()
                
        # Regenerate thumbnails in current order
        for i in range(self.file_list.count()):
            file_path = self.file_list.item(i).text()
            self.generate_thumbnail(file_path)

def main():
    """Main application entry point"""
    app = QApplication(sys.argv)
    
    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Create and show main window
    window = PDFCombiner()
    window.setWindowTitle("PDF Combiner")
    window.resize(800, 600)
    window.show()
    
    # Start application event loop
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
