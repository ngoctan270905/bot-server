import secrets
import string
from datetime import datetime, timezone
from typing import List

from app.repositories.bot_repository import BotRepository
from app.repositories.member_repository import MemberRepository
from app.schemas.bot import BotCreate, BotUpdate, BotDetailResponse, BotListAll
from app.schemas.base import UnifiedResponse
from app.core.exceptions import NotFoundException, ForbiddenException

def generate_sk_key(length: int = 32) -> str:
    """Sinh chuỗi Secret Key ngẫu nhiên."""
    alphabet = string.ascii_letters + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(length))

class BotService:
    def __init__(
        self,
        bot_repo: BotRepository,
        member_repo: MemberRepository
    ):
        self._bot_repo = bot_repo
        self._member_repo = member_repo

    async def get_bots(self, user_id: str, project_id: str) -> UnifiedResponse[List[BotListAll]]:
        """Lấy danh sách bot trong project."""
        # Kiểm tra quyền thành viên
        is_member = await self._member_repo.is_member(user_id, project_id)
        if not is_member:
            raise ForbiddenException(detail="You are not a member of this project")

        bots = await self._bot_repo.get_by_project(project_id)
        data = [BotListAll.model_validate(b) for b in bots]
        return UnifiedResponse[List[BotListAll]](
            success=True,
            message="Bots fetched successfully",
            data=data
        )

    async def create_bot(self, user_id: str, bot_in: BotCreate) -> UnifiedResponse[BotDetailResponse]:
        """Tạo bot mới trong project."""
        # Kiểm tra quyền thành viên của project
        is_member = await self._member_repo.is_member(user_id, bot_in.project_id)
        if not is_member:
            raise ForbiddenException(detail="You are not a member of this project")

        bot_data = {
            "name": bot_in.name,
            "projectId": bot_in.project_id,
            "userId": user_id,
            "tokenUsage": 0,
            "characterUsage": 0,
            "created_at": datetime.now(timezone.utc)
        }
        new_bot = await self._bot_repo.create(bot_data)
        
        data = BotDetailResponse.model_validate(new_bot)
        return UnifiedResponse[BotDetailResponse](
            success=True,
            message="Bot created successfully",
            data=data
        )

    async def get_bot_by_id(self, user_id: str, bot_id: str) -> UnifiedResponse[BotDetailResponse]:
        """Lấy chi tiết bot."""
        bot = await self._bot_repo.get_by_id(bot_id)
        if not bot:
            raise NotFoundException(detail="Bot not found")

        # Kiểm tra quyền thành viên của project chứa bot
        is_member = await self._member_repo.is_member(user_id, bot["projectId"])
        if not is_member:
            raise ForbiddenException(detail="You are not a member of this project")

        data = BotDetailResponse.model_validate(bot)
        return UnifiedResponse[BotDetailResponse](
            success=True,
            data=data
        )

    async def update_bot(self, user_id: str, bot_id: str, bot_in: BotUpdate) -> UnifiedResponse[BotDetailResponse]:
        """Cập nhật cấu hình bot."""
        bot = await self._bot_repo.get_by_id(bot_id)
        if not bot:
            raise NotFoundException(detail="Bot not found")

        # Kiểm tra quyền thành viên
        is_member = await self._member_repo.is_member(user_id, bot["projectId"])
        if not is_member:
            raise ForbiddenException(detail="You are not a member of this project")

        update_data = bot_in.model_dump(exclude_unset=True)

        # Logic xử lý Leads Settings (giống dự án gốc)
        if "leads_settings" in update_data:
            ls = update_data["leads_settings"]
            if ls and any([ls.get("email"), ls.get("phone"), ls.get("name"), ls.get("message")]):
                if not ls.get("title"):
                    update_data["leads_settings"]["title"] = "Let we know how to contact you"
            else:
                update_data["leads_settings"] = None

        # Logic xử lý Public/Private & SK Key
        # Lưu ý: Trong BotUpdate schema chưa có is_public, nếu bạn thêm vào thì code này sẽ chạy
        if "is_public" in update_data:
            is_public = update_data.pop("is_public")
            if is_public is True:
                update_data["skKey"] = generate_sk_key()
            elif is_public is False:
                update_data["skKey"] = None

        # Tách settings (temperature, instructions)
        settings_update = {}
        if "temperature" in update_data:
            settings_update["temperature"] = update_data.pop("temperature")
        if "instructions" in update_data:
            settings_update["instructions"] = update_data.pop("instructions")
        
        if settings_update:
            # Lấy settings hiện tại để merge
            current_settings = bot.get("settings", {})
            if not isinstance(current_settings, dict):
                current_settings = {}
            current_settings.update(settings_update)
            update_data["settings"] = current_settings

        updated_bot = await self._bot_repo.update(bot_id, update_data)
        if not updated_bot:
            raise NotFoundException(detail="Bot not found after update")

        data = BotDetailResponse.model_validate(updated_bot)
        return UnifiedResponse[BotDetailResponse](
            success=True,
            message="Bot updated successfully",
            data=data
        )

    async def delete_bot(self, user_id: str, bot_id: str) -> UnifiedResponse[None]:
        """Xóa bot."""
        bot = await self._bot_repo.get_by_id(bot_id)
        if not bot:
            raise NotFoundException(detail="Bot not found")

        # Kiểm tra quyền thành viên
        is_member = await self._member_repo.is_member(user_id, bot["projectId"])
        if not is_member:
            raise ForbiddenException(detail="You are not a member of this project")

        await self._bot_repo.delete(bot_id)
        return UnifiedResponse[None](
            success=True,
            message="Bot deleted successfully",
            data=None
        )
