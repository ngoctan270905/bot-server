import asyncio
import json
from loguru import logger
from app.core.config import settings
from app.db.mongodb import mongo_manager
from app.db.redis import redis_manager
from app.repositories.social_repository import SocialPageRepository
from app.repositories.customer_repository import CustomerRepository
from app.repositories.conversation_repository import ConversationRepository
from app.services.telegram_service import TelegramService
from app.services.social_service import SocialService
from app.consumers.telegram_consumer import TelegramMessageConsumer
from app.consumers.facebook_consumer import FacebookMessageConsumer

async def start_listener():
    """
    Lắng nghe toàn bộ Redis Streams (Telegram, Facebook...) dùng cơ chế Consumer Group chuẩn.
    """
    # 1. Khởi tạo Repositories & Services sau khi DB đã kết nối
    db = mongo_manager.client[settings.DATABASE_NAME]
    social_repo = SocialPageRepository(db["SocialPage"])
    customer_repo = CustomerRepository(db["Customer"])
    conversation_repo = ConversationRepository(db["Conversation"])
    telegram_service = TelegramService(social_repo)
    social_service = SocialService(social_repo)

    # 2. Khởi tạo các Consumer kế thừa từ RedisStreamConsumer
    # Mỗi consumer sẽ tự động lo việc: Tạo group, Đọc tin mới, và Cứu hộ tin kẹt (XCLAIM)
    tele_consumer = TelegramMessageConsumer(
        redis_manager.client,
        social_repo, customer_repo, conversation_repo, telegram_service,
        consumer_name="PYTHON_TELEGRAM_WORKER_1"
    )

    fb_consumer = FacebookMessageConsumer(
        redis_manager.client,
        social_repo, customer_repo, conversation_repo, social_service,
        consumer_name="PYTHON_FACEBOOK_WORKER_1"
    )

    # 3. Bắt đầu lắng nghe
    logger.info("Starting Stream Consumers with Self-Healing capabilities...")
    await tele_consumer.start()
    await fb_consumer.start()

    # Giữ cho task này sống mãi để duy trì các loop bên trong consumers
    while True:
        await asyncio.sleep(3600)
