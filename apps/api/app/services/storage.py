import os
import uuid
import shutil
from fastapi import UploadFile

UPLOAD_DIR = "uploads"

class StorageService:
    def __init__(self, upload_dir: str = UPLOAD_DIR):
        self.upload_dir = upload_dir
        os.makedirs(self.upload_dir, exist_ok=True)

    def save(self, file: UploadFile) -> str:
        """Saves a file to local storage and returns its path."""
        ext = os.path.splitext(file.filename)[1] if file.filename else ""
        unique_name = f"{uuid.uuid4()}{ext}"
        file_path = os.path.join(self.upload_dir, unique_name)
        
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
            
        return file_path

    def save_bytes(self, content: bytes, ext: str = ".jpg") -> str:
        """Saves raw bytes to local storage."""
        unique_name = f"{uuid.uuid4()}{ext}"
        file_path = os.path.join(self.upload_dir, unique_name)
        
        with open(file_path, "wb") as f:
            f.write(content)
            
        return file_path

storage_service = StorageService()
