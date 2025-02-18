from PyQt5.QtCore import QMimeData, Qt
from PyQt5.QtGui import QPixmap

class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()

    # ... rest of code ...

    def dropEvent(self, event):
        mime_data = event.mimeData()
        if mime_data.hasUrls():
            urls = mime_data.urls()
            for url in urls:
                file_path = url.toLocalFile()
                if file_path.endswith('.pdf'):
                    self.handle_pdf_file(file_path)
        else:
            super().dropEvent(event)

    def handle_pdf_file(self, file_path):
        # Handle PDF file logic here
        print(f"PDF file dropped: {file_path}")
