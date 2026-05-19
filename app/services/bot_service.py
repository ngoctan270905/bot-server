import secrets
import string
from datetime import datetime, timezone
from typing import List

from app.repositories.bot_repository import BotRepository
from app.repositories.member_repository import MemberRepository
from app.schemas.bot import (
    BotCreate,
    BotUpdate,
    BotDetailResponse,
    BotListAll,
    BotPublicResponse,
    SkKeyResponse
)
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

    async def get_bots(self, user_id: str, project_id: str) -> List[BotListAll]:
        """Lấy danh sách bot trong project."""
        is_member = await self._member_repo.is_member(user_id, project_id)
        if not is_member:
            raise ForbiddenException(detail="You are not a member of this project")

        bots = await self._bot_repo.get_by_project(project_id)
        response_bots = []

        for bot in bots:
          validated_bot = BotListAll.model_validate(bot)
          response_bots.append(validated_bot)

        return response_bots

    async def create_bot(self, user_id: str, bot_in: BotCreate) -> BotDetailResponse:
        """Tạo bot mới."""
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
        return BotDetailResponse.model_validate(new_bot)

    async def get_bot_by_id(self, user_id: str, bot_id: str) -> BotDetailResponse:
        """Lấy chi tiết bot."""
        bot = await self._bot_repo.get_by_id(bot_id)
        if not bot:
            raise NotFoundException(detail="Bot not found")

        is_member = await self._member_repo.is_member(user_id, bot["projectId"])
        if not is_member:
            raise ForbiddenException(detail="You are not a member of this project")

        return BotDetailResponse.model_validate(bot)

    async def get_bot_public(self, bot_id: str) -> BotPublicResponse:
        """Lấy thông tin bot công khai (không cần login)."""
        bot = await self._bot_repo.get_by_id(bot_id)
        if not bot:
            raise NotFoundException(detail="Bot not found")

        if not bot.get("skKey"):
            raise ForbiddenException(detail="Bot is not public")

        return BotPublicResponse.model_validate(bot)

    async def update_bot(self, user_id: str, bot_id: str, bot_in: BotUpdate) -> BotDetailResponse:
        """Cập nhật cấu hình bot."""
        bot = await self._bot_repo.get_by_id(bot_id)
        if not bot:
            raise NotFoundException(detail="Bot not found")

        is_member = await self._member_repo.is_member(user_id, bot["projectId"])
        if not is_member:
            raise ForbiddenException(detail="You are not a member of this project")

        update_data = bot_in.model_dump(exclude_unset=True)

        if "leads_settings" in update_data:
          leads_settings = update_data["leads_settings"]

          if leads_settings is not None:
            has_email = leads_settings.get("email")
            has_phone = leads_settings.get("phone")
            has_name = leads_settings.get("name")
            has_message = leads_settings.get("message")

            has_any_contact_field = (
              has_email or has_phone or has_name or has_message
            )
            if has_any_contact_field:
              has_title = leads_settings.get("title")

              if not has_title:
                update_data["leads_settings"]["title"] = (
                  "Let we know how to contact you"
                )
            else:
              update_data["leads_settings"] = None
          else:
            update_data["leads_settings"] = None

        if "is_public" in update_data:
            is_public = update_data.pop("is_public")
            if is_public is True:
                update_data["skKey"] = generate_sk_key()
            elif is_public is False:
                update_data["skKey"] = None

        settings_update = {}
        if "temperature" in update_data:
            settings_update["temperature"] = update_data.pop("temperature")
        if "instructions" in update_data:
            settings_update["instructions"] = update_data.pop("instructions")

        if settings_update:
            current_settings = bot.get("settings", {})
            if not isinstance(current_settings, dict):
                current_settings = {}
            current_settings.update(settings_update)
            update_data["settings"] = current_settings

        updated_bot = await self._bot_repo.update(bot_id, update_data)
        return BotDetailResponse.model_validate(updated_bot)

    async def reset_sk_key(self, user_id: str, bot_id: str) -> SkKeyResponse:
        """Cấp lại Secret Key mới."""
        bot = await self._bot_repo.get_by_id(bot_id)
        if not bot:
            raise NotFoundException(detail="Bot not found")

        is_member = await self._member_repo.is_member(user_id, bot["projectId"])
        if not is_member:
            raise ForbiddenException(detail="You do not have permission to modify this bot")

        new_key = generate_sk_key()
        await self._bot_repo.update(bot_id, {"skKey": new_key})
        return SkKeyResponse.model_validate({"skKey": new_key})

    async def delete_bot(self, user_id: str, bot_id: str) -> None:
        """Xóa bot."""
        bot = await self._bot_repo.get_by_id(bot_id)
        if not bot:
            raise NotFoundException(detail="Bot not found")

        is_member = await self._member_repo.is_member(user_id, bot["projectId"])
        if not is_member:
            raise ForbiddenException(detail="You are not a member of this project")

        await self._bot_repo.delete(bot_id)
