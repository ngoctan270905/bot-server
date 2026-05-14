from datetime import datetime, timezone
from app.db.mongodb import get_database
from loguru import logger

async def save_chat_history_task(ctx, conversation_id: str, bot_id: str, content: str, role: str):
    """Task xử lý ngầm để lưu lịch sử chat vào MongoDB."""
    try:
        db = get_database()
        chat_data = {
            "role": role,
            "botId": bot_id,
            "content": content,
            "conversationId": conversation_id,
            "createdAt": datetime.now(timezone.utc)
        }
        await db["ChatHistory"].insert_one(chat_data)
        logger.bind(context="Task").debug(f"Saved {role} message for conversation {conversation_id}")
    except Exception as e:
        logger.bind(context="Task").error(f"Error saving chat history: {e}")

async def update_bot_token_usage_task(ctx, bot_id: str, token_count: int):
    """Task xử lý ngầm để cập nhật số lượng token đã sử dụng của Bot."""
    try:
        from bson import ObjectId
        db = get_database()
        await db["BotInstance"].update_one(
            {"_id": ObjectId(bot_id)},
            {"$inc": {"tokenUsage": token_count}}
        )
        logger.bind(context="Task").debug(f"Updated token usage for bot {bot_id}: +{token_count}")
    except Exception as e:
        logger.bind(context="Task").error(f"Error updating bot token usage: {e}")
