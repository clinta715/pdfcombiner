# main.py
import sys
import logging
from PyQt6.QtWidgets import QApplication, QMainWindow, QMenuBar, QMenu, QVBoxLayout, QWidget, QTabWidget, QListWidget, QListWidgetItem
from PyQt6.QtCore import Qt, QMimeData

class PDFCombiner(QMainWindow):
    def __init__(self):
        super().__init__()
        
        # Create menu bar first
        self.create_menu_bar()
        
        # Then set up main layout
        self.setCentralWidget(self.create_main_layout())
        
    def create_menu_bar(self):
        """Create and configure the menu bar"""
        menu_bar = self.menuBar()
        
        # File menu
        file_menu = menu_bar.addMenu("File")
        file_menu.addAction("Open")
        file_menu.addAction("Save")
        file_menu.addSeparator()
        file_menu.addAction("Exit")
        
        # Edit menu
        edit_menu = menu_bar.addMenu("Edit")
        edit_menu.addAction("Undo")
        edit_menu.addAction("Redo")
        
    def create_main_layout(self):
        main_layout = QVBoxLayout()
        
        self.tab_widget = QTabWidget()
        
        # File List Tab
        self.file_list_tab = QWidget()
        self.file_list_layout = QVBoxLayout()
        self.file_list = QListWidget()
        self.file_list.setAcceptDrops(True)
        self.file_list.setDragEnabled(True)
        self.file_list_layout.addWidget(self.file_list)
        self.file_list_tab.setLayout(self.file_list_layout)
        
        # Thumbnail Tab
        self.thumbnail_tab = QWidget()
        self.thumbnail_layout = QVBoxLayout()
        self.thumbnail_tab.setLayout(self.thumbnail_layout)
        
        self.tab_widget.addTab(self.file_list_tab, "File List")
        self.tab_widget.addTab(self.thumbnail_tab, "Thumbnails")
        
        main_layout.addWidget(self.tab_widget)
        
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

def main():
    """Main application entry point"""
    app = QApplication(sys.argv)
    
    # Set up logging
    logging.basicConfig(level=logging.INFO)
    
    # Create and show main window
    window = PDFCombiner()
    window.setWindowTitle("PDF Combiner")
    window.resize(800, 600)
    window.show()
    
    # Start application event loop
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
