from typing import Optional
from pymongo.asynchronous.collection import AsyncCollection
from app.repositories.base_repo import BaseRepository

class EmailPasswordUserRepository(BaseRepository):
    """
    Repository quản lý dữ liệu đăng nhập bằng Email/Password.
    """
    def __init__(self, collection: AsyncCollection):
        super().__init__(collection)

    async def get_by_email(self, email: str) -> Optional[dict]:
        """Tìm bản ghi theo email."""
        return await self.find_one({"email": email})

    async def create_email_pw_user(self, data: dict) -> dict:
        """Tạo mới bản ghi email/password."""
        return await self.create(data)

    async def update_password(self, email: str, hashed_password: str) -> bool:
        """Cập nhật mật khẩu mới."""
        result = await self.collection.update_one(
            {"email": email},
            {"$set": {"password": hashed_password}}
        )
        return result.modified_count > 0

    async def get_by_user_id(self, user_id: str) -> Optional[dict]:
      """
      Tìm bản ghi email/password theo user ID.
      """
      filter_query = {"userId": user_id}
      email_password_user = await self.find_one(filter_query)
      return email_password_user
