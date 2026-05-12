from fastapi import APIRouter, Depends, status
from fastapi.security import OAuth2PasswordRequestForm
from typing import Any

from app.services.auth_service import AuthService
from app.api.v1.dependencies import get_auth_service, get_current_user
from app.schemas.user import UserCreate, UserCreateResponse, UserDetailResponse
from app.schemas.base import UnifiedResponse

router = APIRouter()

@router.post("/register", response_model=UnifiedResponse[UserCreateResponse], status_code=status.HTTP_201_CREATED)
async def register(
    user_in: UserCreate,
    auth_service: AuthService = Depends(get_auth_service)
) -> Any:
    """
    Đăng ký tài khoản mới bằng Email và Password.
    """
    return await auth_service.register_email_password(user_in.model_dump())

@router.post("/login", response_model=dict)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    auth_service: AuthService = Depends(get_auth_service)
) -> Any:
    """
    Đăng nhập bằng OAuth2 compatible token login (Email/Password).
    """
    return await auth_service.login_email_password(
        email=form_data.username, 
        password=form_data.password
    )

@router.get("/me", response_model=UnifiedResponse[UserDetailResponse])
async def get_me(
    current_user_schema: UserDetailResponse = Depends(get_current_user),
    auth_service: AuthService = Depends(get_auth_service)
) -> Any:
    """
    Lấy thông tin người dùng hiện tại từ token.
    """
    return await auth_service.get_my_profile(str(current_user_schema.id))
