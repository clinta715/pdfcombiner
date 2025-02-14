import sys
from PyQt6.QtWidgets import QApplication
from ui.main_window import PDFCombiner

if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setApplicationName("PDFCombiner")
    app.setApplicationDisplayName("PDFCombiner")
    pdf_combiner = PDFCombiner()
    pdf_combiner.show()
    sys.exit(app.exec())
