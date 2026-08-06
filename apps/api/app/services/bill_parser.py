import os
import re
try:
    import pytesseract
    from PIL import Image
    from pdf2image import convert_from_path
    OCR_AVAILABLE = True
except ImportError:
    OCR_AVAILABLE = False

from app.services.storage import storage_service

def extract_text(file_path: str) -> str:
    """
    Extracts text from an image or PDF using Tesseract OCR.
    If PDF, converts to images first.
    """
    if not OCR_AVAILABLE:
        return "OCR is not available (dependencies not installed)."

    ext = os.path.splitext(file_path)[1].lower()
    text = ""
    
    # Download to a temporary file if in S3
    local_path = storage_service.download_to_temp(file_path)
    
    try:
        if ext == ".pdf":
            pages = convert_from_path(local_path)
            for page in pages:
                text += pytesseract.image_to_string(page) + "\n"
        else:
            image = Image.open(local_path)
            text = pytesseract.image_to_string(image)
    finally:
        # Clean up temp file if one was created
        if local_path != file_path and os.path.exists(local_path):
            os.remove(local_path)
            
    return text

def parse_line_items(raw_text: str) -> list[dict]:
    """
    Rule-based line item extractor.
    NOTE: This is a placeholder and will be replaced/augmented 
    by an LLM-based extractor in a later PR.
    """
    items = []
    
    # A simple regex to catch common patterns like "Consultation Fee  $150.00" or "X-Ray  120.50"
    # Looks for some description text followed by a monetary amount at the end of a line.
    pattern = re.compile(r"^(.*?)[\s\$]+([\d\.\,]+)$")
    
    for line in raw_text.splitlines():
        match = pattern.search(line)
        if match:
            description = match.group(1).strip()
            amount_str = match.group(2).replace(",", "")
            
            # Filter out very short/bad matches
            if len(description) < 3:
                continue
                
            try:
                amount = float(amount_str)
                items.append({
                    "description": description,
                    "amount": amount
                })
            except ValueError:
                continue
                
    return items
