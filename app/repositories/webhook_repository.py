from app.repositories.base_repo import BaseRepository
from typing import Optional

class WebhookRepository(BaseRepository):
    """
    Repository cho collection 'Webhook'.
    """
    async def get_by_bot_id(self, bot_id: str) -> Optional[dict]:
        """Tìm cấu hình webhook của một Bot."""
        return await self.find_one({"botId": bot_id})
