import json
from loguru import logger
from app.repositories.social_repository import SocialPageRepository
from app.repositories.customer_repository import CustomerRepository
from app.repositories.conversation_repository import ConversationRepository
from app.services.ai.engine import ai_engine
from app.services.telegram_service import TelegramService
from app.schemas.telegram import TelegramUpdate

async def handle_telegram_message_event(
    tele_id: str, 
    payload_str: str,
    social_repo: SocialPageRepository,
    customer_repo: CustomerRepository,
    conversation_repo: ConversationRepository,
    telegram_service: TelegramService
):
    """
    Xử lý một sự kiện tin nhắn Telegram từ Redis Stream.
    """
    try:
        update_data = json.loads(payload_str)
        update = TelegramUpdate(**update_data)
        
        if not update.message or not update.message.text:
            return

        # 1. Tìm SocialPage
        social_page = await social_repo.get_by_page_id(tele_id)
        if not social_page:
            logger.warning(f"SocialPage not found for tele_id: {tele_id}")
            return

        bot_token = social_page["pageAccessToken"]
        bot_id = social_page["botId"]

        # 2. Tìm hoặc tạo Customer
        customer_cid = str(update.message.from_user.id)
        customer = await customer_repo.collection.find_one({
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
            result = await customer_repo.collection.insert_one(customer_data)
            customer = {**customer_data, "_id": result.inserted_id}

        # 3. Tìm hoặc tạo Conversation
        conversation = await conversation_repo.collection.find_one({
            "customerId": customer["_id"]
        })

        if not conversation:
            conversation_data = {
                "customerId": customer["_id"],
                "botId": bot_id,
                "channel": "telegram",
                "autoReply": True
            }
            result = await conversation_repo.collection.insert_one(conversation_data)
            conversation = {**conversation_data, "_id": result.inserted_id}

        # 4. Kiểm tra autoReply (Nếu tắt thì chỉ lưu history - Todo)
        if not conversation.get("autoReply", True):
            return

        # 5. Hỏi AI
        response_text = await ai_engine.ask(
            bot_id=str(bot_id),
            question=update.message.text,
            conversation_id=str(conversation["_id"])
        )

        # 6. Gửi phản hồi
        await telegram_service.send_message(bot_token, update.message.chat.id, response_text)

    except Exception as e:
        logger.error(f"Error handling telegram message: {e}")
