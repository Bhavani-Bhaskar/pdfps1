# ocr.py

import pytesseract
import fitz  # PyMuPDF
from PIL import Image
import io
import cv2
import numpy as np
import re
from typing import List, Dict, Any, Optional

def perform_ocr(pdf_path: str) -> str:
    """
    Perform OCR on PDF pages using enhanced pipeline:
      1. Extract existing text; skip OCR if sufficient.
      2. Convert pages to images, deskew, preprocess.
      3. Try multiple PSMs and engine modes; select best by confidence.
    """
    try:
        # Phase 1: existing text check
        text_content = extract_existing_text(pdf_path)
        if has_sufficient_text(text_content, min_length=200):
            return f"[OCR Note: PDF contains sufficient extractable text]\n\n{text_content}"

        # Phase 2: OCR on images
        doc = fitz.open(pdf_path)
        ocr_results = []
        for page_num in range(len(doc)):
            page = doc[page_num]
            pix = page.get_pixmap(dpi=300)
            img = Image.open(io.BytesIO(pix.pil_tobytes(format="PNG")))
            # Deskew
            img = _deskew_image(img)
            # Advanced preprocess
            proc = preprocess_image_for_ocr(img)
            # Multi-psm OCR
            text, conf = _multi_psm_ocr(proc)
            if text.strip():
                ocr_results.append(f"--- OCR Page {page_num+1} (conf={conf:.1f}) ---")
                ocr_results.append(text.strip())
        doc.close()
        return "\n\n".join(ocr_results) if ocr_results else "[OCR Note: No text extracted via OCR]"
    except Exception as e:
        return f"[OCR Error: {str(e)}]"

def extract_existing_text(pdf_path: str) -> str:
    """
    Extract existing digital text from PDF pages.
    """
    try:
        doc = fitz.open(pdf_path)
        text = "".join(page.get_text() for page in doc)
        doc.close()
        return text.strip()
    except Exception:
        return ""

def has_sufficient_text(text: str, min_length: int = 100) -> bool:
    """
    Determine if extracted text meets the minimum length threshold.
    """
    return bool(text and len(text.strip()) >= min_length)

def extract_text_via_ocr(pdf_path: str) -> str:
    """
    Fallback OCR: simple single-psm pipeline (deprecated).
    """
    return perform_ocr(pdf_path)  # unified in perform_ocr

def preprocess_image_for_ocr(image: Image.Image) -> Image.Image:
    """
    Enhance image for OCR: grayscale, denoise, CLAHE, adaptive threshold.
    """
    try:
        cv_img = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
        gray = cv2.cvtColor(cv_img, cv2.COLOR_BGR2GRAY)
        # CLAHE contrast
        clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8,8))
        gray = clahe.apply(gray)
        # Denoise
        gray = cv2.bilateralFilter(gray, 9, 75, 75)
        # Threshold
        th = cv2.adaptiveThreshold(gray,255,cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                   cv2.THRESH_BINARY,11,2)
        # Clean
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT,(2,2))
        clean = cv2.morphologyEx(th, cv2.MORPH_CLOSE, kernel)
        return Image.fromarray(clean)
    except Exception:
        return image

def extract_text_from_images_in_pdf(pdf_path: str) -> List[Dict[str, Any]]:
    """
    Extract text from embedded images, with confidence.
    """
    results = []
    try:
        doc = fitz.open(pdf_path)
        for pnum in range(len(doc)):
            page = doc[pnum]
            for idx, img in enumerate(page.get_images(full=True), start=1):
                try:
                    xref = img[0]
                    base = doc.extract_image(xref)
                    im = Image.open(io.BytesIO(base["image"]))
                    proc = preprocess_image_for_ocr(im)
                    txt = pytesseract.image_to_string(proc, config='--psm 6')
                    conf = get_ocr_confidence(proc)
                    if txt.strip():
                        results.append({'page':pnum+1,'image_index':idx,'text':txt.strip(),'confidence':conf})
                except Exception as e:
                    results.append({'page':pnum+1,'image_index':idx,'error':str(e)})
        doc.close()
    except Exception as e:
        results = [{'error':str(e)}]
    return results

def get_ocr_confidence(image: Image.Image) -> Optional[float]:
    """
    Compute average confidence of OCR using pytesseract image_to_data.
    """
    try:
        data = pytesseract.image_to_data(image, output_type=pytesseract.Output.DICT)
        confs = [int(c) for c in data['conf'] if c.isdigit() and int(c)>0]
        return round(sum(confs)/len(confs),2) if confs else None
    except Exception:
        return None

def is_scanned_pdf(pdf_path: str, text_threshold: int = 50) -> bool:
    """
    Heuristic: PDF likely scanned if little text and many images per page.
    """
    try:
        doc = fitz.open(pdf_path)
        total_text, total_imgs = 0, 0
        for page in doc:
            txt = page.get_text().strip()
            total_text += len(txt)
            total_imgs += len(page.get_images())
        pages = len(doc)
        doc.close()
        return (total_text/pages if pages else 0) < text_threshold and (total_imgs/pages if pages else 0) > 0.5
    except Exception:
        return False

def configure_tesseract():
    """
    Verify and print Tesseract version; set cmd path if needed.
    """
    try:
        # Example: pytesseract.pytesseract.tesseract_cmd = r'/usr/bin/tesseract'
        ver = pytesseract.get_tesseract_version()
        print(f"Tesseract version: {ver}")
        return True
    except Exception as e:
        print(f"Tesseract configuration error: {e}")
        return False

# Internal helpers

def _deskew_image(image: Image.Image) -> Image.Image:
    """
    Detect skew angle via bounding box and rotate to correct[16].
    """
    cv_img = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2GRAY)
    inv = cv2.bitwise_not(cv_img)
    coords = np.column_stack(np.where(inv>0))
    angle = cv2.minAreaRect(coords)[-1]
    if angle < -45: angle = -(90+angle)
    else: angle = -angle
    (h,w) = cv_img.shape
    M = cv2.getRotationMatrix2D((w//2,h//2), angle, 1.0)
    rotated = cv2.warpAffine(np.array(image), M, (w,h),
                             flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)
    return Image.fromarray(rotated)

def _multi_psm_ocr(image: Image.Image) -> tuple[str,float]:
    """
    Try multiple PSMs and OEMs; return best text and confidence[2][8].
    """
    configs = [
        '--oem 1 --psm 6',   # uniform block
        '--oem 1 --psm 3',   # auto page
        '--oem 1 --psm 13',  # raw line
        '--oem 1 --psm 7',   # single line
        '--oem 1 --psm 8',   # single word
    ]
    best_text, best_conf = "", 0.0
    for cfg in configs:
        txt = pytesseract.image_to_string(image, config=cfg)
        conf = get_ocr_confidence(image) or 0.0
        if conf > best_conf:
            best_conf, best_text = conf, txt
    return best_text, best_conf
