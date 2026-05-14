from app.repositories.base_repo import BaseRepository
from datetime import datetime

class ChatAnalyticsRepository(BaseRepository):
    """
    Repository cho collection 'ChatAnalytics'.
    """
    async def get_analytics_by_bot(self, bot_id: str, from_date: datetime, to_date: datetime):
        """
        Lấy dữ liệu analytics của bot trong khoảng thời gian.
        Dữ liệu đã được pre-aggregated theo từng ngày.
        """
        query = {
            "botId": bot_id,
            "date": {
                "$gte": from_date,
                "$lte": to_date
            }
        }
        cursor = self.collection.find(query).sort([("date", 1)])
        items = [item async for item in cursor]
        return self._format_id(items)

    async def upsert_analytics(self, bot_id: str, date: datetime, data: dict):
        """
        Cập nhật hoặc tạo mới bản ghi analytics cho bot vào ngày cụ thể.
        """
        filter_query = {
            "botId": bot_id,
            "date": date
        }
        update_data = {
            "$set": {
                **data,
                "updatedAt": datetime.now()
            }
        }
        await self.collection.update_one(filter_query, update_data, upsert=True)
