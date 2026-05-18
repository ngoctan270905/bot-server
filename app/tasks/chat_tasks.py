from datetime import datetime, timezone, timedelta
from app.db.mongodb import get_database
from loguru import logger

async def save_chat_history_task(ctx, conversation_id: str, bot_id: str, content: str, role: str):
    """
    Task xử lý ngầm để lưu lịch sử chat vào MongoDB.
    Đã loại bỏ logic sync analytics real-time để chuyển sang Cron Job 60p giống Node.js.
    """
    try:
        db = get_database()
        now = datetime.now(timezone.utc)
        
        chat_data = {
            "role": role,
            "botId": bot_id,
            "content": content,
            "conversationId": conversation_id,
            "createdAt": now
        }
        await db["ChatHistory"].insert_one(chat_data)
        logger.bind(context="Task").debug(f"Saved {role} message for conversation {conversation_id}")
        
    except Exception as e:
        logger.bind(context="Task").error(f"Error saving chat history: {e}")

async def cron_sync_all_bots_analytics_task(ctx):
    """
    Task chạy định kỳ mỗi giờ (Cron) để tổng hợp Analytics cho tất cả các Bot.
    Giống logic chatbot-analytics.ts trong Node.js.
    """
    try:
        db = get_database()
        logger.bind(context="Cron").info("Bắt đầu chạy Cron Job đồng bộ Analytics cho tất cả các Bot...")
        
        # 1. Lấy danh sách tất cả các Bot (find() KHÔNG await trong pymongo async)
        bots_cursor = db["BotInstance"].find({}, {"_id": 1})
        bots = [bot async for bot in bots_cursor]
        
        now = datetime.now(timezone.utc)
        
        # 2. Đồng bộ từng Bot
        for bot in bots:
            bot_id = str(bot["_id"])
            await sync_bot_analytics_internal(db, bot_id, now)
            
        logger.bind(context="Cron").info(f"Hoàn thành đồng bộ Analytics cho {len(bots)} bots.")
    except Exception as e:
        logger.bind(context="Cron").error(f"Lỗi trong Cron Job Analytics: {e}")

async def sync_bot_analytics_internal(db, bot_id: str, date: datetime):
    """Logic tổng hợp dữ liệu từ History và ghi vào Analytics."""
    try:
        start_of_day = date.replace(hour=0, minute=0, second=0, microsecond=0)
        end_of_day = start_of_day + timedelta(days=1)

        # Thống kê Conversations theo Channel (aggregate() PHẢI await)
        conv_pipeline = [
            {
                "$match": {
                    "botId": bot_id,
                    "createdAt": {"$gte": start_of_day, "$lt": end_of_day}
                }
            },
            {
                "$group": {
                    "_id": "$channel",
                    "totalChat": {"$sum": 1}
                }
            }
        ]
        conv_cursor = await db["Conversation"].aggregate(conv_pipeline)
        conv_stats = [item async for item in conv_cursor]
        
        total_chat = sum(item["totalChat"] for item in conv_stats)
        chats_by_channel = [{"channel": item["_id"], "totalChat": item["totalChat"]} for item in conv_stats]

        # Thống kê ChatHistory (Messages và Thumbs) (aggregate() PHẢI await)
        chat_pipeline = [
            {
                "$match": {
                    "botId": bot_id,
                    "createdAt": {"$gte": start_of_day, "$lt": end_of_day}
                }
            },
            {
                "$group": {
                    "_id": "$thumb",
                    "count": {"$sum": 1}
                }
            }
        ]
        chat_cursor = await db["ChatHistory"].aggregate(chat_pipeline)
        chat_stats = [item async for item in chat_cursor]

        total_message = sum(item["count"] for item in chat_stats)
        thumbs_up_message = next((item["count"] for item in chat_stats if item["_id"] == "ThumbsUp"), 0)
        thumbs_down_message = next((item["count"] for item in chat_stats if item["_id"] == "ThumbsDown"), 0)

        # Upsert vào ChatAnalytics
        analytic_data = {
            "botId": bot_id,
            "date": start_of_day,
            "totalChat": total_chat,
            "totalMessage": total_message,
            "thumbsUpMessage": thumbs_up_message,
            "thumbsDownMessage": thumbs_down_message,
            "chatsByChannel": chats_by_channel,
            "updatedAt": datetime.now(timezone.utc)
        }
        
        await db["ChatAnalytics"].update_one(
            {"botId": bot_id, "date": start_of_day},
            {"$set": analytic_data},
            upsert=True
        )
    except Exception as e:
        logger.bind(context="Task").error(f"Error syncing analytics for bot {bot_id}: {e}")

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
