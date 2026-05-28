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
from app.event_handlers.telegram_handler import handle_telegram_message_event
from app.event_handlers.facebook_handler import handle_facebook_message_event

async def start_listener():
    """
    Lắng nghe toàn bộ Redis Streams (Telegram, Facebook...).
    """
    streams_config = {
        "TELEGRAM_MESSAGE_STREAM": "MESSAGE_GROUP",
        "FACEBOOK_MESSAGE_STREAM": "MESSAGE_GROUP"
    }
    consumer_name = "PYTHON_SERVER_CONSUMER_1"

    # 1. Khởi tạo Repositories & Services sau khi DB đã kết nối
    db = mongo_manager.client[settings.DATABASE_NAME]
    social_repo = SocialPageRepository(db["SocialPage"])
    customer_repo = CustomerRepository(db["Customer"])
    conversation_repo = ConversationRepository(db["Conversation"])
    telegram_service = TelegramService(social_repo)
    social_service = SocialService(social_repo)

    # 2. Đảm bảo Consumer Groups tồn tại
    for stream_name, group_name in streams_config.items():
        try:
            await redis_manager.client.xgroup_create(stream_name, group_name, id="0", mkstream=True)
            logger.info(f"Consumer group {group_name} created for stream {stream_name}")
        except Exception:
            # Group already exists
            pass

    logger.info(f"Stream Listener started, listening to: {list(streams_config.keys())}")

    # 3. Vòng lặp lắng nghe Stream
    while True:
        try:
            # Đọc message từ nhiều Redis Stream cùng lúc
            # streams_to_read = { stream_name: ">" }
            streams_to_read = {s: ">" for s in streams_config.keys()}
            
            # Lưu ý: redis-py xreadgroup nhận dict {stream_name: id}
            result = await redis_manager.client.xreadgroup(
                "MESSAGE_GROUP", 
                consumer_name,
                streams_to_read,
                count=5, 
                block=2000
            )

            if not result:
                continue

            # result có dạng: [[stream_name, [(message_id, data), ...]], ...]
            for stream_name_bytes, messages in result:
                stream_name = stream_name_bytes if isinstance(stream_name_bytes, str) else stream_name_bytes.decode()
                
                for message_id, data in messages:
                    try:
                        if stream_name == "TELEGRAM_MESSAGE_STREAM":
                            tele_id = data.get("telebotId")
                            payload = data.get("payload")
                            if tele_id and payload:
                                await handle_telegram_message_event(
                                    tele_id, payload,
                                    social_repo, customer_repo, conversation_repo, telegram_service
                                )

                        elif stream_name == "FACEBOOK_MESSAGE_STREAM":
                            # Định dạng của Facebook : { "message": "{\"type\":..., \"data\":...}" }
                            message_json = data.get("message")
                            if message_json:
                                event_payload = json.loads(message_json)
                                if event_payload.get("type") == "FACEBOOK_MESSAGE":
                                    await handle_facebook_message_event(
                                        event_payload.get("data"),
                                        social_repo, customer_repo, conversation_repo, social_service
                                    )
                        
                        # Ack message sau khi xử lý xong
                        await redis_manager.client.xack(stream_name, "MESSAGE_GROUP", message_id)
                        
                    except Exception as msg_err:
                        logger.error(f"Error processing message {message_id} from {stream_name}: {msg_err}")

        except Exception as e:
            logger.error(f"Listener loop error: {e}")
            await asyncio.sleep(5)
