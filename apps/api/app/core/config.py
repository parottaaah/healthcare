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

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()