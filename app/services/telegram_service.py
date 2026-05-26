import httpx
from loguru import logger
from app.core.config import settings
from app.repositories.social_repository import SocialPageRepository
from app.core.exceptions import (
    BadRequestException,
    InternalServerException
)

class TelegramService:
    """Service xử lý Telegram Bot API."""

    def __init__(self, social_repo: SocialPageRepository):
        """Inject repository để thao tác DB."""
        self.social_repo = social_repo
        self.base_url = "https://api.telegram.org/bot"

    async def get_bot_info(self, bot_token: str) -> dict:
        """Lấy thông tin bot từ Telegram."""

        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}{bot_token}/getMe"
            )

            # Quan trọng: Telegram fail thường trả 200 nhưng ok=false
            # nhưng vẫn check status_code để bắt lỗi network
            if response.status_code != 200:
                logger.error(
                    f"Failed to get Telegram bot info: {response.text}"
                )

                raise BadRequestException(
                    detail="Token không hợp lệ hoặc không thể kết nối tới Telegram"
                )

            return response.json()["result"]

    async def set_webhook(self, bot_token: str, tele_id: int) -> bool:
        """Đăng ký webhook để Telegram push event về server."""

        # URL này phải public (https) thì Telegram mới accept
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

            # Quan trọng: nếu webhook fail thì bot coi như không hoạt động
            if response.status_code != 200:
                logger.error(
                    f"Failed to set Telegram webhook: {response.text}"
                )
                return False

            return True

    async def connect_bot(self, bot_id: str, bot_token: str):
        """Kết nối bot: verify -> set webhook -> lưu DB."""

        # 1. Verify token + lấy info bot
        bot_info = await self.get_bot_info(bot_token)

        tele_id = bot_info["id"]

        # Ghép tên bot (có thể thiếu last_name nên filter None)
        name = " ".join(
            filter(
                None,
                [
                    bot_info.get("first_name"),
                    bot_info.get("last_name")
                ]
            )
        )

        # 2. Set webhook (fail là dừng luôn flow)
        webhook_success = await self.set_webhook(
            bot_token,
            tele_id
        )

        if not webhook_success:
            raise InternalServerException(
                detail="Không thể thiết lập Webhook với Telegram"
            )

        # 3. Lưu thông tin bot vào DB
        social_data = {
            "pageId": str(tele_id),
            "botId": bot_id,
            "channel": "telegram",
            "name": name,
            "pageAccessToken": bot_token,
            "username": bot_info.get("username"),
            "active": True
        }

        await self.social_repo.update_by_page_id(
            str(tele_id),
            social_data
        )

        # 4. Lấy lại record để trả về API
        saved_page = await self.social_repo.get_by_page_id(
            str(tele_id)
        )

        # Mongo ObjectId -> string để tránh lỗi serialize JSON
        if saved_page and "_id" in saved_page:
            saved_page["_id"] = str(saved_page["_id"])

        return saved_page

    async def send_message(
        self,
        bot_token: str,
        chat_id: int,
        text: str
    ):
        """Gửi message tới Telegram user/chat."""

        async with httpx.AsyncClient() as client:
            payload = {
                "chat_id": chat_id,
                "text": text
            }

            response = await client.post(
                f"{self.base_url}{bot_token}/sendMessage",
                json=payload
            )

            # Quan trọng: nếu fail thì cần log để debug webhook flow
            if response.status_code != 200:
                logger.error(
                    f"Failed to send Telegram message: {response.text}"
                )