from fastapi import APIRouter, Depends, status, Body
from app.schemas.telegram import TelegramConnectRequest, TelegramDisconnectRequest
from app.services.telegram_service import TelegramService
from app.api.v1.dependencies import get_telegram_service
from app.schemas.base import UnifiedResponse
from app.core.exceptions import BadRequestException

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

@router.delete("/connect", status_code=status.HTTP_200_OK, response_model=UnifiedResponse)
async def disconnect_telegram(
    request_data: TelegramDisconnectRequest,
    telegram_service: TelegramService = Depends(get_telegram_service)
):
    """
    Disconnect a Telegram bot and remove its webhook
    """
    success = await telegram_service.disconnect_bot(bot_id=request_data.bot_id)
    if not success:
        raise BadRequestException(detail="Failed to disconnect Telegram bot or bot not found")
        
    return UnifiedResponse(
        success=True,
        message="Telegram bot disconnected successfully",
        data=None
    )
