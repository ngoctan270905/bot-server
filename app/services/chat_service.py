import uuid
from datetime import datetime, timezone
from typing import Optional, List

from app.repositories.customer_repository import CustomerRepository
from app.repositories.conversation_repository import ConversationRepository
from app.repositories.chat_history_repository import ChatHistoryRepository
from app.repositories.bot_repository import BotRepository
from app.schemas.chat import (
    ConversationDetailResponse,
    ConversationWithHistory,
    ChatHistoryDetailResponse,
    ConversationUpdate
)
from app.core.exceptions import NotFoundException, ForbiddenException
from app.services.ai_engine import ai_engine
from app.db.redis import redis_manager
from app.core.config import settings

class ChatService:
    def __init__(
        self,
        customer_repo: CustomerRepository,
        conversation_repo: ConversationRepository,
        chat_history_repo: ChatHistoryRepository,
        bot_repo: BotRepository
    ):
        self._customer_repo = customer_repo
        self._conversation_repo = conversation_repo
        self._chat_history_repo = chat_history_repo
        self._bot_repo = bot_repo

    async def get_chatlogs(
        self,
        user_id: str,
        bot_id: str,
        limit: int = 20,
        cursor: Optional[str] = None,
        from_date: Optional[str] = None,
        to_date: Optional[str] = None,
        channels: Optional[str] = None
    ) -> List[ConversationWithHistory]:
        """Lấy danh sách hội thoại cho Admin."""
        # TODO: Kiểm tra quyền truy cập của user với bot này thông qua project

        start_dt = datetime.fromisoformat(from_date).replace(tzinfo=timezone.utc) if from_date else None
        end_dt = datetime.fromisoformat(to_date).replace(tzinfo=timezone.utc) if to_date else None
        channel_list = channels.split(",") if channels else None

        conversations = await self._conversation_repo.get_chatlogs(
            bot_id=bot_id,
            limit=limit,
            cursor=cursor,
            from_date=start_dt,
            to_date=end_dt,
            channels=channel_list
        )

        results = []
        for conv in conversations:
            # Lấy tin nhắn cuối cùng hoặc vài tin nhắn gần đây để preview (giống Prisma include)
            history = await self._chat_history_repo.get_by_conversation(conv["_id"])

            # Map sang schema
            conv_obj = ConversationWithHistory.model_validate(conv)
            conv_obj.chat_histories = [ChatHistoryDetailResponse.model_validate(h) for h in history]
            results.append(conv_obj)

        return results

    async def get_history(self, conversation_id: str) -> List[ChatHistoryDetailResponse]:
        """Lấy toàn bộ lịch sử tin nhắn của một cuộc hội thoại."""
        history = await self._chat_history_repo.get_by_conversation(conversation_id)
        return [ChatHistoryDetailResponse.model_validate(h) for h in history]

    async def update_conversation(self, conversation_id: str, update_in: ConversationUpdate) -> None:
        """Cập nhật thông tin cuộc hội thoại."""
        update_data = update_in.model_dump(exclude_unset=True)
        await self._conversation_repo.update(conversation_id, update_data)

    async def start_chat(self, bot_id: str, channel: str = "web") -> str:
        """Khởi tạo một phiên chat mới, trả về conversation_id."""
        bot = await self._bot_repo.get_by_id(bot_id)
        if not bot:
            raise NotFoundException(detail="Bot not found")

        # Tạo Customer mới
        customer_data = {
            "cid": str(uuid.uuid4()),
            "channel": channel,
            "createdAt": datetime.now(timezone.utc)
        }
        customer = await self._customer_repo.create(customer_data)

        # Tạo Conversation mới
        conversation_data = {
            "customerId": customer["_id"],
            "botId": bot_id,
            "channel": channel,
            "autoReply": True,
            "createdAt": datetime.now(timezone.utc),
            "updatedAt": datetime.now(timezone.utc)
        }
        conversation = await self._conversation_repo.create(conversation_data)

        return str(conversation["_id"])

    async def save_message(self, conversation_id: str, bot_id: str, content: str, role: str):
        """Đẩy task lưu tin nhắn vào hàng đợi arq."""
        try:
            # Kiểm tra client thay vì pool (theo định nghĩa trong db/redis.py)
            if redis_manager.client:
                from arq import create_pool
                from arq.connections import RedisSettings

                # TODO: Nên cache arq_pool này ở class level hoặc dependency thay vì tạo mới mỗi lần
                arq_pool = await create_pool(RedisSettings(
                    host=settings.redis.host,
                    port=settings.redis.port,
                    password=settings.redis.password,
                    database=settings.redis.db
                ))
                await arq_pool.enqueue_job('save_chat_history_task', conversation_id, bot_id, content, role)
                await arq_pool.close()
        except Exception as e:
            import loguru
            loguru.logger.error(f"Failed to enqueue save_message task: {e}")

    async def get_ai_response(self, bot_id: str, message: str, conversation_id: str) -> str:
        """
        Gọi logic AI thực tế (RAG) thông qua AIEngine và cập nhật token usage ngầm.
        """
        bot = await self._bot_repo.get_by_id(bot_id)
        bot_instructions = ""
        if bot and "settings" in bot:
            bot_instructions = bot["settings"].get("instructions", "")

        # 1. Gọi AI Engine lấy phản hồi
        ai_text = await ai_engine.ask(
            bot_id=bot_id, 
            question=message, 
            conversation_id=conversation_id,
            bot_instructions=bot_instructions
        )

        # 2. Ước tính token (4 ký tự ~ 1 token)
        token_count = len(ai_text) // 4

        # 3. Enqueue job cập nhật token usage
        try:
            if redis_manager.client:
                from arq import create_pool
                from arq.connections import RedisSettings
                arq_pool = await create_pool(RedisSettings(
                    host=settings.redis.host,
                    port=settings.redis.port,
                    password=settings.redis.password,
                    database=settings.redis.db
                ))
                await arq_pool.enqueue_job('update_bot_token_usage_task', bot_id, token_count)
                await arq_pool.close()
        except Exception as e:
            import loguru
            loguru.logger.error(f"Failed to enqueue update_token task: {e}")

        return ai_text
