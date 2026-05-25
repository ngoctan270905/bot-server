import json
import httpx
from loguru import logger
from app.core.config import settings
from app.db.mongodb import mongo_manager
from app.db.redis import redis_manager
from app.repositories.social_repository import SocialPageRepository
from app.repositories.customer_repository import CustomerRepository
from app.repositories.conversation_repository import ConversationRepository
from app.services.ai.engine import ai_engine
from app.schemas.telegram import TelegramUpdate

class TelegramWorker:
    def __init__(self):
        self.social_repo = SocialPageRepository(mongo_manager.db["SocialPage"])
        self.customer_repo = CustomerRepository(mongo_manager.db["Customer"])
        self.conversation_repo = ConversationRepository(mongo_manager.db["Conversation"])
        self.base_url = "https://api.telegram.org/bot"

    async def send_message(self, bot_token: str, chat_id: int, text: str):
        async with httpx.AsyncClient() as client:
            payload = {
                "chat_id": chat_id,
                "text": text
            }
            response = await client.post(
                f"{self.base_url}{bot_token}/sendMessage",
                json=payload
            )
            if response.status_code != 200:
                logger.error(f"Failed to send Telegram message: {response.text}")

    async def process_update(self, tele_id: str, payload_str: str):
        try:
            update_data = json.loads(payload_str)
            update = TelegramUpdate(**update_data)
            
            if not update.message or not update.message.text:
                return

            # 1. Tìm SocialPage (Bot config)
            social_page = await self.social_repo.get_by_page_id(tele_id)
            if not social_page:
                logger.warning(f"SocialPage not found for tele_id: {tele_id}")
                return

            bot_token = social_page["pageAccessToken"]
            bot_id = social_page["botId"]

            # 2. Tìm hoặc tạo Customer
            customer_cid = str(update.message.from_user.id)
            customer = await self.customer_repo.collection.find_one({
                "cid": customer_cid,
                "socialPageId": social_page["_id"]
            })

            if not customer:
                customer_data = {
                    "cid": customer_cid,
                    "name": update.message.from_user.first_name,
                    "socialPageId": social_page["_id"],
                    "channel": "telegram"
                }
                result = await self.customer_repo.collection.insert_one(customer_data)
                customer = {**customer_data, "_id": result.inserted_id}

            # 3. Tìm hoặc tạo Conversation
            conversation = await self.conversation_repo.collection.find_one({
                "customerId": customer["_id"]
            })

            if not conversation:
                conversation_data = {
                    "customerId": customer["_id"],
                    "botId": bot_id,
                    "channel": "telegram",
                    "autoReply": True
                }
                result = await self.conversation_repo.collection.insert_one(conversation_data)
                conversation = {**conversation_data, "_id": result.inserted_id}

            # 4. Kiểm tra autoReply
            if not conversation.get("autoReply", True):
                # Lưu history rồi thoát (Todo: Push to save_history_queue)
                return

            # 5. Hỏi AI
            response_text = await ai_engine.ask(
                bot_id=str(bot_id),
                question=update.message.text,
                conversation_id=str(conversation["_id"])
            )

            # 6. Gửi lại Telegram
            await self.send_message(bot_token, update.message.chat.id, response_text)

        except Exception as e:
            logger.error(f"Error processing telegram update: {e}")

    async def run_worker(self):
        """
        Infinite loop lắng nghe Redis Stream.
        """
        stream_name = "TELEGRAM_MESSAGE_STREAM"
        group_name = "TELEGRAM_GROUP"
        consumer_name = "TELEGRAM_CONSUMER_1"

        # Tạo Group nếu chưa có
        try:
            await redis_manager.client.xgroup_create(stream_name, group_name, id="0", mkstream=True)
        except Exception:
            pass # Group đã tồn tại

        logger.info(f"Telegram Worker started, listening to {stream_name}...")

        while True:
            try:
                # Đọc tin nhắn từ Stream
                # block=0 nghĩa là đợi vô tận cho đến khi có tin nhắn mới
                streams = await redis_manager.client.xreadgroup(
                    group_name, consumer_name, {stream_name: ">"}, count=1, block=5000
                )

                if not streams:
                    continue

                for stream, messages in streams:
                    for message_id, data in messages:
                        tele_id = data.get("telebotId")
                        payload = data.get("payload")
                        
                        if tele_id and payload:
                            await self.process_update(tele_id, payload)
                        
                        # Ack tin nhắn đã xử lý xong
                        await redis_manager.client.xack(stream_name, group_name, message_id)

            except Exception as e:
                logger.error(f"Telegram Worker loop error: {e}")
                import asyncio
                await asyncio.sleep(5)

telegram_worker = TelegramWorker()
