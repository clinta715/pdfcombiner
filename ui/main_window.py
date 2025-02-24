# ui/main_window.py
from PyQt6.QtCore import QMimeData, Qt, QTimer
from PyQt6.QtGui import QPixmap
from PyQt6.QtWidgets import (QMainWindow, QTabWidget, QVBoxLayout, QWidget, 
                            QStatusBar, QProgressBar, QLabel)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        
        self.setCentralWidget(self.create_main_layout())
        self.setup_status_bar()
        
    def setup_status_bar(self):
        """Create and configure the status bar"""
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        
        # Add permanent widgets
        self.progress_bar = QProgressBar()
        self.progress_bar.setMaximumWidth(200)
        self.progress_bar.setMinimum(0)
        self.progress_bar.setMaximum(100)
        self.progress_bar.setVisible(False)
        
        self.status_label = QLabel("Ready")
        self.status_label.setMinimumWidth(200)
        
        self.status_bar.addPermanentWidget(self.status_label)
        self.status_bar.addPermanentWidget(self.progress_bar)
        
    def show_status_message(self, message: str, timeout: int = 5000):
        """Show a temporary status message"""
        self.status_bar.showMessage(message, timeout)
        
    def show_progress(self, value: int, maximum: int = 100):
        """Show progress bar with current value"""
        self.progress_bar.setMaximum(maximum)
        self.progress_bar.setValue(value)
        self.progress_bar.setVisible(True)
        
    def hide_progress(self):
        """Hide the progress bar"""
        self.progress_bar.setVisible(False)
        
    def update_status_label(self, text: str):
        """Update the permanent status label"""
        self.status_label.setText(text)
        
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
