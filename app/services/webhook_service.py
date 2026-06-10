from typing import Optional, List
from app.repositories.webhook_repository import WebhookRepository
from app.schemas.webhook import WebhookDetailResponse, WebhookEvent

# Danh sách các sự kiện webhook được hỗ trợ
WEBHOOK_EVENTS = [
    {"id": "leads.submit", "name": "Leads Submit"}
]

class WebhookService:
    def __init__(self, webhook_repo: WebhookRepository):
        self._webhook_repo = webhook_repo

    async def get_webhook_by_bot_id(self, bot_id: str) -> Optional[dict]:
        """
        Lấy chi tiết cấu hình Webhook của một Bot và map thông tin events.
        """
        webhook = await self._webhook_repo.get_by_bot_id(bot_id)
        if not webhook:
            return None

        # Map list event ID sang list object {id, name}
        mapped_events = []
        for event_id in webhook.get("events", []):
            event_info = next((e for e in WEBHOOK_EVENTS if e["id"] == event_id), None)
            if event_info:
                mapped_events.append(event_info)
            else:
                mapped_events.append({"id": event_id, "name": event_id})

        webhook["events"] = mapped_events
        return webhook

    async def list_events(self) -> List[dict]:
        """Trả về danh sách tất cả các sự kiện webhook hỗ trợ."""
        return WEBHOOK_EVENTS
