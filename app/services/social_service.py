from datetime import datetime, timezone
import httpx
import json
import urllib.parse
from typing import Optional, List
from app.core.config import settings
from app.repositories.social_repository import SocialPageRepository
from app.schemas.social import ChannelEnum
from loguru import logger


class SocialService:
    """
    Service xử lý tích hợp Facebook Messenger Platform.

    Chức năng chính:
    - Tạo URL đăng nhập Facebook OAuth
    - Lấy Facebook User Access Token
    - Lấy danh sách Facebook Pages
    - Subscribe webhook cho Fanpage
    - Lưu hoặc cập nhật thông tin Fanpage
    - Lấy profile người dùng Facebook
    - Gửi tin nhắn Messenger qua Graph API
    """

    def __init__(self, social_repo: SocialPageRepository):
        """
        Khởi tạo SocialService.

        Args:
            social_repo (SocialPageRepository):
                Repository dùng để thao tác dữ liệu social page trong database.
        """
        self._social_repo = social_repo
        self._fb_graph_url = "https://graph.facebook.com/v25.0"

        # Danh sách quyền Facebook app yêu cầu khi OAuth
        self._scope = [
            "pages_show_list",
            "pages_manage_metadata",
            "pages_messaging"
        ]

        # Danh sách webhook events cần subscribe cho Fanpage
        self._subscribed_fields = [
            "messages",
            "messaging_postbacks",
            "messaging_optins",
            "messaging_optouts",
            "message_deliveries",
            "message_reads",
            "messaging_payments",
            "messaging_pre_checkouts",
            "messaging_checkout_updates",
            "messaging_account_linking",
            "messaging_referrals",
            "message_echoes",
            "messaging_game_plays",
            "standby",
            "messaging_handovers",
            "messaging_policy_enforcement",
            "message_reactions",
            "inbox_labels",
            "messaging_feedback",
            "messaging_customer_information",
            "group_feed"
        ]

    def get_facebook_login_url(
        self,
        bot_id: str,
        project_id: str,
        redirect_url: Optional[str] = None
    ) -> str:
        """
        Tạo Facebook OAuth Login URL.

        URL này dùng để redirect người dùng sang Facebook đăng nhập
        và cấp quyền cho ứng dụng.

        Args:
            bot_id (str):
                ID của bot nội bộ hệ thống.

            project_id (str):
                ID của project liên kết với bot.

            redirect_url (Optional[str]):
                URL frontend cần redirect sau khi OAuth thành công.

        Returns:
            str:
                Facebook OAuth URL hoàn chỉnh.
        """
        state_data = {
            "botId": bot_id,
            "projectId": project_id,
        }

        if redirect_url:
            state_data["redirectUrl"] = redirect_url

        state_str = json.dumps(state_data)

        params = {
            "scope": ",".join(self._scope),
            "client_id": settings.social.fb_app_id,
            "redirect_uri": settings.social.fb_redirect_uri,
            "response_type": "code",
            "state": state_str
        }

        query_string = urllib.parse.urlencode(params)

        return f"{self._fb_graph_url}/oauth/authorize?{query_string}"

    async def get_facebook_access_token(self, code: str) -> str:
        """
        Lấy Facebook User Access Token từ OAuth code.

        Sau khi user đăng nhập Facebook thành công,
        Facebook sẽ trả về authorization code.
        Hàm này dùng code đó để đổi lấy access token.

        Args:
            code (str):
                Authorization code từ Facebook OAuth callback.

        Returns:
            str:
                Facebook User Access Token.

        Raises:
            Exception:
                Khi không thể lấy access token từ Facebook API.
        """
        params = {
            "client_id": settings.social.fb_app_id,
            "client_secret": settings.social.fb_app_secret,
            "redirect_uri": settings.social.fb_redirect_uri,
            "code": code
        }

        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self._fb_graph_url}/oauth/access_token",
                params=params
            )

            data = response.json()

            if response.status_code != 200:
                logger.error(f"Failed to get FB access token: {data}")

                raise Exception(
                    f"Failed to get access token: "
                    f"{data.get('error', {}).get('message')}"
                )

            access_token = data["access_token"]

            logger.bind(context="Social").info(
                f"Obtained FB User Access Token: {access_token}"
            )

            return access_token

    async def get_facebook_pages_info(
        self,
        user_access_token: str
    ) -> List[dict]:
        """
        Lấy danh sách Fanpage mà user đang quản lý.

        Facebook API `/me/accounts` sẽ trả về:
        - page id
        - page name
        - page access token

        Args:
            user_access_token (str):
                Facebook User Access Token.

        Returns:
            List[dict]:
                Danh sách thông tin Fanpage.

        Raises:
            Exception:
                Khi gọi Facebook API thất bại.
        """
        headers = {
            "Authorization": f"Bearer {user_access_token}"
        }

        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self._fb_graph_url}/me/accounts",
                headers=headers
            )

            data = response.json()

            if response.status_code != 200:
                logger.error(f"Failed to get FB pages: {data}")

                raise Exception(
                    f"Failed to get pages info: "
                    f"{data.get('error', {}).get('message')}"
                )

            return data.get("data", [])

    async def subscribe_page_to_webhook(
        self,
        page_id: str,
        page_access_token: str
    ):
        """
        Subscribe Fanpage vào webhook events.

        Sau khi subscribe thành công,
        Facebook sẽ gửi webhook events về server của hệ thống.

        Args:
            page_id (str):
                Facebook Page ID.

            page_access_token (str):
                Facebook Page Access Token.

        Returns:
            dict:
                Response từ Facebook API.

        Raises:
            Exception:
                Khi subscribe webhook thất bại.
        """
        params = {
            "subscribed_fields": ",".join(self._subscribed_fields),
            "access_token": page_access_token
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self._fb_graph_url}/{page_id}/subscribed_apps",
                params=params
            )

            data = response.json()

            if response.status_code != 200:
                logger.error(f"Failed to subscribe page {page_id}: {data}")

                raise Exception(
                    f"Failed to subscribe to page events: "
                    f"{data.get('error', {}).get('message')}"
                )

            return data

    async def save_or_update_social_page(
        self,
        page_data: dict,
        bot_id: str
    ):
        """
        Lưu mới hoặc cập nhật thông tin Fanpage vào database.

        Nếu Fanpage chưa tồn tại:
        - tạo mới dữ liệu

        Nếu Fanpage đã tồn tại:
        - cập nhật token và thông tin mới nhất

        Args:
            page_data (dict):
                Dữ liệu Fanpage từ Facebook API.

            bot_id (str):
                ID bot liên kết với Fanpage.
        """
        existing = await self._social_repo.get_by_page_id(
            page_data["id"]
        )

        save_data = {
            "name": page_data["name"],
            "pageAccessToken": page_data["access_token"],
            "pageId": page_data["id"],
            "channel": ChannelEnum.FACEBOOK.value,
            "botId": bot_id,
            "active": True
        }

        if not existing:
            save_data["createdAt"] = datetime.now(timezone.utc)

            await self._social_repo.create(save_data)
        else:
            await self._social_repo.update_by_page_id(
                page_data["id"],
                save_data
            )

    async def get_user_profile(
        self,
        profile_id: str,
        page_access_token: str
    ) -> Optional[dict]:
        """
        Lấy thông tin profile người dùng Facebook.

        API trả về:
        - tên
        - avatar
        - giới tính
        - timezone
        - locale

        Args:
            profile_id (str):
                Facebook PSID của user.

            page_access_token (str):
                Facebook Page Access Token.

        Returns:
            Optional[dict]:
                Thông tin user profile hoặc None nếu thất bại.
        """
        params = {
            "fields": "name,profile_pic,gender,timezone,locale",
            "access_token": page_access_token
        }

        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self._fb_graph_url}/{profile_id}",
                params=params
            )

            if response.status_code != 200:
                logger.error(
                    f"Failed to get user profile {profile_id}: "
                    f"{response.json()}"
                )

                return None

            return response.json()

    async def send_facebook_message(
        self,
        page_access_token: str,
        recipient_id: str,
        message_text: str
    ):
        """
        Gửi tin nhắn Messenger tới người dùng Facebook.

        Args:
            page_access_token (str):
                Facebook Page Access Token.

            recipient_id (str):
                Facebook PSID của người nhận.

            message_text (str):
                Nội dung tin nhắn cần gửi.

        Returns:
            dict:
                Response từ Facebook Graph API.

        Raises:
            Exception:
                Khi gửi tin nhắn thất bại.
        """
        url = f"{self._fb_graph_url}/me/messages"

        params = {
            "access_token": page_access_token
        }

        payload = {
            "recipient": {
                "id": recipient_id
            },
            "messaging_type": "RESPONSE",
            "message": {
                "text": message_text
            }
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(
                url,
                params=params,
                json=payload
            )

            if response.status_code != 200:
                logger.error(
                    f"Failed to send FB message to {recipient_id}: "
                    f"{response.json()}"
                )

                raise Exception(
                    f"Failed to send message: "
                    f"{response.json().get('error', {}).get('message')}"
                )

            return response.json()