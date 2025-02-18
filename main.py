import sys
import logging
from PyQt6.QtWidgets import QApplication
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
        app.setApplicationName("PDFCombiner")
        app.setApplicationDisplayName(f"PDFCombiner v{__version__}")
        
        logger.info("Starting PDFCombiner application")
        pdf_combiner = PDFCombiner()
        pdf_combiner.show()
        
        return app.exec()
        
    except Exception as e:
        logger.critical(f"Application error: {str(e)}", exc_info=True)
        return 1

if __name__ == '__main__':
    sys.exit(main())
