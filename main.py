import sys
import logging
from PyQt6.QtWidgets import QApplication, QMainWindow, QListView, QVBoxLayout, QWidget, QMenuBar, QMenu
from PyQt6.QtCore import Qt, QMimeData
from PyQt6.QtGui import QDrag
from ui.main_window import PDFCombiner

__version__ = "1.0.0"

def setup_logging() -> None:
    """Configure logging for the application"""
    try:
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('pdfcombiner.log'),
                logging.StreamHandler()
            ]
        )
    except Exception as e:
        print(f"Error setting up logging: {str(e)}")
        # Add a log message to indicate that there was an issue with logging
        logging.error("Failed to set up logging", exc_info=True)

def main() -> int:
    """Main application entry point"""
    setup_logging()
    logger = logging.getLogger(__name__)
    
    try:
        app = QApplication(sys.argv)
        main_window = QMainWindow()
        
        # Create a menu bar
        menubar = QMenuBar(main_window)
        file_menu = QMenu("File", menubar)
        menubar.addMenu(file_menu)
        
        # Create a list view to display the files
        file_list_view = QListView()
        file_list_view.setDragDropMode(QListView.DragDropMode.InternalMove)
        file_list_view.setDragEnabled(True)  # Add this line
        
        # Create a layout to hold the views
        layout = QVBoxLayout()
        layout.addWidget(file_list_view)
        
        # Create a widget to hold the layout
        widget = QWidget()
        widget.setLayout(layout)
        
        # Add the widget to the main window
        main_window.setCentralWidget(widget)
        
        # Show the main window
        main_window.show()
        
        return app.exec()
        
    except Exception as e:
        logger.critical(f"Application error: {str(e)}", exc_info=True)
        return 1

if __name__ == '__main__':
    sys.exit(main())
