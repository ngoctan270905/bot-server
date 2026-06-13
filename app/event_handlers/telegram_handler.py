import json
import asyncio
from datetime import datetime, timezone
from bson import ObjectId
from loguru import logger

from app.db.redis import get_arq_pool
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
    Handle a Telegram message event received from Redis Stream.
    """
    try:
        update_data = json.loads(payload_str)
        update = TelegramUpdate(**update_data)

        # Ignore non-text messages.
        if not update.message or not update.message.text:
            return

        # Retrieve the associated social page configuration.
        social_page = await social_repo.get_by_page_id(tele_id)
        if not social_page:
            logger.warning(f"SocialPage not found for tele_id: {tele_id}")
            return

        bot_token = social_page["pageAccessToken"]
        bot_id = social_page["botId"]

        # Find or create the customer record.
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
                "channel": "telegram",
                "createdAt": datetime.now(timezone.utc)
            }
            customer = await customer_repo.create(customer_data)

        # Find or create the conversation.
        conversation = await conversation_repo.collection.find_one({
            "customerId": customer["_id"]
        })

        if not conversation:
            conversation_data = {
                "customerId": customer["_id"],
                "botId": bot_id,
                "channel": "telegram",
                "autoReply": True,
                "createdAt": datetime.now(timezone.utc),
                "updatedAt": datetime.now(timezone.utc)
            }
            conversation = await conversation_repo.create(conversation_data)

        # 1. Save Customer message
        try:
            arq_pool = get_arq_pool()
            asyncio.create_task(
                arq_pool.enqueue_job('save_chat_history_task', str(conversation["_id"]), str(bot_id), update.message.text, "customer")
            )
        except Exception as e:
            logger.error(f"Failed to enqueue customer message: {e}")

        # Skip AI processing when auto-reply is disabled.
        if not conversation.get("autoReply", True):
            return

        # Generate a response using the AI engine.
        response_text = await ai_engine.ask(
            bot_id=str(bot_id),
            question=update.message.text,
            conversation_id=str(conversation["_id"])
        )

        # 2. Save AI response
        try:
            arq_pool = get_arq_pool()
            asyncio.create_task(
                arq_pool.enqueue_job('save_chat_history_task', str(conversation["_id"]), str(bot_id), response_text, "ai")
            )
        except Exception as e:
            logger.error(f"Failed to enqueue AI response: {e}")

        # Send the generated response back to Telegram.
        await telegram_service.send_message(
            bot_token,
            update.message.chat.id,
            response_text
        )

    except Exception as e:
        logger.error(f"Error handling telegram message: {e}")
