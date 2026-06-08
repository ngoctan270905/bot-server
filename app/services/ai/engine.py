import json
import httpx
from typing import List, Optional
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, messages_from_dict, messages_to_dict
from loguru import logger
import redis.asyncio as redis

from app.core.config import settings
from app.services.ai.graph_builder import build_workflow
from app.services.ai.embeddings.factory import get_embeddings

class AIEngine:
    """
    Cổng giao tiếp chính của AI Module.
    Quản lý tài nguyên dùng chung (Redis) và thực thi Graph.
    """
    def __init__(self):
        self.redis_url = settings.redis.url
        self._redis_client = None
        self._graphs = {} # Cache compiled graphs theo bot_id
        self._vs_cache = {} # Cache RedisVectorStore instances
        self._http_client = httpx.AsyncClient(timeout=30.0)

    async def start(self):
        """Khởi tạo tài nguyên khi Server Start"""
        try:
            self._redis_client = redis.from_url(self.redis_url, decode_responses=True)
            await self._redis_client.ping()
        except Exception as e:
            logger.error(f"AIEngine start error: {e}")

    async def stop(self):
        """Đóng kết nối khi Server Shutdown"""
        if self._redis_client:
            await self._redis_client.close()
        await self._http_client.aclose()

    def get_embeddings(self):
        """Lấy công cụ Embedding từ factory"""
        return get_embeddings()

    def invalidate_vs_cache(self, bot_id: str):
        if bot_id in self._vs_cache:
            del self._vs_cache[bot_id]

    def _get_graph(self, bot_id: str):
        if bot_id not in self._graphs:
            self._graphs[bot_id] = build_workflow(bot_id, self)
        return self._graphs[bot_id]

    async def get_chat_history(self, conversation_id: str, limit: int = 10) -> List[BaseMessage]:
        if not self._redis_client: return []
        key = f"chat_history:{conversation_id}"
        try:
            raw_msgs = await self._redis_client.lrange(key, -limit, -1)
            if not raw_msgs: return []
            return messages_from_dict([json.loads(m) for m in raw_msgs])
        except Exception: return []

    async def save_chat_history(self, conversation_id: str, messages: List[BaseMessage]):
        if not self._redis_client: return
        key = f"chat_history:{conversation_id}"
        try:
            json_msgs = [json.dumps(d) for d in messages_to_dict(messages)]
            await self._redis_client.rpush(key, *json_msgs)
            await self._redis_client.ltrim(key, -30, -1)
            await self._redis_client.expire(key, 86400)
        except Exception: pass

    async def ask(self, bot_id: str, question: str, conversation_id: str, bot_instructions: Optional[str] = None) -> str:
        """
          Xử lý câu hỏi của người dùng thông qua workflow LangGraph.

          Quy trình:
          1. Tải lịch sử hội thoại từ Redis.
          2. Lấy hoặc khởi tạo graph workflow theo bot_id.
          3. Tạo initial state cho LangGraph.
          4. Thực thi workflow để sinh câu trả lời.
          5. Lưu lịch sử hội thoại mới vào Redis.
          6. Trả về kết quả cuối cùng cho client.

          Args:
              bot_id (str):
                  ID định danh chatbot/workflow cần sử dụng.

              question (str):
                  Câu hỏi hiện tại từ người dùng.

              conversation_id (str):
                  ID cuộc hội thoại dùng để lưu và truy xuất lịch sử chat.

              bot_instructions (Optional[str]):
                  System prompt hoặc instruction bổ sung cho bot.

          Returns:
              str:
                  Nội dung phản hồi cuối cùng từ AI.

          Notes:
              - Workflow sử dụng LangGraph thiết kế Single-Node (tương đương Node.js).
              - Chat history được lưu trên Redis.
              - Graph được cache để tối ưu hiệu năng.
        """
        logger.bind(context="AI-Engine").info(f"New request - Bot: {bot_id}, Conversation: {conversation_id}, Question: {question}")
        try:
            chat_history = await self.get_chat_history(conversation_id)
            graph = self._get_graph(bot_id)

            initial_state = {
                "input": question,
                "chat_history": chat_history,
                "bot_instructions": bot_instructions,
                "context": [],
                "standalone_question": ""
            }

            result = await graph.ainvoke(initial_state)
            answer = result.get("answer", "Xin lỗi, tôi không thể trả lời lúc này.")

            logger.bind(context="AI-Engine").info(f"Final answer for {conversation_id}: {answer[:100]}...")

            await self.save_chat_history(conversation_id, [
                HumanMessage(content=question),
                AIMessage(content=answer)
            ])

            return str(answer)

        except Exception as e:
            logger.error(f"AI Engine Error: {e}")
            return "Xin lỗi, tôi gặp sự cố trong quá trình suy nghĩ. Vui lòng thử lại sau."

# Khởi tạo Singleton
ai_engine = AIEngine()
