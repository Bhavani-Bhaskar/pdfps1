import PyPDF2
import fitz  # PyMuPDF
import re
from typing import Dict, List, Any

def extract_text_and_structure(pdf_path: str) -> Dict[str, Any]:
    """
    Extract text content and document structure from PDF
    """
    try:
        # Use PyMuPDF for better text extraction
        doc = fitz.open(pdf_path)
        
        full_text = ""
        headings = []
        structure = {
            'total_pages': len(doc),
            'headings': [],
            'sections': []
        }
        
        for page_num in range(len(doc)):
            page = doc[page_num]
            
            # Extract text
            page_text = page.get_text()
            full_text += f"\n--- Page {page_num + 1} ---\n"
            full_text += page_text
            
            # Extract potential headings based on font size and formatting
            blocks = page.get_text("dict")
            page_headings = extract_headings_from_blocks(blocks, page_num + 1)
            headings.extend(page_headings)
        
        doc.close()
        
        # Process headings to create structure
        structure['headings'] = [h['text'] for h in headings]
        structure['sections'] = organize_sections(headings)
        
        return {
            'text': full_text,
            'structure': structure,
            'headings': headings
        }
        
    except Exception as e:
        # Fallback to PyPDF2
        return extract_text_pypdf2(pdf_path)

def extract_headings_from_blocks(blocks: Dict, page_num: int) -> List[Dict]:
    """
    Extract headings based on font characteristics
    """
    headings = []
    
    if 'blocks' not in blocks:
        return headings
    
    font_sizes = []
    
    # First pass: collect all font sizes
    for block in blocks['blocks']:
        if 'lines' in block:
            for line in block['lines']:
                if 'spans' in line:
                    for span in line['spans']:
                        if 'size' in span:
                            font_sizes.append(span['size'])
    
    if not font_sizes:
        return headings
    
    # Determine threshold for headings (larger than average)
    avg_font_size = sum(font_sizes) / len(font_sizes)
    heading_threshold = avg_font_size * 1.2
    
    # Second pass: identify headings
    for block in blocks['blocks']:
        if 'lines' in block:
            for line in block['lines']:
                if 'spans' in line:
                    line_text = ""
                    max_font_size = 0
                    is_bold = False
                    
                    for span in line['spans']:
                        if 'text' in span:
                            line_text += span['text']
                        if 'size' in span:
                            max_font_size = max(max_font_size, span['size'])
                        if 'flags' in span and span['flags'] & 2**4:  # Bold flag
                            is_bold = True
                    
                    # Clean and check if it's a potential heading
                    line_text = line_text.strip()
                    if (len(line_text) > 0 and len(line_text) < 200 and 
                        (max_font_size > heading_threshold or is_bold) and
                        not line_text.endswith('.')):
                        
                        headings.append({
                            'text': line_text,
                            'page': page_num,
                            'font_size': max_font_size,
                            'is_bold': is_bold
                        })
    
    return headings

def organize_sections(headings: List[Dict]) -> List[Dict]:
    """
    Organize headings into hierarchical sections
    """
    if not headings:
        return []
    
    # Sort headings by font size (descending) and page number
    sorted_headings = sorted(headings, key=lambda x: (-x['font_size'], x['page']))
    
    sections = []
    current_section = None
    
    for heading in sorted_headings:
        if current_section is None or heading['font_size'] >= current_section['font_size']:
            # New main section
            current_section = {
                'title': heading['text'],
                'page': heading['page'],
                'font_size': heading['font_size'],
                'subsections': []
            }
            sections.append(current_section)
        else:
            # Subsection
            current_section['subsections'].append({
                'title': heading['text'],
                'page': heading['page'],
                'font_size': heading['font_size']
            })
    
    return sections

def extract_text_pypdf2(pdf_path: str) -> Dict[str, Any]:
    """
    Fallback text extraction using PyPDF2
    """
    try:
        with open(pdf_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            full_text = ""
            
            for page_num in range(len(pdf_reader.pages)):
                page = pdf_reader.pages[page_num]
                page_text = page.extract_text()
                full_text += f"\n--- Page {page_num + 1} ---\n"
                full_text += page_text
            
            return {
                'text': full_text,
                'structure': {
                    'total_pages': len(pdf_reader.pages),
                    'headings': [],
                    'sections': []
                },
                'headings': []
            }
    except Exception as e:
        return {
            'text': f"Error extracting text: {str(e)}",
            'structure': {'total_pages': 0, 'headings': [], 'sections': []},
            'headings': []
        }
