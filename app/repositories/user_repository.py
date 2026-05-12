from typing import Optional, Dict, Any
from bson import ObjectId
from pymongo.asynchronous.collection import AsyncCollection
from app.repositories.base_repo import BaseRepository

class UserRepository(BaseRepository):
    """
    Repository quản lý dữ liệu người dùng.
    Kế thừa từ BaseRepository để có các hàm CRUD cơ bản.
    """
    def __init__(self, collection: AsyncCollection):
        super().__init__(collection)

    async def get_by_email(self, email: str) -> Optional[dict]:
        return await self.find_one({"email": email})

    async def get_user_by_id(self, user_id: str) -> Optional[dict]:
        return await self.get_by_id(user_id)

    async def update_user(self, user_id: str, user_data: Dict[str, Any]) -> Optional[dict]:
        return await self.update(user_id, user_data)
