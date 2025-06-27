import pytesseract
import fitz  # PyMuPDF
from PIL import Image
import io
import cv2
import numpy as np
from typing import List, Dict, Any, Optional

def perform_ocr(pdf_path: str) -> str:
    """
    Perform OCR on PDF pages to extract text from images and scanned content
    """
    try:
        # First, check if PDF already has extractable text
        text_content = extract_existing_text(pdf_path)
        
        if has_sufficient_text(text_content):
            # PDF already has sufficient text, OCR may not be necessary
            return f"[OCR Note: PDF contains extractable text, OCR may be redundant]\n\n{text_content}"
        
        # Perform OCR on PDF pages
        ocr_text = extract_text_via_ocr(pdf_path)
        
        if ocr_text.strip():
            return ocr_text
        else:
            return "[OCR Note: No text could be extracted via OCR]"
            
    except Exception as e:
        return f"[OCR Error: {str(e)}]"

def extract_existing_text(pdf_path: str) -> str:
    """
    Extract existing text from PDF to determine if OCR is needed
    """
    try:
        doc = fitz.open(pdf_path)
        text = ""
        
        for page in doc:
            text += page.get_text()
        
        doc.close()
        return text.strip()
        
    except Exception:
        return ""

def has_sufficient_text(text: str, min_length: int = 100) -> bool:
    """
    Check if extracted text is sufficient (not a scanned document)
    """
    if not text:
        return False
    
    # Remove whitespace and check length
    clean_text = text.strip()
    return len(clean_text) >= min_length

def extract_text_via_ocr(pdf_path: str) -> str:
    """
    Convert PDF pages to images and perform OCR
    """
    ocr_results = []
    
    try:
        doc = fitz.open(pdf_path)
        
        for page_num in range(len(doc)):
            try:
                page = doc[page_num]
                
                # Convert page to image
                pix = page.get_pixmap(dpi=300)  # High DPI for better OCR
                img_data = pix.pil_tobytes(format="PNG")
                
                # Open with PIL
                image = Image.open(io.BytesIO(img_data))
                
                # Preprocess image for better OCR
                processed_image = preprocess_image_for_ocr(image)
                
                # Perform OCR
                page_text = pytesseract.image_to_string(processed_image, config='--psm 6')
                
                if page_text.strip():
                    ocr_results.append(f"--- OCR Page {page_num + 1} ---")
                    ocr_results.append(page_text.strip())
                
            except Exception as e:
                ocr_results.append(f"--- OCR Page {page_num + 1} (Error) ---")
                ocr_results.append(f"OCR failed for this page: {str(e)}")
        
        doc.close()
        return "\n\n".join(ocr_results)
        
    except Exception as e:
        return f"OCR processing failed: {str(e)}"

def preprocess_image_for_ocr(image: Image.Image) -> Image.Image:
    """
    Preprocess image to improve OCR accuracy
    """
    try:
        # Convert PIL image to OpenCV format
        cv_image = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
        
        # Convert to grayscale
        gray = cv2.cvtColor(cv_image, cv2.COLOR_BGR2GRAY)
        
        # Apply denoising
        denoised = cv2.fastNlMeansDenoising(gray)
        
        # Apply adaptive thresholding
        thresh = cv2.adaptiveThreshold(
            denoised, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2
        )
        
        # Morphological operations to clean up
        kernel = np.ones((1, 1), np.uint8)
        cleaned = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)
        
        # Convert back to PIL
        processed_image = Image.fromarray(cleaned)
        
        return processed_image
        
    except Exception:
        # If preprocessing fails, return original image
        return image

def extract_text_from_images_in_pdf(pdf_path: str) -> List[Dict[str, Any]]:
    """
    Extract text specifically from images within the PDF
    """
    image_texts = []
    
    try:
        doc = fitz.open(pdf_path)
        
        for page_num in range(len(doc)):
            page = doc[page_num]
            image_list = page.get_images(full=True)
            
            for img_index, img in enumerate(image_list):
                try:
                    # Extract image
                    xref = img[0]
                    base_image = doc.extract_image(xref)
                    image_bytes = base_image["image"]
                    
                    # Convert to PIL Image
                    image = Image.open(io.BytesIO(image_bytes))
                    
                    # Preprocess and OCR
                    processed_image = preprocess_image_for_ocr(image)
                    text = pytesseract.image_to_string(processed_image)
                    
                    if text.strip():
                        image_texts.append({
                            'page': page_num + 1,
                            'image_index': img_index + 1,
                            'text': text.strip(),
                            'confidence': get_ocr_confidence(processed_image)
                        })
                
                except Exception as e:
                    image_texts.append({
                        'page': page_num + 1,
                        'image_index': img_index + 1,
                        'error': f"OCR failed: {str(e)}"
                    })
        
        doc.close()
        return image_texts
        
    except Exception as e:
        return [{'error': f"Image OCR extraction failed: {str(e)}"}]

def get_ocr_confidence(image: Image.Image) -> Optional[float]:
    """
    Get OCR confidence score using pytesseract
    """
    try:
        # Get detailed OCR data
        data = pytesseract.image_to_data(image, output_type=pytesseract.Output.DICT)
        
        # Calculate average confidence
        confidences = [int(conf) for conf in data['conf'] if int(conf) > 0]
        
        if confidences:
            return round(sum(confidences) / len(confidences), 2)
        
        return None
        
    except Exception:
        return None

def is_scanned_pdf(pdf_path: str, text_threshold: int = 50) -> bool:
    """
    Determine if PDF is likely scanned (image-based) rather than text-based
    """
    try:
        doc = fitz.open(pdf_path)
        
        total_text_length = 0
        total_images = 0
        
        for page in doc:
            # Count text
            text = page.get_text()
            total_text_length += len(text.strip())
            
            # Count images
            images = page.get_images()
            total_images += len(images)
        
        doc.close()
        
        # Heuristic: if very little text but many images, likely scanned
        text_per_page = total_text_length / len(doc) if len(doc) > 0 else 0
        images_per_page = total_images / len(doc) if len(doc) > 0 else 0
        
        return text_per_page < text_threshold and images_per_page > 0.5
        
    except Exception:
        return False

def configure_tesseract():
    """
    Configure tesseract settings (call this at startup if needed)
    """
    try:
        # Set tesseract path if needed (uncomment and modify as needed)
        # pytesseract.pytesseract.tesseract_cmd = r'/usr/bin/tesseract'  # Linux
        # pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'  # Windows
        
        # Test if tesseract is available
        version = pytesseract.get_tesseract_version()
        print(f"Tesseract version: {version}")
        return True
        
    except Exception as e:
        print(f"Tesseract configuration error: {str(e)}")
        return False
