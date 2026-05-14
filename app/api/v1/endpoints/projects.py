from fastapi import APIRouter, Depends, status, Query
from typing import List, Any, Optional

from app.services.project_service import ProjectService
from app.api.v1.dependencies import get_project_service, get_current_user
from app.schemas.project import (
    ProjectCreate, ProjectUpdate, ProjectDetailResponse, ProjectListAll,
    ProjectSubscriptionResponse, ProjectUsageResponse
)
from app.schemas.user import UserDetailResponse

router = APIRouter()

@router.get("/", response_model=List[ProjectListAll])
async def list_projects(
    current_user: UserDetailResponse = Depends(get_current_user),
    project_service: ProjectService = Depends(get_project_service)
) -> Any:
    """
    Lấy danh sách các dự án mà người dùng tham gia.
    """
    return await project_service.get_projects(str(current_user.id))

@router.post("/", response_model=ProjectDetailResponse, status_code=status.HTTP_201_CREATED)
async def create_project(
    project_in: ProjectCreate,
    current_user: UserDetailResponse = Depends(get_current_user),
    project_service: ProjectService = Depends(get_project_service)
) -> Any:
    """
    Tạo một dự án mới.
    """
    # Lấy email từ user để gán vào Billing (giống dự án gốc)
    user_email = ""
    if current_user.email_pw:
        user_email = current_user.email_pw.email
    elif current_user.facebook:
        user_email = current_user.facebook.email
    elif current_user.firebase:
        user_email = current_user.firebase.email

    return await project_service.create_project(str(current_user.id), project_in, user_email)

@router.get("/{id}", response_model=ProjectDetailResponse)
async def get_project(
    id: str,
    current_user: UserDetailResponse = Depends(get_current_user),
    project_service: ProjectService = Depends(get_project_service)
) -> Any:
    """
    Lấy thông tin chi tiết của một dự án.
    """
    return await project_service.get_project_by_id(str(current_user.id), id)

@router.put("/{id}", response_model=ProjectDetailResponse)
async def update_project(
    id: str,
    project_in: ProjectUpdate,
    current_user: UserDetailResponse = Depends(get_current_user),
    project_service: ProjectService = Depends(get_project_service)
) -> Any:
    """
    Cập nhật thông tin dự án.
    """
    return await project_service.update_project(str(current_user.id), id, project_in)

@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT, response_model=None)
async def delete_project(
    id: str,
    current_user: UserDetailResponse = Depends(get_current_user),
    project_service: ProjectService = Depends(get_project_service)
) -> None:
    """
    Xóa một dự án (chỉ dành cho Admin của dự án).
    """
    await project_service.delete_project(str(current_user.id), id)

@router.get("/{id}/subscription", response_model=ProjectSubscriptionResponse)
async def get_project_subscription(
    id: str,
    current_user: UserDetailResponse = Depends(get_current_user),
    project_service: ProjectService = Depends(get_project_service)
) -> Any:
    """
    Lấy thông tin subscription của dự án.
    """
    return await project_service.get_project_subscription(str(current_user.id), id)

@router.get("/{id}/usage", response_model=ProjectUsageResponse)
async def get_project_usage(
    id: str,
    from_date: Optional[str] = Query(None, alias="fromDate"),
    to_date: Optional[str] = Query(None, alias="toDate"),
    bot_id: Optional[str] = Query(None, alias="botId"),
    current_user: UserDetailResponse = Depends(get_current_user),
    project_service: ProjectService = Depends(get_project_service)
) -> Any:
    """
    Thống kê mức độ sử dụng của dự án.
    """
    return await project_service.get_project_usage(
        str(current_user.id), id, from_date, to_date, bot_id
    )
