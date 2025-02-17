from PyPDF2 import PdfMerger, PdfReader, PdfWriter
from PyQt6.QtWidgets import QMessageBox, QApplication  # Updated imports

class PDFOperations:
    def combine_pdfs(self, pdf_files, output_file, progress_dialog):
        merger = PdfMerger()

        for i, pdf in enumerate(pdf_files):
            if progress_dialog.wasCanceled():
                merger.close()
                progress_dialog.close()
                QMessageBox.information(progress_dialog, "Cancelled", "PDF combination was cancelled.")
                return

            merger.append(pdf)

            progress_dialog.progress_bar.setValue(i + 1)
            progress_dialog.label.setText(f"Combining PDF {i+1} of {len(pdf_files)}")
            QApplication.processEvents()  # Ensure the UI updates during the operation

        try:
            merger.write(output_file)
        except Exception as e:
            QMessageBox.critical(progress_dialog, "Error", f"Failed to combine PDFs: {str(e)}")
        finally:
            merger.close()
