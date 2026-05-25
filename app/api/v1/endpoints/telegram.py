from fastapi import APIRouter, Depends, status, Header, HTTPException, Request
from app.schemas.telegram import TelegramConnectRequest, TelegramUpdate
from app.services.telegram_service import telegram_service
from app.schemas.base import UnifiedResponse
from app.core.config import settings
from app.db.redis import redis_manager
import json

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

@router.post("/webhook/{tele_id}", status_code=status.HTTP_200_OK)
async def telegram_webhook(
    tele_id: str,
    update: TelegramUpdate,
    x_telegram_bot_api_secret_token: str = Header(None, alias="X-Telegram-Bot-Api-Secret-Token")
):
    """
    Tiếp nhận Webhook từ Telegram và đẩy vào Redis Stream.
    """
    # 1. Xác thực Secret Token
    if x_telegram_bot_api_secret_token != settings.social.tele_secret_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Unauthorized"
        )

    # 2. Đẩy vào Redis Stream
    # Lưu ý: Chúng ta dùng Redis Stream 'TELEGRAM_MESSAGE_STREAM' giống như bản Nodejs
    stream_name = "TELEGRAM_MESSAGE_STREAM"
    
    # Chuẩn bị dữ liệu để push vào Stream (phải là dict dạng {key: value})
    event_data = {
        "telebotId": tele_id,
        "payload": update.model_dump_json(by_alias=True)
    }

    await redis_manager.client.xadd(stream_name, event_data)

    return {"ok": True}
