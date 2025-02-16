import os
import sys
from PyQt6.QtWidgets import (
    QInputDialog, QDialog,
    QMainWindow, QTabWidget, QListWidget, QVBoxLayout, QWidget, QPushButton,
    QHBoxLayout, QFileDialog, QMessageBox, QScrollArea, QLabel, QApplication,
    QToolBar, QSlider
)
from PyQt6.QtCore import Qt, QMimeData
from PyQt6.QtGui import QDrag, QShortcut, QKeySequence
from PyQt6.QtGui import QPixmap, QImage
import fitz  # PyMuPDF
from ui.progress_dialog import ProgressDialog
from batch.batch_processor import BatchProcessor
from operations.pdf_operations import PDFOperations

class PDFCombiner(QMainWindow):
    def __init__(self):
        super().__init__()
        self.pdf_files: list[str] = []
        self.page_ranges: dict[str, str] = {}
        self.undo_stack: list[tuple[str, list[str]]] = []  # For undo functionality
        self.redo_stack: list[tuple[str, list[str]]] = []  # For redo functionality
        self.initUI()
        self.batch_processor = BatchProcessor()
        self.pdf_operations = PDFOperations()

    def initUI(self) -> None:
        """Initialize the main UI components"""
        self.setWindowTitle('PDF Combiner')
        self.create_main_menu()
        self.setGeometry(100, 100, 800, 600)
        
        # Set up keyboard shortcuts
        self.setup_shortcuts()
        
        # Set up accessibility
        self.setAccessibleName("PDF Combiner Main Window")
        self.setAccessibleDescription("Main window for combining and manipulating PDF files")

        # Initialize UI components
        self.tabs = QTabWidget()
        
        # Create file list with enhanced drag and drop
        self.file_list = QListWidget()
        self.file_list.setSelectionMode(QListWidget.SelectionMode.SingleSelection)
        self.file_list.setDragDropMode(QListWidget.DragDropMode.InternalMove)
        self.file_list.setDropIndicatorShown(True)
        self.file_list.setDragEnabled(True)
        self.file_list.setAcceptDrops(True)
        self.file_list.setDefaultDropAction(Qt.DropAction.MoveAction)

        # Enable drag and drop for the main window
        self.setAcceptDrops(True)

        # Connect drag and drop events
        self.file_list.dragEnterEvent = self.dragEnterEvent
        self.file_list.dragMoveEvent = self.dragMoveEvent
        self.file_list.dropEvent = self.dropEvent

        # Thumbnail View
        self.thumbnail_scroll = QScrollArea()
        self.thumbnail_container = QWidget()
        self.thumbnail_container.setAcceptDrops(True)
        self.thumbnail_layout = QVBoxLayout(self.thumbnail_container)
        self.thumbnail_scroll.setWidget(self.thumbnail_container)
        self.thumbnail_scroll.setWidgetResizable(True)
        
        # Enable drag and drop for thumbnails
        self.thumbnail_container.dragEnterEvent = self.dragEnterEvent
        self.thumbnail_container.dragMoveEvent = self.dragMoveEvent
        self.thumbnail_container.dropEvent = self.thumbnail_drop_event

        # Add tabs
        self.tabs.addTab(self.file_list, "List View")
        self.tabs.addTab(self.thumbnail_scroll, "Thumbnail View")

        # Connect tab change signal to update thumbnail view
        self.tabs.currentChanged.connect(self.update_thumbnail_view)

        # Main layout
        layout = QVBoxLayout()
        layout.addWidget(self.tabs)

        # Button layout
        button_layout = QHBoxLayout()
        self.remove_button = QPushButton('Remove Selected')
        self.remove_button.clicked.connect(self.remove_selected)
        button_layout.addWidget(self.remove_button)

        self.combine_button = QPushButton('Combine PDFs')
        self.combine_button.clicked.connect(self.combine_pdfs)
        button_layout.addWidget(self.combine_button)

        layout.addLayout(button_layout)

        # Set central widget
        central_widget = QWidget()
        central_widget.setLayout(layout)
        self.setCentralWidget(central_widget)

    def dragEnterEvent(self, event):
        """Handle drag enter event to accept PDF files"""
        if event.mimeData().hasUrls():
            # Check if all files are PDFs
            all_pdfs = all(url.toLocalFile().lower().endswith('.pdf') for url in event.mimeData().urls())
            if all_pdfs:
                event.acceptProposedAction()
            else:
                event.ignore()
        else:
            event.ignore()

    def dragMoveEvent(self, event):
        """Handle drag move event to allow dropping"""
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            event.ignore()

    def dropEvent(self, event):
        """Handle drop event to add PDF files to the list or reorder existing ones"""
        if event.source() == self.file_list:
            # Handle internal reordering
            super().dropEvent(event)
            self.update_file_order_from_list()
            event.acceptProposedAction()
            
            # Update the thumbnail view to match the new order
            self.update_thumbnail_view()
        elif event.mimeData().hasUrls():
            # Handle external file drops
            for url in event.mimeData().urls():
                file_path = url.toLocalFile()
                if file_path.lower().endswith('.pdf'):
                    if file_path not in self.pdf_files:
                        self.pdf_files.append(file_path)
                        self.file_list.addItem(file_path)
                        # Initialize page range as "all" for new files
                        self.page_ranges[file_path] = "all"
                    else:
                        QMessageBox.warning(self, "Duplicate File", f"{file_path} is already in the list.")
                else:
                    QMessageBox.warning(self, "Invalid File", f"{file_path} is not a PDF file.")
            event.acceptProposedAction()
            self.update_thumbnail_view()  # Update thumbnail view after adding files
        else:
            event.ignore()

    def update_file_order_from_list(self):
        """Update the internal file list order to match the QListWidget order"""
        new_order = []
        for index in range(self.file_list.count()):
            file_path = self.file_list.item(index).text()
            new_order.append(file_path)
        
        # Only update if order actually changed
        if new_order != self.pdf_files:
            self.pdf_files = new_order
            self.update_thumbnail_view()

    def thumbnail_drop_event(self, event):
        """Handle thumbnail reordering in the thumbnail view"""
        if event.source() == self.thumbnail_container:
            # Get the position of the drop
            pos = event.position().toPoint()
            
            # Find which thumbnail we're dropping over
            target_index = -1
            for i in range(self.thumbnail_layout.count()):
                widget = self.thumbnail_layout.itemAt(i).widget()
                if widget and widget.geometry().contains(pos):
                    # Check if we're dropping above or below the middle of the target
                    if pos.y() < widget.geometry().center().y():
                        target_index = i  # Drop above
                    else:
                        target_index = i + 1  # Drop below
                    break
            
            # If dropping below last item, set target to end
            if target_index == -1:
                target_index = len(self.pdf_files)
            
            # Get the source widget (the one being dragged)
            source_widget = self.thumbnail_container.findChild(QWidget, "draggedWidget")
            if source_widget:
                source_path = source_widget.property("filePath")
                if source_path:
                    # Remove from current position
                    current_index = self.pdf_files.index(source_path)
                    
                    # Adjust target index if moving down in list
                    if target_index > current_index:
                        target_index -= 1
                    
                    # Remove and reinsert at new position
                    self.pdf_files.remove(source_path)
                    self.pdf_files.insert(target_index, source_path)
                    
                    # Update both views
                    self.update_file_order_from_list()
                    self.update_thumbnail_view()
                    
                    # Update list view selection
                    self.file_list.clearSelection()
                    self.file_list.setCurrentRow(target_index)
                    
                    event.acceptProposedAction()
                    return
        
        event.ignore()

    def update_thumbnail_view(self):
        """Update the thumbnail view with previews of the first page of each PDF"""
        # Clear existing thumbnails
        while self.thumbnail_layout.count():
            item = self.thumbnail_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        # Add thumbnails for each PDF
        for pdf_file in self.pdf_files:
            try:
                # Open the PDF and load the first page
                doc = fitz.open(pdf_file)
                page = doc.load_page(0)

                # Render the page as a pixmap
                pix = page.get_pixmap(matrix=fitz.Matrix(0.5, 0.5))  # Scale down for thumbnail
                img = QImage(pix.samples, pix.width, pix.height, pix.stride, QImage.Format.Format_RGB888)
                pixmap = QPixmap.fromImage(img)

                # Create a thumbnail widget
                thumbnail_widget = QWidget()
                thumbnail_widget.setProperty("filePath", pdf_file)  # Store file path for selection
                thumbnail_layout = QVBoxLayout(thumbnail_widget)

                # Add thumbnail image
                thumbnail_label = QLabel()
                thumbnail_label.setPixmap(pixmap.scaled(200, 200, Qt.AspectRatioMode.KeepAspectRatio))
                thumbnail_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                thumbnail_layout.addWidget(thumbnail_label)

                # Add file name
                file_name_label = QLabel(os.path.basename(pdf_file))
                file_name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                thumbnail_layout.addWidget(file_name_label)

                # Make the thumbnail draggable
                thumbnail_widget.setObjectName("draggedWidget")
                thumbnail_widget.mousePressEvent = lambda event, path=pdf_file: self.select_thumbnail(path)
                thumbnail_widget.mouseMoveEvent = self.thumbnail_mouse_move

                # Add to thumbnail layout
                self.thumbnail_layout.addWidget(thumbnail_widget)

                doc.close()
            except Exception as e:
                print(f"Error generating thumbnail for {pdf_file}: {str(e)}")

        # Add stretch to push thumbnails to the top
        self.thumbnail_layout.addStretch()

    def thumbnail_mouse_move(self, event):
        """Handle mouse movement for dragging thumbnails"""
        if event.buttons() == Qt.MouseButton.LeftButton:
            drag = QDrag(self)
            mime_data = QMimeData()
            drag.setMimeData(mime_data)
            drag.exec(Qt.DropAction.MoveAction)

    def select_thumbnail(self, file_path):
        """Handle thumbnail click to select the corresponding file in the list view"""
        # Clear all selections
        self.file_list.clearSelection()

        # Select the corresponding item in the list view
        items = self.file_list.findItems(file_path, Qt.MatchFlag.MatchExactly)
        if items:
            items[0].setSelected(True)

    def remove_selected(self) -> None:
        """Remove selected files from the list"""
        selected_items = self.file_list.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "No Selection", "Please select files to remove.")
            return

        # Save state for undo
        self.save_state("remove")

        try:
            for item in selected_items:
                file_path = item.text()
                self.pdf_files.remove(file_path)
                if file_path in self.page_ranges:
                    del self.page_ranges[file_path]
                self.file_list.takeItem(self.file_list.row(item))

            # Update thumbnail view after removal
            self.update_thumbnail_view()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to remove files: {str(e)}")
            self.undo_last_action()  # Revert if error occurs






    def combine_pdfs(self) -> None:
        """Combine selected PDF files"""
        if not self.pdf_files:
            QMessageBox.warning(self, "No Files", "Please add PDF files before combining.")
            return

        output_file, _ = QFileDialog.getSaveFileName(self, "Save Combined PDF", "", "PDF Files (*.pdf)")
        if not output_file:
            return

        progress_dialog = ProgressDialog(self)
        progress_dialog.progress_bar.setMaximum(len(self.pdf_files))
        progress_dialog.show()

        self.pdf_operations.combine_pdfs(self.pdf_files, output_file, progress_dialog)

        progress_dialog.close()

        QMessageBox.information(self, "Success", "PDFs combined successfully!")
        reply = QMessageBox.question(self, 'Clear List',
            'Are you sure you want to clear the file list?',
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, QMessageBox.StandardButton.No)

        if reply == QMessageBox.StandardButton.Yes:
            self.pdf_files.clear()
            self.file_list.clear()
            self.update_thumbnail_view()  # Clear thumbnail view

    def create_main_menu(self):
        """Create the main application menu"""
        menubar = self.menuBar()
        
        # File Menu
        file_menu = menubar.addMenu('File')
        open_action = file_menu.addAction('Open PDF')
        open_action.triggered.connect(self.open_pdf)
        save_action = file_menu.addAction('Save Combined PDF')
        save_action.triggered.connect(self.combine_pdfs)
        file_menu.addSeparator()
        exit_action = file_menu.addAction('Exit')
        exit_action.triggered.connect(self.close)

        # Edit Menu
        edit_menu = menubar.addMenu('Edit')
        remove_action = edit_menu.addAction('Remove Selected')
        remove_action.triggered.connect(self.remove_selected)
        clear_action = edit_menu.addAction('Clear List')
        clear_action.triggered.connect(self.clear_list)

        # Tools Menu
        tools_menu = menubar.addMenu('Tools')
        split_action = tools_menu.addAction('Split PDF')
        split_action.triggered.connect(self.split_pdf)
        rotate_action = tools_menu.addAction('Rotate Pages')
        rotate_action.triggered.connect(self.rotate_pages)
        compress_action = tools_menu.addAction('Compress PDF')
        compress_action.triggered.connect(self.compress_pdf)
        
        # Add existing functionality to Tools menu
        preview_action = tools_menu.addAction('Preview PDF')
        preview_action.triggered.connect(self.preview_pdf)
        ocr_action = tools_menu.addAction('Perform OCR')
        ocr_action.triggered.connect(self.perform_ocr)
        encrypt_action = tools_menu.addAction('Encrypt PDF')
        encrypt_action.triggered.connect(self.encrypt_pdf)

        # Help Menu
        help_menu = menubar.addMenu('Help')
        about_action = help_menu.addAction('About')
        about_action.triggered.connect(self.show_about)
        docs_action = help_menu.addAction('Documentation')
        docs_action.triggered.connect(self.show_documentation)

    def open_pdf(self):
        """Open individual PDF files"""
        files, _ = QFileDialog.getOpenFileNames(self, "Open PDF Files", "", "PDF Files (*.pdf)")
        if files:
            for file_path in files:
                if file_path not in self.pdf_files:
                    self.pdf_files.append(file_path)
                    self.file_list.addItem(file_path)
                    self.page_ranges[file_path] = "all"
            self.update_thumbnail_view()

    def clear_list(self):
        """Clear the entire file list"""
        reply = QMessageBox.question(self, 'Clear List',
                                   'Are you sure you want to clear the file list?',
                                   QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            self.pdf_files.clear()
            self.file_list.clear()
            self.page_ranges.clear()
            self.update_thumbnail_view()

    def split_pdf(self):
        """Split PDF into individual pages"""
        # TODO: Implement PDF splitting functionality
        QMessageBox.information(self, "Coming Soon", "PDF splitting feature will be available in the next version")

    def rotate_pages(self):
        """Rotate pages in selected PDF(s)"""
        selected_items = self.file_list.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "No Selection", "Please select PDF file(s) to rotate.")
            return
        
        # Get rotation angle from user
        angle, ok = QInputDialog.getItem(self, 'Rotate PDF', 
                                       'Select rotation angle:',
                                       ['90° Clockwise', '90° Counter-Clockwise', '180°'], 
                                       0, False)
        if not ok:
            return
            
        # Map selection to rotation angle
        rotation_map = {
            '90° Clockwise': 270,
            '90° Counter-Clockwise': 90,
            '180°': 180
        }
        rotation_angle = rotation_map.get(angle, 0)
        
        # Create progress dialog
        progress_dialog = ProgressDialog(self)
        progress_dialog.setWindowTitle("Rotating PDFs")
        progress_dialog.progress_bar.setMaximum(len(selected_items))
        progress_dialog.show()
        
        success_count = 0
        failed_files = []
        
        try:
            for i, item in enumerate(selected_items):
                file_path = item.text()
                progress_dialog.set_current_file(os.path.basename(file_path))
                progress_dialog.progress_bar.setValue(i + 1)
                
                try:
                    # Call PDF operations to rotate
                    output_path = self.pdf_operations.rotate_pdf(file_path, rotation_angle)
                    success_count += 1
                    
                    # Update thumbnail if the rotated file is still in the list
                    if file_path in self.pdf_files:
                        self.update_thumbnail_view()
                except Exception as e:
                    failed_files.append((file_path, str(e)))
                    continue
                
                # Process events to keep UI responsive
                QApplication.processEvents()
                
        finally:
            progress_dialog.close()
            
        # Show results summary
        if failed_files:
            error_details = "\n".join(f"{os.path.basename(f[0])}: {f[1]}" for f in failed_files)
            QMessageBox.warning(self, "Rotation Complete", 
                               f"Successfully rotated {success_count} file(s).\n\n"
                               f"Failed to rotate {len(failed_files)} file(s):\n{error_details}")
        else:
            QMessageBox.information(self, "Rotation Complete", 
                                   f"Successfully rotated {success_count} file(s).")

    def compress_pdf(self):
        """Compress PDF file size"""
        # TODO: Implement PDF compression functionality
        QMessageBox.information(self, "Coming Soon", "PDF compression feature will be available in the next version")

    def show_about(self):
        """Show about dialog"""
        QMessageBox.about(self, "About PDFCombiner", 
                         "PDFCombiner\nVersion 1.0\n\nA comprehensive PDF management tool")

    def show_documentation(self):
        """Show documentation"""
        QMessageBox.information(self, "Documentation", 
                              "Documentation is available at:\nhttps://github.com/your-repo/pdfcombiner")

    def preview_pdf(self):
        """Preview the selected PDF file"""
        selected_items = self.file_list.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "No Selection", "Please select a PDF file to preview.")
            return
        
        file_path = selected_items[0].text()
        try:
            self.preview_window = PreviewWindow(file_path)
            self.preview_window.show()
        except Exception as e:
            QMessageBox.critical(self, "Preview Error", f"Could not preview PDF: {str(e)}")

class PreviewWindow(QDialog):
    """Internal PDF preview window"""
    def __init__(self, file_path: str):
        super().__init__()
        self.file_path = file_path
        self.current_page = 0
        self.zoom_level = 1.0
        self.initUI()
        self.load_pdf()

    def initUI(self):
        """Initialize the preview UI"""
        self.setWindowTitle(f"Preview - {os.path.basename(self.file_path)}")
        self.setMinimumSize(800, 600)
        
        # Main layout
        main_layout = QVBoxLayout()
        self.setLayout(main_layout)
        
        # Toolbar
        toolbar = QToolBar()
        main_layout.addWidget(toolbar)
        
        # Navigation buttons
        self.prev_button = QPushButton("Previous")
        self.prev_button.clicked.connect(self.prev_page)
        toolbar.addWidget(self.prev_button)
        
        self.next_button = QPushButton("Next")
        self.next_button.clicked.connect(self.next_page)
        toolbar.addWidget(self.next_button)
        
        # Page number display
        self.page_label = QLabel()
        toolbar.addWidget(self.page_label)
        
        # Zoom controls
        toolbar.addSeparator()
        self.zoom_out_button = QPushButton("-")
        self.zoom_out_button.clicked.connect(self.zoom_out)
        toolbar.addWidget(self.zoom_out_button)
        
        self.zoom_slider = QSlider(Qt.Orientation.Horizontal)
        self.zoom_slider.setMinimum(50)
        self.zoom_slider.setMaximum(200)
        self.zoom_slider.setValue(100)
        self.zoom_slider.valueChanged.connect(self.zoom_changed)
        toolbar.addWidget(self.zoom_slider)
        
        self.zoom_in_button = QPushButton("+")
        self.zoom_in_button.clicked.connect(self.zoom_in)
        toolbar.addWidget(self.zoom_in_button)
        
        # Image display
        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(self.image_label)
        
        # Load first page
        self.update_page()

    def load_pdf(self):
        """Load the PDF document"""
        self.doc = fitz.open(self.file_path)
        self.page_count = len(self.doc)
        self.update_page_controls()

    def update_page_controls(self):
        """Update navigation controls based on current page"""
        self.prev_button.setEnabled(self.current_page > 0)
        self.next_button.setEnabled(self.current_page < self.page_count - 1)
        self.page_label.setText(f"Page {self.current_page + 1} of {self.page_count}")

    def update_page(self):
        """Render and display the current page"""
        page = self.doc.load_page(self.current_page)
        zoom_matrix = fitz.Matrix(self.zoom_level, self.zoom_level)
        pix = page.get_pixmap(matrix=zoom_matrix)
        
        # Convert to QImage
        img = QImage(pix.samples, pix.width, pix.height, pix.stride, QImage.Format.Format_RGB888)
        self.image_label.setPixmap(QPixmap.fromImage(img))
        self.update_page_controls()

    def prev_page(self):
        """Go to previous page"""
        if self.current_page > 0:
            self.current_page -= 1
            self.update_page()

    def next_page(self):
        """Go to next page"""
        if self.current_page < self.page_count - 1:
            self.current_page += 1
            self.update_page()

    def zoom_in(self):
        """Zoom in"""
        self.zoom_level = min(2.0, self.zoom_level + 0.1)
        self.zoom_slider.setValue(int(self.zoom_level * 100))
        self.update_page()

    def zoom_out(self):
        """Zoom out"""
        self.zoom_level = max(0.5, self.zoom_level - 0.1)
        self.zoom_slider.setValue(int(self.zoom_level * 100))
        self.update_page()

    def zoom_changed(self, value):
        """Handle zoom slider change"""
        self.zoom_level = value / 100.0
        self.update_page()

    def perform_ocr(self):
        """Perform OCR on the selected PDF"""
        selected_items = self.file_list.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "No Selection", "Please select a PDF file to perform OCR.")
            return
        
        file_path = selected_items[0].text()
        try:
            # Call the existing OCR functionality
            output_path = self.pdf_operations.perform_ocr(file_path)
            QMessageBox.information(self, "OCR Complete", f"OCR completed successfully!\nOutput saved to: {output_path}")
        except Exception as e:
            QMessageBox.critical(self, "OCR Error", f"Error performing OCR: {str(e)}")

    def encrypt_pdf(self):
        """Encrypt the selected PDF with a password"""
        selected_items = self.file_list.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "No Selection", "Please select a PDF file to encrypt.")
            return
        
        file_path = selected_items[0].text()
        password, ok = QInputDialog.getText(self, 'Encrypt PDF', 'Enter password:')
        if ok and password:
            try:
                # Call the existing encryption functionality
                output_path = self.pdf_operations.encrypt_pdf(file_path, password)
                QMessageBox.information(self, "Encryption Complete", f"PDF encrypted successfully!\nOutput saved to: {output_path}")
            except Exception as e:
                QMessageBox.critical(self, "Encryption Error", f"Error encrypting PDF: {str(e)}")

    def setup_shortcuts(self) -> None:
        """Set up keyboard shortcuts for common actions"""
        # File operations
        QShortcut(QKeySequence("Ctrl+O"), self, self.open_pdf)
        QShortcut(QKeySequence("Ctrl+S"), self, self.combine_pdfs)
        QShortcut(QKeySequence("Ctrl+Q"), self, self.close)
        
        # Edit operations
        QShortcut(QKeySequence("Ctrl+Z"), self, self.undo_last_action)
        QShortcut(QKeySequence("Ctrl+Shift+Z"), self, self.redo_last_action)
        QShortcut(QKeySequence("Del"), self, self.remove_selected)
        QShortcut(QKeySequence("Ctrl+D"), self, self.clear_list)

    def save_state(self, action: str) -> None:
        """Save current state for undo/redo functionality"""
        self.undo_stack.append((action, self.pdf_files.copy()))
        self.redo_stack.clear()  # Clear redo stack when new action is performed

    def undo_last_action(self) -> None:
        """Undo the last action"""
        if self.undo_stack:
            action, state = self.undo_stack.pop()
            self.redo_stack.append((action, self.pdf_files.copy()))
            self.pdf_files = state
            self.update_file_list()
            self.update_thumbnail_view()

    def redo_last_action(self) -> None:
        """Redo the last undone action"""
        if self.redo_stack:
            action, state = self.redo_stack.pop()
            self.undo_stack.append((action, self.pdf_files.copy()))
            self.pdf_files = state
            self.update_file_list()
            self.update_thumbnail_view()

    def update_file_list(self) -> None:
        """Update the file list widget to match the internal state"""
        self.file_list.clear()
        self.file_list.addItems(self.pdf_files)

