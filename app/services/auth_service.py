from datetime import datetime, timezone
import secrets
import string
from typing import Any
from bson import ObjectId
import httpx

from app.repositories.user_repository import UserRepository
from app.repositories.email_password_repository import EmailPasswordUserRepository
from app.core.security import (
    get_password_hash,
    verify_password,
    create_access_token,
    create_refresh_token,
    decode_token
)
from app.schemas.user import UserCreate, UserCreateResponse, UserDetailResponse
from app.schemas.auth import Token
from app.schemas.base import UnifiedResponse
from app.core.exceptions import (
    BadRequestException,
    ConflictException,
    NotFoundException,
    UnauthorizedException
)

class AuthService:
    """
    Service xử lý logic xác thực và người dùng.
    """
    def __init__(
        self,
        user_repository: UserRepository,
        email_pw_repository: EmailPasswordUserRepository
    ):
        self._user_repo = user_repository
        self._email_pw_repo = email_pw_repository

    async def register_email_password(self, user_in: UserCreate) -> Token:
        """
        Đăng ký tài khoản bằng email/password.
        Trả về tokens ngay sau khi đăng ký.
        """
        email = user_in.email
        password = user_in.password

        # 1. Kiểm tra tồn tại
        existing_pw_user = await self._email_pw_repo.get_by_email(email)
        if existing_pw_user:
            raise ConflictException(detail="User with this email already exists.")

        # 2. Tạo EmailPasswordUser
        hashed_password = get_password_hash(password)
        email_pw_data = {
            "email": email,
            "password": hashed_password
        }
        new_email_pw = await self._email_pw_repo.create(email_pw_data)

        # 3. Tạo User chính liên kết
        user_data = {
            "name": email.split("@")[0],
            "provider": "email",
            "active": True,
            "created_at": datetime.now(timezone.utc)
        }
        new_user = await self._user_repo.create(user_data)

        # 4. Cập nhật ngược lại relation
        await self._email_pw_repo.update(new_email_pw["_id"], {"userId": new_user["_id"]})

        # 5. Tạo tokens
        access_token = create_access_token(subject=new_user["_id"])
        refresh_token = create_refresh_token(subject=new_user["_id"])

        # 6. Lưu token vào DB
        await self._user_repo.update_tokens(new_user["_id"], access_token, refresh_token)

        return Token(
            access_token=access_token,
            token_type="bearer",
            refresh_token=refresh_token
        )

    async def login_email_password(self, email: str, password: str) -> Token:
        """
        Đăng nhập bằng email/password.
        """
        # 1. Tìm EmailPasswordUser
        email_pw_user = await self._email_pw_repo.get_by_email(email)
        if not email_pw_user:
            raise BadRequestException(detail="User not found.")

        # 2. Kiểm tra password
        if not verify_password(password, email_pw_user["password"]):
            raise BadRequestException(detail="Invalid password.")

        # 3. Tìm User chính
        user_id = email_pw_user.get("userId")
        if not user_id:
            raise BadRequestException(detail="User data corruption: Missing userId in password record.")

        user = await self._user_repo.get_by_id(str(user_id))
        if not user:
            raise BadRequestException(detail="User not found.")

        # 4. Tạo tokens
        access_token = create_access_token(subject=user["_id"])
        refresh_token = create_refresh_token(subject=user["_id"])

        # 5. Lưu token vào DB
        await self._user_repo.update_tokens(user["_id"], access_token, refresh_token)

        return Token(
            access_token=access_token,
            token_type="bearer",
            refresh_token=refresh_token
        )

    async def logout(self, user_id: str) -> None:
        """
        Đăng xuất: Xóa token và refreshToken trong database.
        """
        await self._user_repo.update_tokens(user_id, "", "")
        return None

    async def refresh_token(self, refresh_token: str) -> Token:
        """
        Làm mới Access Token từ Refresh Token.
        """
        try:
            payload = decode_token(refresh_token)
            user_id = payload.get("sub")

            user = await self._user_repo.get_by_id(user_id)
            if not user or user.get("refresh_token") != refresh_token:
                raise UnauthorizedException(detail="Invalid refresh token")

            new_access_token = create_access_token(subject=user_id)
            await self._user_repo.update(user_id, {"token": new_access_token})

            return Token(
                access_token=new_access_token,
                token_type="bearer",
                refresh_token=refresh_token
            )
        except Exception:
            raise UnauthorizedException(detail="Refresh token expired or invalid")

    async def reset_password(self, user_id: str, current_password: str, new_password: str) -> None:
        """
        Đổi mật khẩu cho người dùng đã đăng nhập.
        """
        email_pw = await self._email_pw_repo.find_one({"userId": user_id})
        if not email_pw:
            raise BadRequestException(detail="User does not have an email/password account")

        if not verify_password(current_password, email_pw["password"]):
            raise BadRequestException(detail="Invalid current password")

        new_hashed_password = get_password_hash(new_password)
        await self._email_pw_repo.update(email_pw["_id"], {"password": new_hashed_password})

        return None

    async def forgot_password(self, email: str) -> None:
        """
        Quên mật khẩu: Tạo mật khẩu ngẫu nhiên và cập nhật.
        """
        email_pw = await self._email_pw_repo.get_by_email(email)
        if not email_pw:
            raise NotFoundException(detail="User with this email does not exist.")

        # Tạo mật khẩu ngẫu nhiên
        new_password = ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(12))
        hashed_pw = get_password_hash(new_password)

        await self._email_pw_repo.update(email_pw["_id"], {"password": hashed_pw})

        # TODO: Gửi email chứa new_password ở đây
        # await send_forgot_password_email(email, new_password)

        return None

    async def login_facebook(self, access_token: str) -> Token:
        """
        Đăng nhập bằng Facebook Access Token.
        """
        url = "https://graph.facebook.com/me"
        params = {
            "fields": "id,name,email",
            "access_token": access_token
        }

        async with httpx.AsyncClient() as client:
            response = await client.get(url, params=params)
            if response.status_code != 200:
                raise UnauthorizedException(detail="Invalid Facebook access token")

            fb_user = response.json()
            profile_id = fb_user.get("id")
            email = fb_user.get("email")
            name = fb_user.get("name")

        return await self.login_social(
            provider="fb",
            profile_id=profile_id,
            email=email,
            access_token=access_token,
            name=name
        )

    async def login_social(self, provider: str, profile_id: str, email: str | None, access_token: str, name: str | None = None) -> Token:
        """
        Logic chung cho Social Login.
        """
        provider_filter = {
            "provider": provider,
            f"{provider}.profileId": profile_id
        }
        user = await self._user_repo.find_one(provider_filter)

        if not user:
            user_data = {
                "name": name or (email.split("@")[0] if email else provider),
                "provider": provider,
                "active": True,
                f"{provider}": {
                    "profileId": profile_id,
                    "accessToken": access_token,
                    "email": email
                },
                "created_at": datetime.now(timezone.utc)
            }
            user = await self._user_repo.create(user_data)
        else:
            await self._user_repo.update(user["_id"], {f"{provider}.accessToken": access_token})

        access_token_jwt = create_access_token(subject=user["_id"])
        refresh_token_jwt = create_refresh_token(subject=user["_id"])

        await self._user_repo.update_tokens(user["_id"], access_token_jwt, refresh_token_jwt)

        return Token(
            access_token=access_token_jwt,
            token_type="bearer",
            refresh_token=refresh_token_jwt
        )
