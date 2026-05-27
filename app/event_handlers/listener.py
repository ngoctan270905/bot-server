import asyncio
from loguru import logger
from app.core.config import settings
from app.db.mongodb import mongo_manager
from app.db.redis import redis_manager
from app.repositories.social_repository import SocialPageRepository
from app.repositories.customer_repository import CustomerRepository
from app.repositories.conversation_repository import ConversationRepository
from app.services.telegram_service import TelegramService
from app.event_handlers.telegram_handler import handle_telegram_message_event

async def start_listener():
    """
    Lắng nghe toàn bộ Redis Streams (Telegram, Facebook...).
    """
    stream_name = "TELEGRAM_MESSAGE_STREAM"
    group_name = "TELEGRAM_GROUP"
    consumer_name = "TELEGRAM_CONSUMER_1"

    # 1. Khởi tạo Repositories & Services sau khi DB đã kết nối
    db = mongo_manager.client[settings.DATABASE_NAME]
    social_repo = SocialPageRepository(db["SocialPage"])
    customer_repo = CustomerRepository(db["Customer"])
    conversation_repo = ConversationRepository(db["Conversation"])
    telegram_service = TelegramService(social_repo)

    # 2. Đảm bảo Consumer Group tồn tại
    try:
        await redis_manager.client.xgroup_create(stream_name, group_name, id="0", mkstream=True)
    except Exception:
        pass

    logger.info(f"Stream Listener started, listening to {stream_name}...")

    # 3. Vòng lặp lắng nghe Stream
    while True:
        try:
            # Đọc message từ Redis Stream theo Consumer Group
            streams = await redis_manager.client.xreadgroup(
                group_name, # nhóm worker (TELEGRAM_GROUP)
                consumer_name, # tên worker hiện tại
                {stream_name: ">"}, # chỉ đọc message MỚI chưa xử lý
                count=1, # mỗi lần lấy 1 message
                block=2000 # nếu không có message thì chờ tối đa 2s
            )

            if not streams:
                continue

            # streams có dạng: [(stream_name, [(message_id, data), ...])]
            for stream, messages in streams:
                for message_id, data in messages:
                    tele_id = data.get("telebotId")
                    payload = data.get("payload")
                    
                    if tele_id and payload:
                        # Gọi Handler tương ứng
                        await handle_telegram_message_event(
                            tele_id, payload,
                            social_repo, customer_repo, conversation_repo, telegram_service
                        )
                    
                    await redis_manager.client.xack(stream_name, group_name, message_id)

        except Exception as e:
            logger.error(f"Listener loop error: {e}")
            await asyncio.sleep(5)
