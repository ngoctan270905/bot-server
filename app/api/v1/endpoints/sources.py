from fastapi import APIRouter, Depends, status, Query
from typing import List, Any
from app.services.bot_source_service import BotSourceService
from app.api.v1.dependencies import get_bot_source_service, get_current_user
from app.schemas.source import SourceUpsertRequest, SourceResponse, TrainingHistoryResponse
from app.schemas.user import UserDetailResponse

router = APIRouter()

@router.put("/upsert", status_code=status.HTTP_200_OK)
async def upsert_sources(
    request: SourceUpsertRequest,
    current_user: UserDetailResponse = Depends(get_current_user),
    source_service: BotSourceService = Depends(get_bot_source_service)
) -> Any:
    """
    Cập nhật hoặc thêm mới các nguồn dữ liệu cho Bot (File, Text, Website, QA).
    Sau khi thêm, hệ thống sẽ tự động kích hoạt Training Job.
    """
    return await source_service.upsert_sources(str(current_user.id), request)

@router.delete("/{id}", status_code=status.HTTP_200_OK)
async def delete_source(
    id: str,
    current_user: UserDetailResponse = Depends(get_current_user),
    source_service: BotSourceService = Depends(get_bot_source_service)
) -> Any:
    """
    Xóa một nguồn dữ liệu của Bot.
    """
    return await source_service.delete_source(str(current_user.id), id)
