import redis.asyncio as redis
from typing import Optional
from loguru import logger
from app.core.config import settings
from arq import create_pool, ArqRedis
from arq.connections import RedisSettings as ArqRedisSettings
from fastapi import Request

class RedisManager:
    """
    Quản lý kết nối Redis (Async) và Arq Pool dùng cho Caching, Queue và History.
    Thiết kế theo dạng Singleton để quản lý tập trung connection pool.
    """
    def __init__(self):
        self._client: Optional[redis.Redis] = None
        self._arq_pool: Optional[ArqRedis] = None

    async def connect(self):
        """Khởi tạo toàn bộ kết nối Redis pools."""
        if self._client and self._arq_pool:
            return

        try:
            # 1. Khởi tạo Redis Client (Dùng cho Cache, Chat History, Rate Limit)
            self._client = redis.Redis.from_url(
                settings.redis.url,
                decode_responses=True,
                encoding="utf-8",
                socket_timeout=5.0,
                retry_on_timeout=True,
                max_connections=100 # Giới hạn pool để bảo vệ server
            )
            await self._client.ping()

            # 2. Khởi tạo Arq Pool (Dùng cho Background Jobs)
            self._arq_pool = await create_pool(ArqRedisSettings(
                host=settings.redis.host,
                port=settings.redis.port,
                password=settings.redis.password,
                database=settings.redis.db
            ))

            logger.bind(context="Redis").info(
                f"Redis & Arq Pools initialized (Host: {settings.redis.host}, DB: {settings.redis.db})"
            )
        except Exception as e:
            logger.bind(context="Redis").error(f"Lỗi khởi tạo Redis Pools: {e}")
            raise

    async def disconnect(self):
        """Đóng toàn bộ kết nối khi shutdown."""
        if self._client:
            await self._client.close()
            self._client = None
        if self._arq_pool:
            await self._arq_pool.close()
            self._arq_pool = None
        logger.bind(context="Redis").info("Đã đóng kết nối Redis & Arq.")

    @property
    def client(self) -> redis.Redis:
        if self._client is None:
            raise RuntimeError("Redis chưa kết nối. Hãy gọi redis_manager.connect() trong lifespan.")
        return self._client

    @property
    def arq_pool(self) -> ArqRedis:
        if self._arq_pool is None:
            raise RuntimeError("Arq pool chưa khởi tạo. Hãy gọi redis_manager.connect() trong lifespan.")
        return self._arq_pool

# Singleton instance
redis_manager = RedisManager()

# --- Helper functions (Idiomatic FastAPI + Fallback for Workers) ---

async def get_redis(request: Request = None) -> redis.Redis:
    """
    Dependency injection cho Redis Client.
    Ưu tiên lấy từ app.state nếu có request context.
    """
    if request:
        redis_service = getattr(request.app.state, "redis", None)
        if redis_service:
            return redis_service.client
            
    return redis_manager.client

def get_arq_pool(request: Request = None) -> ArqRedis:
    """
    Lấy Arq pool để enqueue jobs.
    Ưu tiên lấy từ app.state nếu có request context.
    """
    if request:
        pool = getattr(request.app.state, "arq_pool", None)
        if pool:
            return pool
            
    return redis_manager.arq_pool

def set_arq_pool(pool: ArqRedis):
    """(Deprecated) Giữ lại để tránh lỗi import ở main.py cũ"""
    pass
