from fastapi import APIRouter, Depends, status, Query
from typing import List, Any

from app.services.bot_service import BotService
from app.api.v1.dependencies import get_bot_service, get_current_user
from app.schemas.bot import BotCreate, BotUpdate, BotDetailResponse, BotListAll
from app.schemas.user import UserDetailResponse
from app.schemas.base import UnifiedResponse

router = APIRouter()

@router.get("/", response_model=UnifiedResponse[List[BotListAll]])
async def list_bots(
    project_id: str = Query(..., alias="projectId"),
    current_user: UserDetailResponse = Depends(get_current_user),
    bot_service: BotService = Depends(get_bot_service)
) -> Any:
    """
    Lấy danh sách các Bot trong một dự án.
    """
    return await bot_service.get_bots(str(current_user.id), project_id)

@router.post("/", response_model=UnifiedResponse[BotDetailResponse], status_code=status.HTTP_201_CREATED)
async def create_bot(
    bot_in: BotCreate,
    current_user: UserDetailResponse = Depends(get_current_user),
    bot_service: BotService = Depends(get_bot_service)
) -> Any:
    """
    Tạo một Bot mới.
    """
    return await bot_service.create_bot(str(current_user.id), bot_in)

@router.get("/{id}", response_model=UnifiedResponse[BotDetailResponse])
async def get_bot(
    id: str,
    current_user: UserDetailResponse = Depends(get_current_user),
    bot_service: BotService = Depends(get_bot_service)
) -> Any:
    """
    Lấy thông tin chi tiết cấu hình của một Bot.
    """
    return await bot_service.get_bot_by_id(str(current_user.id), id)

@router.put("/{id}", response_model=UnifiedResponse[BotDetailResponse])
async def update_bot(
    id: str,
    bot_in: BotUpdate,
    current_user: UserDetailResponse = Depends(get_current_user),
    bot_service: BotService = Depends(get_bot_service)
) -> Any:
    """
    Cập nhật cấu hình Bot (model, temperature, instructions, leadsSettings, public).
    """
    return await bot_service.update_bot(str(current_user.id), id, bot_in)

@router.delete("/{id}", response_model=UnifiedResponse[None])
async def delete_bot(
    id: str,
    current_user: UserDetailResponse = Depends(get_current_user),
    bot_service: BotService = Depends(get_bot_service)
) -> Any:
    """
    Xóa một Bot.
    """
    return await bot_service.delete_bot(str(current_user.id), id)
