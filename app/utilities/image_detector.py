import fitz  # PyMuPDF
import os
from PIL import Image
from typing import List, Dict, Any
import io

def extract_images(pdf_path: str) -> List[Dict[str, Any]]:
    """
    Extract all images from PDF and return metadata
    """
    images_info = []
    
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
                    image_ext = base_image["ext"]
                    
                    # Get image properties
                    image_obj = Image.open(io.BytesIO(image_bytes))
                    width, height = image_obj.size
                    
                    # Generate description
                    description = generate_image_description(image_obj, width, height)
                    
                    image_info = {
                        'page': page_num + 1,
                        'index': img_index + 1,
                        'format': image_ext,
                        'size': f"{width}x{height}",
                        'width': width,
                        'height': height,
                        'file_size': len(image_bytes),
                        'description': description,
                        'xref': xref
                    }
                    
                    images_info.append(image_info)
                    
                except Exception as e:
                    # Log error but continue processing
                    error_info = {
                        'page': page_num + 1,
                        'index': img_index + 1,
                        'error': f"Failed to extract image: {str(e)}"
                    }
                    images_info.append(error_info)
        
        doc.close()
        return images_info
        
    except Exception as e:
        return [{'error': f"Image extraction failed: {str(e)}"}]

def generate_image_description(image_obj: Image.Image, width: int, height: int) -> str:
    """
    Generate a basic description of the image
    """
    try:
        # Basic image analysis
        aspect_ratio = width / height
        total_pixels = width * height
        
        # Determine image characteristics
        size_category = "small" if total_pixels < 50000 else "medium" if total_pixels < 500000 else "large"
        
        orientation = "landscape" if aspect_ratio > 1.3 else "portrait" if aspect_ratio < 0.7 else "square"
        
        # Try to get color information
        try:
            colors = image_obj.getcolors(maxcolors=256)
            if colors:
                dominant_colors = len(colors)
                color_desc = f"with {dominant_colors} dominant colors"
            else:
                color_desc = "with complex color palette"
        except:
            color_desc = ""
        
        # Check if image might be a chart/graph (high contrast, geometric)
        try:
            # Convert to grayscale for analysis
            gray_image = image_obj.convert('L')
            # Simple heuristic: if image has very few colors, might be a chart
            if colors and len(colors) < 10:
                content_type = "possibly a chart, diagram, or logo"
            else:
                content_type = "photographic or complex image"
        except:
            content_type = "image"
        
        return f"{size_category.title()} {orientation} {content_type} ({width}x{height} pixels) {color_desc}".strip()
        
    except Exception as e:
        return f"Image analysis failed: {str(e)}"

def detect_image_content_type(image_obj: Image.Image) -> str:
    """
    Simple heuristic to detect image content type
    """
    try:
        width, height = image_obj.size
        
        # Convert to grayscale for analysis
        gray_image = image_obj.convert('L')
        
        # Get histogram
        histogram = gray_image.histogram()
        
        # Simple analysis
        total_pixels = width * height
        
        # Check for high contrast (charts/diagrams tend to have high contrast)
        dark_pixels = sum(histogram[:85])  # Dark pixels
        light_pixels = sum(histogram[170:])  # Light pixels
        contrast_ratio = (dark_pixels + light_pixels) / total_pixels
        
        if contrast_ratio > 0.7:
            return "chart/diagram/text"
        else:
            return "photograph/illustration"
            
    except Exception:
        return "unknown"

def save_extracted_images(pdf_path: str, output_dir: str = "extracted_images") -> List[str]:
    """
    Save extracted images to disk (optional utility)
    """
    saved_files = []
    
    try:
        os.makedirs(output_dir, exist_ok=True)
        doc = fitz.open(pdf_path)
        pdf_name = os.path.splitext(os.path.basename(pdf_path))[0]
        
        for page_num in range(len(doc)):
            page = doc[page_num]
            image_list = page.get_images(full=True)
            
            for img_index, img in enumerate(image_list):
                try:
                    xref = img[0]
                    base_image = doc.extract_image(xref)
                    image_bytes = base_image["image"]
                    image_ext = base_image["ext"]
                    
                    # Create filename
                    filename = f"{pdf_name}_page{page_num+1}_img{img_index+1}.{image_ext}"
                    filepath = os.path.join(output_dir, filename)
                    
                    # Save image
                    with open(filepath, "wb") as image_file:
                        image_file.write(image_bytes)
                    
                    saved_files.append(filepath)
                    
                except Exception as e:
                    print(f"Failed to save image: {str(e)}")
        
        doc.close()
        return saved_files
        
    except Exception as e:
        print(f"Image saving failed: {str(e)}")
        return saved_files
