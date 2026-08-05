from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str
    redis_url: str
    anthropic_api_key: str | None = None
    whatsapp_access_token: str | None = None
    whatsapp_phone_number_id: str | None = None
    whatsapp_verify_token: str | None = None
    jwt_secret: str = "secret"
    jwt_expires_in_minutes: int = 60
    frontend_origin: str = "http://localhost:5173"
    
    # AWS S3 Storage Settings
    s3_bucket_name: str | None = None
    aws_region: str | None = None
    aws_access_key_id: str | None = None
    aws_secret_access_key: str | None = None
    kms_key_id: str | None = None

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8-sig"
        extra = "ignore"


settings = Settings()