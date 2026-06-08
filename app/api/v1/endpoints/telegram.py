from fastapi import APIRouter, Depends, status
from app.schemas.telegram import TelegramConnectRequest
from app.services.telegram_service import TelegramService
from app.api.v1.dependencies import get_telegram_service
from app.schemas.base import UnifiedResponse

router = APIRouter()

@router.post("/connect", status_code=status.HTTP_200_OK, response_model=UnifiedResponse)
async def connect_telegram(
    request_data: TelegramConnectRequest,
    telegram_service: TelegramService = Depends(get_telegram_service)
):
    """
    Connect a Telegram bot to the system and set up a webhook
    """
    result = await telegram_service.connect_bot(
        bot_id=request_data.bot_id,
        bot_token=request_data.bot_token
    )
    return UnifiedResponse(
        success=True,
        message="Telegram bot connected successfully",
        data=result
    )
