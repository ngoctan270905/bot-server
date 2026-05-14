from datetime import datetime, timezone
from bson import ObjectId
from typing import List, Optional

from app.repositories.project_repository import ProjectRepository
from app.repositories.member_repository import MemberRepository
from app.repositories.billing_repository import BillingRepository
from app.repositories.bot_repository import BotRepository
from app.repositories.chat_history_repository import ChatHistoryRepository
from app.schemas.project import (
    ProjectCreate, ProjectUpdate, ProjectDetailResponse, ProjectListAll,
    ProjectSubscriptionResponse, ProjectUsageResponse, MessagePerDay, MessagePerBot,
    SubscriptionService as SubscriptionServiceSchema, SubscriptionPrice
)
from app.core.exceptions import NotFoundException, ForbiddenException

# Giả lập dữ liệu subscription (giống bản Node.js)
SUBSCRIPTIONS = [
    {
        "id": "package_starter",
        "name": "Starter",
        "description": "Starter package",
        "isFree": True,
        "prices": [
            {"currency": "usd", "price": 0, "reccuringInterval": "month"},
            {"currency": "usd", "price": 0, "reccuringInterval": "year"}
        ],
        "services": {"tokensPerBotPerMonth": 10000, "charactersPerBot": 400000, "teamMembers": 1},
        "features": ["Token per bot: 10,000", "Characters per bot: 400,000", "1 team member"]
    },
    {
        "id": "package_basic",
        "name": "Basic",
        "description": "Basic package",
        "prices": [
            {"currency": "usd", "price": 999, "reccuringInterval": "month"},
            {"currency": "usd", "price": 9990, "reccuringInterval": "year"}
        ],
        "services": {"tokensPerBotPerMonth": 100000, "charactersPerBot": 10000000, "teamMembers": 3},
        "features": ["Token per bot: 100,000", "Characters per bot: 10,000,000", "3 team members"]
    }
]

class ProjectService:
    def __init__(
        self,
        project_repo: ProjectRepository,
        member_repo: MemberRepository,
        billing_repo: BillingRepository,
        bot_repo: BotRepository,
        chat_history_repo: ChatHistoryRepository
    ):
        self._project_repo = project_repo
        self._member_repo = member_repo
        self._billing_repo = billing_repo
        self._bot_repo = bot_repo
        self._chat_history_repo = chat_history_repo

    async def get_projects(self, user_id: str) -> List[ProjectListAll]:
        """Lấy danh sách project mà user tham gia."""
        project_ids = await self._member_repo.get_user_projects(user_id)
        
        projects = []
        for pid in project_ids:
            p = await self._project_repo.get_by_id(pid)
            if p:
                projects.append(p)
                
        return [ProjectListAll.model_validate(p) for p in projects]

    async def create_project(self, user_id: str, project_in: ProjectCreate, user_email: str) -> ProjectDetailResponse:
        """Tạo project mới, thêm member admin và billing placeholder."""
        # 1. Tạo Project
        project_data = {
            "name": project_in.name,
            "url": project_in.url,
            "subscriptionId": "package_starter", # Mặc định là gói starter
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

        return ProjectDetailResponse.model_validate(new_project)

    async def get_project_by_id(self, user_id: str, project_id: str) -> ProjectDetailResponse:
        """Lấy chi tiết project nếu user là thành viên."""
        is_member = await self._member_repo.is_member(user_id, project_id)
        if not is_member:
            raise ForbiddenException(detail="You are not a member of this project")

        project = await self._project_repo.get_by_id(project_id)
        if not project:
            raise NotFoundException(detail="Project not found")

        return ProjectDetailResponse.model_validate(project)

    async def update_project(self, user_id: str, project_id: str, project_in: ProjectUpdate) -> ProjectDetailResponse:
        """Cập nhật project nếu user là thành viên."""
        is_member = await self._member_repo.is_member(user_id, project_id)
        if not is_member:
            raise ForbiddenException(detail="You are not a member of this project")

        update_data = project_in.model_dump(exclude_unset=True)
        updated_project = await self._project_repo.update(project_id, update_data)
        
        if not updated_project:
            raise NotFoundException(detail="Project not found")

        return ProjectDetailResponse.model_validate(updated_project)

    async def delete_project(self, user_id: str, project_id: str) -> None:
        """Xóa project nếu user là admin."""
        role = await self._member_repo.get_role(user_id, project_id)
        if role != "admin":
            raise ForbiddenException(detail="Only admins can delete the project")

        success = await self._project_repo.delete(project_id)
        if not success:
            raise NotFoundException(detail="Project not found")

        return None

    async def get_project_subscription(self, user_id: str, project_id: str) -> ProjectSubscriptionResponse:
        """Lấy thông tin subscription của project."""
        is_member = await self._member_repo.is_member(user_id, project_id)
        if not is_member:
            raise ForbiddenException(detail="You are not a member of this project")

        project = await self._project_repo.get_by_id(project_id)
        if not project:
            raise NotFoundException(detail="Project not found")

        sub_id = project.get("subscriptionId", "package_starter")
        sub_data = next((s for s in SUBSCRIPTIONS if s["id"] == sub_id), SUBSCRIPTIONS[0])
        
        return ProjectSubscriptionResponse.model_validate(sub_data)

    async def get_project_usage(
        self, 
        user_id: str, 
        project_id: str, 
        from_date: Optional[str] = None, 
        to_date: Optional[str] = None, 
        bot_id: Optional[str] = None
    ) -> ProjectUsageResponse:
        """Thống kê sử dụng của project."""
        is_member = await self._member_repo.is_member(user_id, project_id)
        if not is_member:
            raise ForbiddenException(detail="You are not a member of this project")

        # 1. Lấy danh sách bots của project để lọc tin nhắn
        bots = await self._bot_repo.get_by_project(project_id)
        bot_ids = [str(b["_id"]) for b in bots]
        
        if bot_id and bot_id not in bot_ids:
             raise ForbiddenException(detail="Bot does not belong to this project")

        # 2. Query tin nhắn
        start_dt = datetime.fromisoformat(from_date).replace(tzinfo=timezone.utc) if from_date else None
        end_dt = datetime.fromisoformat(to_date).replace(tzinfo=timezone.utc) if to_date else None
        
        # Cần cập nhật repository để lọc theo danh sách bot_ids nếu không có bot_id cụ thể
        query = {"role": "agent", "botId": {"$in": bot_ids}}
        if bot_id:
            query["botId"] = bot_id
        if start_dt or end_dt:
            query["created_at"] = {}
            if start_dt: query["created_at"]["$gte"] = start_dt
            if end_dt: query["created_at"]["$lt"] = end_dt

        chat_histories = await self._chat_history_repo.find_many(filter=query, limit=10000)
        
        total_messages = len(chat_histories)
        message_per_days = {}
        message_per_bots = {}

        for chat in chat_histories:
            # Group by date
            dt = chat.get("created_at")
            if dt:
                if isinstance(dt, str):
                    date_str = dt.split('T')[0]
                else:
                    date_str = dt.strftime('%Y-%m-%d')
                message_per_days[date_str] = message_per_days.get(date_str, 0) + 1
            
            # Group by bot
            bid = chat.get("botId")
            if bid:
                message_per_bots[bid] = message_per_bots.get(bid, 0) + 1

        return ProjectUsageResponse(
            total_messages=total_messages,
            message_per_days=[MessagePerDay(date=d, count=c) for d, c in message_per_days.items()],
            message_per_bots=[MessagePerBot(bot_id=b, count=c) for b, c in message_per_bots.items()]
        )
