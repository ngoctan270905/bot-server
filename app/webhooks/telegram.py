from fastapi import APIRouter, Depends, status, Header, HTTPException, Request
from app.schemas.telegram import TelegramUpdate
from app.core.config import settings
from app.db.redis import redis_manager
import json

router = APIRouter()

@router.post("/telegram/{tele_id}", status_code=status.HTTP_200_OK)
async def telegram_webhook(
    tele_id: str,
    update: TelegramUpdate,
    x_telegram_bot_api_secret_token: str = Header(None, alias="X-Telegram-Bot-Api-Secret-Token")
):
    """
    Receive webhook updates from Telegram and push them into a Redis Stream.
    """
    # 1. Validate the secret token
    if x_telegram_bot_api_secret_token != settings.social.tele_secret_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Unauthorized"
        )

    # 2. Push the event into Redis Stream
    stream_name = "TELEGRAM_MESSAGE_STREAM"
    
    event_data = {
        "telebotId": tele_id,
        "payload": update.model_dump_json(by_alias=True)
    }

    await redis_manager.client.xadd(stream_name, event_data)

    return {"ok": True}
