from typing import List, Optional
from bson import ObjectId
from app.repositories.base_repo import BaseRepository

class BotDataSourceRepository(BaseRepository):
    """
    Repository cho collection 'BotDataSource'.
    """
    async def get_by_bot(self, bot_id: str) -> List[dict]:
        """Lấy danh sách nguồn dữ liệu của bot."""
        cursor = self.collection.find({"botId": bot_id})
        items = [item async for item in cursor]
        return self._format_id(items)

    async def get_by_ids(self, ids: List[str]) -> List[dict]:
        """Lấy danh sách nguồn dữ liệu theo danh sách IDs."""
        object_ids = [ObjectId(id) for id in ids]
        cursor = self.collection.find({"_id": {"$in": object_ids}})
        items = [item async for item in cursor]
        return self._format_id(items)

    async def update_status_by_bot(self, bot_id: str, status: str):
        """Cập nhật trạng thái training cho tất cả nguồn của bot."""
        await self.collection.update_many(
            {"botId": bot_id},
            {"$set": {"trainingStatus": status}}
        )
