from datetime import datetime, timezone
from app.repositories.user_repository import UserRepository
from app.repositories.email_password_repository import EmailPasswordUserRepository
from app.core.security import get_password_hash, verify_password, create_access_token, create_refresh_token
from app.schemas.user import UserCreateResponse, UserDetailResponse
from app.schemas.base import UnifiedResponse
from app.core.exceptions import (
    BadRequestException, 
    ConflictException, 
    NotFoundException
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

    async def register_email_password(self, user_in: dict) -> UnifiedResponse[UserCreateResponse]:
        """
        Đăng ký tài khoản bằng email/password.
        """
        email = user_in.get("email")
        password = user_in.get("password")
        
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
            "name": user_in.get("name", email.split("@")[0]),
            "provider": "email",
            "active": True,
            "created_at": datetime.now(timezone.utc)
        }
        new_user = await self._user_repo.create(user_data)
        
        # 4. Cập nhật ngược lại relation
        await self._email_pw_repo.update(new_email_pw["_id"], {"userId": new_user["_id"]})
        
        data = UserCreateResponse(
            _id=new_user["_id"],
            name=new_user["name"],
            provider=new_user["provider"],
            active=new_user["active"]
        )
        return UnifiedResponse[UserCreateResponse](
            success=True,
            message="User registered successfully",
            data=data
        )

    async def login_email_password(self, email: str, password: str) -> dict:
        """
        Đăng nhập bằng email/password.
        Trả về cấu trúc phẳng để tương thích với OAuth2 (Swagger Authorize).
        """
        # 1. Tìm EmailPasswordUser
        email_pw_user = await self._email_pw_repo.get_by_email(email)
        if not email_pw_user:
            raise BadRequestException(detail="User not found.")
            
        # 2. Kiểm tra password
        if not verify_password(password, email_pw_user["password"]):
            raise BadRequestException(detail="Invalid password.")
            
        # 3. Tìm User chính
        user = await self._user_repo.find_one({"_id": email_pw_user.get("userId")})
        if not user:
            user = await self._user_repo.create({
                "provider": "email",
                "active": True,
                "name": email.split("@")[0]
            })
            await self._email_pw_repo.update(email_pw_user["_id"], {"userId": user["_id"]})

        # 4. Tạo tokens
        access_token = create_access_token(subject=user["_id"])
        refresh_token = create_refresh_token(subject=user["_id"])
        
        # 5. Lưu token vào DB
        await self._user_repo.update_tokens(user["_id"], access_token, refresh_token)
        
        # Trả về cấu trúc phẳng cho OAuth2
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "refresh_token": refresh_token
        }

    async def get_my_profile(self, user_id: str) -> UnifiedResponse[UserDetailResponse]:
        """
        Lấy thông tin cá nhân.
        """
        user = await self._user_repo.get_by_id(user_id)
        if not user:
            raise NotFoundException(detail="Profile not found.")
        
        # Lấy thêm thông tin email_pw để trả về
        email_pw = await self._email_pw_repo.find_one({"userId": user_id})
        if email_pw:
            user["emailPw"] = email_pw
            
        data = UserDetailResponse.model_validate(user)
        return UnifiedResponse[UserDetailResponse](
            success=True,
            message="Profile fetched successfully",
            data=data
        )
