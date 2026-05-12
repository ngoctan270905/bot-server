from typing import Optional
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

class RedisSettings(BaseSettings):
    host: str = Field("localhost", alias="REDIS_HOST")
    port: int = Field(6379, alias="REDIS_PORT")
    password: Optional[str] = Field(None, alias="REDIS_PASSWORD")
    db: int = Field(0, alias="REDIS_DB")

class AISettings(BaseSettings):
    gemini_key: Optional[str] = Field(None, alias="GGG_AI_API_KEY")
    openai_key: Optional[str] = Field(None, alias="OPENAI_API_KEY")
    jina_key: Optional[str] = Field(None, alias="JINA_API_KEY")
    cohere_key: Optional[str] = Field(None, alias="COHERE_API_KEY")

    # Existing Bot-Server specific AI settings
    gemini_model: str = Field("gemini-1.5-flash", alias="GEMINI_MODEL")
    gemini_timeout: float = Field(30.0, alias="GEMINI_TIMEOUT")
    gemini_max_history: int = Field(20, alias="GEMINI_MAX_HISTORY")

class SocialSettings(BaseSettings):
    # Facebook
    fb_app_id: Optional[str] = Field(None, alias="FACEBOOK_APP_ID")
    fb_redirect_uri: Optional[str] = Field(None, alias="FACEBOOK_REDIRECT_URI")
    fb_app_secret: Optional[str] = Field(None, alias="FACEBOOK_APP_SECRET")
    fb_verify_token: Optional[str] = Field(None, alias="FACEBOOK_WEBHOOK_VERIFY_TOKEN")

    # Zalo
    zalo_app_id: Optional[str] = Field(None, alias="ZALO_APP_ID")
    zalo_redirect_uri: Optional[str] = Field(None, alias="ZALO_REDIRECT_URI")
    zalo_app_secret: Optional[str] = Field(None, alias="ZALO_APP_SECRET")

    # Telegram
    tele_secret_token: Optional[str] = Field(None, alias="TELEGRAM_WEBHOOK_SECRET_TOKEN")

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=True
    )

    # --- Application ---
    PROJECT_NAME: str = Field("Bot Server", alias="PROJECT_NAME")
    API_V1_STR: str = Field("/api/v1", alias="API_V1_STR")
    ENVIRONMENT: str = Field("development", alias="ENVIRONMENT")
    
    # CORS Origins - Có thể cấu hình qua .env: BACKEND_CORS_ORIGINS="http://localhost:3000,https://myapp.com"
    BACKEND_CORS_ORIGINS: list[str] = Field(
        ["http://localhost:5173", "http://localhost:3000"], 
        alias="BACKEND_CORS_ORIGINS"
    )

    @field_validator("BACKEND_CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: str | list[str]) -> list[str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError(v)
    PORT: int = Field(3041, alias="PORT")
    HOST: str = Field("0.0.0.0", alias="HOST")
    DOMAIN_URL: str = Field("http://localhost:3041", alias="DOMAIN_URL")
    FRONTEND_URL: Optional[str] = Field(None, alias="FRONTEND_URL")
    SHOW_DOCS: bool = Field(True, alias="SHOW_DOCS")

    # --- Logging ---
    LOG_LEVEL: str = Field("INFO", alias="LOG_LEVEL")
    LOG_FILE: str = Field("logs/app.log", alias="LOG_FILE")
    LOG_MAX_BYTES: int = Field(10485760, alias="LOG_MAX_BYTES")
    LOG_BACKUP_COUNT: int = Field(7, alias="LOG_BACKUP_COUNT")

    # --- MongoDB ---
    MONGODB_URL: str = Field(..., alias="DATABASE_URI")
    DATABASE_NAME: str = Field(..., alias="DATABASE_NAME")
    MIN_POOL_SIZE: int = Field(10, alias="MIN_POOL_SIZE")
    MAX_POOL_SIZE: int = Field(100, alias="MAX_POOL_SIZE")
    MONGODB_MAX_RETRIES: int = Field(5, alias="MONGODB_MAX_RETRIES")
    MONGODB_RETRY_DELAY: int = Field(2, alias="MONGODB_RETRY_DELAY")

    # --- Redis ---
    redis: RedisSettings = RedisSettings()

    # --- Security ---
    SECRET_KEY: str = Field(..., alias="JWT_SECRET")
    ALGORITHM: str = Field("HS256", alias="ALGORITHM")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(60, alias="ACCESS_TOKEN_EXPIRE_MINUTES")
    REFRESH_TOKEN_EXPIRE_MINUTES: int = Field(43200, alias="REFRESH_TOKEN_EXPIRE_MINUTES") # 30 days

    SALT_ROUNDS: int = Field(10, alias="SALT_ROUNDS")
    HASH_PEPPER: str = Field("pepper", alias="HASH_PEPPER")

    # --- AI ---
    ai: AISettings = AISettings()

    # --- Social ---
    social: SocialSettings = SocialSettings()

    # --- Third Party ---
    STRIPE_SECRET_KEY: Optional[str] = Field(None, alias="STRIPE_SECRET_KEY")
    STRIPE_WEBHOOK_SECRET: Optional[str] = Field(None, alias="STRIPE_WEBHOOK_SECRET")

    SENDGRID_SENDER: Optional[str] = Field(None, alias="SENDGRID_SENDER")
    SENDGRID_API_KEY: Optional[str] = Field(None, alias="SENDGRID_API_KEY")

    SVIX_API_KEY: Optional[str] = Field(None, alias="SVIX_API_KEY")
    SVIX_SERVER_URL: Optional[str] = Field(None, alias="SVIX_SERVER_URL")

    NOTION_CLIENT_ID: Optional[str] = Field(None, alias="NOTION_CLIENT_ID")
    NOTION_CLIENT_SECRET: Optional[str] = Field(None, alias="NOTION_CLIENT_SECRET")

    STATIC_FILES_URL: str = "http://localhost:8000/static"
    UPLOADS_DIR: str = "static/uploads"
    MAX_UPLOAD_SIZE_MB: int = 5
    ALLOWED_IMAGE_TYPES: set[str] = {"image/jpeg", "image/png", "image/webp", "image/gif"}
    ALLOWED_EXTENSIONS: set[str] = {".jpg", ".jpeg", ".png", ".webp", ".gif"}
settings = Settings()
