import os
import puremagic
import PyPDF2
from typing import Dict, Any


def validate_pdf(file_path: str) -> Dict[str, Any]:
    """
    Comprehensive PDF validation using puremagic
    """
    try:
        # Check if file exists
        if not os.path.exists(file_path):
            return {'valid': False, 'error': 'File does not exist'}
        
        # Check file size (50MB limit)
        file_size = os.path.getsize(file_path)
        max_size = 50 * 1024 * 1024  # 50MB
        
        if file_size == 0:
            return {'valid': False, 'error': 'File is empty'}
        
        if file_size > max_size:
            return {'valid': False, 'error': f'File too large: {file_size / (1024*1024):.1f}MB (max: 50MB)'}
        
        # Check file type using puremagic
        try:
            # Using puremagic to detect MIME type
            file_type = puremagic.from_file(file_path, mime=True)
            if file_type != 'application/pdf':
                return {'valid': False, 'error': f'Invalid file type: {file_type}. Expected PDF.'}
        except Exception as e:
            # Fallback to extension check if puremagic fails
            if not file_path.lower().endswith('.pdf'):
                return {'valid': False, 'error': f'File type detection failed and no .pdf extension: {str(e)}'}
            # If it has .pdf extension but puremagic failed, we'll continue with PyPDF2 validation
        
        # Try to open and validate with PyPDF2
        try:
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                num_pages = len(pdf_reader.pages)
                
                if num_pages == 0:
                    return {'valid': False, 'error': 'PDF has no pages'}
                
                # Try to read first page to ensure it's not corrupted
                first_page = pdf_reader.pages[0]
                text = first_page.extract_text()
                
        except PyPDF2.errors.PdfReadError as e:
            return {'valid': False, 'error': f'Corrupted PDF: {str(e)}'}
        except Exception as e:
            return {'valid': False, 'error': f'PDF validation failed: {str(e)}'}
        
        return {
            'valid': True,
            'file_size': file_size,
            'num_pages': num_pages,
            'has_text': len(text.strip()) > 0
        }
        
    except Exception as e:
        return {'valid': False, 'error': f'Validation error: {str(e)}'}


def validate_file_extension(filename: str) -> bool:
    """
    Check if file has valid PDF extension
    """
    allowed_extensions = ['.pdf']
    return any(filename.lower().endswith(ext) for ext in allowed_extensions)


def check_file_size(file_path: str, max_size_mb: int = 50) -> Dict[str, Any]:
    """
    Check if file size is within limits
    """
    try:
        file_size = os.path.getsize(file_path)
        max_size_bytes = max_size_mb * 1024 * 1024
        
        return {
            'valid': file_size <= max_size_bytes,
            'size_mb': file_size / (1024 * 1024),
            'max_size_mb': max_size_mb
        }
    except Exception as e:
        return {'valid': False, 'error': str(e)}


def advanced_pdf_validation(file_path: str) -> Dict[str, Any]:
    """
    Advanced PDF validation with multiple checks using puremagic
    """
    try:
        # Basic file existence and size checks
        if not os.path.exists(file_path):
            return {'valid': False, 'error': 'File does not exist'}
        
        file_size = os.path.getsize(file_path)
        if file_size == 0:
            return {'valid': False, 'error': 'File is empty'}
        
        # Multiple validation approaches
        validation_results = {
            'file_exists': True,
            'file_size_ok': file_size <= 50 * 1024 * 1024,
            'has_pdf_extension': file_path.lower().endswith('.pdf'),
            'mime_type_valid': False,
            'pypdf2_readable': False,
            'has_pages': False,
            'has_text': False
        }
        
        # MIME type validation with puremagic
        try:
            detected_mime = puremagic.from_file(file_path, mime=True)
            validation_results['detected_mime_type'] = detected_mime
            validation_results['mime_type_valid'] = detected_mime == 'application/pdf'
        except Exception as e:
            validation_results['mime_detection_error'] = str(e)
        
        # Alternative: Use puremagic.magic_file for more detailed info
        try:
            magic_results = puremagic.magic_file(file_path)
            if magic_results:
                # Get the highest confidence match
                best_match = magic_results[0]
                validation_results['magic_extension'] = best_match[0]
                validation_results['magic_mime'] = best_match[1]
                validation_results['magic_description'] = best_match[2]
                validation_results['magic_confidence'] = best_match[3]
                
                # Check if any of the matches indicate PDF
                pdf_matches = [match for match in magic_results if 
                             match[0] == '.pdf' or match[1] == 'application/pdf']
                validation_results['has_pdf_matches'] = len(pdf_matches) > 0
        except Exception as e:
            validation_results['magic_file_error'] = str(e)
        
        # PyPDF2 validation
        try:
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                num_pages = len(pdf_reader.pages)
                
                validation_results['pypdf2_readable'] = True
                validation_results['num_pages'] = num_pages
                validation_results['has_pages'] = num_pages > 0
                
                if num_pages > 0:
                    try:
                        first_page = pdf_reader.pages[0]
                        text = first_page.extract_text()
                        validation_results['has_text'] = len(text.strip()) > 0
                        validation_results['first_page_text_length'] = len(text.strip())
                    except Exception as e:
                        validation_results['text_extraction_error'] = str(e)
                
        except PyPDF2.errors.PdfReadError as e:
            validation_results['pypdf2_error'] = f'PDF read error: {str(e)}'
        except Exception as e:
            validation_results['pypdf2_error'] = f'General PDF error: {str(e)}'
        
        # Determine overall validity
        is_valid = (
            validation_results['file_size_ok'] and
            validation_results['has_pdf_extension'] and
            validation_results['pypdf2_readable'] and
            validation_results['has_pages']
        )
        
        # If MIME type detection worked, include it in validation
        if 'detected_mime_type' in validation_results:
            is_valid = is_valid and validation_results['mime_type_valid']
        
        return {
            'valid': is_valid,
            'file_size': file_size,
            'details': validation_results
        }
        
    except Exception as e:
        return {'valid': False, 'error': f'Advanced validation error: {str(e)}'}


def validate_pdf_with_fallback(file_path: str) -> Dict[str, Any]:
    """
    PDF validation with multiple fallback methods
    """
    try:
        # Step 1: Basic checks
        if not os.path.exists(file_path):
            return {'valid': False, 'error': 'File does not exist'}
        
        file_size = os.path.getsize(file_path)
        if file_size == 0:
            return {'valid': False, 'error': 'File is empty'}
        
        if file_size > 50 * 1024 * 1024:
            return {'valid': False, 'error': f'File too large: {file_size / (1024*1024):.1f}MB (max: 50MB)'}
        
        # Step 2: Try puremagic first
        mime_type_valid = False
        try:
            detected_type = puremagic.from_file(file_path, mime=True)
            mime_type_valid = detected_type == 'application/pdf'
            if not mime_type_valid:
                # Try the more detailed magic_file method
                magic_results = puremagic.magic_file(file_path)
                if magic_results:
                    pdf_matches = [m for m in magic_results if '.pdf' in m[0] or 'application/pdf' in m[1]]
                    mime_type_valid = len(pdf_matches) > 0
        except Exception:
            # If puremagic fails, fall back to extension check
            mime_type_valid = file_path.lower().endswith('.pdf')
        
        # Step 3: Validate with PyPDF2
        try:
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                num_pages = len(pdf_reader.pages)
                
                if num_pages == 0:
                    return {'valid': False, 'error': 'PDF has no pages'}
                
                # Try to read first page
                first_page = pdf_reader.pages[0]
                text = first_page.extract_text()
                
                return {
                    'valid': mime_type_valid,
                    'file_size': file_size,
                    'num_pages': num_pages,
                    'has_text': len(text.strip()) > 0,
                    'mime_type_valid': mime_type_valid
                }
                
        except PyPDF2.errors.PdfReadError as e:
            return {'valid': False, 'error': f'Corrupted PDF: {str(e)}'}
        except Exception as e:
            return {'valid': False, 'error': f'PDF validation failed: {str(e)}'}
        
    except Exception as e:
        return {'valid': False, 'error': f'Validation error: {str(e)}'}
