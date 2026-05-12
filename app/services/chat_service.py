import uuid
from datetime import datetime, timezone
from typing import Optional

from app.repositories.customer_repository import CustomerRepository
from app.repositories.conversation_repository import ConversationRepository
from app.repositories.chat_history_repository import ChatHistoryRepository
from app.repositories.bot_repository import BotRepository
from app.core.exceptions import NotFoundException

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
        """Lưu tin nhắn vào lịch sử chat."""
        chat_data = {
            "role": role,
            "botId": bot_id,
            "content": content,
            "conversationId": conversation_id,
            "createdAt": datetime.now(timezone.utc)
        }
        await self._chat_history_repo.create(chat_data)

    async def get_ai_response(self, bot_id: str, message: str, conversation_id: str) -> str:
        """
        Gọi logic AI để lấy câu trả lời. 
        Tạm thời trả về Echo để test luồng WS.
        """
        # TODO: Tích hợp RAG logic (Embed -> Search -> Rerank -> LLM) ở đây
        return f"AI Response: {message}"
