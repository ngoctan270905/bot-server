from app.repositories.base_repo import BaseRepository

class BotRepository(BaseRepository):
    """
    Repository cho collection 'BotInstance'.
    """
    async def get_by_project(self, project_id: str):
        """Lấy danh sách bot thuộc về project."""
        cursor = self.collection.find({"projectId": project_id})
        return await cursor.to_list(length=100)
