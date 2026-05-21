import asyncio
from typing import Optional
from loguru import logger
from pymongo import AsyncMongoClient, uri_parser
from app.core.config import settings
from fastapi import Request


class MongoManager:
    """
    Quản lý MongoDB client (Async) dùng chung cho toàn bộ ứng dụng.
    Thiết kế để khởi tạo pool một lần duy nhất.
    """
    def __init__(self):
        self.client: Optional[AsyncMongoClient] = None
        self.db_name: str = settings.DATABASE_NAME

    async def connect(self):
        """Kết nối tới MongoDB với cơ chế retry."""
        attempt = 0
        while attempt < settings.MONGODB_MAX_RETRIES:
            try:
                attempt += 1
                client = AsyncMongoClient(
                    settings.MONGODB_URL,
                    minPoolSize=settings.MIN_POOL_SIZE,
                    maxPoolSize=settings.MAX_POOL_SIZE,
                    serverSelectionTimeoutMS=5000,
                )
                await client.admin.command("ping")
                
                self.client = client
                parsed = uri_parser.parse_uri(settings.MONGODB_URL)
                safe_url = f"{parsed['nodelist'][0][0]}:{parsed['nodelist'][0][1]}"
                logger.info(f"Đã kết nối MongoDB tại {safe_url} (Pool: {settings.MIN_POOL_SIZE}-{settings.MAX_POOL_SIZE})")
                return
            except Exception as e:
                if attempt >= settings.MONGODB_MAX_RETRIES:
                    logger.error(f"Thất bại kết nối MongoDB sau {attempt} lần thử: {e}")
                    raise
                logger.warning(f"Lần thử {attempt} thất bại, thử lại sau {settings.MONGODB_RETRY_DELAY}s...")
                await asyncio.sleep(settings.MONGODB_RETRY_DELAY)

    async def close(self):
        """Đóng toàn bộ kết nối trong pool."""
        if self.client:
            await self.client.close()
            self.client = None
            logger.info("Đã đóng kết nối MongoDB.")


# Singleton instance để quản lý lifecycle (dùng trong main.py)
mongo_manager = MongoManager()

async def connect_to_mongo():
    """Wrapper cho main.py lifespan"""
    await mongo_manager.connect()

async def close_mongo_connection():
    """Wrapper cho main.py lifespan"""
    await mongo_manager.close()


def get_database(request: Request = None):
    """
    Dependency cung cấp đối tượng database.
    
    - Nếu được gọi trong một FastAPI request, ưu tiên lấy client từ app.state (Chuẩn Production).
    - Nếu gọi từ Background Task hoặc Worker, fallback về singleton mongo_manager.
    """
    client = None
    if request:
        client = getattr(request.app.state, "mongodb", None)
    
    if client is None:
        client = mongo_manager.client

    if client is None:
        raise RuntimeError("Database chưa được kết nối. Hãy gọi mongo_manager.connect() trong lifespan.")
        
    return client[settings.DATABASE_NAME]


def get_client(request: Request = None):
    """Trả về MongoDB client (dùng chung pool)."""
    client = None
    if request:
        client = getattr(request.app.state, "mongodb", None)
    
    if client is None:
        client = mongo_manager.client

    if client is None:
        raise RuntimeError("Database chưa được kết nối.")
    return client
