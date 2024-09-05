import sys
from PyQt5.QtWidgets import (QApplication, QWidget, QVBoxLayout, QPushButton, QListWidget, 
                             QFileDialog, QMessageBox, QProgressBar, QDialog, QLabel, QHBoxLayout)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QColor
from PyPDF2 import PdfMerger

class ProgressDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Combining PDFs")
        self.setFixedSize(300, 100)
        self.canceled = False
        
        layout = QVBoxLayout()
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

class PDFCombiner(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()
        self.pdf_files = []

    def initUI(self):
        self.setWindowTitle('PDF Combiner')
        self.setGeometry(100, 100, 400, 500)
        self.setAcceptDrops(True)

        layout = QVBoxLayout()

        self.file_list = QListWidget()
        self.file_list.setStyleSheet("QListWidget { background-color: #f0f0f0; border: 2px dashed #cccccc; }")
        layout.addWidget(self.file_list)

        self.combine_button = QPushButton('Combine PDFs')
        self.combine_button.clicked.connect(self.combine_pdfs)
        layout.addWidget(self.combine_button)

        self.setLayout(layout)

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.accept()
        else:
            event.ignore()

    def dropEvent(self, event):
        files = [u.toLocalFile() for u in event.mimeData().urls()]
        for f in files:
            if f.lower().endswith('.pdf'):
                self.pdf_files.append(f)
                self.file_list.addItem(f)
            else:
                QMessageBox.warning(self, "Invalid File", f"{f} is not a PDF file.")

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
            merger.append(pdf)
            progress_dialog.progress_bar.setValue(i + 1)
            progress_dialog.label.setText(f"Combining PDF {i+1} of {len(self.pdf_files)}")
            QApplication.processEvents()

        merger.write(output_file)
        merger.close()

        progress_dialog.close()

        QMessageBox.information(self, "Success", "PDFs combined successfully!")
        self.pdf_files.clear()
        self.file_list.clear()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    pdf_combiner = PDFCombiner()
    pdf_combiner.show()
    sys.exit(app.exec_())