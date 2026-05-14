from fastapi import APIRouter, Depends, status
from typing import Any

from app.services.profile_service import ProfileService
from app.api.v1.dependencies import get_profile_service, get_current_user
from app.schemas.user import UserUpdate, UserDetailResponse

router = APIRouter()

@router.get("/me", response_model=UserDetailResponse)
async def get_my_profile(
    current_user: UserDetailResponse = Depends(get_current_user),
    profile_service: ProfileService = Depends(get_profile_service)
) -> Any:
    """
    Lấy thông tin cá nhân của người dùng hiện tại.
    """
    return await profile_service.get_my_profile(str(current_user.id))

@router.get("/{id}", response_model=UserDetailResponse)
async def get_profile_by_id(
    id: str,
    current_user: UserDetailResponse = Depends(get_current_user),
    profile_service: ProfileService = Depends(get_profile_service)
) -> Any:
    """
    Lấy thông tin cá nhân của người dùng theo ID.
    """
    return await profile_service.get_profile_by_id(id)

@router.put("/", response_model=UserDetailResponse)
async def update_profile(
    profile_in: UserUpdate,
    current_user: UserDetailResponse = Depends(get_current_user),
    profile_service: ProfileService = Depends(get_profile_service)
) -> Any:
    """
    Cập nhật thông tin cá nhân (name, avatar, ...).
    """
    return await profile_service.update_profile(str(current_user.id), profile_in)

@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_profile(
    id: str,
    current_user: UserDetailResponse = Depends(get_current_user),
    profile_service: ProfileService = Depends(get_profile_service)
) -> None:
    """
    Xóa hồ sơ người dùng. (Trong thực tế nên kiểm tra quyền nếu xóa id khác).
    """
    await profile_service.delete_profile(id)
