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
