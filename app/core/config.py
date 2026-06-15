from typing import Optional, List
from pydantic import Field, field_validator, BaseModel, ConfigDict
from pydantic_settings import BaseSettings, SettingsConfigDict

class RedisSettings(BaseModel):
    host: str = Field("localhost", alias="REDIS_HOST")
    port: int = Field(6379, alias="REDIS_PORT")
    password: Optional[str] = Field(None, alias="REDIS_PASSWORD")
    db: int = Field(0, alias="REDIS_DB")
    model_config = ConfigDict(populate_by_name=True)

    @property
    def redis_arq(self):
        from arq.connections import RedisSettings as ArqRedisSettings
        return ArqRedisSettings(
            host=self.host,
            port=self.port,
            password=self.password,
            database=self.db
        )

    @property
    def url(self) -> str:
        if self.password:
            return f"redis://:{self.password}@{self.host}:{self.port}/{self.db}"
        return f"redis://{self.host}:{self.port}/{self.db}"

class AISettings(BaseModel):
    openrouter_key: Optional[str] = Field(None, alias="OPENROUTER_API_KEY")
    gemini_key: Optional[str] = Field(None, alias="GGG_AI_API_KEY")
    openai_key: Optional[str] = Field(None, alias="OPENAI_API_KEY")
    jina_key: Optional[str] = Field(None, alias="JINA_API_KEY")
    cohere_key: Optional[str] = Field(None, alias="COHERE_API_KEY")



    # Bot-Server specific AI settings (Synced with ChatBot-Model)
    embedding_url: str = Field("http://localhost:8081/v1/embeddings", alias="EMBEDDING_URL")
    embedding_model: str = Field("jina-embeddings-v2-base-en", alias="EMBEDDING_MODEL")

    reranker_url: str = Field("http://localhost:8082/v1/rerank", alias="RERANKER_URL")
    reranker_model: str = Field("bge-reranker-v2-m3", alias="RERANKER_MODEL")

    llm_url: str = Field("http://localhost:8080/v1/chat/completions", alias="LLM_URL")
    llm_model: str = Field("gemma-3-1b-it", alias="LLM_MODEL")

    qdrant_url: str = Field("http://localhost:6333", alias="QDRANT_URL")
    qdrant_collection: str = Field("bot_collection", alias="QDRANT_COLLECTION")

    gemini_model: str = Field("gemini-1.5-flash", alias="GEMINI_MODEL")
    gemini_timeout: float = Field(30.0, alias="GEMINI_TIMEOUT")
    gemini_max_history: int = Field(20, alias="GEMINI_MAX_HISTORY")
    model_config = ConfigDict(populate_by_name=True)

class SocialSettings(BaseModel):
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
    model_config = ConfigDict(populate_by_name=True)

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=True,
        populate_by_name=True
    )

    # --- Application ---
    PROJECT_NAME: str = Field("Bot Server", alias="PROJECT_NAME")
    API_V1_STR: str = Field("/api/v1", alias="API_V1_STR")
    ENVIRONMENT: str = Field("development", alias="ENVIRONMENT")

    # CORS Origins
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
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_PASSWORD: Optional[str] = None
    REDIS_DB: int = 0

    @property
    def redis(self) -> RedisSettings:
        return RedisSettings(
            host=self.REDIS_HOST,
            port=self.REDIS_PORT,
            password=self.REDIS_PASSWORD,
            db=self.REDIS_DB
        )

    # --- Security ---
    SECRET_KEY: str = Field(..., alias="JWT_SECRET")
    ALGORITHM: str = Field("HS256", alias="ALGORITHM")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(60, alias="ACCESS_TOKEN_EXPIRE_MINUTES")
    REFRESH_TOKEN_EXPIRE_MINUTES: int = Field(43200, alias="REFRESH_TOKEN_EXPIRE_MINUTES") # 30 days

    SALT_ROUNDS: int = Field(10, alias="SALT_ROUNDS")
    HASH_PEPPER: str = Field("pepper", alias="HASH_PEPPER")

    # --- AI ---
    OPENROUTER_API_KEY: Optional[str] = None
    GGG_AI_API_KEY: Optional[str] = None
    OPENAI_API_KEY: Optional[str] = None
    JINA_API_KEY: Optional[str] = None
    COHERE_API_KEY: Optional[str] = None
    EMBEDDING_URL: str = "http://localhost:8081/v1/embeddings"
    EMBEDDING_MODEL: str = "bge-m3"
    RERANKER_URL: str = "http://localhost:8082/v1/rerank"
    RERANKER_MODEL: str = "bge-reranker-v2-m3"
    LLM_URL: str = "http://localhost:8080/v1/chat/completions"
    LLM_MODEL: str = "gemma-3-1b-it"
    QDRANT_URL: str = "http://localhost:6333"
    QDRANT_COLLECTION: str = "bot_collection"
    GEMINI_MODEL: str = "gemini-1.5-flash"
    GEMINI_TIMEOUT: float = 30.0
    GEMINI_MAX_HISTORY: int = 20

    @property
    def ai(self) -> AISettings:
        return AISettings(
            openrouter_key=self.OPENROUTER_API_KEY,
            gemini_key=self.GGG_AI_API_KEY,
            openai_key=self.OPENAI_API_KEY,
            jina_key=self.JINA_API_KEY,
            cohere_key=self.COHERE_API_KEY,
            embedding_url=self.EMBEDDING_URL,
            embedding_model=self.EMBEDDING_MODEL,
            reranker_url=self.RERANKER_URL,
            reranker_model=self.RERANKER_MODEL,
            llm_url=self.LLM_URL,
            llm_model=self.LLM_MODEL,
            qdrant_url=self.QDRANT_URL,
            qdrant_collection=self.QDRANT_COLLECTION,
            gemini_model=self.GEMINI_MODEL,
            gemini_timeout=self.GEMINI_TIMEOUT,
            gemini_max_history=self.GEMINI_MAX_HISTORY
        )

    # --- Social ---
    FACEBOOK_APP_ID: Optional[str] = None
    FACEBOOK_REDIRECT_URI: Optional[str] = None
    FACEBOOK_APP_SECRET: Optional[str] = None
    FACEBOOK_WEBHOOK_VERIFY_TOKEN: Optional[str] = None
    ZALO_APP_ID: Optional[str] = None
    ZALO_REDIRECT_URI: Optional[str] = None
    ZALO_APP_SECRET: Optional[str] = None
    TELEGRAM_WEBHOOK_SECRET_TOKEN: Optional[str] = None

    @property
    def social(self) -> SocialSettings:
        return SocialSettings(
            fb_app_id=self.FACEBOOK_APP_ID,
            fb_redirect_uri=self.FACEBOOK_REDIRECT_URI,
            fb_app_secret=self.FACEBOOK_APP_SECRET,
            fb_verify_token=self.FACEBOOK_WEBHOOK_VERIFY_TOKEN,
            zalo_app_id=self.ZALO_APP_ID,
            zalo_redirect_uri=self.ZALO_REDIRECT_URI,
            zalo_app_secret=self.ZALO_APP_SECRET,
            tele_secret_token=self.TELEGRAM_WEBHOOK_SECRET_TOKEN
        )

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
