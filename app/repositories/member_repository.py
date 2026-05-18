from app.repositories.base_repo import BaseRepository

class MemberRepository(BaseRepository):
    """
    Repository cho collection 'Member'.
    """
    async def get_user_projects(self, user_id: str):
        """
        Lấy danh sách ID các project mà user tham gia.
        """
        cursor = self.collection.find({"userId": user_id})
        member_documents = await cursor.to_list(length=100)

        project_id_list = []

        for member_document in member_documents:
          project_id = member_document["projectId"]
          project_id_list.append(str(project_id))

        return project_id_list

    async def is_member(self, user_id: str, project_id: str) -> bool:
        """
        Kiểm tra user có phải thành viên của project không.
        """
        member_document = await self.collection.find_one({"userId": user_id, "projectId": project_id})

        if member_document is not None:
          return True
        return False

    async def get_role(self, user_id: str, project_id: str) -> str | None:
        """Lấy quyền của user trong project."""
        member_document = await self.collection.find_one({"userId": user_id, "projectId": project_id})

        if member_document is None:
          return None

        role = member_document.get("role")
        return role
