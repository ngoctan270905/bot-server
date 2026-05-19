import json
from datetime import datetime, timezone
from typing import List, Optional
from app.repositories.leads_repository import LeadsRepository
from app.repositories.bot_repository import BotRepository
from app.repositories.member_repository import MemberRepository
from app.schemas.bot import LeadCreate, LeadDetailResponse
from app.core.exceptions import NotFoundException, ForbiddenException
from app.db.redis import redis_manager
from loguru import logger

class LeadService:
    def __init__(
        self,
        leads_repo: LeadsRepository,
        bot_repo: BotRepository,
        member_repo: MemberRepository
    ):
        self._leads_repo = leads_repo
        self._bot_repo = bot_repo
        self._member_repo = member_repo

    async def get_bot_leads(
        self,
        user_id: str,
        bot_id: str,
        from_date: Optional[datetime] = None,
        to_date: Optional[datetime] = None
    ) -> List[LeadDetailResponse]:
        """Lấy danh sách leads của bot."""
        # 1. Kiểm tra bot tồn tại
        bot = await self._bot_repo.get_by_id(bot_id)
        if not bot:
            raise NotFoundException(detail="Bot not found")

        # 2. Kiểm tra quyền sở hữu/thành viên project
        is_member = await self._member_repo.is_member(user_id, bot["projectId"])
        if not is_member:
            raise ForbiddenException(detail="You do not have permission to view this bot's leads")

        # 3. Lấy dữ liệu
        leads = await self._leads_repo.get_leads_by_bot(bot_id, from_date, to_date)
        response_leads = []

        for lead in leads:
          validated_lead = LeadDetailResponse.model_validate(lead)
          response_leads.append(validated_lead)

        return response_leads

    async def create_lead(self, bot_id: str, lead_in: LeadCreate) -> LeadDetailResponse:
        """
        Tạo lead mới.
        Tính năng này thường được gọi từ Public API hoặc Widget chat.
        """
        # 1. Kiểm tra bot tồn tại
        bot = await self._bot_repo.get_by_id(bot_id)
        if not bot:
            raise NotFoundException(detail="Bot not found")

        # 2. Lưu vào DB
        lead_data = {
            "botId": bot_id,
            "conversationId": lead_in.conversation_id,
            "name": lead_in.name,
            "email": lead_in.email,
            "phone": lead_in.phone,
            "message": lead_in.message,
            "createdAt": datetime.now(timezone.utc)
        }
        new_lead = await self._leads_repo.create(lead_data)

        # 3. Kích hoạt Webhook nếu có cấu hình
        await self._trigger_leads_webhook(bot, lead_data)

        return LeadDetailResponse.model_validate(new_lead)

    async def _trigger_leads_webhook(self, bot: dict, lead_data: dict):
        """
        Đẩy message vào Redis Stream để gửi Webhook.
        """
        try:
            webhooks = bot.get("webhooks")
            if not webhooks:
                return

            events = webhooks.get("events", [])
            if "leads.submit" in events:
                # Định dạng message giống bản gốc
                event_message = {
                    "type": "LEADS_SUBMIT",
                    "data": {
                        "name": lead_data.get("name"),
                        "email": lead_data.get("email"),
                        "phone": lead_data.get("phone"),
                        "message": lead_data.get("message"),
                        "botId": str(bot["_id"])
                    }
                }

                # Đẩy vào Redis Stream
                stream_name = "WEBHOOK_SEND_EVENT_STREAM"
                await redis_manager.client.xadd(
                    stream_name,
                    {"message": json.dumps(event_message)},
                    id="*"
                )
                logger.bind(context="Webhook").info(f"Pushed leads.submit event to stream for bot {bot['_id']}")
        except Exception as e:
            logger.bind(context="Webhook").error(f"Error triggering leads webhook: {e}")
