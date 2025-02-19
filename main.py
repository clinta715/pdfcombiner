# main.py
import sys
import logging
from PyQt6.QtWidgets import QApplication, QMainWindow, QMenuBar, QMenu, QVBoxLayout, QWidget, QTabWidget, QListWidget, QListWidgetItem
from PyQt6.QtCore import Qt, QMimeData

class PDFCombiner(QMainWindow):
    def open_files(self):
        """Handle open files action"""
        from PyQt6.QtWidgets import QFileDialog
        files, _ = QFileDialog.getOpenFileNames(
            self,
            "Select PDF Files",
            "",
            "PDF Files (*.pdf)"
        )
        if files:
            self.file_list.addItems(files)

    def save_files(self):
        """Handle save files action"""
        from PyQt6.QtWidgets import QFileDialog
        file, _ = QFileDialog.getSaveFileName(
            self,
            "Save Combined PDF",
            "",
            "PDF Files (*.pdf)"
        )
        if file:
            # TODO: Implement save logic
            pass

    def undo_action(self):
        """Handle undo action"""
        # TODO: Implement undo logic
        pass

    def redo_action(self):
        """Handle redo action"""
        # TODO: Implement redo logic
        pass
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
        open_action = file_menu.addAction("Open")
        save_action = file_menu.addAction("Save")
        file_menu.addSeparator()
        exit_action = file_menu.addAction("Exit")
        
        # Connect actions
        open_action.triggered.connect(self.open_files)
        save_action.triggered.connect(self.save_files)
        exit_action.triggered.connect(self.close)
        
        # Edit menu
        edit_menu = menu_bar.addMenu("Edit")
        undo_action = edit_menu.addAction("Undo")
        redo_action = edit_menu.addAction("Redo")
        
        # Connect actions
        undo_action.triggered.connect(self.undo_action)
        redo_action.triggered.connect(self.redo_action)
        
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
        """Handle drag enter event"""
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            event.ignore()
    
    def dropEvent(self, event):
        """Handle drop event"""
        if event.mimeData().hasUrls():
            event.setDropAction(Qt.DropAction.CopyAction)
            event.accept()
            
            # Get the list of dropped files
            for url in event.mimeData().urls():
                file_path = url.toLocalFile()
                if file_path.lower().endswith('.pdf'):
                    # Add to the file list
                    self.file_list.addItem(file_path)
        else:
            event.ignore()

def main():
    """Main application entry point"""
    app = QApplication(sys.argv)
    
    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Create and show main window
    window = PDFCombiner()
    window.setWindowTitle("PDF Combiner")
    window.resize(800, 600)
    window.show()
    
    # Start application event loop
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
