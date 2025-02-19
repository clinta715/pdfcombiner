from dataclasses import dataclass
from typing import List, Optional, Dict, Callable
from datetime import datetime
import os
import threading
from queue import Queue
from PyQt6.QtWidgets import (QDialog, QProgressBar, QLabel, QVBoxLayout,
                            QMessageBox, QPushButton, QTextEdit, QWidget)
from PyQt6.QtCore import Qt, pyqtSignal, QObject
from PyPDF2 import PdfReader, PdfWriter, PdfMerger

class ProcessSignals(QObject):
    """Signal class for process communication"""
    progress = pyqtSignal(int, str)  # value, message
    error = pyqtSignal(str)
    completed = pyqtSignal()
    file_progress = pyqtSignal(str, int)  # filename, percentage

@dataclass
class BatchOperation:
    operation_type: str
    files: List[str]
    output_dir: str
    settings: dict
    status: str = 'pending'
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    retry_count: int = 0
    max_retries: int = 3

class EnhancedProgressDialog(QDialog):
    """Enhanced progress dialog with detailed information"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Processing...")
        self.setModal(True)
        self.setMinimumWidth(500)
        self.setMinimumHeight(400)

        layout = QVBoxLayout(self)

        # Overall progress
        self.overall_label = QLabel("Overall Progress:")
        layout.addWidget(self.overall_label)
        self.overall_progress = QProgressBar()
        layout.addWidget(self.overall_progress)

        # Current file progress
        self.file_label = QLabel("Current File:")
        layout.addWidget(self.file_label)
        self.file_progress = QProgressBar()
        layout.addWidget(self.file_progress)

        # Log viewer
        self.log_viewer = QTextEdit()
        self.log_viewer.setReadOnly(True)
        layout.addWidget(self.log_viewer)

        # Cancel button
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.request_cancellation)
        layout.addWidget(self.cancel_button)

        self.cancelled = False

    def request_cancellation(self):
        self.cancelled = True
        self.cancel_button.setEnabled(False)
        self.cancel_button.setText("Cancelling...")
        self.log("Cancellation requested. Completing current operation...")

    def log(self, message: str):
        """Add message to log viewer"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_viewer.append(f"[{timestamp}] {message}")

class PDFValidator:
    """PDF validation utilities"""
    @staticmethod
    def validate_pdf(file_path: str) -> tuple[bool, str]:
        try:
            with open(file_path, 'rb') as file:
                # Check if file starts with PDF signature
                if not file.read(4) == b'%PDF':
                    return False, "Not a valid PDF file"

            reader = PdfReader(file_path)

            # Check for encryption
            if reader.is_encrypted:
                return False, "PDF is encrypted"

            # Try to access pages to check for corruption
            try:
                num_pages = len(reader.pages)
                _ = reader.pages[0]  # Try to access first page
            except Exception:
                return False, "PDF appears to be corrupted"

            return True, "PDF is valid"
        except Exception as e:
            return False, f"Validation error: {str(e)}"

class BatchProcessor:
    """Enhanced batch processor with advanced features"""
    def __init__(self):
        self.queue: List[BatchOperation] = []
        self.current_operation: Optional[BatchOperation] = None
        self.progress_dialog: Optional[EnhancedProgressDialog] = None
        self.signals = ProcessSignals()
        self.operation_thread: Optional[threading.Thread] = None
        self.validator = PDFValidator()

    def add_operation(self, operation: BatchOperation):
        """Add operation to queue with validation"""
        # Validate all PDF files before adding to queue
        invalid_files = []
        for file in operation.files:
            valid, message = self.validator.validate_pdf(file)
            if not valid:
                invalid_files.append((file, message))

        if invalid_files:
            error_msg = "\n".join(f"{file}: {msg}" for file, msg in invalid_files)
            msg = QMessageBox()
            msg.setWindowTitle("Invalid PDFs")
            msg.setText("Some PDFs failed validation:")
            msg.setDetailedText(error_msg)
            msg.setIcon(QMessageBox.Icon.Warning)
            msg.exec()
            return False

        self.queue.append(operation)
        return True

    def start_processing(self, parent: QWidget):
        """Start batch processing in a separate thread"""
        self.progress_dialog = EnhancedProgressDialog(parent)
        self.progress_dialog.overall_progress.setMaximum(len(self.queue))

        # Connect signals
        self.signals.progress.connect(self.update_progress)
        self.signals.error.connect(self.handle_error)
        self.signals.completed.connect(self.handle_completion)
        self.signals.file_progress.connect(self.update_file_progress)

        # Start processing thread
        self.operation_thread = threading.Thread(target=self.process_queue)
        self.operation_thread.start()

        self.progress_dialog.exec()

    def process_queue(self):
        """Process all operations in queue"""
        while self.queue and not self.progress_dialog.cancelled:
            self.current_operation = self.queue.pop(0)
            success = self.process_operation()

            if not success and self.current_operation.retry_count < self.current_operation.max_retries:
                self.current_operation.retry_count += 1
                self.queue.insert(0, self.current_operation)
                self.signals.progress.emit(0, f"Retrying operation (attempt {self.current_operation.retry_count + 1})")

            self.signals.progress.emit(
                self.progress_dialog.overall_progress.maximum() - len(self.queue),
                "Processing complete"
            )

        self.signals.completed.emit()

    def process_operation(self) -> bool:
        """Process single operation with progress updates"""
        try:
            method = getattr(self, f"process_{self.current_operation.operation_type}")
            return method()
        except Exception as e:
            self.signals.error.emit(str(e))
            return False

    def process_combine(self) -> bool:
        """Combine multiple PDFs into a single file"""
        try:
            merger = PdfMerger()
            total_files = len(self.current_operation.files)

            for idx, pdf in enumerate(self.current_operation.files):
                if self.progress_dialog.cancelled:
                    return False

                self.signals.file_progress.emit(
                    os.path.basename(pdf),
                    int((idx / total_files) * 100)
                )

                if not os.path.exists(pdf):
                    raise FileNotFoundError(f"PDF file not found: {pdf}")
                merger.append(pdf)

            os.makedirs(self.current_operation.output_dir, exist_ok=True)
            output_path = os.path.join(
                self.current_operation.output_dir,
                f"combined_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
            )

            merger.write(output_path)
            merger.close()

            self.current_operation.status = 'completed'
            return True

        except Exception as e:
            self.current_operation.status = f'failed: {str(e)}'
            raise

    def process_split(self) -> bool:
        """Split PDFs into individual pages"""
        try:
            os.makedirs(self.current_operation.output_dir, exist_ok=True)
            total_files = len(self.current_operation.files)

            for file_idx, pdf in enumerate(self.current_operation.files):
                if self.progress_dialog.cancelled:
                    return False

                if not os.path.exists(pdf):
                    raise FileNotFoundError(f"PDF file not found: {pdf}")

                reader = PdfReader(pdf)
                total_pages = len(reader.pages)

                for page_idx, page in enumerate(reader.pages):
                    if self.progress_dialog.cancelled:
                        return False

                    self.signals.file_progress.emit(
                        f"{os.path.basename(pdf)} (Page {page_idx + 1}/{total_pages})",
                        int(((file_idx * total_pages + page_idx) / (total_files * total_pages)) * 100)
                    )

                    writer = PdfWriter()
                    writer.add_page(page)
                    output_path = os.path.join(
                        self.current_operation.output_dir,
                        f"{os.path.splitext(os.path.basename(pdf))[0]}_page{page_idx+1}.pdf"
                    )
                    with open(output_path, 'wb') as f:
                        writer.write(f)

            self.current_operation.status = 'completed'
            return True

        except Exception as e:
            self.current_operation.status = f'failed: {str(e)}'
            raise

    def process_watermark(self) -> bool:
        """Add watermark to PDFs"""
        try:
            if not self.current_operation.settings.get('watermark_file'):
                raise ValueError("Watermark file not specified")

            watermark_file = self.current_operation.settings['watermark_file']
            if not os.path.exists(watermark_file):
                raise FileNotFoundError(f"Watermark file not found: {watermark_file}")

            watermark_reader = PdfReader(watermark_file)
            watermark_page = watermark_reader.pages[0]

            os.makedirs(self.current_operation.output_dir, exist_ok=True)
            total_files = len(self.current_operation.files)

            for idx, pdf in enumerate(self.current_operation.files):
                if self.progress_dialog.cancelled:
                    return False

                self.signals.file_progress.emit(
                    os.path.basename(pdf),
                    int((idx / total_files) * 100)
                )

                if not os.path.exists(pdf):
                    raise FileNotFoundError(f"PDF file not found: {pdf}")

                reader = PdfReader(pdf)
                writer = PdfWriter()

                for page in reader.pages:
                    page.merge_page(watermark_page)
                    writer.add_page(page)

                output_path = os.path.join(
                    self.current_operation.output_dir,
                    f"watermarked_{os.path.basename(pdf)}"
                )

                with open(output_path, 'wb') as f:
                    writer.write(f)

            self.current_operation.status = 'completed'
            return True

        except Exception as e:
            self.current_operation.status = f'failed: {str(e)}'
            raise

    def update_progress(self, value: int, message: str):
        """Update progress dialog"""
        self.progress_dialog.overall_progress.setValue(value)
        self.progress_dialog.log(message)

    def update_file_progress(self, filename: str, percentage: int):
        """Update current file progress"""
        self.progress_dialog.file_label.setText(f"Processing: {filename}")
        self.progress_dialog.file_progress.setValue(percentage)

    def handle_error(self, error_message: str):
        """Handle operation errors"""
        self.progress_dialog.log(f"Error: {error_message}")

    def handle_completion(self):
        """Handle completion of all operations"""
        if self.progress_dialog.cancelled:
            self.progress_dialog.log("Processing cancelled")
        else:
            self.progress_dialog.log("All operations completed successfully")

        self.progress_dialog.cancel_button.setText("Close")
        self.progress_dialog.cancel_button.setEnabled(True)
