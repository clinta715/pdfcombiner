import sys
import logging
from PyQt6.QtWidgets import QApplication, QMainWindow, QListView, QVBoxLayout, QWidget, QMenuBar, QMenu
from PyQt6.QtCore import Qt, QMimeData
from PyQt6.QtGui import QDrag

class PDFCombiner(QMainWindow):
    def __init__(self):
        super().__init__()
        
        # Create a menu bar
        menubar = QMenuBar(self)
        file_menu = QMenu("File", menubar)
        menubar.addMenu(file_menu)
        
        # Create a list view to display the files
        self.file_list_view = QListView()
        self.file_list_view.setDragDropMode(QListView.DragDropMode.InternalMove)
        self.file_list_view.setDragEnabled(True)  
        
        # Create a layout to hold the views
        layout = QVBoxLayout()
        layout.addWidget(self.file_list_view)
        
        # Create a widget to hold the layout
        widget = QWidget()
        widget.setLayout(layout)
        
        # Add the widget to the main window
        self.setCentralWidget(widget)
        
    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.accept()
        else:
            event.ignore()
    
    def dropEvent(self, event):
        mime_data = event.mimeData()
        if mime_data.hasUrls():
            urls = mime_data.urls()
            for url in urls:
                print(f"Adding PDF: {url.toString()}")
                # Add the PDF to the list view
                self.file_list_view.addItem(url.toString())
        
if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = PDFCombiner()
    window.show()
    sys.exit(app.exec())
