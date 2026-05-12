from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from app.core.config import settings
from app.core.exceptions import UnauthorizedException
from app.core.security import decode_token
from app.db.mongodb import get_database
from app.repositories.user_repository import UserRepository
from app.schemas.user import UserMeResponse

# Định nghĩa scheme xác thực OAuth2 (header Authorization: Bearer <token>)
oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl=f"{settings.API_V1_STR}/auth/login"
)

async def get_user_repository(db = Depends(get_database)) -> UserRepository:
    """Dependency cung cấp UserRepository."""
    return UserRepository(collection=db["users"])

async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db = Depends(get_database)
) -> UserMeResponse:
    """
    Dependency lấy thông tin user hiện tại từ access token.
    Thực hiện truy vấn DB để đảm bảo user vẫn tồn tại, đang hoạt động
    và token cung cấp là token mới nhất (Single Session logic giống dự án gốc).
    """
    # 1. Giải mã token để lấy subject (user_id)
    payload = decode_token(token)
    user_id: str = payload.get("sub")

    user_repo = UserRepository(collection=db["users"])
    user_raw = await user_repo.get_user_by_id(user_id)

    if user_raw is None:
        raise UnauthorizedException(detail="Người dùng không tồn tại")

    # 2. Cơ chế Single Session giống dự án gốc
    if user_raw.get("token") != token:
        raise UnauthorizedException(detail="Phiên đăng nhập đã hết hạn hoặc đã đăng nhập ở nơi khác")

    if not user_raw.get("is_active", True):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Tài khoản đã bị vô hiệu hóa"
        )

    user_raw['_id'] = str(user_id)

    return UserMeResponse(**user_raw)


async def get_admin_user(current_user: UserMeResponse = Depends(get_current_user)) -> UserMeResponse:
    """
    Dependency để đảm bảo người dùng hiện tại có vai trò "admin".
    """
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Bạn không có quyền truy cập vào tài nguyên này."
        )
    return current_user
