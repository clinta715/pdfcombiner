# main.py
import sys
import logging
import os
from PyQt6.QtWidgets import (QApplication, QMainWindow, QMenuBar, QMenu, QVBoxLayout, 
                            QWidget, QTabWidget, QListWidget, QListWidgetItem, QMessageBox,
                            QLineEdit, QLabel, QScrollArea, QGridLayout, QPushButton)
from PyQt6.QtCore import Qt, QMimeData, QPoint
from PyQt6.QtGui import QPixmap, QMouseEvent
import fitz  # PyMuPDF
import tempfile

class DraggableThumbnail(QWidget):
    """Custom widget for draggable thumbnails"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.drag_start_position = QPoint()
        self.setStyleSheet("""
            QWidget {
                border: 1px solid #ccc;
                border-radius: 5px;
                padding: 5px;
                background-color: white;
            }
            QWidget:hover {
                border: 1px solid #888;
                background-color: #f0f0f0;
            }
        """)

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            self.drag_start_position = event.position().toPoint()

    def mouseMoveEvent(self, event: QMouseEvent):
        if not (event.buttons() & Qt.MouseButton.LeftButton):
            return
        if (event.position().toPoint() - self.drag_start_position).manhattanLength() < 10:
            return
            
        # Get the current position in the grid
        layout = self.parent.thumbnail_layout
        index = layout.indexOf(self)
        row = index // 3
        col = index % 3
        
        # Remove from current position
        layout.removeWidget(self)
        self.hide()
        
        # Calculate new position based on mouse
        pos = self.mapToParent(event.position().toPoint())
        new_index = layout.count()
        for i in range(layout.count()):
            item = layout.itemAt(i)
            if item and item.geometry().contains(pos):
                new_index = i
                break
                
        # Insert at new position
        layout.insertWidget(new_index, self)
        self.show()
        
        # Update the order of PDF paths
        self.parent.update_pdf_order()

class PDFCombiner(QMainWindow):
    def __init__(self):
        super().__init__()
        
        # Create menu bar first
        self.create_menu_bar()
        
        # Then set up main layout
        self.setCentralWidget(self.create_main_layout())
        
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
            from operations.pdf_operations import PDFOperations
            pdf_ops = PDFOperations()
            try:
                # Get all PDF paths from thumbnails
                pdf_paths = [widget.pdf_path for i in range(self.thumbnail_layout.count()) 
                            if hasattr(widget := self.thumbnail_layout.itemAt(i).widget(), 'pdf_path')]
                
                if not pdf_paths:
                    QMessageBox.warning(self, "No Files", "Please add PDF files first")
                    return
                
                # Combine PDFs
                pdf_ops.combine_pdfs(pdf_paths, file, None)
                QMessageBox.information(self, "Success", "PDFs combined successfully!")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Could not save PDF: {str(e)}")

    def undo_action(self):
        """Handle undo action"""
        QMessageBox.information(self, "Undo", "Undo feature coming soon")

    def redo_action(self):
        """Handle redo action"""
        QMessageBox.information(self, "Redo", "Redo feature coming soon")

    def add_watermark(self):
        """Handle watermark operation"""
        from operations.watermark import Watermark
        from PyQt6.QtWidgets import QInputDialog, QColorDialog
        
        # Get selected files from thumbnails
        pdf_paths = [widget.pdf_path for i in range(self.thumbnail_layout.count()) 
                    if hasattr(widget := self.thumbnail_layout.itemAt(i).widget(), 'pdf_path')]
        
        if not pdf_paths:
            QMessageBox.warning(self, "No Files", "Please add PDF files first")
            return
            
        # Get watermark text
        text, ok = QInputDialog.getText(self, "Watermark Text", "Enter watermark text:")
        if not ok or not text:
            return
            
        # Get color
        color = QColorDialog.getColor()
        if not color.isValid():
            return
            
        # Create and apply watermark
        watermark = Watermark()
        for pdf_path in pdf_paths:
            try:
                watermark.add_text_watermark(
                    pdf_path, 
                    text, 
                    48,  # font size
                    0.5, # opacity
                    45,  # rotation
                    color, 
                    "Center"
                )
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Could not add watermark to {pdf_path}: {str(e)}")
        
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
            
    def update_pdf_order(self):
        """Update the internal list of PDFs based on thumbnail order"""
        pdf_paths = []
        for i in range(self.thumbnail_layout.count()):
            widget = self.thumbnail_layout.itemAt(i).widget()
            if hasattr(widget, 'pdf_path'):
                pdf_paths.append(widget.pdf_path)
        
        # Update any internal lists or data structures here
        # For now, just store the order
        self.pdf_order = pdf_paths

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
