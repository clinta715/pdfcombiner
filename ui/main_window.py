from PyQt5.QtWidgets import (QMainWindow, QTabWidget, QListWidget, QVBoxLayout, 
                            QWidget, QPushButton, QHBoxLayout, QFileDialog, 
                            QMessageBox, QGridLayout, QLabel)
from PyQt5.QtCore import Qt, QMimeData
from PyQt5.QtGui import QPixmap, QDrag
import resources_rc
import os
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
        self.setGeometry(100, 100, 400, 500)

        # Initialize UI components
        self.tabs = QTabWidget()
        
        # List View
        self.file_list = QListWidget()
        self.file_list.setAcceptDrops(True)
        self.file_list.setDragEnabled(True)
        self.file_list.setSelectionMode(QListWidget.ExtendedSelection)
        
        # Thumbnail View
        self.thumbnail_widget = QWidget()
        self.thumbnail_layout = QGridLayout()
        self.thumbnail_widget.setLayout(self.thumbnail_layout)
        self.thumbnail_widget.setAcceptDrops(True)
        
        self.tabs.addTab(self.file_list, "List View")
        self.tabs.addTab(self.thumbnail_widget, "Thumbnail View")

        layout = QVBoxLayout()
        layout.addWidget(self.tabs)

        button_layout = QHBoxLayout()
        self.remove_button = QPushButton('Remove Selected')
        self.remove_button.clicked.connect(self.remove_selected)
        button_layout.addWidget(self.remove_button)

        self.combine_button = QPushButton('Combine PDFs')
        self.combine_button.clicked.connect(self.combine_pdfs)
        button_layout.addWidget(self.combine_button)

        layout.addLayout(button_layout)

        central_widget = QWidget()
        central_widget.setLayout(layout)
        self.setCentralWidget(central_widget)

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event):
        for url in event.mimeData().urls():
            file_path = url.toLocalFile()
            if file_path.lower().endswith('.pdf'):
                self.add_pdf(file_path)
        event.acceptProposedAction()

    def add_pdf(self, file_path):
        if file_path not in self.pdf_files:
            self.pdf_files.append(file_path)
            self.file_list.addItem(file_path)
            self.add_thumbnail(file_path)

    def add_thumbnail(self, file_path):
        # Create a thumbnail label
        thumbnail = QLabel()
        thumbnail.setPixmap(QPixmap(":/icons/pdf_icon.png").scaled(100, 100, Qt.KeepAspectRatio))
        thumbnail.setAlignment(Qt.AlignCenter)
        thumbnail.setStyleSheet("border: 1px solid gray; padding: 5px;")
        thumbnail.setToolTip(file_path)
        
        # Add to grid layout
        position = self.thumbnail_layout.count()
        row = position // 3
        col = position % 3
        self.thumbnail_layout.addWidget(thumbnail, row, col)

    def remove_selected(self):
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
            
            # Remove corresponding thumbnail
            for i in reversed(range(self.thumbnail_layout.count())):
                widget = self.thumbnail_layout.itemAt(i).widget()
                if widget and widget.toolTip() == file_path:
                    widget.deleteLater()
                    self.thumbnail_layout.removeWidget(widget)

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

        self.pdf_operations.combine_pdfs(self.pdf_files, output_file, progress_dialog)

        progress_dialog.close()

        QMessageBox.information(self, "Success", "PDFs combined successfully!")
        reply = QMessageBox.question(self, 'Clear List',
            'Are you sure you want to clear the file list?',
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No)

        if reply == QMessageBox.Yes:
            self.pdf_files.clear()
            self.file_list.clear()
