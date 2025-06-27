import PyPDF2
import fitz  # PyMuPDF
from datetime import datetime
from typing import Dict, Any, Optional

def extract_metadata(pdf_path: str) -> Dict[str, Any]:
    """
    Extract comprehensive metadata from PDF
    """
    metadata = {}
    
    try:
        # Try PyMuPDF first (more comprehensive)
        metadata.update(extract_metadata_pymupdf(pdf_path))
        
        # Supplement with PyPDF2 if needed
        pypdf2_metadata = extract_metadata_pypdf2(pdf_path)
        for key, value in pypdf2_metadata.items():
            if key not in metadata and value:
                metadata[key] = value
        
        # Add file system metadata
        file_metadata = extract_file_metadata(pdf_path)
        metadata.update(file_metadata)
        
        return metadata
        
    except Exception as e:
        return {'error': f"Metadata extraction failed: {str(e)}"}

def extract_metadata_pymupdf(pdf_path: str) -> Dict[str, Any]:
    """
    Extract metadata using PyMuPDF
    """
    metadata = {}
    
    try:
        doc = fitz.open(pdf_path)
        
        # Basic document info
        meta = doc.metadata
        
        # Standard metadata fields
        metadata_mapping = {
            'title': meta.get('title', ''),
            'author': meta.get('author', ''),
            'subject': meta.get('subject', ''),
            'keywords': meta.get('keywords', ''),
            'creator': meta.get('creator', ''),
            'producer': meta.get('producer', ''),
            'creation_date': parse_pdf_date(meta.get('creationDate', '')),
            'modification_date': parse_pdf_date(meta.get('modDate', '')),
            'trapped': meta.get('trapped', ''),
            'format': meta.get('format', ''),
        }
        
        # Add non-empty metadata
        for key, value in metadata_mapping.items():
            if value:
                metadata[key] = value
        
        # Document statistics
        metadata['page_count'] = doc.page_count
        metadata['is_encrypted'] = doc.is_encrypted
        metadata['is_pdf'] = doc.is_pdf
        
        # Check if document has forms
        metadata['has_forms'] = bool(doc.form_n())
        
        # Check for annotations
        annotation_count = 0
        for page in doc:
            annotation_count += len(page.annots())
        metadata['annotation_count'] = annotation_count
        
        # Check for bookmarks/outline
        outline = doc.get_toc()
        metadata['has_bookmarks'] = len(outline) > 0
        metadata['bookmark_count'] = len(outline)
        
        # Language detection (if available)
        try:
            lang = doc.metadata.get('language', '')
            if lang:
                metadata['language'] = lang
        except:
            pass
        
        doc.close()
        return metadata
        
    except Exception as e:
        return {'pymupdf_error': str(e)}

def extract_metadata_pypdf2(pdf_path: str) -> Dict[str, Any]:
    """
    Extract metadata using PyPDF2 as fallback
    """
    metadata = {}
    
    try:
        with open(pdf_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            
            # Basic info
            metadata['page_count_pypdf2'] = len(pdf_reader.pages)
            metadata['is_encrypted_pypdf2'] = pdf_reader.is_encrypted
            
            # Document info
            if pdf_reader.metadata:
                doc_info = pdf_reader.metadata
                
                metadata_mapping = {
                    'title_pypdf2': doc_info.get('/Title', ''),
                    'author_pypdf2': doc_info.get('/Author', ''),
                    'subject_pypdf2': doc_info.get('/Subject', ''),
                    'creator_pypdf2': doc_info.get('/Creator', ''),
                    'producer_pypdf2': doc_info.get('/Producer', ''),
                    'creation_date_pypdf2': parse_pdf_date(str(doc_info.get('/CreationDate', ''))),
                    'modification_date_pypdf2': parse_pdf_date(str(doc_info.get('/ModDate', ''))),
                }
                
                # Add non-empty metadata
                for key, value in metadata_mapping.items():
                    if value:
                        metadata[key] = value
        
        return metadata
        
    except Exception as e:
        return {'pypdf2_error': str(e)}

def extract_file_metadata(pdf_path: str) -> Dict[str, Any]:
    """
    Extract file system metadata
    """
    import os
    import stat
    
    metadata = {}
    
    try:
        file_stats = os.stat(pdf_path)
        
        metadata['file_size'] = file_stats.st_size
        metadata['file_size_mb'] = round(file_stats.st_size / (1024 * 1024), 2)
        
        # File timestamps
        metadata['file_created'] = datetime.fromtimestamp(file_stats.st_ctime).isoformat()
        metadata['file_modified'] = datetime.fromtimestamp(file_stats.st_mtime).isoformat()
        metadata['file_accessed'] = datetime.fromtimestamp(file_stats.st_atime).isoformat()
        
        # File permissions
        metadata['file_permissions'] = oct(file_stats.st_mode)[-3:]
        
        # File path info
        metadata['filename'] = os.path.basename(pdf_path)
        metadata['file_directory'] = os.path.dirname(pdf_path)
        metadata['file_extension'] = os.path.splitext(pdf_path)[1]
        
        return metadata
        
    except Exception as e:
        return {'file_metadata_error': str(e)}

def parse_pdf_date(date_str: str) -> Optional[str]:
    """
    Parse PDF date format to ISO format
    """
    if not date_str:
        return None
    
    try:
        # PDF date format: D:YYYYMMDDHHmmSSOHH'mm'
        if date_str.startswith("D:"):
            date_str = date_str[2:]  # Remove "D:" prefix
        
        # Extract date components
        if len(date_str) >= 14:
            year = int(date_str[:4])
            month = int(date_str[4:6])
            day = int(date_str[6:8])
            hour = int(date_str[8:10])
            minute = int(date_str[10:12])
            second = int(date_str[12:14])
            
            dt = datetime(year, month, day, hour, minute, second)
            return dt.isoformat()
        elif len(date_str) >= 8:
            # Date only
            year = int(date_str[:4])
            month = int(date_str[4:6])
            day = int(date_str[6:8])
            
            dt = datetime(year, month, day)
            return dt.isoformat()
    
    except (ValueError, IndexError):
        # Try to parse as regular datetime string
        try:
            # Remove common PDF date prefixes/suffixes
            clean_date = date_str.strip().replace("D:", "").split("+")[0].split("-")[0]
            
            # Try different date formats
            for fmt in ["%Y%m%d%H%M%S", "%Y-%m-%d %H:%M:%S", "%Y-%m-%d"]:
                try:
                    dt = datetime.strptime(clean_date[:len(fmt.replace("%", ""))], fmt)
                    return dt.isoformat()
                except ValueError:
                    continue
        except:
            pass
    
    return date_str if date_str else None

def format_metadata_for_display(metadata: Dict[str, Any]) -> str:
    """
    Format metadata dictionary for readable display
    """
    formatted_lines = []
    
    # Define display order and labels
    display_mapping = {
        'title': 'Title',
        'author': 'Author',
        'subject': 'Subject',
        'creator': 'Creator',
        'producer': 'Producer',
        'creation_date': 'Created',
        'modification_date': 'Modified',
        'page_count': 'Pages',
        'file_size_mb': 'File Size (MB)',
        'language': 'Language',
        'has_bookmarks': 'Has Bookmarks',
        'bookmark_count': 'Bookmark Count',
        'annotation_count': 'Annotations',
        'has_forms': 'Has Forms',
        'is_encrypted': 'Encrypted'
    }
    
    for key, label in display_mapping.items():
        if key in metadata and metadata[key]:
            value = metadata[key]
            formatted_lines.append(f"{label}: {value}")
    
    return "\n".join(formatted_lines) if formatted_lines else "No metadata available"
