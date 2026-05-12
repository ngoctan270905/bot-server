from app.repositories.base_repo import BaseRepository

class MemberRepository(BaseRepository):
    """
    Repository cho collection 'Member'.
    """
    async def get_user_projects(self, user_id: str):
        """Lấy danh sách ID các project mà user tham gia."""
        cursor = self.collection.find({"userId": user_id})
        members = await cursor.to_list(length=100)
        return [str(m["projectId"]) for m in members]

    async def is_member(self, user_id: str, project_id: str) -> bool:
        """Kiểm tra user có phải thành viên của project không."""
        member = await self.collection.find_one({"userId": user_id, "projectId": project_id})
        return member is not None

    async def get_role(self, user_id: str, project_id: str) -> str | None:
        """Lấy quyền của user trong project."""
        member = await self.collection.find_one({"userId": user_id, "projectId": project_id})
        return member.get("role") if member else None
