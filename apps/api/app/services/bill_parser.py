import os
import re
import pytesseract
from PIL import Image
from pdf2image import convert_from_path

def extract_text(file_path: str) -> str:
    """
    Extracts text from an image or PDF using Tesseract OCR.
    If PDF, converts to images first.
    """
    ext = os.path.splitext(file_path)[1].lower()
    text = ""
    
    if ext == ".pdf":
        pages = convert_from_path(file_path)
        for page in pages:
            text += pytesseract.image_to_string(page) + "\n"
    else:
        image = Image.open(file_path)
        text = pytesseract.image_to_string(image)
        
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
