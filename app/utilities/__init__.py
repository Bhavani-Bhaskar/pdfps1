# """
# PDF Processing Utilities Package

# This package contains utilities for processing PDF documents:
# - pdf_parser: Extract text and document structure
# - image_detector: Extract and analyze images
# - table_extractor: Extract and process tables
# - metadata_extractor: Extract document metadata
# - ocr: Optical character recognition for scanned content
# """

# __version__ = "1.0.0"
# __author__ = "PDF Processing System"

# # Import main functions for easy access
# from .pdf_parser import extract_text_and_structure
# from .image_detector import extract_images
# from .table_extractor import extract_tables
# from .metadata_extractor import extract_metadata
# from .ocr import perform_ocr

# __all__ = [
#     'extract_text_and_structure',
#     'extract_images',
#     'extract_tables', 
#     'extract_metadata',
#     'perform_ocr'
# ]


# """
# PDF Processing Utilities Package

# This package contains utilities for processing PDF documents:
# - pdf_parser: Extract text and document structure
# - image_detector: Extract and analyze images
# - table_extractor: Extract and process tables
# - metadata_extractor: Extract document metadata
# - ocr: Optical character recognition for scanned content
# - content_organizer: Organize content by page for structured output
# """

# __version__ = "2.0.0"
# __author__ = "PDF Processing System"

# # Import main functions for easy access
# from .pdf_parser import extract_text_and_structure
# from .image_detector import extract_images
# from .table_extractor import extract_tables
# from .metadata_extractor import extract_metadata, format_metadata_for_display
# from .ocr import perform_ocr
# from .content_organizer import organize_content_by_page, generate_documentation_section, format_page_wise_content

# __all__ = [
#     'extract_text_and_structure',
#     'extract_images', 
#     'extract_tables',
#     'extract_metadata',
#     'format_metadata_for_display',
#     'perform_ocr',
#     'organize_content_by_page',
#     'generate_documentation_section', 
#     'format_page_wise_content'
# ]


# utilities/__init__.py

"""
PDF Processing Utilities Package
Enhanced for research paper processing with warning suppression
"""

__version__ = "2.1.0"
__author__ = "PDF Processing System"

# Configure warnings before importing other modules
from .warning_config import configure_pdf_processing_warnings
configure_pdf_processing_warnings()

# Import main functions for easy access
from .pdf_parser import extract_text_and_structure
from .image_detector import extract_images
from .table_extractor import extract_tables
from .metadata_extractor import extract_metadata, format_metadata_for_display
from .ocr import perform_ocr
from .content_organizer import organize_content_by_page, generate_documentation_section, format_page_wise_content

__all__ = [
    'extract_text_and_structure',
    'extract_images', 
    'extract_tables',
    'extract_metadata',
    'format_metadata_for_display',
    'perform_ocr',
    'organize_content_by_page',
    'generate_documentation_section', 
    'format_page_wise_content'
]
