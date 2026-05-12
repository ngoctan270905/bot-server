import redis.asyncio as redis
from typing import Optional
from loguru import logger
from app.core.config import settings

class RedisManager:
    """
    Quản lý kết nối Redis (Async) dùng cho Caching, Queue và Streams.
    Thiết kế theo dạng Singleton với Connection Pool.
    """
    def __init__(self):
        self._client: Optional[redis.Redis] = None

    async def connect(self):
        """Khởi tạo kết nối Redis pool."""
        if self._client:
            return

        try:
            # Tạo client với connection pool mặc định
            self._client = redis.Redis(
                host=settings.redis.host,
                port=settings.redis.port,
                password=settings.redis.password,
                db=settings.redis.db,
                decode_responses=True, # Tự động chuyển bytes sang string
                encoding="utf-8",
                socket_timeout=5.0,
                retry_on_timeout=True
            )
            # Kiểm tra kết nối bằng lệnh PING
            await self._client.ping()
            logger.bind(context="Redis").info(
                f"Đã kết nối Redis tại {settings.redis.host}:{settings.redis.port} (DB: {settings.redis.db})"
            )
        except Exception as e:
            logger.bind(context="Redis").error(f"Lỗi kết nối Redis: {e}")
            raise

    async def disconnect(self):
        """Đóng toàn bộ kết nối trong pool."""
        if self._client:
            await self._client.close()
            self._client = None
            logger.bind(context="Redis").info("Đã đóng kết nối Redis.")

    @property
    def client(self) -> redis.Redis:
        """Trả về instance redis client (dùng chung pool)."""
        if self._client is None:
            raise RuntimeError("Redis chưa được kết nối. Hãy gọi connect() trong lifespan.")
        return self._client

# Singleton instance dùng cho toàn bộ app
redis_manager = RedisManager()

async def get_redis() -> redis.Redis:
    """Dependency injection cho các FastAPI endpoints."""
    return redis_manager.client
