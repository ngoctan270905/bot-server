from fastapi import APIRouter
from app.schemas.webhook import WebhookEvent
from app.schemas.base import UnifiedResponse

router = APIRouter()

# Danh sách các sự kiện webhook được hỗ trợ
WEBHOOK_EVENTS = [
    {"id": "leads.submit", "name": "Leads Submit"}
]

@router.get("/list-event", response_model=UnifiedResponse)
async def list_webhook_events():
    """
    Trả về danh sách các sự kiện Webhook mà hệ thống hỗ trợ.
    """
    return UnifiedResponse(
        success=True,
        message="Fetched webhook events successfully",
        data=WEBHOOK_EVENTS
    )
