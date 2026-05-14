from typing import List, Optional
from datetime import datetime
from app.repositories.base_repo import BaseRepository

class ChatHistoryRepository(BaseRepository):
    """
    Repository cho collection 'ChatHistory'.
    """
    async def get_usage(
        self, 
        project_id: str, 
        start_date: Optional[datetime] = None, 
        end_date: Optional[datetime] = None, 
        bot_id: Optional[str] = None
    ) -> List[dict]:
        """
        Lấy danh sách tin nhắn để thống kê sử dụng.
        """
        query = {
            "role": "agent"
        }
        
        # Nếu có bot_id cụ thể
        if bot_id:
            query["botId"] = bot_id
        
        # Lọc theo thời gian
        if start_date or end_date:
            query["created_at"] = {}
            if start_date:
                query["created_at"]["$gte"] = start_date
            if end_date:
                query["created_at"]["$lt"] = end_date
        
        # Phải lọc theo project thông qua botId (cần join hoặc lấy danh sách botId của project trước)
        # Trong MongoDB thô, thường ta sẽ truyền danh sách botIds vào query
        
        cursor = self.collection.find(query)
        return await cursor.to_list(length=None)

    async def get_by_conversation(self, conversation_id: str) -> List[dict]:
        """
        Lấy lịch sử tin nhắn của một cuộc hội thoại.
        """
        query = {"conversationId": conversation_id}
        sort = [("created_at", 1)]  # Cũ đến mới
        # Sử dụng find_many từ BaseRepository
        return await self.find_many(filter=query, sort=sort, limit=1000)
