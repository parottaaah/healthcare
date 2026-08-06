import os
import uuid
import shutil
import tempfile
import logging
from fastapi import UploadFile
import boto3
from botocore.exceptions import ClientError

from app.core.config import settings

logger = logging.getLogger(__name__)

UPLOAD_DIR = "uploads"

class StorageService:
    def __init__(self, upload_dir: str = UPLOAD_DIR):
        self.upload_dir = upload_dir
        self.s3_bucket = settings.s3_bucket_name
        self.s3_client = None
        
        if self.s3_bucket:
            s3_kwargs = {}
            if settings.aws_region:
                s3_kwargs["region_name"] = settings.aws_region
            if settings.aws_access_key_id:
                s3_kwargs["aws_access_key_id"] = settings.aws_access_key_id
            if settings.aws_secret_access_key:
                s3_kwargs["aws_secret_access_key"] = settings.aws_secret_access_key
                
            self.s3_client = boto3.client('s3', **s3_kwargs)
            logger.info(f"Initialized S3 storage with bucket: {self.s3_bucket}")
        else:
            logger.warning("S3 not configured, using local disk storage — do not use in production")
            os.makedirs(self.upload_dir, exist_ok=True)

    def _get_encryption_args(self) -> dict:
        if settings.kms_key_id:
            return {"ServerSideEncryption": "aws:kms", "SSEKMSKeyId": settings.kms_key_id}
        return {"ServerSideEncryption": "AES256"}

    def save(self, file: UploadFile) -> str:
        """Saves a file to S3 or local storage and returns its path/key."""
        ext = os.path.splitext(file.filename)[1] if file.filename else ""
        unique_name = f"{uuid.uuid4()}{ext}"
        
        if self.s3_bucket and self.s3_client:
            # Upload to S3
            extra_args = self._get_encryption_args()
            if file.content_type:
                extra_args["ContentType"] = file.content_type
                
            self.s3_client.upload_fileobj(
                file.file,
                self.s3_bucket,
                unique_name,
                ExtraArgs=extra_args
            )
            return unique_name
        else:
            # Local fallback
            file_path = os.path.join(self.upload_dir, unique_name)
            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
            return file_path

    def save_bytes(self, content: bytes, ext: str = ".jpg") -> str:
        """Saves raw bytes to S3 or local storage."""
        unique_name = f"{uuid.uuid4()}{ext}"
        
        if self.s3_bucket and self.s3_client:
            extra_args = self._get_encryption_args()
            self.s3_client.put_object(
                Bucket=self.s3_bucket,
                Key=unique_name,
                Body=content,
                **extra_args
            )
            return unique_name
        else:
            file_path = os.path.join(self.upload_dir, unique_name)
            with open(file_path, "wb") as f:
                f.write(content)
            return file_path

    def get_presigned_url(self, file_path: str, expires_in: int = 300) -> str:
        """Returns a presigned URL for an S3 object, or the local path if S3 is not used."""
        if self.s3_bucket and self.s3_client and not file_path.startswith(self.upload_dir):
            try:
                response = self.s3_client.generate_presigned_url(
                    'get_object',
                    Params={'Bucket': self.s3_bucket, 'Key': file_path},
                    ExpiresIn=expires_in
                )
                return response
            except ClientError as e:
                logger.error(f"Error generating presigned URL: {e}")
                return ""
        else:
            return file_path
            
    def download_to_temp(self, file_path: str) -> str:
        """Downloads an object from S3 to a temporary file, or returns the local path."""
        if self.s3_bucket and self.s3_client and not file_path.startswith(self.upload_dir):
            ext = os.path.splitext(file_path)[1]
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=ext)
            temp_file.close()
            
            try:
                self.s3_client.download_file(self.s3_bucket, file_path, temp_file.name)
                return temp_file.name
            except ClientError as e:
                logger.error(f"Error downloading file from S3: {e}")
                if os.path.exists(temp_file.name):
                    os.remove(temp_file.name)
                raise
        else:
            return file_path

storage_service = StorageService()
