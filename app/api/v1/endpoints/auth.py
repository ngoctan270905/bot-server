from fastapi import APIRouter, Depends, status, Body
from fastapi.security import OAuth2PasswordRequestForm
from typing import Any

from app.services.auth_service import AuthService
from app.api.v1.dependencies import get_auth_service, get_current_user
from app.schemas.user import UserCreate, UserDetailResponse
from app.schemas.auth import Token, RefreshTokenRequest

router = APIRouter()

@router.post("/register", response_model=Token, status_code=status.HTTP_201_CREATED)
async def register(
    user_in: UserCreate,
    auth_service: AuthService = Depends(get_auth_service)
) -> Token:
    """
    Đăng ký tài khoản mới và trả về Token.
    """
    return await auth_service.register_email_password(user_in)

@router.post("/login", response_model=Token)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    auth_service: AuthService = Depends(get_auth_service)
) -> Token:
    """
    Đăng nhập bằng OAuth2 compatible token login (Email/Password).
    """
    return await auth_service.login_email_password(
        email=form_data.username,
        password=form_data.password
    )

@router.get("/logout", response_model=None)
async def logout(
    current_user: UserDetailResponse = Depends(get_current_user),
    auth_service: AuthService = Depends(get_auth_service)
) -> Any:
    """
    Đăng xuất: Xóa token hiện tại trong Database.
    """
    return await auth_service.logout(str(current_user.id))

@router.post("/refresh-token", response_model=Token)
async def refresh_token(
    request: RefreshTokenRequest,
    auth_service: AuthService = Depends(get_auth_service)
) -> Token:
    """
    Làm mới Access Token bằng Refresh Token.
    """
    return await auth_service.refresh_token(request.refresh_token)

@router.post("/reset-password", response_model=None)
async def reset_password(
    current_password: str = Body(..., alias="currentPassword"),
    new_password: str = Body(..., alias="newPassword"),
    current_user: UserDetailResponse = Depends(get_current_user),
    auth_service: AuthService = Depends(get_auth_service)
) -> Any:
    """
    Đổi mật khẩu (yêu cầu đang đăng nhập).
    """
    return await auth_service.reset_password(
        user_id=str(current_user.id),
        current_password=current_password,
        new_password=new_password
    )

@router.post("/forget-password", response_model=None)
async def forgot_password(
    email: str = Body(..., embed=True),
    auth_service: AuthService = Depends(get_auth_service)
) -> Any:
    """
    Quên mật khẩu: Gửi mật khẩu mới qua email.
    """
    return await auth_service.forgot_password(email)

# Social Login
@router.post("/login-facebook", response_model=Token)
async def login_facebook(
    accessToken: str = Body(..., embed=True),
    auth_service: AuthService = Depends(get_auth_service)
) -> Token:
    """
    Đăng nhập bằng Facebook Access Token.
    """
    return await auth_service.login_facebook(accessToken)

@router.post("/login-firebase", response_model=Token)
async def login_firebase(
    accessToken: str = Body(..., embed=True),
    auth_service: AuthService = Depends(get_auth_service)
) -> Token:
    """
    Đăng nhập bằng Firebase ID Token.
    """
    return await auth_service.login_social(
        provider="firebase",
        profile_id="fire_123_temp", # Cần logic verify token
        email="fire@example.com",
        access_token=accessToken
    )
