from typing import List
from app.repositories.base_repo import BaseRepository

class TrainingHistoryRepository(BaseRepository):
    """
    Repository cho collection 'TrainingHistory'.
    """
    async def get_by_bot(self, bot_id: str, limit: int = 20) -> List[dict]:
        """Lấy lịch sử training của bot."""
        cursor = self.collection.find({"botId": bot_id}).sort([("createdAt", -1)]).limit(limit)
        items = [item async for item in cursor]
        return self._format_id(items)
