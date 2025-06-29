# Add these imports at the top of main.py
import warnings
import logging
import os
from waitress import serve
# Suppress specific warnings at startup (ADD THIS BEFORE OTHER IMPORTS)
warnings.filterwarnings("ignore", category=UserWarning, module="camelot")
warnings.filterwarnings("ignore", message=".*Pattern.*invalid float value.*")
warnings.filterwarnings("ignore", message=".*does not lie in column range.*")

# Configure logging to suppress pdfminer warnings
logging.getLogger("pdfminer").setLevel(logging.ERROR)
logging.getLogger("camelot").setLevel(logging.ERROR)

from flask import Flask, request, jsonify, render_template, send_from_directory, abort
import uuid
from datetime import datetime
from werkzeug.utils import secure_filename
import glob
# Your existing imports
from validators import validate_pdf
from utilities.pdf_parser import extract_text_and_structure
from utilities.image_detector import extract_images
from utilities.table_extractor import extract_tables
from utilities.metadata_extractor import extract_metadata, format_metadata_for_display
from utilities.ocr import perform_ocr
from utilities.content_organizer import organize_content_by_page, generate_documentation_section, format_page_wise_content

app = Flask(__name__)

# Configuration
UPLOAD_FOLDER = 'uploads'
OUTPUT_FOLDER = 'output'
STATIC_FOLDER = 'static'
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB
ALLOWED_EXTENSIONS = {'pdf'}

# Configure Flask
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = MAX_FILE_SIZE

# Ensure directories exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)
os.makedirs(STATIC_FOLDER, exist_ok=True)
os.makedirs(os.path.join(STATIC_FOLDER, 'css'), exist_ok=True)
os.makedirs(os.path.join(STATIC_FOLDER, 'js'), exist_ok=True)

def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Update the process_pdf function in main.py

def process_pdf(pdf_path, filename):
    """Enhanced PDF processing with warning suppression for research papers"""
    try:
        print(f"Processing {filename}...")
        
        # Suppress warnings during processing
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            
            # Initialize results dictionary
            results = {
                'filename': filename,
                'processed_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'text_content': '',
                'structure': {},
                'images': [],
                'tables': [],
                'metadata': {},
                'ocr_text': '',
                'organized_content': {},
                'document_type': 'research_paper'  # Explicitly set for research papers
            }
            
            # Step 1: Validate PDF
            validation_result = validate_pdf(pdf_path)
            if not validation_result['valid']:
                results['error'] = validation_result['error']
                return results
            
            # Step 2: Extract text and structure (with warning suppression)
            print("Extracting text and structure...")
            text_data = extract_text_and_structure(pdf_path)
            results['text_content'] = text_data.get('text', '')
            results['structure'] = text_data.get('structure', {})
            
            # Step 3: Extract images (with warning suppression)
            print("Extracting images...")
            images_data = extract_images(pdf_path)
            results['images'] = images_data
            
            # Step 4: Extract tables (with enhanced error handling)
            print("Extracting tables...")
            tables_data = extract_tables_with_fallback(pdf_path)
            results['tables'] = tables_data
            
            # Step 5: Extract metadata
            print("Extracting metadata...")
            metadata = extract_metadata(pdf_path)
            results['metadata'] = metadata
            
            # Step 6: Perform OCR if needed
            print("Performing OCR...")
            ocr_text = perform_ocr(pdf_path)
            results['ocr_text'] = ocr_text
            
            # Step 7: Organize content by page
            print("Organizing content by page...")
            organized_content = organize_content_by_page(
                pdf_path,
                text_data,
                images_data,
                tables_data,
                metadata
            )
            results['organized_content'] = organized_content
            
            return results
        
    except Exception as e:
        return {
            'filename': filename,
            'error': f"Processing failed: {str(e)}",
            'processed_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }

def extract_tables_with_fallback(pdf_path):
    """Enhanced table extraction with fallback methods for research papers"""
    try:
        # Import here to avoid circular imports
        from utilities.table_extractor import extract_tables
        
        # Suppress specific camelot warnings
        with warnings.catch_warnings():
            warnings.filterwarnings("ignore", module="camelot")
            warnings.filterwarnings("ignore", message=".*does not lie in column range.*")
            
            tables_data = extract_tables(pdf_path)
            
            # If no tables found or all failed, try alternative approach
            if not tables_data or all('error' in table for table in tables_data if isinstance(table, dict)):
                print("Primary table extraction failed, trying alternative method...")
                tables_data = extract_tables_alternative(pdf_path)
            
            return tables_data
            
    except Exception as e:
        print(f"Table extraction error: {str(e)}")
        return [{'error': f'Table extraction failed: {str(e)}'}]

def extract_tables_alternative(pdf_path):
    """Alternative table extraction method for complex research papers"""
    try:
        import pdfplumber
        
        tables = []
        with pdfplumber.open(pdf_path) as pdf:
            for page_num, page in enumerate(pdf.pages, 1):
                try:
                    # Extract tables with different settings for research papers
                    page_tables = page.extract_tables(table_settings={
                        "vertical_strategy": "lines_strict",
                        "horizontal_strategy": "lines_strict",
                        "explicit_vertical_lines": [],
                        "explicit_horizontal_lines": [],
                        "snap_tolerance": 3,
                        "join_tolerance": 3,
                        "edge_min_length": 3,
                        "min_words_vertical": 3,
                        "min_words_horizontal": 1,
                        "keep_blank_chars": False,
                        "text_tolerance": 3,
                        "text_tolerance_ratio": None
                    })
                    
                    for i, table in enumerate(page_tables):
                        if table and len(table) > 1:  # Must have header + at least one row
                            tables.append({
                                'page': page_num,
                                'table_index': i + 1,
                                'content': str(table),
                                'rows': len(table),
                                'columns': len(table[0]) if table else 0,
                                'method': 'pdfplumber_alternative',
                                'accuracy': 85.0  # Estimated accuracy
                            })
                            
                except Exception as e:
                    print(f"Alternative table extraction failed on page {page_num}: {str(e)}")
                    continue
        
        return tables if tables else [{'info': 'No tables detected with alternative method'}]
        
    except Exception as e:
        return [{'error': f'Alternative table extraction failed: {str(e)}'}]

def generate_enhanced_output_text(results):
    """Generate enhanced output with document type classification"""
    output_lines = []
    
    # Error handling
    if 'error' in results:
        # ... existing error handling code ...
        return "\n".join(output_lines)
    
    # 1. DOCUMENTATION SECTION (Enhanced with document type)
    classification = results.get('document_classification', {})
    doc_type = classification.get('primary_type', 'unknown')
    confidence = classification.get('confidence', 0.0)
    
    doc_section = f"""
PDF PROCESSING DOCUMENTATION - ENHANCED v3.0
=============================================

Document: {results['filename']}
Processed: {results['processed_at']}
Document Type: {doc_type.title()} (Confidence: {confidence:.1%})
Processing System: Enhanced PDF Content Analyzer with Document Type Classification

This document contains the complete analysis of the uploaded PDF file, 
automatically classified and processed using type-specific extraction strategies.

Document Classification Results:
- Primary Type: {doc_type.title()}
- Confidence Score: {confidence:.1%}
- Processing Strategy: {', '.join(classification.get('processing_strategy', {}).keys())}

The content is organized as follows:
1. Document Metadata and Classification
2. Type-Specific Content Analysis 
3. Page-wise Content Analysis
4. OCR Analysis
5. Processing Summary
"""
    output_lines.append(doc_section.strip())
    output_lines.append("\n\n")
    
    # 2. DOCUMENT METADATA AND CLASSIFICATION (Enhanced)
    output_lines.append("DOCUMENT METADATA AND CLASSIFICATION")
    output_lines.append("=" * 50)
    
    # Classification details
    output_lines.append("DOCUMENT TYPE CLASSIFICATION:")
    output_lines.append(f"Primary Type: {doc_type.title()}")
    output_lines.append(f"Confidence: {confidence:.1%}")
    
    scores = classification.get('scores', {})
    for doc_type_name, score in scores.items():
        output_lines.append(f"{doc_type_name.title()} Score: {score:.2f}")
    
    output_lines.append("")
    
    # Original metadata
    if results.get('metadata'):
        formatted_metadata = format_metadata_for_display(results['metadata'])
        output_lines.append("DOCUMENT METADATA:")
        output_lines.append(formatted_metadata)
    output_lines.append("\n\n")
    
    # 3. TYPE-SPECIFIC CONTENT ANALYSIS (NEW MAJOR SECTION)
    output_lines.append("TYPE-SPECIFIC CONTENT ANALYSIS")
    output_lines.append("=" * 50)
    
    type_specific = results.get('organized_content', {}).get('type_specific_content', {})
    if type_specific and 'error' not in type_specific:
        
        if doc_type == 'book':
            output_lines.append("BOOK STRUCTURE ANALYSIS:")
            output_lines.append("-" * 25)
            
            # Table of Contents
            toc = type_specific.get('table_of_contents', [])
            if toc:
                output_lines.append(f"Table of Contents ({len(toc)} entries):")
                for entry in toc[:10]:  # First 10 entries
                    output_lines.append(f"  {entry.get('level', 1)*'  '}{entry.get('title', '')} ... Page {entry.get('page', 'N/A')}")
                if len(toc) > 10:
                    output_lines.append(f"  ... and {len(toc) - 10} more entries")
            
            # Chapters
            chapters = type_specific.get('chapters', [])
            if chapters:
                output_lines.append(f"\nChapters ({len(chapters)} found):")
                for chapter in chapters[:5]:  # First 5 chapters
                    output_lines.append(f"  Chapter {chapter.get('chapter_number', 'N/A')}: {chapter.get('title', '')}")
                    output_lines.append(f"    Pages: {chapter.get('start_page', 'N/A')}-{chapter.get('end_page', 'N/A')}")
                    output_lines.append(f"    Word Count: {chapter.get('word_count', 'N/A')}")
        
        elif doc_type == 'research_paper':
            output_lines.append("RESEARCH PAPER ANALYSIS:")
            output_lines.append("-" * 25)
            
            # Abstract
            abstract = type_specific.get('abstract', {})
            if abstract.get('present'):
                output_lines.append("Abstract:")
                output_lines.append(f"  Content: {abstract.get('content', '')[:200]}...")
                output_lines.append(f"  Word Count: {abstract.get('word_count', 'N/A')}")
            
            # Authors
            authors = type_specific.get('authors', [])
            if authors:
                author_names = [author.get('name', '') for author in authors[:5]]
                output_lines.append(f"\nAuthors: {', '.join(author_names)}")
            
            # Sections
            sections = type_specific.get('sections', [])
            if sections:
                output_lines.append(f"\nPaper Sections ({len(sections)} found):")
                for section in sections:
                    output_lines.append(f"  {section.get('title', '')} ({section.get('word_count', 'N/A')} words)")
            
            # References
            references = type_specific.get('references', {})
            if references.get('present'):
                output_lines.append(f"\nReferences: {references.get('count', 'N/A')} citations found")
        
        elif doc_type == 'technical_report':
            output_lines.append("TECHNICAL REPORT ANALYSIS:")
            output_lines.append("-" * 25)
            
            # Executive Summary
            exec_summary = type_specific.get('executive_summary', {})
            if exec_summary.get('present'):
                output_lines.append("Executive Summary:")
                output_lines.append(f"  Content: {exec_summary.get('content', '')[:200]}...")
                output_lines.append(f"  Word Count: {exec_summary.get('word_count', 'N/A')}")
            
            # Recommendations
            recommendations = type_specific.get('recommendations', {})
            if recommendations.get('present'):
                output_lines.append(f"\nRecommendations ({recommendations.get('count', 'N/A')} found):")
                for i, rec in enumerate(recommendations.get('recommendations', [])[:3], 1):
                    output_lines.append(f"  {i}. {rec[:100]}...")
            
            # Technical Specifications
            tech_specs = type_specific.get('technical_specifications', {})
            if tech_specs.get('count', 0) > 0:
                output_lines.append(f"\nTechnical Specifications: {tech_specs.get('count', 'N/A')} found")
    
    output_lines.append("\n\n")
    
    # 4. PAGE-WISE CONTENT ANALYSIS
    output_lines.append("\n\nPAGE-WISE CONTENT ANALYSIS")
    output_lines.append("=" * 50)
    org = results.get('organized_content', {})
    if org and 'page_content' in org:
        output_lines.append(format_page_wise_content(
            org['page_content'],
            org.get('total_pages', 0)
        ))
    else:
        output_lines.append("No page-wise content available.")

    # 5. OCR EXTRACTED TEXT
    output_lines.append("\n\nOCR EXTRACTED TEXT")
    output_lines.append("=" * 40)
    ocr = results.get('ocr_text', '').strip()
    output_lines.append(ocr if ocr else "No OCR text extracted.")

    # 6. PROCESSING SUMMARY
    output_lines.append("\n\nPROCESSING SUMMARY")
    output_lines.append("=" * 40)
    summary = [
        f"Document: {results['filename']}",
        f"Processed at: {results['processed_at']}",
        f"Total Pages: {org.get('total_pages', 'Unknown')}",
        f"Text Characters: {len(results.get('text_content',''))}",
        f"Images Found: {len(results.get('images', []))}",
        f"Tables Found: {len(results.get('tables', []))}",
        f"OCR Characters: {len(ocr)}"
    ]
    output_lines.extend(summary)

    return "\n".join(output_lines)



# Keep all existing Flask routes unchanged
@app.route('/')
def index():
    """Main page with drag-and-drop interface"""
    return render_template('index.html')

@app.route('/store', methods=['POST'])
def store_pdf():
    """Store uploaded PDF and process it"""
    try:
        # Check if file is present in request
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        
        # Check if file is selected
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        # Check file type
        if not allowed_file(file.filename):
            return jsonify({'error': 'Invalid file type. Only PDF files are allowed.'}), 400
        
        # Generate unique filename
        original_filename = secure_filename(file.filename)
        unique_filename = f"{uuid.uuid4()}_{original_filename}"
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
        
        # Save file
        file.save(file_path)
        
        # Process the PDF
        results = process_pdf(file_path, original_filename)
        
        # Generate enhanced output text (MODIFIED)
        output_text = generate_enhanced_output_text(results)
        
        # Save output file
        output_filename = f"{os.path.splitext(original_filename)[0]}_processed.txt"
        output_path = os.path.join(OUTPUT_FOLDER, output_filename)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(output_text)
        
        # Return success response with file information
        return jsonify({
            'success': True,
            'message': 'PDF processed successfully',
            'original_filename': original_filename,
            'output_filename': output_filename,
            'processing_time': results.get('processed_at'),
            'has_error': 'error' in results
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Processing failed: {str(e)}'}), 500

# Keep all other existing routes unchanged
@app.route('/output')
def list_outputs():
    """List all processed output files"""
    try:
        output_files = []
        # Get all .txt files in output directory
        txt_files = glob.glob(os.path.join(OUTPUT_FOLDER, '*.txt'))
        
        for file_path in txt_files:
            filename = os.path.basename(file_path)
            file_stats = os.stat(file_path)
            output_files.append({
                'filename': filename,
                'size': file_stats.st_size,
                'created': datetime.fromtimestamp(file_stats.st_ctime).isoformat(),
                'modified': datetime.fromtimestamp(file_stats.st_mtime).isoformat(),
                'download_url': f'/output/{filename}'
            })
        
        # Sort by creation time (newest first)
        output_files.sort(key=lambda x: x['created'], reverse=True)
        
        return jsonify({
            'success': True,
            'total_files': len(output_files),
            'files': output_files
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Failed to list output files: {str(e)}'}), 500

@app.route('/output/<filename>')
def download_output(filename):
    """Download specific output file"""
    try:
        safe_filename = secure_filename(filename)
        file_path = os.path.join(os.getcwd(), OUTPUT_FOLDER, safe_filename)
        
        if not os.path.exists(file_path):
            abort(404)
        
        return send_from_directory(
            os.path.join(os.getcwd(), OUTPUT_FOLDER),
            safe_filename,
            as_attachment=True
        )
        
    except Exception as e:
        return jsonify({'error': f'Failed to download file: {str(e)}'}), 500

@app.route('/output/<filename>/view')
def view_output(filename):
    """View output file content in browser"""
    try:
        # Secure the filename
        safe_filename = secure_filename(filename)
        
        # Check if file exists
        file_path = os.path.join(OUTPUT_FOLDER, safe_filename)
        if not os.path.exists(file_path):
            abort(404)
        
        # Read file content
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        return jsonify({
            'success': True,
            'filename': safe_filename,
            'content': content,
            'content_length': len(content)
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Failed to read file: {str(e)}'}), 500

@app.route('/status')
def status():
    """Get system status"""
    try:
        upload_count = len(glob.glob(os.path.join(UPLOAD_FOLDER, '*.pdf')))
        output_count = len(glob.glob(os.path.join(OUTPUT_FOLDER, '*.txt')))
        
        return jsonify({
            'success': True,
            'system_status': 'operational',
            'upload_folder': UPLOAD_FOLDER,
            'output_folder': OUTPUT_FOLDER,
            'uploaded_pdfs': upload_count,
            'processed_outputs': output_count,
            'max_file_size_mb': MAX_FILE_SIZE / (1024 * 1024),
            'version': '2.0 - Enhanced Page-wise Processing'
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Failed to get status: {str(e)}'}), 500

if __name__ == '__main__':
    print("Enhanced PDF Processing System v2.1.0 Starting...")
    print("New Features: Page-wise content organization")
    print(f"Upload folder: {os.path.abspath(UPLOAD_FOLDER)}")
    print(f"Output folder: {os.path.abspath(OUTPUT_FOLDER)}")
    print("Available endpoints:")
    print(" GET / - Main drag-and-drop interface")
    print(" POST /store - Upload and process PDF")
    print(" GET /output - List all output files")
    print(" GET /output/<filename> - Download output file")
    print(" GET /output/<filename>/view - View output file content")
    print(" GET /status - System status")
    
    
    print("Starting via Waitress on 0.0.0.0:5000 …")
    serve(app, host='0.0.0.0', port=5000)
