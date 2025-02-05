from PyQt5.QtWidgets import QMainWindow, QTabWidget, QListWidget, QVBoxLayout, QWidget, QPushButton, QHBoxLayout, QFileDialog, QMessageBox
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
        self.file_list = QListWidget()
        self.tabs.addTab(self.file_list, "List View")

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
