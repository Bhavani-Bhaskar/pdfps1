"""
PDF Processing Utilities Package

This package contains utilities for processing PDF documents:
- pdf_parser: Extract text and document structure
- image_detector: Extract and analyze images
- table_extractor: Extract and process tables
- metadata_extractor: Extract document metadata
- ocr: Optical character recognition for scanned content
"""

__version__ = "1.0.0"
__author__ = "PDF Processing System"

# Import main functions for easy access
from .pdf_parser import extract_text_and_structure
from .image_detector import extract_images
from .table_extractor import extract_tables
from .metadata_extractor import extract_metadata
from .ocr import perform_ocr

__all__ = [
    'extract_text_and_structure',
    'extract_images',
    'extract_tables', 
    'extract_metadata',
    'perform_ocr'
]
