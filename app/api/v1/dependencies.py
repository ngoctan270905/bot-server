from fastapi import Depends, status
from fastapi.security import OAuth2PasswordBearer
from app.core.config import settings
from app.core.exceptions import (
    UnauthorizedException, 
    BadRequestException, 
    ForbiddenException
)
from app.core.security import decode_token
from app.db.mongodb import get_database
from app.repositories.user_repository import UserRepository
from app.repositories.email_password_repository import EmailPasswordUserRepository
from app.services.auth_service import AuthService
from app.services.profile_service import ProfileService
from app.schemas.user import UserDetailResponse

# Định nghĩa scheme xác thực OAuth2
oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl=f"{settings.API_V1_STR}/auth/login"
)

async def get_user_repository(db = Depends(get_database)) -> UserRepository:
    """Dependency cung cấp UserRepository."""
    return UserRepository(collection=db["User"])

async def get_email_password_repository(db = Depends(get_database)) -> EmailPasswordUserRepository:
    """Dependency cung cấp EmailPasswordUserRepository."""
    return EmailPasswordUserRepository(collection=db["EmailPasswordUser"])

async def get_auth_service(
    user_repo: UserRepository = Depends(get_user_repository),
    email_pw_repo: EmailPasswordUserRepository = Depends(get_email_password_repository)
) -> AuthService:
    """Dependency cung cấp AuthService."""
    return AuthService(user_repository=user_repo, email_pw_repository=email_pw_repo)

async def get_profile_service(
    user_repo: UserRepository = Depends(get_user_repository),
    email_pw_repo: EmailPasswordUserRepository = Depends(get_email_password_repository)
) -> ProfileService:
    """Dependency cung cấp ProfileService."""
    return ProfileService(user_repository=user_repo, email_pw_repository=email_pw_repo)

async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db = Depends(get_database)
) -> UserDetailResponse:
    """
    Dependency lấy thông tin user hiện tại từ access token.
    Thực hiện truy vấn DB để đảm bảo user vẫn tồn tại và token là mới nhất.
    """
    payload = decode_token(token)
    user_id: str = payload.get("sub")

    user_repo = UserRepository(collection=db["User"])
    user_raw = await user_repo.get_user_by_id(user_id)

    if user_raw is None:
        raise UnauthorizedException(detail="Người dùng không tồn tại")

    # Cơ chế Single Session (giống dự án gốc)
    if user_raw.get("token") != token:
        raise UnauthorizedException(detail="Phiên đăng nhập đã hết hạn hoặc đã đăng nhập ở nơi khác")

    if not user_raw.get("active", True):
        raise BadRequestException(detail="Tài khoản đã bị vô hiệu hóa")

    return UserDetailResponse.model_validate(user_raw)

