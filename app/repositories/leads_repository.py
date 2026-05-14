from app.repositories.base_repo import BaseRepository
from datetime import datetime

class LeadsRepository(BaseRepository):
    """
    Repository cho collection 'Leads'.
    """
    async def get_leads_by_bot(self, bot_id: str, from_date: datetime = None, to_date: datetime = None):
        """Lấy danh sách leads của bot, có lọc theo thời gian."""
        query = {"botId": bot_id}
        if from_date or to_date:
            query["createdAt"] = {}
            if from_date:
                query["createdAt"]["$gte"] = from_date
            if to_date:
                query["createdAt"]["$lte"] = to_date
        
        cursor = self.collection.find(query).sort([("createdAt", -1)])
        items = [item async for item in cursor]
        return self._format_id(items)
