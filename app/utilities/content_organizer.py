# utilities/content_organizer.py

import fitz  # PyMuPDF
from typing import Dict, List, Any, Optional
from collections import defaultdict
from .document_classifier import DocumentTypeClassifier
from .book_extractor import BookExtractor
from .research_paper_extractor import ResearchPaperExtractor
from .technical_report_extractor import TechnicalReportExtractor


def organize_content_by_page(pdf_path: str, text_data: Dict, images_data: List, 
                           tables_data: List, metadata: Dict) -> Dict[str, Any]:
    """
    Organize extracted content by page number for structured output.
    
    Args:
        pdf_path: Path to the PDF file
        text_data: Text and structure data from pdf_parser
        images_data: Image data from image_detector  
        tables_data: Table data from table_extractor
        metadata: Metadata from metadata_extractor
    
    Returns:
        Dictionary with page-wise organized content
    """
    try:
        # Initialize page organization structure
        doc = fitz.open(pdf_path)
        total_pages = len(doc)
        doc.close()
        
        page_content = {}
        
        # Initialize each page
        for page_num in range(1, total_pages + 1):
            page_content[page_num] = {
                'text': '',
                'images': [],
                'tables': []
            }
        
        # Organize text content by page
        if text_data.get('text'):
            page_content = _organize_text_by_page(text_data['text'], page_content)
        
        # Organize images by page
        for image in images_data:
            if not isinstance(image, dict) or 'error' in image:
                continue
            page_num = image.get('page', 1)
            if page_num in page_content:
                page_content[page_num]['images'].append(image)
        
        # Organize tables by page  
        for table in tables_data:
            if not isinstance(table, dict) or 'error' in table:
                continue
            page_num = table.get('page', 1)
            if page_num in page_content:
                page_content[page_num]['tables'].append(table)
        
        return {
            'total_pages': total_pages,
            'page_content': page_content,
            'structure': text_data.get('structure', {}),
            'metadata': metadata
        }
        
    except Exception as e:
        return {
            'error': f"Content organization failed: {str(e)}",
            'total_pages': 0,
            'page_content': {},
            'structure': {},
            'metadata': {}
        }

def _organize_text_by_page(full_text: str, page_content: Dict) -> Dict:
    """
    Parse full text and assign to appropriate pages.
    """
    try:
        # Split text by page markers
        lines = full_text.split('\n')
        current_page = 1
        current_page_text = []
        
        for line in lines:
            # Check for page markers like "--- Page X ---"
            if line.strip().startswith('--- Page') and 'Page' in line:
                # Save previous page content
                if current_page_text and current_page in page_content:
                    page_content[current_page]['text'] = '\n'.join(current_page_text).strip()
                
                # Extract new page number
                try:
                    page_parts = line.split('Page')[1].split('---')[0].strip()
                    current_page = int(page_parts)
                    current_page_text = []
                except (IndexError, ValueError):
                    current_page_text.append(line)
            else:
                current_page_text.append(line)
        
        # Save last page content
        if current_page_text and current_page in page_content:
            page_content[current_page]['text'] = '\n'.join(current_page_text).strip()
        
        return page_content
        
    except Exception as e:
        # Fallback: assign all text to page 1
        if 1 in page_content:
            page_content[1]['text'] = full_text
        return page_content

def generate_documentation_section(filename: str, processed_at: str) -> str:
    """
    Generate documentation section for the output.
    """
    doc_content = f"""
PDF PROCESSING DOCUMENTATION
===============================

Document: {filename}
Processed: {processed_at}
Processing System: Enhanced PDF Content Analyzer v2.0

This document contains the complete analysis of the uploaded PDF file, 
organized in a structured format for easy navigation and understanding.

The content is organized as follows:
1. Document Metadata - Basic information about the PDF
2. Page-wise Content Analysis - Detailed breakdown per page
3. OCR Analysis - Text extraction from scanned content
4. Processing Summary - Overview of extraction results

Each page section contains:
- Extracted text content
- Embedded images (if any)
- Tables and structured data (if any)

===============================
"""
    return doc_content.strip()

def format_page_wise_content(page_content: Dict, total_pages: int) -> str:
    """
    Format page-wise content for output display.
    """
    content_lines = []
    content_lines.append("PAGE-WISE CONTENT ANALYSIS")
    content_lines.append("=" * 50)
    content_lines.append("")
    
    for page_num in range(1, total_pages + 1):
        if page_num not in page_content:
            continue
            
        page_data = page_content[page_num]
        content_lines.append(f"PAGE {page_num}")
        content_lines.append("-" * 20)
        content_lines.append("")
        
        # Text content
        if page_data.get('text') and page_data['text'].strip():
            content_lines.append("EXTRACTED TEXT:")
            content_lines.append("~" * 15)
            content_lines.append(page_data['text'].strip())
            content_lines.append("")
        
        # Images
        if page_data.get('images'):
            content_lines.append("EXTRACTED IMAGES:")
            content_lines.append("~" * 16)
            for i, img in enumerate(page_data['images'], 1):
                content_lines.append(f"Image {i}:")
                content_lines.append(f"  Size: {img.get('size', 'Unknown')}")
                content_lines.append(f"  Format: {img.get('format', 'Unknown')}")
                if img.get('description'):
                    content_lines.append(f"  Description: {img['description']}")
                content_lines.append("")
        
        # Tables
        if page_data.get('tables'):
            content_lines.append("EXTRACTED TABLES:")
            content_lines.append("~" * 16)
            for i, table in enumerate(page_data['tables'], 1):
                content_lines.append(f"Table {i}:")
                content_lines.append(f"  Dimensions: {table.get('shape', 'Unknown')}")
                content_lines.append(f"  Accuracy: {table.get('accuracy', 'Unknown')}%")
                content_lines.append(f"  Method: {table.get('method', 'Unknown')}")
                if table.get('summary'):
                    content_lines.append(f"  Summary: {table['summary']}")
                if 'content' in table:
                    preview = table['content'][:200] + "..." if len(str(table['content'])) > 200 else str(table['content'])
                    content_lines.append(f"  Preview: {preview}")
                content_lines.append("")
        
        # Add separator between pages
        if page_num < total_pages:
            content_lines.append("=" * 50)
            content_lines.append("")
    
    return "\n".join(content_lines)

def organize_content_by_document_type(pdf_path: str, text_data: Dict, images_data: List, 
                                    tables_data: List, metadata: Dict) -> Dict[str, Any]:
    """
    Enhanced content organization with document type classification
    """
    try:
        # Step 1: Classify document type
        classifier = DocumentTypeClassifier()
        classification = classifier.classify_document(pdf_path)
        
        # Step 2: Apply type-specific extraction
        type_specific_data = {}
        
        if classification['primary_type'] == 'book':
            book_extractor = BookExtractor()
            type_specific_data = book_extractor.extract_book_structure(pdf_path)
        
        elif classification['primary_type'] == 'research_paper':
            paper_extractor = ResearchPaperExtractor()
            type_specific_data = paper_extractor.extract_paper_structure(pdf_path)
        
        elif classification['primary_type'] == 'technical_report':
            report_extractor = TechnicalReportExtractor()
            type_specific_data = report_extractor.extract_report_structure(pdf_path)
        
        # Step 3: Organize by page (existing functionality)
        page_organized = organize_content_by_page(pdf_path, text_data, images_data, tables_data, metadata)
        
        # Step 4: Combine with type-specific data
        return {
            'classification': classification,
            'type_specific_content': type_specific_data,
            'page_organized_content': page_organized,
            'processing_strategy': classification.get('processing_strategy', {}),
            'extraction_priorities': classification.get('extraction_priorities', [])
        }
        
    except Exception as e:
        return {
            'error': f"Enhanced content organization failed: {str(e)}",
            'classification': {'primary_type': 'unknown', 'confidence': 0.0},
            'type_specific_content': {},
            'page_organized_content': {}
        }
