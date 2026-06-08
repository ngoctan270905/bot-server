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
    Listen to all Redis Streams (Telegram, Facebook, ...) using Consumer Group mechanism.
    """
    # 1. Initialize repositories and services after database connection is established
    db = mongo_manager.client[settings.DATABASE_NAME]
    social_repo = SocialPageRepository(db["SocialPage"])
    customer_repo = CustomerRepository(db["Customer"])
    conversation_repo = ConversationRepository(db["Conversation"])
    telegram_service = TelegramService(social_repo)
    social_service = SocialService(social_repo)

    # 2. Initialize consumers that inherit from RedisStreamConsumer
    # Each consumer automatically handles: group creation, consuming new messages,
    # and recovering pending messages (XCLAIM)
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

    # 3. Start Listening
    logger.info("Starting Stream Consumers with Self-Healing capabilities...")
    await tele_consumer.start()
    await fb_consumer.start()

    # Keep this task alive to maintain internal consumer loops
    while True:
        await asyncio.sleep(3600)
