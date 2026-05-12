from datetime import datetime, timezone
from bson import ObjectId
from typing import List

from app.repositories.project_repository import ProjectRepository
from app.repositories.member_repository import MemberRepository
from app.repositories.billing_repository import BillingRepository
from app.schemas.project import ProjectCreate, ProjectUpdate, ProjectDetailResponse, ProjectListAll
from app.schemas.base import UnifiedResponse
from app.core.exceptions import NotFoundException, ForbiddenException

class ProjectService:
    def __init__(
        self,
        project_repo: ProjectRepository,
        member_repo: MemberRepository,
        billing_repo: BillingRepository
    ):
        self._project_repo = project_repo
        self._member_repo = member_repo
        self._billing_repo = billing_repo

    async def get_projects(self, user_id: str) -> UnifiedResponse[List[ProjectListAll]]:
        """Lấy danh sách project mà user tham gia."""
        project_ids = await self._member_repo.get_user_projects(user_id)
        
        projects = []
        for pid in project_ids:
            p = await self._project_repo.get_by_id(pid)
            if p:
                projects.append(p)
                
        data = [ProjectListAll.model_validate(p) for p in projects]
        return UnifiedResponse[List[ProjectListAll]](
            success=True,
            message="Projects fetched successfully",
            data=data
        )

    async def create_project(self, user_id: str, project_in: ProjectCreate, user_email: str) -> UnifiedResponse[ProjectDetailResponse]:
        """Tạo project mới, thêm member admin và billing placeholder."""
        # 1. Tạo Project
        project_data = {
            "name": project_in.name,
            "url": project_in.url,
            "subscriptionId": "free", # Mặc định là gói free
            "created_at": datetime.now(timezone.utc)
        }
        new_project = await self._project_repo.create(project_data)
        project_id = str(new_project["_id"])

        # 2. Tạo Member (Admin)
        member_data = {
            "userId": user_id,
            "projectId": project_id,
            "role": "admin",
            "isCreator": True,
            "created_at": datetime.now(timezone.utc)
        }
        await self._member_repo.create(member_data)

        # 3. Tạo Billing Placeholder (Bỏ qua Stripe)
        billing_data = {
            "projectId": project_id,
            "invoiceReceiverEmail": user_email,
            "customerId": "placeholder_customer_id", # Placeholder thay cho Stripe
            "created_at": datetime.now(timezone.utc)
        }
        await self._billing_repo.create(billing_data)

        data = ProjectDetailResponse.model_validate(new_project)
        return UnifiedResponse[ProjectDetailResponse](
            success=True,
            message="Project created successfully",
            data=data
        )

    async def get_project_by_id(self, user_id: str, project_id: str) -> UnifiedResponse[ProjectDetailResponse]:
        """Lấy chi tiết project nếu user là thành viên."""
        is_member = await self._member_repo.is_member(user_id, project_id)
        if not is_member:
            raise ForbiddenException(detail="You are not a member of this project")

        project = await self._project_repo.get_by_id(project_id)
        if not project:
            raise NotFoundException(detail="Project not found")

        data = ProjectDetailResponse.model_validate(project)
        return UnifiedResponse[ProjectDetailResponse](
            success=True,
            data=data
        )

    async def update_project(self, user_id: str, project_id: str, project_in: ProjectUpdate) -> UnifiedResponse[ProjectDetailResponse]:
        """Cập nhật project nếu user là thành viên."""
        is_member = await self._member_repo.is_member(user_id, project_id)
        if not is_member:
            raise ForbiddenException(detail="You are not a member of this project")

        update_data = project_in.model_dump(exclude_unset=True)
        updated_project = await self._project_repo.update(project_id, update_data)
        
        if not updated_project:
            raise NotFoundException(detail="Project not found")

        data = ProjectDetailResponse.model_validate(updated_project)
        return UnifiedResponse[ProjectDetailResponse](
            success=True,
            message="Project updated successfully",
            data=data
        )

    async def delete_project(self, user_id: str, project_id: str) -> UnifiedResponse[None]:
        """Xóa project nếu user là admin."""
        role = await self._member_repo.get_role(user_id, project_id)
        if role != "admin":
            raise ForbiddenException(detail="Only admins can delete the project")

        success = await self._project_repo.delete(project_id)
        if not success:
            raise NotFoundException(detail="Project not found")

        # TODO: Xóa các dữ liệu liên quan (Member, Billing, Bot, Chat...)
        
        return UnifiedResponse[None](
            success=True,
            message="Project deleted successfully",
            data=None
        )
