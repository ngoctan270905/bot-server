from typing import List, Optional, Tuple
from datetime import datetime
from bson import ObjectId
from app.repositories.base_repo import BaseRepository

class ConversationRepository(BaseRepository):
    """
    Repository cho collection 'Conversation'.
    """
    async def get_chatlogs(
        self,
        bot_id: str,
        skip: int = 0,
        limit: int = 20,
        from_date: Optional[datetime] = None,
        to_date: Optional[datetime] = None,
        channels: Optional[List[str]] = None,
        cursor: Optional[str] = None
    ) -> List[dict]:
        """
        Lấy danh sách hội thoại có kèm bộ lọc và phân trang.
        """
        query = {"botId": bot_id}

        if from_date or to_date:
            query["createdAt"] = {}
            if from_date:
                query["createdAt"]["$gte"] = from_date
            if to_date:
                query["createdAt"]["$lte"] = to_date

        if channels:
            query["channel"] = {"$in": channels}
            
        if cursor:
            # Phân trang dựa trên cursor (id)
            query["_id"] = {"$lt": ObjectId(cursor)}

        # Sắp xếp theo updatedAt mới nhất
        sort = [("updatedAt", -1)]
        
        return await self.find_many(filter=query, sort=sort, skip=skip, limit=limit)
