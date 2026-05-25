from app.repositories.social_repository import SocialPageRepository
import httpx
from fastapi import HTTPException, status
from loguru import logger
from app.core.config import settings

class TelegramService:
    def __init__(self, social_repo: SocialPageRepository):
        self.social_repo = social_repo
        self.base_url = "https://api.telegram.org/bot"

    async def get_bot_info(self, bot_token: str) -> dict:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{self.base_url}{bot_token}/getMe")
            if response.status_code != 200:
                logger.error(f"Failed to get Telegram bot info: {response.text}")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Token không hợp lệ hoặc không thể kết nối tới Telegram"
                )
            return response.json()["result"]

    async def set_webhook(self, bot_token: str, tele_id: int) -> bool:
        webhook_url = f"{settings.DOMAIN_URL}{settings.API_V1_STR}/telegram/webhook/{tele_id}"
        secret_token = settings.social.tele_secret_token
        
        async with httpx.AsyncClient() as client:
            params = {
                "url": webhook_url,
                "secret_token": secret_token
            }
            response = await client.post(
                f"{self.base_url}{bot_token}/setWebhook",
                json=params
            )
            if response.status_code != 200:
                logger.error(f"Failed to set Telegram webhook: {response.text}")
                return False
            return True

    async def connect_bot(self, bot_id: str, bot_token: str):
        # 1. Lấy thông tin Bot từ Telegram
        bot_info = await self.get_bot_info(bot_token)
        tele_id = bot_info["id"]
        name = " ".join(filter(None, [bot_info.get("first_name"), bot_info.get("last_name")]))

        # 2. Thiết lập Webhook
        webhook_success = await self.set_webhook(bot_token, tele_id)
        if not webhook_success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Không thể thiết lập Webhook với Telegram"
            )

        # 3. Lưu vào database
        social_data = {
            "pageId": str(tele_id),
            "botId": bot_id,
            "channel": "telegram",
            "name": name,
            "pageAccessToken": bot_token,
            "username": bot_info.get("username")
        }
        
        await self.social_repo.update_by_page_id(str(tele_id), social_data)
        
        return {
            "pageId": str(tele_id),
            "name": name,
            "username": bot_info.get("username"),
            "channel": "telegram"
        }
