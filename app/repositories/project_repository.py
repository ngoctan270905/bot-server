from typing import List
from bson import ObjectId
from app.repositories.base_repo import BaseRepository

class ProjectRepository(BaseRepository):
    """
    Repository cho collection 'Project'.
    """
    async def get_by_member(self, user_id: str):
        """
        Logic này thường cần join với collection Member.
        Tuy nhiên với MongoDB, chúng ta sẽ thực hiện tìm kiếm Member trước rồi lấy Project sau,
        hoặc dùng aggregation.
        """
        pass

    async def get_by_ids(self, project_id_list: List[str]) -> List[dict]:
        """
        Lấy danh sách project theo nhiều ID.
        """
        try:
            ids = [ObjectId(pid) for pid in project_id_list]
            filter_query = {"_id": {"$in": ids}}
            return await self.find_many(filter=filter_query, limit=len(project_id_list))
        except Exception:
            return []
