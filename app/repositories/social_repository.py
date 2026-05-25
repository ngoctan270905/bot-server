from app.repositories.base_repo import BaseRepository
from typing import Optional

class SocialPageRepository(BaseRepository):
    """
    Repository cho collection 'SocialPage'.
    """
    async def get_by_page_id(self, page_id: str) -> Optional[dict]:
        return await self.collection.find_one({"pageId": page_id})

    async def get_by_bot_id(self, bot_id: str) -> list[dict]:
        cursor = self.collection.find({"botId": bot_id})
        return await cursor.to_list(length=100)

    async def update_by_page_id(self, page_id: str, data: dict):
        return await self.collection.update_one(
            {"pageId": page_id},
            {"$set": data},
            upsert=True
        )
