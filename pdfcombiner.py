import sys
import os
from PyQt5.QtWidgets import (QApplication, QWidget, QVBoxLayout, QPushButton, QListWidget, 
                            QFileDialog, QMessageBox, QProgressBar, QDialog, QLabel, QHBoxLayout,
                            QScrollArea, QAction, QCheckBox, QSlider, QMenu, QInputDialog,
                            QFormLayout, QLineEdit, QDialogButtonBox, QMainWindow, QActionGroup,
                            QTabWidget, QGridLayout, QTextEdit, QSpinBox, QDoubleSpinBox, 
                            QComboBox, QColorDialog)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap, QImage
import fitz  # PyMuPDF
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QKeySequence
from PyQt5.QtWidgets import QShortcut
from PyQt5.QtGui import QColor
import pytesseract
from pdf2image import convert_from_path
from PyPDF2 import PdfMerger, PdfReader, PdfWriter

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
        
        # Encryption settings
        self.encryption_layout = QFormLayout()
        
        self.password_edit = QLineEdit()
        self.password_edit.setEchoMode(QLineEdit.Password)
        self.encryption_layout.addRow("Password:", self.password_edit)
        
        self.confirm_password_edit = QLineEdit()
        self.confirm_password_edit.setEchoMode(QLineEdit.Password)
        self.encryption_layout.addRow("Confirm Password:", self.confirm_password_edit)
        
        self.permissions_check = QCheckBox("Restrict Permissions")
        self.encryption_layout.addRow(self.permissions_check)
        
        # Only show encryption fields when needed
        # Create main layout first
        layout = QVBoxLayout()
        
        self.encryption_widget = QWidget()
        self.encryption_widget.setLayout(self.encryption_layout)
        self.encryption_widget.hide()
        layout.insertWidget(1, self.encryption_widget)
        
        
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
        
        

class PDFCombiner(QMainWindow):
    def __init__(self):
        super().__init__()
        self.pdf_files = []
        self.page_ranges = {}  # Store page ranges for each file
        self.initUI()

    def initUI(self):
        self.setWindowTitle('PDF Combiner')
        self.setGeometry(100, 100, 400, 500)
        self.setAcceptDrops(True)
        
        # Initialize dark mode state
        self.dark_mode = False
        
        # Create menu bar
        menubar = self.menuBar()
        
        # Add View menu
        view_menu = menubar.addMenu('View')
        dark_mode_action = QAction('Toggle Dark Mode', self)
        dark_mode_action.triggered.connect(self.toggle_dark_mode)
        view_menu.addAction(dark_mode_action)
        
        # Add Security menu
        security_menu = menubar.addMenu('Security')
        
        self.encrypt_action = QAction('Encrypt PDF', self)
        self.encrypt_action.setCheckable(True)
        self.encrypt_action.triggered.connect(self.toggle_encryption)
        security_menu.addAction(self.encrypt_action)
        
        self.permissions_action = QAction('Restrict Permissions', self)
        self.permissions_action.setCheckable(True)
        self.permissions_action.setEnabled(False)
        security_menu.addAction(self.permissions_action)
        
        # Add Watermark menu
        watermark_menu = menubar.addMenu('Watermark')
        
        # Text watermark
        self.text_watermark_action = QAction('Add Text Watermark...', self)
        self.text_watermark_action.triggered.connect(self.add_text_watermark)
        watermark_menu.addAction(self.text_watermark_action)
        
        # Image watermark
        self.image_watermark_action = QAction('Add Image Watermark...', self)
        self.image_watermark_action.triggered.connect(self.add_image_watermark)
        watermark_menu.addAction(self.image_watermark_action)
        
        # Remove watermark
        self.remove_watermark_action = QAction('Remove Watermark', self)
        self.remove_watermark_action.triggered.connect(self.remove_watermark)
        watermark_menu.addAction(self.remove_watermark_action)
        
        # Add Compression menu
        compression_menu = menubar.addMenu('Compression')
        
        self.compress_action = QAction('Compress PDF', self)
        self.compress_action.setCheckable(True)
        self.compress_action.triggered.connect(self.toggle_compression)
        compression_menu.addAction(self.compress_action)
        
        self.compression_level_menu = compression_menu.addMenu('Compression Level')
        
        levels = [
            ('None', 0),
            ('Low', 1),
            ('Medium', 2),
            ('High', 3)
        ]
        
        self.compression_level_group = QActionGroup(self)
        for name, level in levels:
            action = QAction(name, self, checkable=True)
            action.setData(level)
            if level == 2:  # Default to Medium
                action.setChecked(True)
            action.triggered.connect(self.set_compression_level)
            self.compression_level_group.addAction(action)
            self.compression_level_menu.addAction(action)
        
        # Set up keyboard shortcuts
        self.add_files_shortcut = QShortcut("Ctrl+O", self)
        self.add_files_shortcut.activated.connect(self.add_files)
        self.remove_selected_shortcut = QShortcut("Ctrl+R", self)
        self.remove_selected_shortcut.activated.connect(self.remove_selected)
        self.combine_shortcut = QShortcut("Ctrl+S", self)
        self.combine_shortcut.activated.connect(self.combine_pdfs)

        layout = QVBoxLayout()

        # Create tabbed interface
        self.tabs = QTabWidget()
        
        # List view tab
        self.file_list = QListWidget()
        self.file_list.setStyleSheet("""
            QListWidget {
                background-color: #f0f0f0;
                border: 2px dashed #cccccc;
            }
            QListWidget::item {
                padding: 5px;
                border-bottom: 1px solid #ddd;
            }
            QListWidget::item:hover {
                background-color: #e0e0e0;
            }
            QListWidget::item:selected {
                background-color: #cce8ff;
                color: black;
            }
            QListWidget::item[dragActive=true] {
                background-color: #ffeb3b;
            }
        """)
        self.file_list.setDragDropMode(QListWidget.InternalMove)
        self.file_list.model().rowsMoved.connect(self.update_file_order)
        
        self.file_list.setDropIndicatorShown(True)
        self.file_list.setSelectionMode(QListWidget.SingleSelection)
        
        # Add context menu for page ranges
        self.file_list.setContextMenuPolicy(Qt.CustomContextMenu)
        self.file_list.customContextMenuRequested.connect(self.show_context_menu)
        
        # Thumbnail view tab
        self.thumbnail_view = QScrollArea()
        self.thumbnail_container = QWidget()
        self.thumbnail_layout = QVBoxLayout(self.thumbnail_container)
        self.thumbnail_view.setWidget(self.thumbnail_container)
        self.thumbnail_view.setWidgetResizable(True)
        
        # Connect tab change signal
        self.tabs.currentChanged.connect(self.update_thumbnail_view)
        
        # Add tabs
        self.tabs.addTab(self.file_list, "List View")
        self.tabs.addTab(self.thumbnail_view, "Thumbnail View")
        layout.addWidget(self.tabs)

        # Create button layout
        button_layout = QHBoxLayout()
        
        self.remove_button = QPushButton('Remove Selected')
        self.remove_button.clicked.connect(self.remove_selected)
        button_layout.addWidget(self.remove_button)
        
        self.preview_button = QPushButton('Preview PDF')
        self.preview_button.clicked.connect(self.preview_pdf)
        button_layout.addWidget(self.preview_button)
        
        self.split_button = QPushButton('Split PDF')
        self.split_button.clicked.connect(self.split_pdf)
        button_layout.addWidget(self.split_button)
        
        self.combine_button = QPushButton('Combine PDFs')
        self.combine_button.clicked.connect(self.combine_pdfs)
        button_layout.addWidget(self.combine_button)
        
        layout.addLayout(button_layout)

        central_widget = QWidget()
        central_widget.setLayout(layout)
        self.setCentralWidget(central_widget)

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            # Check if all files are PDFs
            all_pdfs = all(url.toLocalFile().lower().endswith('.pdf') 
                         for url in event.mimeData().urls())
            
            if all_pdfs:
                # Green border for valid PDFs
                if self.dark_mode:
                    self.file_list.setStyleSheet("""
                        QListWidget {
                            background-color: #3d3d3d;
                            border: 2px dashed #4CAF50;
                            color: #ffffff;
                        }
                    """)
                else:
                    self.file_list.setStyleSheet("""
                        QListWidget {
                            background-color: #f0f0f0;
                            border: 2px dashed #4CAF50;
                        }
                        QListWidget::item {
                            padding: 5px;
                            border-bottom: 1px solid #ddd;
                        }
                        QListWidget::item:hover {
                            background-color: #e0e0e0;
                        }
                        QListWidget::item:selected {
                            background-color: #cce8ff;
                            color: black;
                        }
                        QListWidget::item[dragActive=true] {
                            background-color: #ffeb3b;
                        }
                    """)
                event.accept()
            else:
                # Red border for invalid files
                if self.dark_mode:
                    self.file_list.setStyleSheet("""
                        QListWidget {
                            background-color: #3d3d3d;
                            border: 2px dashed #ff4444;
                            color: #ffffff;
                        }
                    """)
                else:
                    self.file_list.setStyleSheet("""
                        QListWidget {
                            background-color: #f0f0f0;
                            border: 2px dashed #ff4444;
                        }
                        QListWidget::item {
                            padding: 5px;
                            border-bottom: 1px solid #ddd;
                        }
                        QListWidget::item:hover {
                            background-color: #e0e0e0;
                        }
                        QListWidget::item:selected {
                            background-color: #cce8ff;
                            color: black;
                        }
                        QListWidget::item[dragActive=true] {
                            background-color: #ffeb3b;
                        }
                    """)
                event.accept()
        else:
            # Blue border for internal reordering
            if self.dark_mode:
                self.file_list.setStyleSheet("""
                    QListWidget {
                        background-color: #3d3d3d;
                        border: 2px dashed #2196F3;
                        color: #ffffff;
                    }
                """)
            else:
                self.file_list.setStyleSheet("""
                    QListWidget {
                        background-color: #f0f0f0;
                        border: 2px dashed #2196F3;
                    }
                    QListWidget::item {
                        padding: 5px;
                        border-bottom: 1px solid #ddd;
                    }
                    QListWidget::item:hover {
                        background-color: #e0e0e0;
                    }
                    QListWidget::item:selected {
                        background-color: #cce8ff;
                        color: black;
                    }
                    QListWidget::item[dragActive=true] {
                        background-color: #ffeb3b;
                    }
                """)
            event.accept()

    def dropEvent(self, event):
        # Reset to default style
        if self.dark_mode:
            self.file_list.setStyleSheet("""
                QListWidget {
                    background-color: #3d3d3d;
                    border: 2px dashed #666666;
                    color: #ffffff;
                }
            """)
        else:
            self.file_list.setStyleSheet("""
                QListWidget {
                    background-color: #f0f0f0;
                    border: 2px dashed #cccccc;
                }
                QListWidget::item {
                    padding: 5px;
                    border-bottom: 1px solid #ddd;
                }
                QListWidget::item:hover {
                    background-color: #e0e0f0;
                }
                QListWidget::item:selected {
                    background-color: #cce8ff;
                    color: black;
                }
                QListWidget::item[dragActive=true] {
                    background-color: #ffeb3b;
                }
            """)
        
        # If dropping files from outside
        if event.mimeData().hasUrls():
            files = [u.toLocalFile() for u in event.mimeData().urls()]
            for f in files:
                if f.lower().endswith('.pdf'):
                    if f not in self.pdf_files:
                        self.pdf_files.append(f)
                        self.file_list.addItem(f)
                        # Initialize page range as "all" for new files
                        self.page_ranges[f] = "all"
                    else:
                        QMessageBox.warning(self, "Duplicate File", f"{f} is already in the list.")
                else:
                    QMessageBox.warning(self, "Invalid File", f"{f} is not a PDF file.")
            
            # Force thumbnail view update
            self.update_thumbnail_view()
            if self.tabs.currentIndex() == 1:  # If on thumbnail view
                self.tabs.setCurrentIndex(0)  # Switch to list view
                self.tabs.setCurrentIndex(1)  # Switch back to thumbnail view

    def update_file_order(self):
        """Update the internal file list when items are reordered"""
        self.pdf_files = []
        for i in range(self.file_list.count()):
            self.pdf_files.append(self.file_list.item(i).text())
        self.update_thumbnail_view()

    def add_files(self):
        """Add files using file dialog"""
        files, _ = QFileDialog.getOpenFileNames(self, "Select PDF Files", "", "PDF Files (*.pdf)")
        if files:
            for f in files:
                if f.lower().endswith('.pdf'):
                    self.pdf_files.append(f)
                    self.file_list.addItem(f)
                    # Initialize page range as "all" for new files
                    self.page_ranges[f] = "all"
            
            # Force thumbnail view update
            self.update_thumbnail_view()
            if self.tabs.currentIndex() == 1:  # If on thumbnail view
                self.tabs.setCurrentIndex(0)  # Switch to list view
                self.tabs.setCurrentIndex(1)  # Switch back to thumbnail view

    def ocr_pdf(self, file_path):
        """Perform OCR on a PDF file"""
        try:
            # Convert PDF to images
            pages = convert_from_path(file_path, dpi=300)
            
            # Perform OCR on each page
            ocr_text = ""
            for i, page in enumerate(pages):
                text = pytesseract.image_to_string(page)
                ocr_text += f"--- Page {i+1} ---\n{text}\n\n"
            
            # Show OCR results in a dialog
            dialog = QDialog(self)
            dialog.setWindowTitle("OCR Results")
            dialog.setMinimumSize(600, 400)
            
            layout = QVBoxLayout()
            text_edit = QTextEdit()
            text_edit.setPlainText(ocr_text)
            text_edit.setReadOnly(True)
            layout.addWidget(text_edit)
            
            button_box = QDialogButtonBox(QDialogButtonBox.Ok)
            button_box.accepted.connect(dialog.accept)
            layout.addWidget(button_box)
            
            dialog.setLayout(layout)
            dialog.exec_()
            
        except Exception as e:
            QMessageBox.critical(self, "OCR Error", f"Could not perform OCR: {str(e)}")

    def preview_pdf(self):
        """Show preview of selected PDF with navigation controls"""
        selected_items = self.file_list.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "No Selection", "Please select a PDF file to preview.")
            return
            
        if len(selected_items) > 1:
            QMessageBox.warning(self, "Multiple Selection", "Please select only one PDF file to preview.")
            return
            
        pdf_path = selected_items[0].text()
        
        # Create preview dialog
        preview_dialog = QDialog(self)
        preview_dialog.setWindowTitle(f"Preview - {pdf_path}")
        preview_dialog.setMinimumSize(600, 800)
        
        # Apply current theme
        if self.dark_mode:
            preview_dialog.setStyleSheet("""
                QDialog {
                    background-color: #2d2d2d;
                    color: #ffffff;
                }
                QLabel {
                    color: #ffffff;
                }
            """)
        
        layout = QVBoxLayout()
        
        # Navigation controls
        nav_layout = QHBoxLayout()
        
        self.prev_button = QPushButton("Previous Page (←)")
        self.prev_button.clicked.connect(lambda: self.change_page(-1))
        nav_layout.addWidget(self.prev_button)
        
        self.next_button = QPushButton("Next Page (→)")
        self.next_button.clicked.connect(lambda: self.change_page(1))
        nav_layout.addWidget(self.next_button)
        
        # Add keyboard shortcuts
        prev_shortcut = QShortcut("Left", preview_dialog)
        prev_shortcut.activated.connect(lambda: self.change_page(-1))
        next_shortcut = QShortcut("Right", preview_dialog)
        next_shortcut.activated.connect(lambda: self.change_page(1))
        
        self.page_label = QLabel()
        nav_layout.addWidget(self.page_label)
        
        layout.addLayout(nav_layout)
        
        # Create scroll area for large PDFs
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        
        # PDF document and current page
        self.current_doc = None
        self.current_page = 0
        
        try:
            self.current_doc = fitz.open(pdf_path)
            self.total_pages = len(self.current_doc)
            self.update_page_display()
            
            layout.addWidget(self.scroll_area)
            preview_dialog.setLayout(layout)
            preview_dialog.exec_()
            
        except Exception as e:
            QMessageBox.critical(self, "Preview Error", f"Could not preview PDF: {str(e)}")
        finally:
            if self.current_doc:
                self.current_doc.close()

    def update_thumbnail_view(self):
        """Update the thumbnail view with current PDF files"""
        # Clear existing thumbnails
        while self.thumbnail_layout.count():
            item = self.thumbnail_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
            
        # Add thumbnails for each PDF
        for pdf_file in self.pdf_files:
            try:
                # Create thumbnail container
                container = QWidget()
                layout = QVBoxLayout(container)
                
                # Add file name label
                file_label = QLabel(os.path.basename(pdf_file))
                file_label.setAlignment(Qt.AlignCenter)
                layout.addWidget(file_label)
                
                # Generate thumbnail from first page
                doc = fitz.open(pdf_file)
                page = doc.load_page(0)
                pix = page.get_pixmap(matrix=fitz.Matrix(0.5, 0.5))
                
                # Convert to QImage
                img = QImage(pix.samples, pix.width, pix.height, pix.stride, QImage.Format_RGB888)
                pixmap = QPixmap.fromImage(img)
                
                # Create thumbnail label
                thumbnail = QLabel()
                thumbnail.setPixmap(pixmap.scaled(200, 200, Qt.KeepAspectRatio))
                thumbnail.setAlignment(Qt.AlignCenter)
                layout.addWidget(thumbnail)
                
                # Add to thumbnail view
                self.thumbnail_layout.addWidget(container)
                
                doc.close()
            except Exception as e:
                print(f"Error generating thumbnail for {pdf_file}: {str(e)}")
                
        # Add stretch to push thumbnails to top
        self.thumbnail_layout.addStretch()

    def update_page_display(self):
        """Update the displayed page and navigation controls"""
        if not self.current_doc:
            return
            
        # Update page label
        self.page_label.setText(f"Page {self.current_page + 1} of {self.total_pages}")
        
        # Enable/disable navigation buttons
        self.prev_button.setEnabled(self.current_page > 0)
        self.next_button.setEnabled(self.current_page < self.total_pages - 1)
        
        # Load and display current page
        page = self.current_doc.load_page(self.current_page)
        zoom = 2  # Zoom factor for better quality
        mat = fitz.Matrix(zoom, zoom)
        pix = page.get_pixmap(matrix=mat)
        
        # Convert to QImage
        img = QImage(pix.samples, pix.width, pix.height, pix.stride, QImage.Format_RGB888)
        pixmap = QPixmap.fromImage(img)
        
        # Create label to display the image
        label = QLabel()
        label.setPixmap(pixmap)
        self.scroll_area.setWidget(label)

    def change_page(self, delta):
        """Change the current page by delta (1 or -1)"""
        new_page = self.current_page + delta
        if 0 <= new_page < self.total_pages:
            self.current_page = new_page
            self.update_page_display()

    def remove_selected(self):
        """Remove selected files using shortcut or button"""
        selected_items = self.file_list.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "No Selection", "Please select files to remove.")
            return
            
        for item in selected_items:
            file_path = item.text()
            self.pdf_files.remove(file_path)
            if file_path in self.page_ranges:
                del self.page_ranges[file_path]
            self.file_list.takeItem(self.file_list.row(item))
        self.update_thumbnail_view()

    def split_pdf(self):
        """Split a selected PDF into individual pages"""
        selected_items = self.file_list.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "No Selection", "Please select a PDF file to split.")
            return
            
        if len(selected_items) > 1:
            QMessageBox.warning(self, "Multiple Selection", "Please select only one PDF file to split.")
            return
            
        pdf_path = selected_items[0].text()
        
        # Ask for output directory
        output_dir = QFileDialog.getExistingDirectory(self, "Select Output Directory")
        if not output_dir:
            return
            
        try:
            reader = PdfReader(pdf_path)
            total_pages = len(reader.pages)
            
            progress_dialog = ProgressDialog(self)
            progress_dialog.setWindowTitle("Splitting PDF")
            progress_dialog.progress_bar.setMaximum(total_pages)
            progress_dialog.show()
            
            for i, page in enumerate(reader.pages):
                if progress_dialog.wasCanceled():
                    break
                    
                writer = PdfWriter()
                writer.add_page(page)
                
                output_path = f"{output_dir}/page_{i+1}.pdf"
                with open(output_path, "wb") as output_pdf:
                    writer.write(output_pdf)
                
                progress_dialog.progress_bar.setValue(i + 1)
                progress_dialog.label.setText(f"Splitting page {i+1} of {total_pages}")
                QApplication.processEvents()
            
            progress_dialog.close()
            
            if not progress_dialog.wasCanceled():
                QMessageBox.information(self, "Success", 
                    f"PDF split successfully into {total_pages} pages in:\n{output_dir}")
                
        except Exception as e:
            QMessageBox.critical(self, "Split Error", f"Could not split PDF: {str(e)}")

    def toggle_dark_mode(self):
        """Toggle between dark and light modes"""
        self.dark_mode = not self.dark_mode
        self.apply_theme()
        
    def apply_theme(self):
        """Apply the current theme (dark/light) to all UI elements"""
        if self.dark_mode:
            dark_style = """
                QWidget {
                    background-color: #2d2d2d;
                    color: #ffffff;
                }
                QListWidget {
                    background-color: #3d3d3d;
                    border: 2px dashed #666666;
                    color: #ffffff;
                }
                QListWidget::item {
                    padding: 5px;
                    border-bottom: 1px solid #555555;
                }
                QListWidget::item:hover {
                    background-color: #4d4d4d;
                }
                QListWidget::item:selected {
                    background-color: #0066cc;
                    color: #ffffff;
                }
                QPushButton {
                    background-color: #444444;
                    color: #ffffff;
                    border: 1px solid #666666;
                    padding: 5px;
                }
                QPushButton:hover {
                    background-color: #555555;
                }
                QPushButton:pressed {
                    background-color: #333333;
                }
                QProgressBar {
                    background-color: #444444;
                    color: #ffffff;
                    border: 1px solid #666666;
                    text-align: center;
                }
                QProgressBar::chunk {
                    background-color: #0066cc;
                }
                QDialog {
                    background-color: #2d2d2d;
                    color: #ffffff;
                }
                QLabel {
                    color: #ffffff;
                }
            """
            self.setStyleSheet(dark_style)
        else:
            # Reset to default light theme
            self.setStyleSheet("")
            
        # Update file list style
        self.update_file_list_style()

    def update_file_list_style(self):
        """Update file list style based on current theme"""
        if self.dark_mode:
            self.file_list.setStyleSheet("""
                QListWidget {
                    background-color: #3d3d3d;
                    border: 2px dashed #666666;
                    color: #ffffff;
                }
                QListWidget::item {
                    padding: 5px;
                    border-bottom: 1px solid #555555;
                }
                QListWidget::item:hover {
                    background-color: #4d4d4d;
                }
                QListWidget::item:selected {
                    background-color: #0066cc;
                    color: #ffffff;
                }
            """)
        else:
            self.file_list.setStyleSheet("""
                QListWidget {
                    background-color: #f0f0f0;
                    border: 2px dashed #cccccc;
                }
                QListWidget::item {
                    padding: 5px;
                    border-bottom: 1px solid #ddd;
                }
                QListWidget::item:hover {
                    background-color: #e0e0e0;
                }
                QListWidget::item:selected {
                    background-color: #cce8ff;
                    color: black;
                }
            """)

    def show_context_menu(self, position):
        """Show context menu for setting page ranges"""
        item = self.file_list.itemAt(position)
        if not item:
            return
            
        file_path = item.text()
        menu = QMenu()
        
        # Add metadata edit action
        metadata_action = QAction("Edit Metadata...", self)
        metadata_action.triggered.connect(lambda: self.edit_metadata(file_path))
        menu.addAction(metadata_action)
        
        # Add page range action
        page_range_action = QAction("Set Page Range...", self)
        page_range_action.triggered.connect(lambda: self.set_page_range(file_path))
        menu.addAction(page_range_action)
        
        # Add rotate page submenu
        rotate_menu = menu.addMenu("Rotate Pages")
        rotate_90 = QAction("Rotate 90° Clockwise", self)
        rotate_90.triggered.connect(lambda: self.rotate_pages(file_path, 90))
        rotate_menu.addAction(rotate_90)
        
        rotate_180 = QAction("Rotate 180°", self)
        rotate_180.triggered.connect(lambda: self.rotate_pages(file_path, 180))
        rotate_menu.addAction(rotate_180)
        
        rotate_270 = QAction("Rotate 90° Counter-Clockwise", self)
        rotate_270.triggered.connect(lambda: self.rotate_pages(file_path, 270))
        rotate_menu.addAction(rotate_270)
        
        menu.exec_(self.file_list.viewport().mapToGlobal(position))
        
    def edit_metadata(self, file_path):
        """Edit PDF metadata"""
        try:
            reader = PdfReader(file_path)
            current_metadata = reader.metadata
            
            # Create dialog
            dialog = QDialog(self)
            dialog.setWindowTitle(f"Edit Metadata - {file_path}")
            dialog.setMinimumSize(400, 300)
            
            layout = QFormLayout()
            
            # Create fields for common metadata
            title_edit = QLineEdit(current_metadata.get('/Title', ''))
            author_edit = QLineEdit(current_metadata.get('/Author', ''))
            subject_edit = QLineEdit(current_metadata.get('/Subject', ''))
            keywords_edit = QLineEdit(current_metadata.get('/Keywords', ''))
            
            layout.addRow("Title:", title_edit)
            layout.addRow("Author:", author_edit)
            layout.addRow("Subject:", subject_edit)
            layout.addRow("Keywords:", keywords_edit)
            
            # Add buttons
            button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
            button_box.accepted.connect(dialog.accept)
            button_box.rejected.connect(dialog.reject)
            layout.addRow(button_box)
            
            dialog.setLayout(layout)
            
            if dialog.exec_() == QDialog.Accepted:
                # Create new metadata
                new_metadata = {
                    '/Title': title_edit.text(),
                    '/Author': author_edit.text(),
                    '/Subject': subject_edit.text(),
                    '/Keywords': keywords_edit.text()
                }
                
                # Write updated PDF
                writer = PdfWriter()
                writer.append_pages_from_reader(reader)
                writer.add_metadata(new_metadata)
                
                # Save to temporary file first
                temp_file = file_path + '.tmp'
                with open(temp_file, 'wb') as f:
                    writer.write(f)
                
                # Replace original file
                import os
                os.replace(temp_file, file_path)
                
                QMessageBox.information(self, "Success", "Metadata updated successfully!")
                
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Could not edit metadata: {str(e)}")
            
    def rotate_pages(self, file_path, degrees):
        """Rotate all pages in a PDF by specified degrees"""
        try:
            reader = PdfReader(file_path)
            writer = PdfWriter()
            
            for page in reader.pages:
                page.rotate(degrees)
                writer.add_page(page)
                
            # Save to temporary file first
            temp_file = file_path + '.tmp'
            with open(temp_file, 'wb') as f:
                writer.write(f)
            
            # Replace original file
            import os
            os.replace(temp_file, file_path)
            
            QMessageBox.information(self, "Success", f"Pages rotated by {degrees}° successfully!")
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Could not rotate pages: {str(e)}")

    def set_page_range(self, file_path):
        """Set page range for a specific file"""
        current_range = self.page_ranges.get(file_path, "all")
        range_text, ok = QInputDialog.getText(self, "Set Page Range",
            f"Enter page range for {file_path} (e.g., 1-3,5,7-9):",
            text=current_range)
            
        if ok and range_text:
            # Validate the page range format
            try:
                # Test parsing the range
                pages = []
                for part in range_text.split(','):
                    if '-' in part:
                        start, end = map(int, part.split('-'))
                        pages.extend(range(start-1, end))
                    else:
                        pages.append(int(part)-1)
                self.page_ranges[file_path] = range_text
            except ValueError:
                QMessageBox.warning(self, "Invalid Format", 
                    "Please enter page ranges in format like: 1-3,5,7-9")
                
    def toggle_encryption(self):
        """Toggle PDF encryption settings"""
        self.encrypt = self.encrypt_action.isChecked()
        self.permissions_action.setEnabled(self.encrypt)
        
        if self.encrypt:
            self.encryption_widget.show()
            self.password_edit.setFocus()
        else:
            self.encryption_widget.hide()
            self.password = None

    def toggle_compression(self):
        """Toggle PDF compression"""
        self.compress = self.compress_action.isChecked()
        
    def set_compression_level(self):
        """Set the compression level from menu selection"""
        action = self.compression_level_group.checkedAction()
        self.compression_level = action.data()

    def add_text_watermark(self):
        """Add text watermark to selected PDF"""
        selected_items = self.file_list.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "No Selection", "Please select a PDF file to watermark.")
            return
            
        if len(selected_items) > 1:
            QMessageBox.warning(self, "Multiple Selection", "Please select only one PDF file to watermark.")
            return
            
        pdf_path = selected_items[0].text()
        
        # Create watermark dialog
        dialog = QDialog(self)
        dialog.setWindowTitle("Add Text Watermark")
        dialog.setMinimumSize(400, 300)
        
        layout = QFormLayout()
        
        # Text input
        text_edit = QLineEdit("Confidential")
        layout.addRow("Watermark Text:", text_edit)
        
        # Font size
        font_size = QSpinBox()
        font_size.setRange(10, 100)
        font_size.setValue(48)
        layout.addRow("Font Size:", font_size)
        
        # Opacity
        opacity = QDoubleSpinBox()
        opacity.setRange(0.1, 1.0)
        opacity.setValue(0.5)
        opacity.setSingleStep(0.1)
        layout.addRow("Opacity:", opacity)
        
        # Rotation
        rotation = QSpinBox()
        rotation.setRange(0, 360)
        rotation.setValue(45)
        layout.addRow("Rotation (degrees):", rotation)
        
        # Color
        color_button = QPushButton("Choose Color")
        color = QColor(0, 0, 0, 128)  # Default to semi-transparent black
        def choose_color():
            nonlocal color
            color = QColorDialog.getColor(color, self)
            if color.isValid():
                color_button.setStyleSheet(f"background-color: {color.name()}")
        color_button.clicked.connect(choose_color)
        layout.addRow("Color:", color_button)
        
        # Position
        position_combo = QComboBox()
        position_combo.addItems(["Center", "Top Left", "Top Right", "Bottom Left", "Bottom Right"])
        layout.addRow("Position:", position_combo)
        
        # Add buttons
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(dialog.accept)
        button_box.rejected.connect(dialog.reject)
        layout.addRow(button_box)
        
        dialog.setLayout(layout)
        
        if dialog.exec_() == QDialog.Accepted:
            try:
                # Apply watermark
                from reportlab.pdfgen import canvas
                from reportlab.lib.pagesizes import A4
                from io import BytesIO
                
                # Create watermark PDF
                packet = BytesIO()
                can = canvas.Canvas(packet, pagesize=A4)
                can.setFont("Helvetica", font_size.value())
                can.setFillColorRGB(color.redF(), color.greenF(), color.blueF(), opacity.value())
                
                # Calculate position
                width, height = A4
                text = text_edit.text()
                text_width = can.stringWidth(text, "Helvetica", font_size.value())
                
                if position_combo.currentText() == "Center":
                    x = (width - text_width) / 2
                    y = height / 2
                elif position_combo.currentText() == "Top Left":
                    x = 50
                    y = height - 50
                elif position_combo.currentText() == "Top Right":
                    x = width - text_width - 50
                    y = height - 50
                elif position_combo.currentText() == "Bottom Left":
                    x = 50
                    y = 50
                elif position_combo.currentText() == "Bottom Right":
                    x = width - text_width - 50
                    y = 50
                
                can.saveState()
                can.translate(x, y)
                can.rotate(rotation.value())
                can.drawString(0, 0, text)
                can.restoreState()
                can.save()
                
                # Merge watermark with original PDF
                watermark_pdf = PdfReader(packet)
                original_pdf = PdfReader(pdf_path)
                output_pdf = PdfWriter()
                
                for i in range(len(original_pdf.pages)):
                    page = original_pdf.pages[i]
                    page.merge_page(watermark_pdf.pages[0])
                    output_pdf.add_page(page)
                
                # Save to temporary file first
                temp_file = pdf_path + '.tmp'
                with open(temp_file, 'wb') as f:
                    output_pdf.write(f)
                
                # Replace original file
                import os
                os.replace(temp_file, pdf_path)
                
                QMessageBox.information(self, "Success", "Text watermark added successfully!")
                
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Could not add watermark: {str(e)}")

    def add_image_watermark(self):
        """Add image watermark to selected PDF"""
        selected_items = self.file_list.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "No Selection", "Please select a PDF file to watermark.")
            return
            
        if len(selected_items) > 1:
            QMessageBox.warning(self, "Multiple Selection", "Please select only one PDF file to watermark.")
            return
            
        pdf_path = selected_items[0].text()
        
        # Get image file
        image_path, _ = QFileDialog.getOpenFileName(self, "Select Watermark Image", 
                                                  "", "Images (*.png *.jpg *.jpeg *.bmp)")
        if not image_path:
            return
            
        # Create watermark dialog
        dialog = QDialog(self)
        dialog.setWindowTitle("Add Image Watermark")
        dialog.setMinimumSize(400, 200)
        
        layout = QFormLayout()
        
        # Opacity
        opacity = QDoubleSpinBox()
        opacity.setRange(0.1, 1.0)
        opacity.setValue(0.5)
        opacity.setSingleStep(0.1)
        layout.addRow("Opacity:", opacity)
        
        # Scale
        scale = QDoubleSpinBox()
        scale.setRange(0.1, 2.0)
        scale.setValue(1.0)
        scale.setSingleStep(0.1)
        layout.addRow("Scale:", scale)
        
        # Position
        position_combo = QComboBox()
        position_combo.addItems(["Center", "Top Left", "Top Right", "Bottom Left", "Bottom Right"])
        layout.addRow("Position:", position_combo)
        
        # Add buttons
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(dialog.accept)
        button_box.rejected.connect(dialog.reject)
        layout.addRow(button_box)
        
        dialog.setLayout(layout)
        
        if dialog.exec_() == QDialog.Accepted:
            try:
                # Apply watermark
                from reportlab.pdfgen import canvas
                from reportlab.lib.pagesizes import A4
                from io import BytesIO
                from PIL import Image
                
                # Create watermark PDF
                packet = BytesIO()
                can = canvas.Canvas(packet, pagesize=A4)
                
                # Open and resize image
                img = Image.open(image_path)
                img_width, img_height = img.size
                img_width *= scale.value()
                img_height *= scale.value()
                
                # Calculate position
                width, height = A4
                
                if position_combo.currentText() == "Center":
                    x = (width - img_width) / 2
                    y = (height - img_height) / 2
                elif position_combo.currentText() == "Top Left":
                    x = 50
                    y = height - img_height - 50
                elif position_combo.currentText() == "Top Right":
                    x = width - img_width - 50
                    y = height - img_height - 50
                elif position_combo.currentText() == "Bottom Left":
                    x = 50
                    y = 50
                elif position_combo.currentText() == "Bottom Right":
                    x = width - img_width - 50
                    y = 50
                
                can.drawImage(image_path, x, y, width=img_width, height=img_height, 
                            mask='auto', preserveAspectRatio=True, opacity=opacity.value())
                can.save()
                
                # Merge watermark with original PDF
                watermark_pdf = PdfReader(packet)
                original_pdf = PdfReader(pdf_path)
                output_pdf = PdfWriter()
                
                for i in range(len(original_pdf.pages)):
                    page = original_pdf.pages[i]
                    page.merge_page(watermark_pdf.pages[0])
                    output_pdf.add_page(page)
                
                # Save to temporary file first
                temp_file = pdf_path + '.tmp'
                with open(temp_file, 'wb') as f:
                    output_pdf.write(f)
                
                # Replace original file
                import os
                os.replace(temp_file, pdf_path)
                
                QMessageBox.information(self, "Success", "Image watermark added successfully!")
                
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Could not add watermark: {str(e)}")

    def validate_encryption(self):
        """Validate encryption settings before processing"""
        if self.encrypt:
            password = self.password_edit.text()
            confirm = self.confirm_password_edit.text()
            
            if not password or password != confirm:
                QMessageBox.warning(self, "Password Error",
                    "Passwords do not match or are empty.")
                return False
                
            if len(password) < 6:
                QMessageBox.warning(self, "Password Error",
                    "Password must be at least 6 characters.")
                return False
                
        return True

    def remove_watermark(self):
        """Remove watermark from selected PDF"""
        selected_items = self.file_list.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "No Selection", "Please select a PDF file to remove watermark.")
            return
            
        if len(selected_items) > 1:
            QMessageBox.warning(self, "Multiple Selection", "Please select only one PDF file to remove watermark.")
            return
            
        pdf_path = selected_items[0].text()
        
        try:
            # Create new PDF without watermark
            reader = PdfReader(pdf_path)
            writer = PdfWriter()
            
            for page in reader.pages:
                # Create new blank page with same size
                new_page = writer.add_blank_page(
                    width=page.mediabox.width,
                    height=page.mediabox.height
                )
                
                # Copy all content except watermark
                new_page.merge_page(page)
                
            # Save to temporary file first
            temp_file = pdf_path + '.tmp'
            with open(temp_file, 'wb') as f:
                writer.write(f)
            
            # Replace original file
            import os
            os.replace(temp_file, pdf_path)
            
            QMessageBox.information(self, "Success", "Watermark removed successfully!")
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Could not remove watermark: {str(e)}")


    def combine_pdfs(self):
        if not self.pdf_files:
            QMessageBox.warning(self, "No Files", "Please add PDF files before combining.")
            return

        output_file, _ = QFileDialog.getSaveFileName(self, "Save Combined PDF", "", "PDF Files (*.pdf)")
        if not output_file:
            return

        progress_dialog = ProgressDialog(self)
        progress_dialog.progress_bar.setMaximum(len(self.pdf_files))
        progress_dialog.show()

        merger = PdfMerger()
        
        for i, pdf in enumerate(self.pdf_files):
            if progress_dialog.wasCanceled():
                merger.close()
                progress_dialog.close()
                QMessageBox.information(self, "Cancelled", "PDF combination was cancelled.")
                return
                
            # Get page range for this file
            page_range = self.page_ranges.get(pdf, "all")
            
            if page_range == "all":
                merger.append(pdf)
            else:
                try:
                    # Parse page range (e.g., "1-3,5,7-9")
                    pages = []
                    for part in page_range.split(','):
                        if '-' in part:
                            start, end = map(int, part.split('-'))
                            pages.extend(range(start-1, end))  # Convert to 0-based
                        else:
                            pages.append(int(part)-1)
                    merger.append(pdf, pages=pages)
                except Exception as e:
                    QMessageBox.warning(self, "Invalid Page Range", 
                        f"Invalid page range for {pdf}: {page_range}\nUsing all pages instead.")
                    merger.append(pdf)
                    
            # Apply compression if enabled
            if progress_dialog.compress:
                writer = PdfWriter()
                writer.append_pages_from_reader(PdfReader(pdf))
                writer.add_metadata(PdfReader(pdf).metadata)
                
                # Set compression level
                if progress_dialog.compression_level == 0:
                    writer.compress_content_streams = False
                else:
                    writer.compress_content_streams = True
                    # Adjust compression based on level (1-3)
                    if progress_dialog.compression_level >= 2:
                        writer.compress_images = True
                    if progress_dialog.compression_level == 3:
                        writer.compress_fonts = True
                
                merger.append(writer)
            
            progress_dialog.progress_bar.setValue(i + 1)
            progress_dialog.label.setText(f"Combining PDF {i+1} of {len(self.pdf_files)}")
            QApplication.processEvents()

        try:
            # Apply encryption if enabled
            if progress_dialog.encrypt:
                password = progress_dialog.password_edit.text()
                
                # Set up encryption with permissions
                permissions = {
                    'print': True,
                    'modify': not progress_dialog.permissions_check.isChecked(),
                    'copy': True,
                    'annotate': True,
                    'forms': True,
                    'extract': True,
                    'assemble': True,
                    'print_highres': True
                }
                
                writer = PdfWriter()
                for pdf in self.pdf_files:
                    writer.append_pages_from_reader(PdfReader(pdf))
                
                writer.encrypt(
                    user_password=password,
                    owner_password=password,
                    permissions=permissions
                )
                
                with open(output_file, "wb") as f:
                    writer.write(f)
            else:
                merger.write(output_file)
                
        except Exception as e:
            QMessageBox.critical(self, "Encryption Error",
                f"Failed to encrypt PDF: {str(e)}")
            return
        merger.close()

        progress_dialog.close()

        QMessageBox.information(self, "Success", "PDFs combined successfully!")
        reply = QMessageBox.question(self, 'Clear List', 
            'Are you sure you want to clear the file list?',
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            
        if reply == QMessageBox.Yes:
            self.pdf_files.clear()
            self.file_list.clear()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    pdf_combiner = PDFCombiner()
    pdf_combiner.show()
    sys.exit(app.exec_())
