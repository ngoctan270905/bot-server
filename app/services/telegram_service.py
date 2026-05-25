import httpx
from loguru import logger
from app.core.config import settings
from app.repositories.social_repository import SocialPageRepository
from app.core.exceptions import BadRequestException, InternalServerException

class TelegramService:
    def __init__(self, social_repo: SocialPageRepository):
        self.social_repo = social_repo
        self.base_url = "https://api.telegram.org/bot"

    async def get_bot_info(self, bot_token: str) -> dict:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{self.base_url}{bot_token}/getMe")
            if response.status_code != 200:
                logger.error(f"Failed to get Telegram bot info: {response.text}")
                raise BadRequestException(
                    detail="Token không hợp lệ hoặc không thể kết nối tới Telegram"
                )
            return response.json()["result"]

    async def set_webhook(self, bot_token: str, tele_id: int) -> bool:
        # URL Webhook giống bản Node: /webhook/telegram/{id} (không có /api/v1)
        webhook_url = f"{settings.DOMAIN_URL}/webhook/telegram/{tele_id}"
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
        bot_info = await self.get_bot_info(bot_token)
        tele_id = bot_info["id"]
        name = " ".join(filter(None, [bot_info.get("first_name"), bot_info.get("last_name")]))

        webhook_success = await self.set_webhook(bot_token, tele_id)
        if not webhook_success:
            raise InternalServerException(
                detail="Không thể thiết lập Webhook với Telegram"
            )

        social_data = {
            "pageId": str(tele_id),
            "botId": bot_id,
            "channel": "telegram",
            "name": name,
            "pageAccessToken": bot_token,
            "username": bot_info.get("username"),
            "active": True
        }
        
        await self.social_repo.update_by_page_id(str(tele_id), social_data)
        
        saved_page = await self.social_repo.get_by_page_id(str(tele_id))
        if saved_page and "_id" in saved_page:
            saved_page["_id"] = str(saved_page["_id"])
            
        return saved_page

    async def send_message(self, bot_token: str, chat_id: int, text: str):
        """Gửi tin nhắn phản hồi tới Telegram."""
        async with httpx.AsyncClient() as client:
            payload = {
                "chat_id": chat_id,
                "text": text
            }
            response = await client.post(
                f"{self.base_url}{bot_token}/sendMessage",
                json=payload
            )
            if response.status_code != 200:
                logger.error(f"Failed to send Telegram message: {response.text}")
