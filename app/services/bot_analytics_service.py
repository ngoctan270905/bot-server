from datetime import datetime, timezone, timedelta
from typing import List
from app.repositories.chat_analytics_repository import ChatAnalyticsRepository
from app.repositories.bot_repository import BotRepository
from app.repositories.member_repository import MemberRepository
from app.repositories.chat_history_repository import ChatHistoryRepository
from app.repositories.conversation_repository import ConversationRepository
from app.schemas.bot import BotAnalyticsResponse, BotAnalyticsTotal, ChatAnalyticsDetail, ChatByChannelCount
from app.core.exceptions import NotFoundException, ForbiddenException

class BotAnalyticsService:
    def __init__(
        self,
        analytics_repo: ChatAnalyticsRepository,
        bot_repo: BotRepository,
        member_repo: MemberRepository,
        chat_history_repo: ChatHistoryRepository = None,
        conversation_repo: ConversationRepository = None
    ):
        self._analytics_repo = analytics_repo
        self._bot_repo = bot_repo
        self._member_repo = member_repo
        self._chat_history_repo = chat_history_repo
        self._conversation_repo = conversation_repo

    async def get_bot_analytics(
        self, 
        user_id: str, 
        bot_id: str, 
        from_date: datetime, 
        to_date: datetime
    ) -> BotAnalyticsResponse:
        """
        Lấy thống kê chat của bot.
        Thực hiện cộng dồn (Aggregate) dữ liệu từ bảng ChatAnalytics.
        """
        # 1. Kiểm tra bot tồn tại
        bot = await self._bot_repo.get_by_id(bot_id)
        if not bot:
            raise NotFoundException(detail="Bot not found")

        # 2. Kiểm tra quyền sở hữu/thành viên project
        is_member = await self._member_repo.is_member(user_id, bot["projectId"])
        if not is_member:
            raise ForbiddenException(detail="You do not have permission to view this bot's analytics")

        # 3. Lấy dữ liệu thô từ repository
        analytics_data = await self._analytics_repo.get_analytics_by_bot(bot_id, from_date, to_date)

        # 4. Logic cộng dồn (Aggregate)
        total_chat = 0
        total_message = 0
        thumbs_up_message = 0
        thumbs_down_message = 0
        channels_map = {}

        details = []
        for doc in analytics_data:
            # Cộng dồn tổng quát
            total_chat += doc.get("totalChat", 0)
            total_message += doc.get("totalMessage", 0)
            thumbs_up_message += doc.get("thumbsUpMessage", 0)
            thumbs_down_message += doc.get("thumbsDownMessage", 0)

            # Cộng dồn theo kênh cho Total
            for channel_data in doc.get("chatsByChannel", []):
                ch = channel_data.get("channel")
                count = channel_data.get("totalChat", 0)
                channels_map[ch] = channels_map.get(ch, 0) + count

            # Chuẩn bị dữ liệu chi tiết từng ngày
            details.append(ChatAnalyticsDetail(
                date=doc["date"],
                total_chat=doc.get("totalChat", 0),
                total_message=doc.get("totalMessage", 0),
                thumbs_up_message=doc.get("thumbsUpMessage", 0),
                thumbs_down_message=doc.get("thumbsDownMessage", 0),
                chats_by_channel=[
                    ChatByChannelCount(channel=c["channel"], total_chat=c["totalChat"])
                    for c in doc.get("chatsByChannel", [])
                ]
            ))

        # Chuyển channels_map sang list
        total_channels = [
            ChatByChannelCount(channel=ch, total_chat=count)
            for ch, count in channels_map.items()
        ]

        return BotAnalyticsResponse(
            bot_id=bot_id,
            total=BotAnalyticsTotal(
                total_chat=total_chat,
                total_message=total_message,
                thumbs_up_message=thumbs_up_message,
                thumbs_down_message=thumbs_down_message,
                chats_by_channel=total_channels
            ),
            data=details
        )

    async def sync_bot_analytics(self, bot_id: str, date: datetime = None):
        """
        Đồng bộ dữ liệu analytics cho bot vào một ngày cụ thể.
        Logic: Query từ ChatHistory và Conversation rồi ghi đè vào ChatAnalytics.
        """
        if not date:
            date = datetime.now(timezone.utc)
        
        # Đưa về đầu ngày (00:00:00 UTC)
        start_of_day = date.replace(hour=0, minute=0, second=0, microsecond=0)
        end_of_day = start_of_day + timedelta(days=1)

        # 1. Thống kê Conversations theo Channel
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
        conv_stats = await self._conversation_repo.collection.aggregate(conv_pipeline).to_list(length=None)
        
        total_chat = sum(item["totalChat"] for item in conv_stats)
        chats_by_channel = [{"channel": item["_id"], "totalChat": item["totalChat"]} for item in conv_stats]

        # 2. Thống kê ChatHistory (Messages và Thumbs)
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
        chat_stats = await self._chat_history_repo.collection.aggregate(chat_pipeline).to_list(length=None)

        total_message = sum(item["count"] for item in chat_stats)
        thumbs_up_message = next((item["count"] for item in chat_stats if item["_id"] == "ThumbsUp"), 0)
        thumbs_down_message = next((item["count"] for item in chat_stats if item["_id"] == "ThumbsDown"), 0)

        # 3. Upsert vào ChatAnalytics
        analytic_data = {
            "totalChat": total_chat,
            "totalMessage": total_message,
            "thumbsUpMessage": thumbs_up_message,
            "thumbsDownMessage": thumbs_down_message,
            "chatsByChannel": chats_by_channel
        }
        
        await self._analytics_repo.upsert_analytics(bot_id, start_of_day, analytic_data)
        return analytic_data
