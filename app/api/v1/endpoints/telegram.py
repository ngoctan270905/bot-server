from fastapi import APIRouter, Depends, status
from app.schemas.telegram import TelegramConnectRequest
from app.services.telegram_service import telegram_service
from app.schemas.base import UnifiedResponse

router = APIRouter()

@router.post("/connect", status_code=status.HTTP_200_OK, response_model=UnifiedResponse)
async def connect_telegram(request_data: TelegramConnectRequest):
    """
    Kết nối Telegram Bot vào hệ thống và thiết lập Webhook.
    """
    result = await telegram_service.connect_bot(
        bot_id=request_data.bot_id,
        bot_token=request_data.bot_token
    )
    return UnifiedResponse(
        success=True,
        message="Kết nối Telegram Bot thành công",
        data=result
    )
