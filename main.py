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

class PDFCombiner(QMainWindow):
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
            
            # Create draggable container widget for thumbnail and filename
            container = DraggableThumbnail(self)
            container_layout = QVBoxLayout()
            container.setLayout(container_layout)
            container.setAcceptDrops(True)
            
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
