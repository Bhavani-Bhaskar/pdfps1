# utilities/warning_config.py

import warnings
import logging
import os

def configure_pdf_processing_warnings():
    """
    Configure warning suppression for PDF processing libraries
    """
    
    # Suppress PDFMiner warnings
    warnings.filterwarnings("ignore", module="pdfminer")
    warnings.filterwarnings("ignore", message=".*Cannot set gray non-stroke color.*")
    warnings.filterwarnings("ignore", message=".*Pattern.*invalid float value.*")
    
    # Suppress Camelot warnings  
    warnings.filterwarnings("ignore", module="camelot")
    warnings.filterwarnings("ignore", message=".*does not lie in column range.*")
    
    # Suppress PDFPlumber warnings
    warnings.filterwarnings("ignore", module="pdfplumber")
    
    # Configure logging levels
    logging.getLogger("pdfminer").setLevel(logging.ERROR)
    logging.getLogger("pdfminer.pdfinterp").setLevel(logging.ERROR)
    logging.getLogger("camelot").setLevel(logging.ERROR)
    logging.getLogger("pdfplumber").setLevel(logging.ERROR)
    
    # Set environment variable to suppress Werkzeug warnings in Flask
    os.environ['WERKZEUG_RUN_MAIN'] = 'true'

def suppress_warnings_context():
    """
    Context manager for temporary warning suppression
    """
    class WarningSuppressionContext:
        def __enter__(self):
            configure_pdf_processing_warnings()
            return self
            
        def __exit__(self, exc_type, exc_val, exc_tb):
            # Warnings remain suppressed - no need to restore
            pass
    
    return WarningSuppressionContext()
