import os
from PyQt6.QtWidgets import (
    QMainWindow, QTabWidget, QListWidget, QVBoxLayout, QWidget, QPushButton,
    QHBoxLayout, QFileDialog, QMessageBox, QScrollArea, QLabel
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPixmap, QImage
import fitz  # PyMuPDF
from ui.progress_dialog import ProgressDialog
from batch.batch_processor import BatchProcessor
from operations.pdf_operations import PDFOperations

class PDFCombiner(QMainWindow):
    def __init__(self):
        super().__init__()
        self.pdf_files = []
        self.page_ranges = {}
        self.initUI()
        self.batch_processor = BatchProcessor()
        self.pdf_operations = PDFOperations()

    def initUI(self):
        self.setWindowTitle('PDF Combiner')
        self.setGeometry(100, 100, 800, 600)

        # Enable drag and drop
        self.setAcceptDrops(True)

        # Initialize UI components
        self.tabs = QTabWidget()

        # List View
        self.file_list = QListWidget()
        self.file_list.setDragDropMode(QListWidget.DragDropMode.InternalMove)  # Allow internal reordering
        self.file_list.setDropIndicatorShown(True)  # Show drop indicator
        self.file_list.setSelectionMode(QListWidget.SelectionMode.SingleSelection)

        # Connect drag and drop events
        self.file_list.dragEnterEvent = self.dragEnterEvent
        self.file_list.dragMoveEvent = self.dragMoveEvent
        self.file_list.dropEvent = self.dropEvent

        # Thumbnail View
        self.thumbnail_scroll = QScrollArea()
        self.thumbnail_container = QWidget()
        self.thumbnail_layout = QVBoxLayout(self.thumbnail_container)
        self.thumbnail_scroll.setWidget(self.thumbnail_container)
        self.thumbnail_scroll.setWidgetResizable(True)

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
        """Handle drop event to add PDF files to the list"""
        if event.mimeData().hasUrls():
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

                # Make the thumbnail clickable
                thumbnail_widget.mousePressEvent = lambda event, path=pdf_file: self.select_thumbnail(path)

                # Add to thumbnail layout
                self.thumbnail_layout.addWidget(thumbnail_widget)

                doc.close()
            except Exception as e:
                print(f"Error generating thumbnail for {pdf_file}: {str(e)}")

        # Add stretch to push thumbnails to the top
        self.thumbnail_layout.addStretch()

    def select_thumbnail(self, file_path):
        """Handle thumbnail click to select the corresponding file in the list view"""
        # Clear all selections
        self.file_list.clearSelection()

        # Select the corresponding item in the list view
        items = self.file_list.findItems(file_path, Qt.MatchFlag.MatchExactly)
        if items:
            items[0].setSelected(True)

    def remove_selected(self):
        """Remove selected files from the list"""
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

        # Update thumbnail view after removal
        self.update_thumbnail_view()

    def combine_pdfs(self):
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
