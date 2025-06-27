from flask import Flask, request, jsonify, render_template, send_from_directory, abort
import os
import glob
import uuid
from datetime import datetime
from werkzeug.utils import secure_filename
from validators import validate_pdf
from utilities.pdf_parser import extract_text_and_structure
from utilities.image_detector import extract_images
from utilities.table_extractor import extract_tables
from utilities.metadata_extractor import extract_metadata
from utilities.ocr import perform_ocr

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

def process_pdf(pdf_path, filename):
    """Process a single PDF file through all utilities"""
    try:
        print(f"Processing {filename}...")
        
        # Initialize results dictionary
        results = {
            'filename': filename,
            'processed_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'text_content': '',
            'structure': {},
            'images': [],
            'tables': [],
            'metadata': {},
            'ocr_text': ''
        }
        
        # Step 1: Validate PDF
        validation_result = validate_pdf(pdf_path)
        if not validation_result['valid']:
            results['error'] = validation_result['error']
            return results
        
        # Step 2: Extract text and structure
        print("Extracting text and structure...")
        text_data = extract_text_and_structure(pdf_path)
        results['text_content'] = text_data.get('text', '')
        results['structure'] = text_data.get('structure', {})
        
        # Step 3: Extract images
        print("Extracting images...")
        images_data = extract_images(pdf_path)
        results['images'] = images_data
        
        # Step 4: Extract tables
        print("Extracting tables...")
        tables_data = extract_tables(pdf_path)
        results['tables'] = tables_data
        
        # Step 5: Extract metadata
        print("Extracting metadata...")
        metadata = extract_metadata(pdf_path)
        results['metadata'] = metadata
        
        # Step 6: Perform OCR if needed
        print("Performing OCR...")
        ocr_text = perform_ocr(pdf_path)
        results['ocr_text'] = ocr_text
        
        return results
        
    except Exception as e:
        return {
            'filename': filename,
            'error': f"Processing failed: {str(e)}",
            'processed_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }

def generate_output_text(results):
    """Generate comprehensive text output from processing results"""
    output_lines = []
    
    # Header
    output_lines.append("=" * 80)
    output_lines.append(f"PDF PROCESSING RESULTS: {results['filename']}")
    output_lines.append(f"Processed at: {results['processed_at']}")
    output_lines.append("=" * 80)
    output_lines.append("")
    
    # Error handling
    if 'error' in results:
        output_lines.append(f"ERROR: {results['error']}")
        return "\n".join(output_lines)
    
    # Metadata section
    if results.get('metadata'):
        output_lines.append("DOCUMENT METADATA:")
        output_lines.append("-" * 40)
        for key, value in results['metadata'].items():
            if value:
                output_lines.append(f"{key.title()}: {value}")
        output_lines.append("")
    
    # Document structure
    if results.get('structure'):
        output_lines.append("DOCUMENT STRUCTURE:")
        output_lines.append("-" * 40)
        structure = results['structure']
        output_lines.append(f"Total Pages: {structure.get('total_pages', 'Unknown')}")
        
        if 'headings' in structure:
            output_lines.append("Headings Found:")
            for heading in structure['headings']:
                output_lines.append(f"  - {heading}")
        output_lines.append("")
    
    # Images section
    if results.get('images'):
        output_lines.append("EXTRACTED IMAGES:")
        output_lines.append("-" * 40)
        for i, img_info in enumerate(results['images'], 1):
            output_lines.append(f"Image {i}:")
            output_lines.append(f"  Page: {img_info.get('page', 'Unknown')}")
            output_lines.append(f"  Size: {img_info.get('size', 'Unknown')}")
            output_lines.append(f"  Format: {img_info.get('format', 'Unknown')}")
            if img_info.get('description'):
                output_lines.append(f"  Description: {img_info['description']}")
        output_lines.append("")
    
    # Tables section
    if results.get('tables'):
        output_lines.append("EXTRACTED TABLES:")
        output_lines.append("-" * 40)
        for i, table_info in enumerate(results['tables'], 1):
            output_lines.append(f"Table {i}:")
            output_lines.append(f"  Page: {table_info.get('page', 'Unknown')}")
            output_lines.append(f"  Dimensions: {table_info.get('shape', 'Unknown')}")
            output_lines.append(f"  Accuracy: {table_info.get('accuracy', 'Unknown')}%")
            
            if 'content' in table_info:
                output_lines.append("  Content Summary:")
                content = table_info['content']
                if isinstance(content, str):
                    preview = content[:200] + "..." if len(content) > 200 else content
                    output_lines.append(f"    {preview}")
        output_lines.append("")
    
    # Main text content
    if results.get('text_content'):
        output_lines.append("EXTRACTED TEXT CONTENT:")
        output_lines.append("-" * 40)
        output_lines.append(results['text_content'])
        output_lines.append("")
    
    # OCR text (if different from main text)
    if results.get('ocr_text') and results['ocr_text'] != results.get('text_content', ''):
        output_lines.append("OCR EXTRACTED TEXT:")
        output_lines.append("-" * 40)
        output_lines.append(results['ocr_text'])
        output_lines.append("")
    
    # Summary
    output_lines.append("PROCESSING SUMMARY:")
    output_lines.append("-" * 40)
    output_lines.append(f"Text Length: {len(results.get('text_content', ''))} characters")
    output_lines.append(f"Images Found: {len(results.get('images', []))}")
    output_lines.append(f"Tables Found: {len(results.get('tables', []))}")
    output_lines.append(f"OCR Length: {len(results.get('ocr_text', ''))} characters")
    
    return "\n".join(output_lines)

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
        
        # Generate output text
        output_text = generate_output_text(results)
        
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
        
        # Use positional arguments instead of named parameters
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
            'max_file_size_mb': MAX_FILE_SIZE / (1024 * 1024)
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Failed to get status: {str(e)}'}), 500

if __name__ == '__main__':
    print("Enhanced PDF Processing System Starting...")
    print(f"Upload folder: {os.path.abspath(UPLOAD_FOLDER)}")
    print(f"Output folder: {os.path.abspath(OUTPUT_FOLDER)}")
    print("Available endpoints:")
    print("  GET  / - Main drag-and-drop interface")
    print("  POST /store - Upload and process PDF")
    print("  GET  /output - List all output files")
    print("  GET  /output/<filename> - Download output file")
    print("  GET  /output/<filename>/view - View output file content")
    print("  GET  /status - System status")
    
    app.run(debug=True, host='0.0.0.0', port=5000)
