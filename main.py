# main.py
import sys
import logging
from PyQt6.QtWidgets import QApplication, QMainWindow, QListView, QVBoxLayout, QWidget, QMenuBar, QMenu, QTabWidget, QListWidget, QListWidgetItem
from PyQt6.QtCore import Qt, QMimeData
from PyQt6.QtGui import QDrag

class PDFCombiner(QMainWindow):
    def __init__(self):
        super().__init__()
        
        self.setCentralWidget(self.create_main_layout())
        
    def create_main_layout(self):
        main_layout = QVBoxLayout()
        
        tab_widget = QTabWidget()
        
        file_list_tab = QWidget()
        file_list_tab_layout = QVBoxLayout()
        file_list_tab.setLayout(file_list_tab_layout)
        
        thumbnail_tab = QWidget()
        thumbnail_tab_layout = QVBoxLayout()
        thumbnail_tab.setLayout(thumbnail_tab_layout)
        
        tab_widget.addTab(file_list_tab, "File List")
        tab_widget.addTab(thumbnail_tab, "Thumbnails")
        
        main_layout.addWidget(tab_widget)
        
        central_widget = QWidget()
        central_widget.setLayout(main_layout)
        
        return central_widget
    
    def dragEnterEvent(self, event):
        if event.mimeData().hasFormat('application/x-qabstractitemmodeldatalist'):
            event.accept()
        else:
            event.ignore()
    
    def dropEvent(self, event):
        mime_data = event.mimeData()
        model_index = mime_data.modelIndex()
        
        # Get the current layout of the file list tab
        layout = self.file_list_tab_layout()
        
        # Create a new item for the list
        item = QListWidgetItem(mime_data.text())
        
        # Add the item to the list
        layout.addItem(item)
        
if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = PDFCombiner()
    window.show()
    sys.exit(app.exec())
