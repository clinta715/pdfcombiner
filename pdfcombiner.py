import sys
import os
import subprocess
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
from dataclasses import dataclass
from typing import List, Optional
from datetime import datetime

@dataclass
class BatchOperation:
    operation_type: str  # 'combine', 'split', 'watermark', etc.
    files: List[str]
    output_dir: str
    settings: dict  # Operation-specific settings
    status: str = 'pending'
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None

class BatchProcessor:
    def __init__(self):
        self.queue: List[BatchOperation] = []
        self.current_operation: Optional[BatchOperation] = None
        self.progress_dialog = None

    def add_operation(self, operation: BatchOperation):
        self.queue.append(operation)

    def start_processing(self, parent):
        self.progress_dialog = ProgressDialog(parent)
        self.progress_dialog.setWindowTitle("Batch Processing")
        self.progress_dialog.progress_bar.setMaximum(len(self.queue))
        self.progress_dialog.show()
        self.process_next()

    def process_next(self):
        if not self.queue:
            self.progress_dialog.close()
            QMessageBox.information(self.progress_dialog, "Complete", 
                                  "Batch processing completed!")
            return

        self.current_operation = self.queue.pop(0)
        self.current_operation.status = 'processing'
        self.current_operation.start_time = datetime.now()
        
        # Update progress dialog
        self.progress_dialog.label.setText(
            f"Processing {self.current_operation.operation_type} "
            f"({len(self.queue)} remaining)"
        )
        self.progress_dialog.progress_bar.setValue(
            self.progress_dialog.progress_bar.maximum() - len(self.queue)
        )

        # Process based on operation type
        if self.current_operation.operation_type == 'combine':
            self.process_combine()
        elif self.current_operation.operation_type == 'split':
            self.process_split()
        elif self.current_operation.operation_type == 'watermark':
            self.process_watermark()
        # Add more operation types as needed

    def process_combine(self):
        try:
            merger = PdfMerger()
            for pdf in self.current_operation.files:
                merger.append(pdf)
            
            output_path = os.path.join(
                self.current_operation.output_dir,
                f"combined_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
            )
            merger.write(output_path)
            merger.close()
            self.current_operation.status = 'completed'
        except Exception as e:
            self.current_operation.status = f'failed: {str(e)}'
        finally:
            self.current_operation.end_time = datetime.now()
            self.process_next()

    def process_split(self):
        try:
            for pdf in self.current_operation.files:
                reader = PdfReader(pdf)
                for i, page in enumerate(reader.pages):
                    writer = PdfWriter()
                    writer.add_page(page)
                    output_path = os.path.join(
                        self.current_operation.output_dir,
                        f"{os.path.splitext(os.path.basename(pdf))[0]}_page{i+1}.pdf"
                    )
                    with open(output_path, 'wb') as f:
                        writer.write(f)
            self.current_operation.status = 'completed'
        except Exception as e:
            self.current_operation.status = f'failed: {str(e)}'
        finally:
            self.current_operation.end_time = datetime.now()
            self.process_next()

    def process_watermark(self):
        # Implement watermark processing
        pass

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
        
        # Initialize batch processor
        self.batch_processor = BatchProcessor()
        
        # Initialize dark mode state
        self.dark_mode = True
        
        # Create menu bar
        menubar = self.menuBar()
        
        # Add OCR menu
        ocr_menu = menubar.addMenu('OCR')
        
        # Basic OCR action
        ocr_action = QAction('Perform OCR...', self)
        ocr_action.triggered.connect(self.perform_ocr)
        ocr_menu.addAction(ocr_action)
        
        # OCR settings submenu
        ocr_settings_menu = ocr_menu.addMenu('Settings')
        
        # Language selection
        self.ocr_language_action = QAction('Select Language...', self)
        self.ocr_language_action.triggered.connect(self.select_ocr_language)
        ocr_settings_menu.addAction(self.ocr_language_action)
        
        # OCR quality
        self.ocr_quality_menu = ocr_settings_menu.addMenu('Quality')
        self.ocr_quality_group = QActionGroup(self)
        qualities = [
            ('Fast', 1),
            ('Balanced', 2),
            ('Best', 3)
        ]
        for name, level in qualities:
            action = QAction(name, self, checkable=True)
            action.setData(level)
            if level == 2:  # Default to Balanced
                action.setChecked(True)
            action.triggered.connect(self.set_ocr_quality)
            self.ocr_quality_group.addAction(action)
            self.ocr_quality_menu.addAction(action)
        
        # Page range selection
        self.ocr_page_range_action = QAction('Set Page Range...', self)
        self.ocr_page_range_action.triggered.connect(self.set_ocr_page_range)
        ocr_settings_menu.addAction(self.ocr_page_range_action)
        
        # Initialize OCR settings
        self.ocr_language = 'eng'  # Default to English
        self.ocr_quality = 2       # Default to Balanced
        self.ocr_page_range = None # Process all pages by default

        # Add View menu
        view_menu = menubar.addMenu('View')
        dark_mode_action = QAction('Toggle Dark Mode', self)
        dark_mode_action.triggered.connect(self.toggle_dark_mode)
        view_menu.addAction(dark_mode_action)
        
        # Add Security menu
        security_menu = menubar.addMenu('Security')
        
        # Encryption
        self.encrypt_action = QAction('Encrypt PDF', self)
        self.encrypt_action.setCheckable(True)
        self.encrypt_action.triggered.connect(self.toggle_encryption)
        security_menu.addAction(self.encrypt_action)
        
        # Permissions
        self.permissions_action = QAction('Restrict Permissions', self)
        self.permissions_action.setCheckable(True)
        self.permissions_action.setEnabled(False)
        security_menu.addAction(self.permissions_action)
        
        # Digital Signature
        self.sign_action = QAction('Add Digital Signature...', self)
        self.sign_action.triggered.connect(self.add_digital_signature)
        security_menu.addAction(self.sign_action)
        
        # Redaction
        self.redact_action = QAction('Redact Content...', self)
        self.redact_action.triggered.connect(self.redact_content)
        security_menu.addAction(self.redact_action)
        
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
        
        # Add Batch menu
        batch_menu = menubar.addMenu('Batch')
        
        batch_combine_action = QAction('Batch Combine', self)
        batch_combine_action.triggered.connect(self.setup_batch_combine)
        batch_menu.addAction(batch_combine_action)
        
        batch_split_action = QAction('Batch Split', self)
        batch_split_action.triggered.connect(self.setup_batch_split)
        batch_menu.addAction(batch_split_action)
        
        batch_watermark_action = QAction('Batch Watermark', self)
        batch_watermark_action.triggered.connect(self.setup_batch_watermark)
        batch_menu.addAction(batch_watermark_action)
        
        start_batch_action = QAction('Start Batch Processing', self)
        start_batch_action.triggered.connect(self.start_batch_processing)
        batch_menu.addAction(start_batch_action)

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
        
        # Apply theme after UI is fully initialized
        self.apply_theme()

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
        
    def thumbnail_clicked(self, container):
        """Handle thumbnail click events"""
        file_path = container.property("filePath")
        
        # Clear all selections
        self.file_list.clearSelection()
        for i in range(self.thumbnail_layout.count()):
            widget = self.thumbnail_layout.itemAt(i).widget()
            if widget:
                self.highlight_thumbnail(widget, False)
        
        # Select corresponding item in list view
        items = self.file_list.findItems(file_path, Qt.MatchExactly)
        if items:
            items[0].setSelected(True)
            self.highlight_thumbnail(container, True)
            
    def highlight_thumbnail(self, container, selected):
        """Highlight or unhighlight a thumbnail"""
        if selected:
            container.setStyleSheet("""
                QWidget#thumbnailContainer {
                    border: 2px solid #2196F3;
                    background-color: #e3f2fd;
                    border-radius: 5px;
                    padding: 5px;
                }
            """)
        else:
            container.setStyleSheet("""
                QWidget#thumbnailContainer {
                    border: 2px solid transparent;
                    background-color: transparent;
                    padding: 5px;
                }
            """)

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

    def select_ocr_language(self):
        """Select OCR language"""
        languages = pytesseract.get_languages(config='')
        lang, ok = QInputDialog.getItem(self, "Select OCR Language",
                                      "Choose OCR language:", languages, 0, False)
        if ok and lang:
            self.ocr_language = lang

    def set_ocr_quality(self):
        """Set OCR quality level"""
        action = self.ocr_quality_group.checkedAction()
        self.ocr_quality = action.data()

    def set_ocr_page_range(self):
        """Set page range for OCR processing"""
        range_text, ok = QInputDialog.getText(self, "Set OCR Page Range",
            "Enter page range (e.g., 1-3,5,7-9):")
        if ok and range_text:
            try:
                # Parse page range
                pages = []
                for part in range_text.split(','):
                    if '-' in part:
                        start, end = map(int, part.split('-'))
                        pages.extend(range(start-1, end))  # Convert to 0-based
                    else:
                        pages.append(int(part)-1)
                self.ocr_page_range = pages
            except ValueError:
                QMessageBox.warning(self, "Invalid Format", 
                    "Please enter page ranges in format like: 1-3,5,7-9")

    def check_poppler_installed(self):
        """Check if Poppler is installed and in PATH"""
        try:
            from pdf2image import pdfinfo_from_path
            from pdf2image.exceptions import PDFInfoNotInstalledError
            
            # Try to set Poppler path explicitly for macOS Homebrew installation
            poppler_path = "/opt/homebrew/bin"
            if os.path.exists(poppler_path):
                os.environ["PATH"] = poppler_path + os.pathsep + os.environ["PATH"]
            
            # Try to get info from pdfinfo command directly
            result = subprocess.run(["pdfinfo", "-v"], capture_output=True, text=True)
            if result.returncode == 0:
                return True
        except PDFInfoNotInstalledError:
            QMessageBox.critical(self, "Poppler Not Found",
                "Poppler utilities are required for OCR.\n\n"
                "Even though Poppler is installed, the program cannot find it.\n"
                "Please ensure Poppler's bin directory is in your PATH.\n\n"
                "Try running this command in your terminal:\n"
                f"export PATH=$PATH:{poppler_path}\n\n"
                "Then restart the application.")
            return False
        except Exception as e:
            QMessageBox.critical(self, "Poppler Error", 
                f"Error checking Poppler installation: {str(e)}")
            return False

    def perform_ocr(self):
        """Perform OCR on selected PDF with current settings"""
        # First check if Poppler is installed
        if not self.check_poppler_installed():
            QMessageBox.critical(self, "Poppler Required",
                "Poppler utilities are required for OCR.\n\n"
                "To install on macOS:\n"
                "1. Install Homebrew if you haven't: /bin/bash -c \"$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)\"\n"
                "2. Install Poppler: brew install poppler\n"
                "3. Restart the application")
            return
            
        selected_items = self.file_list.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "No Selection", "Please select a PDF file to OCR.")
            return
            
        if len(selected_items) > 1:
            QMessageBox.warning(self, "Multiple Selection", 
                "Please select only one PDF file to OCR.")
            return
            
        pdf_path = selected_items[0].text()
        
        # Create progress dialog
        progress_dialog = ProgressDialog(self)
        progress_dialog.setWindowTitle("Performing OCR")
        
        try:
            # Convert PDF to images
            pages = convert_from_path(pdf_path, dpi=self.get_ocr_dpi())
            total_pages = len(pages)
            
            if self.ocr_page_range:
                pages = [pages[i] for i in self.ocr_page_range if i < total_pages]
                total_pages = len(pages)
            
            progress_dialog.progress_bar.setMaximum(total_pages)
            progress_dialog.show()
            
            # Perform OCR on each page
            ocr_text = ""
            for i, page in enumerate(pages):
                if progress_dialog.wasCanceled():
                    break
                    
                # Set OCR configuration based on quality
                config = self.get_ocr_config()
                
                text = pytesseract.image_to_string(page, lang=self.ocr_language, config=config)
                ocr_text += f"--- Page {i+1} ---\n{text}\n\n"
                
                progress_dialog.progress_bar.setValue(i + 1)
                progress_dialog.label.setText(f"Processing page {i+1} of {total_pages}")
                QApplication.processEvents()
            
            progress_dialog.close()
            
            if not progress_dialog.wasCanceled():
                # Show OCR results in a dialog
                dialog = QDialog(self)
                dialog.setWindowTitle("OCR Results")
                dialog.setMinimumSize(800, 600)
                
                layout = QVBoxLayout()
                
                # Add save button
                button_box = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Close)
                button_box.accepted.connect(lambda: self.save_ocr_results(ocr_text))
                button_box.rejected.connect(dialog.reject)
                
                # Add text editor
                text_edit = QTextEdit()
                text_edit.setPlainText(ocr_text)
                text_edit.setReadOnly(False)
                
                layout.addWidget(text_edit)
                layout.addWidget(button_box)
                
                dialog.setLayout(layout)
                dialog.exec_()
                
        except Exception as e:
            progress_dialog.close()
            QMessageBox.critical(self, "OCR Error", f"Could not perform OCR: {str(e)}")

    def get_ocr_dpi(self):
        """Get DPI setting based on OCR quality"""
        return {
            1: 200,  # Fast
            2: 300,  # Balanced
            3: 400   # Best
        }.get(self.ocr_quality, 300)

    def get_ocr_config(self):
        """Get OCR configuration based on quality"""
        if self.ocr_quality == 1:  # Fast
            return '--oem 1 --psm 3'  # LSTM OCR, auto page segmentation
        elif self.ocr_quality == 3:  # Best
            return '--oem 1 --psm 6'  # LSTM OCR, assume uniform block of text
        else:  # Balanced
            return '--oem 1 --psm 4'  # LSTM OCR, assume single column of text

    def save_ocr_results(self, text):
        """Save OCR results to text file"""
        file_path, _ = QFileDialog.getSaveFileName(self, "Save OCR Results", 
                                                 "", "Text Files (*.txt)")
        if file_path:
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(text)
                QMessageBox.information(self, "Success", "OCR results saved successfully!")
            except Exception as e:
                QMessageBox.critical(self, "Save Error", f"Could not save OCR results: {str(e)}")

    def preview_pdf(self):
        """Show advanced preview of selected PDF"""
        selected_items = self.file_list.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "No Selection", "Please select a PDF file to preview.")
            return
            
        if len(selected_items) > 1:
            QMessageBox.warning(self, "Multiple Selection", "Please select only one PDF file to preview.")
            return
            
        pdf_path = selected_items[0].text()
        
        # Create preview dialog
        self.preview_dialog = QDialog(self)
        self.preview_dialog.setWindowTitle(f"Preview - {pdf_path}")
        self.preview_dialog.setMinimumSize(800, 1000)
        
        # Apply current theme
        if self.dark_mode:
            self.preview_dialog.setStyleSheet("""
                QDialog {
                    background-color: #2d2d2d;
                    color: #ffffff;
                }
                QLabel {
                    color: #ffffff;
                }
                QTextEdit {
                    background-color: #3d3d3d;
                    color: #ffffff;
                }
            """)
        
        layout = QVBoxLayout()
        
        # Create toolbar
        toolbar = QHBoxLayout()
        
        # Navigation controls
        nav_layout = QHBoxLayout()
        
        self.prev_button = QPushButton("◄ Previous")
        self.prev_button.clicked.connect(lambda: self.change_page(-1))
        nav_layout.addWidget(self.prev_button)
        
        self.next_button = QPushButton("Next ►")
        self.next_button.clicked.connect(lambda: self.change_page(1))
        nav_layout.addWidget(self.next_button)
        
        # Page number display
        self.page_label = QLabel()
        nav_layout.addWidget(self.page_label)
        
        # Zoom controls
        zoom_layout = QHBoxLayout()
        self.zoom_out_button = QPushButton("-")
        self.zoom_out_button.clicked.connect(lambda: self.adjust_zoom(-0.1))
        zoom_layout.addWidget(self.zoom_out_button)
        
        self.zoom_in_button = QPushButton("+")
        self.zoom_in_button.clicked.connect(lambda: self.adjust_zoom(0.1))
        zoom_layout.addWidget(self.zoom_in_button)
        
        self.zoom_reset_button = QPushButton("Reset Zoom")
        self.zoom_reset_button.clicked.connect(self.reset_zoom)
        zoom_layout.addWidget(self.zoom_reset_button)
        
        # Rotation controls
        rotate_layout = QHBoxLayout()
        self.rotate_left_button = QPushButton("↺")
        self.rotate_left_button.clicked.connect(lambda: self.rotate_page(-90))
        rotate_layout.addWidget(self.rotate_left_button)
        
        self.rotate_right_button = QPushButton("↻")
        self.rotate_right_button.clicked.connect(lambda: self.rotate_page(90))
        rotate_layout.addWidget(self.rotate_right_button)
        
        # Search controls
        search_layout = QHBoxLayout()
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("Search text...")
        search_layout.addWidget(self.search_edit)
        
        self.search_button = QPushButton("Search")
        self.search_button.clicked.connect(self.search_text)
        search_layout.addWidget(self.search_button)
        
        # Add all controls to toolbar
        toolbar.addLayout(nav_layout)
        toolbar.addStretch()
        toolbar.addLayout(zoom_layout)
        toolbar.addLayout(rotate_layout)
        toolbar.addLayout(search_layout)
        
        layout.addLayout(toolbar)
        
        # Create scroll area for large PDFs
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        
        # Create container for PDF display and annotations
        self.preview_container = QWidget()
        self.preview_layout = QVBoxLayout(self.preview_container)
        
        # PDF document and current page
        self.current_doc = None
        self.current_page = 0
        self.current_zoom = 1.0
        self.current_rotation = 0
        self.search_results = []
        self.current_search_index = -1
        
        try:
            self.current_doc = fitz.open(pdf_path)
            self.total_pages = len(self.current_doc)
            
            # Add text display area
            self.text_display = QTextEdit()
            self.text_display.setReadOnly(True)
            self.text_display.setMaximumHeight(150)
            self.preview_layout.addWidget(self.text_display)
            
            # Add PDF display
            self.update_page_display()
            
            self.scroll_area.setWidget(self.preview_container)
            layout.addWidget(self.scroll_area)
            
            # Add keyboard shortcuts
            prev_shortcut = QShortcut("Left", self.preview_dialog)
            prev_shortcut.activated.connect(lambda: self.change_page(-1))
            next_shortcut = QShortcut("Right", self.preview_dialog)
            next_shortcut.activated.connect(lambda: self.change_page(1))
            zoom_in_shortcut = QShortcut("Ctrl+=", self.preview_dialog)
            zoom_in_shortcut.activated.connect(lambda: self.adjust_zoom(0.1))
            zoom_out_shortcut = QShortcut("Ctrl+-", self.preview_dialog)
            zoom_out_shortcut.activated.connect(lambda: self.adjust_zoom(-0.1))
            search_shortcut = QShortcut("Ctrl+F", self.preview_dialog)
            search_shortcut.activated.connect(self.focus_search)
            
            self.preview_dialog.setLayout(layout)
            self.preview_dialog.exec_()
            
        except Exception as e:
            QMessageBox.critical(self, "Preview Error", f"Could not preview PDF: {str(e)}")
        finally:
            if self.current_doc:
                self.current_doc.close()

    def update_thumbnail_view(self):
        """Update the thumbnail view with current PDF files"""
        # Store current selection
        selected_files = [item.text() for item in self.file_list.selectedItems()]
        
        # Clear existing thumbnails
        while self.thumbnail_layout.count():
            item = self.thumbnail_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
                
        # Restore selection after update
        self.file_list.clearSelection()
        for file_path in selected_files:
            items = self.file_list.findItems(file_path, Qt.MatchExactly)
            if items:
                items[0].setSelected(True)
            
        # Add thumbnails for each PDF
        for pdf_file in self.pdf_files:
            try:
                # Create thumbnail container
                container = QWidget()
                container.setObjectName("thumbnailContainer")
                container.setProperty("filePath", pdf_file)
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
                
                # Make container clickable
                container.mousePressEvent = lambda event, c=container: self.thumbnail_clicked(c)
                
                # Add to thumbnail view
                self.thumbnail_layout.addWidget(container)
                
                # Set initial selection state
                if pdf_file in [item.text() for item in self.file_list.selectedItems()]:
                    self.highlight_thumbnail(container, True)
                
                doc.close()
            except Exception as e:
                print(f"Error generating thumbnail for {pdf_file}: {str(e)}")
                
        # Add stretch to push thumbnails to top
        self.thumbnail_layout.addStretch()

    def update_page_display(self):
        """Update the displayed page with current zoom and rotation"""
        if not self.current_doc:
            return
            
        # Update page label
        self.page_label.setText(f"Page {self.current_page + 1} of {self.total_pages}")
        
        # Enable/disable navigation buttons
        self.prev_button.setEnabled(self.current_page > 0)
        self.next_button.setEnabled(self.current_page < self.total_pages - 1)
        
        # Load and display current page
        page = self.current_doc.load_page(self.current_page)
        
        # Extract text for display
        text = page.get_text("text")
        self.text_display.setPlainText(text)
        
        # Create pixmap with current zoom and rotation
        zoom = 2 * self.current_zoom
        mat = fitz.Matrix(zoom, zoom).prerotate(self.current_rotation)
        pix = page.get_pixmap(matrix=mat)
        
        # Convert to QImage
        img = QImage(pix.samples, pix.width, pix.height, pix.stride, QImage.Format_RGB888)
        pixmap = QPixmap.fromImage(img)
        
        # Create label to display the image
        if hasattr(self, 'page_label_widget'):
            self.preview_layout.removeWidget(self.page_label_widget)
            self.page_label_widget.deleteLater()
            
        self.page_label_widget = QLabel()
        self.page_label_widget.setPixmap(pixmap)
        self.page_label_widget.setAlignment(Qt.AlignCenter)
        self.preview_layout.insertWidget(0, self.page_label_widget)
        
        # Highlight search results if any
        if self.search_results:
            self.highlight_search_results()

    def change_page(self, delta):
        """Change the current page by delta (1 or -1)"""
        new_page = self.current_page + delta
        if 0 <= new_page < self.total_pages:
            self.current_page = new_page
            self.current_rotation = 0  # Reset rotation on page change
            self.update_page_display()
            
    def adjust_zoom(self, factor):
        """Adjust zoom level by factor"""
        self.current_zoom = max(0.5, min(3.0, self.current_zoom + factor))
        self.update_page_display()
        
    def reset_zoom(self):
        """Reset zoom to 1.0"""
        self.current_zoom = 1.0
        self.update_page_display()
        
    def rotate_page(self, degrees):
        """Rotate the current page by degrees"""
        self.current_rotation = (self.current_rotation + degrees) % 360
        self.update_page_display()
        
    def search_text(self):
        """Search for text in the current document"""
        search_term = self.search_edit.text()
        if not search_term:
            return
            
        self.search_results = []
        self.current_search_index = -1
        
        # Search through all pages
        for page_num in range(self.total_pages):
            page = self.current_doc.load_page(page_num)
            text_instances = page.search_for(search_term)
            for inst in text_instances:
                self.search_results.append((page_num, inst))
                
        if self.search_results:
            self.current_search_index = 0
            self.jump_to_search_result()
        else:
            QMessageBox.information(self, "Search", "No matches found.")
            
    def jump_to_search_result(self):
        """Jump to current search result"""
        if not self.search_results or self.current_search_index < 0:
            return
            
        page_num, rect = self.search_results[self.current_search_index]
        self.current_page = page_num
        self.update_page_display()
        
        # Scroll to the search result
        zoom = 2 * self.current_zoom
        mat = fitz.Matrix(zoom, zoom).prerotate(self.current_rotation)
        mapped_rect = rect * mat
        
        # Calculate scroll position
        scroll_x = mapped_rect.x0
        scroll_y = mapped_rect.y0
        self.scroll_area.ensureVisible(scroll_x, scroll_y)
        
    def highlight_search_results(self):
        """Highlight all search results on current page"""
        if not self.search_results:
            return
            
        # Get current page results
        current_page_results = [r for r in self.search_results if r[0] == self.current_page]
        
        # Create highlight annotations
        page = self.current_doc.load_page(self.current_page)
        for _, rect in current_page_results:
            annot = page.add_highlight_annot(rect)
            annot.set_colors(stroke=(1, 1, 0))  # Yellow highlight
            annot.update()
            
        self.update_page_display()
        
    def focus_search(self):
        """Focus the search input field"""
        self.search_edit.setFocus()

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
            
            # Add encryption algorithm selection
            self.encryption_algorithm = QComboBox()
            self.encryption_algorithm.addItems(["AES-256", "AES-128", "RC4-128"])
            self.encryption_layout.addRow("Algorithm:", self.encryption_algorithm)
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
                
            if len(password) < 8:
                QMessageBox.warning(self, "Password Error",
                    "Password must be at least 8 characters.")
                return False
                
            # Check password strength
            if not any(char.isdigit() for char in password):
                QMessageBox.warning(self, "Password Error",
                    "Password must contain at least one number.")
                return False
                
            if not any(char.isupper() for char in password):
                QMessageBox.warning(self, "Password Error",
                    "Password must contain at least one uppercase letter.")
                return False
                
        return True

    def add_digital_signature(self):
        """Add digital signature to selected PDF"""
        selected_items = self.file_list.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "No Selection", "Please select a PDF file to sign.")
            return
            
        if len(selected_items) > 1:
            QMessageBox.warning(self, "Multiple Selection", "Please select only one PDF file to sign.")
            return
            
        pdf_path = selected_items[0].text()
        
        # Create signature dialog
        dialog = QDialog(self)
        dialog.setWindowTitle("Add Digital Signature")
        dialog.setMinimumSize(400, 300)
        
        layout = QFormLayout()
        
        # Certificate file
        cert_edit = QLineEdit()
        cert_button = QPushButton("Browse...")
        def browse_cert():
            cert_file, _ = QFileDialog.getOpenFileName(self, "Select Certificate File",
                                                     "", "Certificate Files (*.pfx *.p12)")
            if cert_file:
                cert_edit.setText(cert_file)
        cert_button.clicked.connect(browse_cert)
        cert_layout = QHBoxLayout()
        cert_layout.addWidget(cert_edit)
        cert_layout.addWidget(cert_button)
        layout.addRow("Certificate File:", cert_layout)
        
        # Certificate password
        cert_password = QLineEdit()
        cert_password.setEchoMode(QLineEdit.Password)
        layout.addRow("Certificate Password:", cert_password)
        
        # Reason
        reason_edit = QLineEdit()
        layout.addRow("Reason:", reason_edit)
        
        # Location
        location_edit = QLineEdit()
        layout.addRow("Location:", location_edit)
        
        # Contact Info
        contact_edit = QLineEdit()
        layout.addRow("Contact Info:", contact_edit)
        
        # Add buttons
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(dialog.accept)
        button_box.rejected.connect(dialog.reject)
        layout.addRow(button_box)
        
        dialog.setLayout(layout)
        
        if dialog.exec_() == QDialog.Accepted:
            try:
                from endesive import pdf
                import hashlib
                
                # Read certificate
                with open(cert_edit.text(), "rb") as f:
                    cert_data = f.read()
                
                # Sign the PDF
                dct = {
                    "sigflags": 3,
                    "contact": contact_edit.text(),
                    "location": location_edit.text(),
                    "signingdate": datetime.now().strftime("%Y%m%d%H%M%S"),
                    "reason": reason_edit.text(),
                }
                
                # Create signed PDF
                data = open(pdf_path, "rb").read()
                hash_algo = hashlib.sha256
                signed_pdf = pdf.cms.sign(data, dct,
                    cert_data, cert_password.text(),
                    "sha256"
                )
                
                # Save signed PDF
                output_path = pdf_path.replace(".pdf", "_signed.pdf")
                with open(output_path, "wb") as f:
                    f.write(signed_pdf)
                    
                QMessageBox.information(self, "Success", f"PDF signed successfully!\nSaved to: {output_path}")
                
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Could not sign PDF: {str(e)}")

    def redact_content(self):
        """Redact sensitive content from PDF"""
        selected_items = self.file_list.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "No Selection", "Please select a PDF file to redact.")
            return
            
        if len(selected_items) > 1:
            QMessageBox.warning(self, "Multiple Selection", "Please select only one PDF file to redact.")
            return
            
        pdf_path = selected_items[0].text()
        
        # Create redaction dialog
        dialog = QDialog(self)
        dialog.setWindowTitle("Redact Content")
        dialog.setMinimumSize(600, 400)
        
        layout = QVBoxLayout()
        
        # Add PDF preview
        self.redact_preview = QScrollArea()
        self.redact_preview.setWidgetResizable(True)
        
        # PDF document and current page
        self.redact_doc = None
        self.redact_page = 0
        
        try:
            self.redact_doc = fitz.open(pdf_path)
            self.redact_total_pages = len(self.redact_doc)
            self.update_redact_preview()
            
            layout.addWidget(self.redact_preview)
            
            # Add redaction controls
            control_layout = QHBoxLayout()
            
            self.redact_prev_button = QPushButton("Previous Page (←)")
            self.redact_prev_button.clicked.connect(lambda: self.change_redact_page(-1))
            control_layout.addWidget(self.redact_prev_button)
            
            self.redact_next_button = QPushButton("Next Page (→)")
            self.redact_next_button.clicked.connect(lambda: self.change_redact_page(1))
            control_layout.addWidget(self.redact_next_button)
            
            self.redact_page_label = QLabel()
            control_layout.addWidget(self.redact_page_label)
            
            layout.addLayout(control_layout)
            
            # Add redaction button
            self.redact_button = QPushButton("Mark Area for Redaction")
            self.redact_button.clicked.connect(self.mark_redaction_area)
            layout.addWidget(self.redact_button)
            
            # Add buttons
            button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
            button_box.accepted.connect(dialog.accept)
            button_box.rejected.connect(dialog.reject)
            layout.addWidget(button_box)
            
            dialog.setLayout(layout)
            
            if dialog.exec_() == QDialog.Accepted:
                try:
                    # Apply redactions
                    output_path = pdf_path.replace(".pdf", "_redacted.pdf")
                    self.redact_doc.save(output_path)
                    QMessageBox.information(self, "Success", f"PDF redacted successfully!\nSaved to: {output_path}")
                except Exception as e:
                    QMessageBox.critical(self, "Error", f"Could not save redacted PDF: {str(e)}")
            else:
                # Clear any redactions if cancelled
                for page in self.redact_doc:
                    page.clean_contents()
                
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Could not open PDF for redaction: {str(e)}")
        finally:
            if self.redact_doc:
                self.redact_doc.close()

    def update_redact_preview(self):
        """Update the redaction preview display"""
        if not self.redact_doc:
            return
            
        # Update page label
        self.redact_page_label.setText(f"Page {self.redact_page + 1} of {self.redact_total_pages}")
        
        # Enable/disable navigation buttons
        self.redact_prev_button.setEnabled(self.redact_page > 0)
        self.redact_next_button.setEnabled(self.redact_page < self.redact_total_pages - 1)
        
        # Load and display current page
        page = self.redact_doc.load_page(self.redact_page)
        zoom = 2  # Zoom factor for better quality
        mat = fitz.Matrix(zoom, zoom)
        pix = page.get_pixmap(matrix=mat)
        
        # Convert to QImage
        img = QImage(pix.samples, pix.width, pix.height, pix.stride, QImage.Format_RGB888)
        pixmap = QPixmap.fromImage(img)
        
        # Create label to display the image
        label = QLabel()
        label.setPixmap(pixmap)
        self.redact_preview.setWidget(label)

    def change_redact_page(self, delta):
        """Change the current redaction page by delta (1 or -1)"""
        new_page = self.redact_page + delta
        if 0 <= new_page < self.redact_total_pages:
            self.redact_page = new_page
            self.update_redact_preview()

    def mark_redaction_area(self):
        """Mark an area on the page for redaction"""
        if not self.redact_doc:
            return
            
        # Get current page
        page = self.redact_doc.load_page(self.redact_page)
        
        # Create redaction annotation
        rect = fitz.Rect(100, 100, 200, 200)  # Example rectangle
        annot = page.add_redact_annot(rect)
        
        # Apply the redaction
        page.apply_redactions()
        
        # Update preview
        self.update_redact_preview()

    def setup_batch_combine(self):
        """Setup batch combine operation"""
        files, _ = QFileDialog.getOpenFileNames(self, "Select PDFs to Combine", 
                                              "", "PDF Files (*.pdf)")
        if not files:
            return
            
        output_dir = QFileDialog.getExistingDirectory(self, "Select Output Directory")
        if not output_dir:
            return
            
        operation = BatchOperation(
            operation_type='combine',
            files=files,
            output_dir=output_dir,
            settings={}  # Add combine-specific settings here
        )
        self.batch_processor.add_operation(operation)
        QMessageBox.information(self, "Added", "Batch combine operation added to queue")

    def setup_batch_split(self):
        """Setup batch split operation"""
        files, _ = QFileDialog.getOpenFileNames(self, "Select PDFs to Split", 
                                              "", "PDF Files (*.pdf)")
        if not files:
            return
            
        output_dir = QFileDialog.getExistingDirectory(self, "Select Output Directory")
        if not output_dir:
            return
            
        operation = BatchOperation(
            operation_type='split',
            files=files,
            output_dir=output_dir,
            settings={}  # Add split-specific settings here
        )
        self.batch_processor.add_operation(operation)
        QMessageBox.information(self, "Added", "Batch split operation added to queue")

    def setup_batch_watermark(self):
        """Setup batch watermark operation"""
        files, _ = QFileDialog.getOpenFileNames(self, "Select PDFs to Watermark", 
                                              "", "PDF Files (*.pdf)")
        if not files:
            return
            
        output_dir = QFileDialog.getExistingDirectory(self, "Select Output Directory")
        if not output_dir:
            return
            
        # Get watermark settings (you can reuse the existing watermark dialog)
        settings = self.get_watermark_settings()
        if not settings:
            return
            
        operation = BatchOperation(
            operation_type='watermark',
            files=files,
            output_dir=output_dir,
            settings=settings
        )
        self.batch_processor.add_operation(operation)
        QMessageBox.information(self, "Added", "Batch watermark operation added to queue")

    def start_batch_processing(self):
        """Start processing all batch operations"""
        if not self.batch_processor.queue:
            QMessageBox.warning(self, "Empty Queue", "No batch operations to process")
            return
            
        self.batch_processor.start_processing(self)

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
    app.setApplicationName("PDFCombiner")
    app.setApplicationDisplayName("PDFCombiner")
    pdf_combiner = PDFCombiner()
    pdf_combiner.show()
    sys.exit(app.exec_())
