# main.py
import sys
import logging
import os
from PyQt6.QtWidgets import (QApplication, QMainWindow, QMenuBar, QMenu, QVBoxLayout, 
                            QWidget, QTabWidget, QListWidget, QListWidgetItem, QMessageBox,
                            QLineEdit, QLabel, QScrollArea, QGridLayout, QPushButton)
from PyQt6.QtCore import Qt, QMimeData, QPoint
from PyQt6.QtGui import QPixmap, QMouseEvent, QPainter
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
        
        # Calculate new position based on mouse
        pos = self.mapToParent(event.position().toPoint())
        
        # Find the widget under the mouse position
        target_index = -1
        for i in range(layout.count()):
            item = layout.itemAt(i)
            if item and item.geometry().contains(pos):
                target_index = i
                break
                
        # If we found a target position and it's different from current
        if target_index != -1 and target_index != index:
            # Remove all widgets from layout
            widgets = []
            while layout.count():
                item = layout.takeAt(0)
                if item.widget():
                    widgets.append(item.widget())
            
            # Reorder widgets
            widgets.insert(target_index, widgets.pop(index))
            
            # Add widgets back in new order
            for i, widget in enumerate(widgets):
                row = i // 3
                col = i % 3
                layout.addWidget(widget, row, col)
            
            # Update the order of PDF paths
            self.parent.update_pdf_order()

class PDFCombiner(QMainWindow):
    def __init__(self):
        super().__init__()
        
        # Initialize undo stack
        self.undo_stack = []
        self.current_state = []
        
        # Create menu bar first
        self.create_menu_bar()
        
        # Then set up main layout
        self.setCentralWidget(self.create_main_layout())
        
        # Save initial state
        self.save_state()
        
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
            self.push_to_undo_stack('open_files', {'files': files})
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

    def save_state(self):
        """Save current state of PDF files"""
        self.current_state = [widget.pdf_path for i in range(self.thumbnail_layout.count())
                            if hasattr(widget := self.thumbnail_layout.itemAt(i).widget(), 'pdf_path')]
        
    def push_to_undo_stack(self, action_type: str, data: dict):
        """Push an action to the undo stack"""
        self.undo_stack.append({
            'type': action_type,
            'data': data,
            'previous_state': self.current_state.copy()
        })
        self.save_state()

    def undo_action(self):
        """Handle undo action"""
        if not self.undo_stack:
            QMessageBox.information(self, "Undo", "Nothing to undo")
            return
            
        # Get last action
        last_action = self.undo_stack.pop()
        
        # Clear current thumbnails
        while self.thumbnail_layout.count():
            item = self.thumbnail_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()
        
        # Restore previous state
        for pdf_path in last_action['previous_state']:
            self.generate_thumbnail(pdf_path)
        
        # No confirmation message needed
        pass

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

    def perform_ocr(self):
        """Handle OCR operation"""
        from ocr.ocr_processor import OCRProcessor
        from PyQt6.QtWidgets import QInputDialog
        
        # Get selected files from thumbnails
        pdf_paths = [widget.pdf_path for i in range(self.thumbnail_layout.count()) 
                    if hasattr(widget := self.thumbnail_layout.itemAt(i).widget(), 'pdf_path')]
        
        if not pdf_paths:
            QMessageBox.warning(self, "No Files", "Please add PDF files first")
            return
            
        # Get OCR language
        languages = ["eng", "fra", "spa", "deu", "ita"]  # Add more as needed
        language, ok = QInputDialog.getItem(
            self,
            "Select OCR Language",
            "Choose the language for OCR:",
            languages,
            current=0,
            editable=False
        )
        
        if not ok or not language:
            return
            
        # Perform OCR on each file
        processor = OCRProcessor()
        processor.ocr_language = language
        
        for pdf_path in pdf_paths:
            try:
                output_path = pdf_path.replace('.pdf', '_ocr.pdf')
                processor.perform_ocr(pdf_path)
                QMessageBox.information(self, "OCR Complete", f"OCR completed. Output saved to {output_path}")
            except Exception as e:
                QMessageBox.critical(self, "OCR Error", f"Could not perform OCR on {pdf_path}: {str(e)}")

    def edit_metadata(self):
        """Handle metadata editing"""
        from operations.metadata import Metadata
        from PyQt6.QtWidgets import QInputDialog
        
        # Get selected files from thumbnails
        pdf_paths = [widget.pdf_path for i in range(self.thumbnail_layout.count()) 
                    if hasattr(widget := self.thumbnail_layout.itemAt(i).widget(), 'pdf_path')]
        
        if not pdf_paths:
            QMessageBox.warning(self, "No Files", "Please add PDF files first")
            return
            
        # Get metadata fields
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
                
        # Apply metadata to each file
        meta = Metadata()
        for pdf_path in pdf_paths:
            try:
                meta.edit_metadata(pdf_path, metadata)
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Could not edit metadata for {pdf_path}: {str(e)}")

    def encrypt_pdf(self):
        """Handle PDF encryption"""
        from operations.security import Security
        from PyQt6.QtWidgets import QInputDialog
        
        # Get selected files from thumbnails
        pdf_paths = [widget.pdf_path for i in range(self.thumbnail_layout.count()) 
                    if hasattr(widget := self.thumbnail_layout.itemAt(i).widget(), 'pdf_path')]
        
        if not pdf_paths:
            QMessageBox.warning(self, "No Files", "Please add PDF files first")
            return
            
        # Get password
        password, ok = QInputDialog.getText(self, "Encrypt PDF", "Enter password:", echo=QLineEdit.Password)
        if not ok or not password:
            return
            
        # Get confirmation
        confirm_password, ok = QInputDialog.getText(self, "Confirm Password", "Confirm password:", echo=QLineEdit.Password)
        if not ok or password != confirm_password:
            QMessageBox.warning(self, "Error", "Passwords do not match")
            return
            
        # Encrypt each file
        security = Security()
        for pdf_path in pdf_paths:
            try:
                security.encrypt_pdf(pdf_path, password, {})
                QMessageBox.information(self, "Success", f"PDF encrypted successfully: {pdf_path}")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Could not encrypt PDF: {str(e)}")

    def decrypt_pdf(self):
        """Handle PDF decryption"""
        from operations.security import Security
        from PyQt6.QtWidgets import QInputDialog
        
        # Get selected files from thumbnails
        pdf_paths = [widget.pdf_path for i in range(self.thumbnail_layout.count()) 
                    if hasattr(widget := self.thumbnail_layout.itemAt(i).widget(), 'pdf_path')]
        
        if not pdf_paths:
            QMessageBox.warning(self, "No Files", "Please add PDF files first")
            return
            
        # Get password
        password, ok = QInputDialog.getText(self, "Decrypt PDF", "Enter password:", echo=QLineEdit.Password)
        if not ok or not password:
            return
            
        # Decrypt each file
        security = Security()
        for pdf_path in pdf_paths:
            try:
                security.decrypt_pdf(pdf_path, password)
                QMessageBox.information(self, "Success", f"PDF decrypted successfully: {pdf_path}")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Could not decrypt PDF: {str(e)}")

    def redact_pdf(self):
        """Handle PDF redaction"""
        from operations.redaction import Redaction
        from PyQt6.QtWidgets import QInputDialog, QFileDialog
        
        # Get selected files from thumbnails
        pdf_paths = [widget.pdf_path for i in range(self.thumbnail_layout.count()) 
                    if hasattr(widget := self.thumbnail_layout.itemAt(i).widget(), 'pdf_path')]
        
        if not pdf_paths:
            QMessageBox.warning(self, "No Files", "Please add PDF files first")
            return
            
        # Get redaction areas
        redactions = []
        while True:
            # Prompt for page number and rectangle coordinates
            page_num, ok = QInputDialog.getInt(
                self,
                "Redact Page",
                "Enter page number to redact (1-based):",
                min=1
            )
            if not ok:
                break
                
            # Get rectangle coordinates
            rect_str, ok = QInputDialog.getText(
                self,
                "Redact Area",
                "Enter rectangle coordinates (x1,y1,x2,y2):"
            )
            if not ok:
                continue
                
            try:
                x1, y1, x2, y2 = map(float, rect_str.split(','))
                redactions.append((page_num - 1, (x1, y1, x2, y2)))
            except ValueError:
                QMessageBox.warning(self, "Invalid Input", "Please enter coordinates in format: x1,y1,x2,y2")
                continue
                
            # Ask if user wants to add more redactions
            reply = QMessageBox.question(
                self,
                "Add More Redactions",
                "Do you want to add more redactions?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if reply == QMessageBox.StandardButton.No:
                break
                
        if not redactions:
            return
            
        # Apply redactions
        redaction = Redaction()
        for pdf_path in pdf_paths:
            try:
                redaction.redact_pdf(pdf_path, redactions)
                QMessageBox.information(self, "Success", f"PDF redacted successfully: {pdf_path}")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Could not redact PDF: {str(e)}")
        
    def create_menu_bar(self):
        """Create and configure the menu bar"""
        menu_bar = self.menuBar()
        
        # File menu
        file_menu = menu_bar.addMenu("File")
        open_action = file_menu.addAction("Open")
        save_action = file_menu.addAction("Save")
        print_action = file_menu.addAction("Print")
        file_menu.addSeparator()
        exit_action = file_menu.addAction("Exit")
        
        # Connect actions
        open_action.triggered.connect(self.open_files)
        save_action.triggered.connect(self.save_files)
        print_action.triggered.connect(self.print_pdf)
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
        
        # Add Combine button
        self.combine_button = QPushButton("Combine PDFs")
        self.combine_button.clicked.connect(self.combine_pdfs)
        main_layout.addWidget(self.combine_button)
        
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
            container.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
            container.customContextMenuRequested.connect(lambda pos, c=container: self.show_context_menu(c, pos))
            
            # Connect double-click event
            container.mouseDoubleClickEvent = lambda event: self.preview_pdf(pdf_path)
            
            # Create container with thumbnail and filename
            container_layout.setSpacing(5)
            container_layout.setContentsMargins(5, 5, 5, 5)
            
            # Create QLabel with the thumbnail
            label = QLabel()
            pixmap = QPixmap(thumbnail_path)
            label.setPixmap(pixmap.scaled(180, 180, Qt.AspectRatioMode.KeepAspectRatio))
            label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            
            # Add filename label with word wrap
            filename = QLabel(os.path.basename(pdf_path))
            filename.setAlignment(Qt.AlignmentFlag.AlignCenter)
            filename.setWordWrap(True)
            filename.setMaximumWidth(200)
            filename.setStyleSheet("""
                QLabel {
                    font-size: 10px;
                    padding: 2px;
                    background-color: rgba(255, 255, 255, 200);
                    border-radius: 3px;
                }
            """)
            
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

    def show_context_menu(self, container, pos):
        """Show context menu for removing items"""
        from PyQt6.QtWidgets import QMenu
        
        menu = QMenu(self)
        remove_action = menu.addAction("Remove")
        action = menu.exec(container.mapToGlobal(pos))
        
        if action == remove_action:
            self.remove_thumbnail(container)
            
    def remove_thumbnail(self, container):
        """Remove a thumbnail from the layout"""
        if hasattr(container, 'pdf_path'):
            self.push_to_undo_stack('remove_thumbnail', {'file': container.pdf_path})
            
        # Remove the widget from the layout
        self.thumbnail_layout.removeWidget(container)
        container.deleteLater()
        
        # Update the PDF order
        self.update_pdf_order()

    def preview_pdf(self, pdf_path):
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
        
        # Create and show preview dialog
        preview = PDFPreviewDialog(pdf_path, self)
        preview.exec()
        
    def combine_pdfs(self):
        """Handle PDF combining operation"""
        from PyQt6.QtWidgets import QFileDialog
        
        # Get PDF paths from thumbnails
        pdf_paths = [widget.pdf_path for i in range(self.thumbnail_layout.count()) 
                    if hasattr(widget := self.thumbnail_layout.itemAt(i).widget(), 'pdf_path')]
        
        if not pdf_paths:
            QMessageBox.warning(self, "No Files", "Please add PDF files first")
            return
            
        # Get output file path
        output_file, _ = QFileDialog.getSaveFileName(
            self,
            "Save Combined PDF",
            "",
            "PDF Files (*.pdf)"
        )
        
        if not output_file:
            return
            
        try:
            from operations.pdf_operations import PDFOperations
            pdf_ops = PDFOperations()
            pdf_ops.combine_pdfs(pdf_paths, output_file, None)
            QMessageBox.information(self, "Success", "PDFs combined successfully!")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Could not combine PDFs: {str(e)}")

    def print_pdf(self):
        """Handle PDF printing"""
        from PyQt6.QtPrintSupport import QPrintDialog, QPrinter
        from PyQt6.QtWidgets import QFileDialog
        
        # Get selected files from thumbnails
        pdf_paths = [widget.pdf_path for i in range(self.thumbnail_layout.count()) 
                    if hasattr(widget := self.thumbnail_layout.itemAt(i).widget(), 'pdf_path')]
        
        if not pdf_paths:
            QMessageBox.warning(self, "No Files", "Please add PDF files first")
            return
            
        # Create printer
        printer = QPrinter(QPrinter.PrinterMode.HighResolution)
        print_dialog = QPrintDialog(printer, self)
        
        if print_dialog.exec() == QPrintDialog.DialogCode.Accepted:
            try:
                for pdf_path in pdf_paths:
                    # Print each PDF
                    from PyQt6.QtGui import QPdfDocument
                    document = QPdfDocument(self)
                    document.load(pdf_path)
                    
                    for i in range(document.pageCount()):
                        if i > 0:
                            printer.newPage()
                        page = document.render(i, printer.pageRect().size())
                        painter = QPainter()
                        painter.begin(printer)
                        painter.drawImage(0, 0, page)
                        painter.end()
                    
                QMessageBox.information(self, "Success", "PDFs printed successfully!")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Could not print PDF: {str(e)}")

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
