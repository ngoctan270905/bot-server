from fastapi import APIRouter, Depends, status, Query
from typing import List, Any
from datetime import datetime

from app.services.bot_service import BotService
from app.services.bot_analytics_service import BotAnalyticsService
from app.services.lead_service import LeadService
from app.services.bot_source_service import BotSourceService
from app.api.v1.dependencies import (
    get_bot_service, 
    get_bot_analytics_service, 
    get_lead_service, 
    get_bot_source_service,
    get_current_user
)
from app.schemas.bot import (
    BotCreate, 
    BotUpdate, 
    BotDetailResponse, 
    BotListAll, 
    BotAnalyticsResponse, 
    LeadDetailResponse, 
    LeadCreate,
    BotPublicResponse,
    SkKeyResponse
)
from app.schemas.source import SourceResponse, TrainingHistoryResponse
from app.schemas.user import UserDetailResponse
from app.schemas.base import UnifiedResponse

router = APIRouter()

@router.get("/public/{id}", response_model=BotPublicResponse)
async def get_public_bot(
    id: str,
    bot_service: BotService = Depends(get_bot_service)
) -> Any:
    """
    Lấy thông tin Bot công khai (dùng cho Widget chat, không cần login).
    """
    return await bot_service.get_bot_public(id)

@router.post("/{id}/reset-key", response_model=SkKeyResponse)
async def reset_bot_key(
    id: str,
    current_user: UserDetailResponse = Depends(get_current_user),
    bot_service: BotService = Depends(get_bot_service)
) -> Any:
    """
    Cấp lại Secret Key mới cho Bot.
    """
    return await bot_service.reset_sk_key(str(current_user.id), id)

@router.get("/", response_model=List[BotListAll])
async def list_bots(
    project_id: str = Query(..., alias="projectId"),
    current_user: UserDetailResponse = Depends(get_current_user),
    bot_service: BotService = Depends(get_bot_service)
) -> Any:
    """
    Lấy danh sách các Bot trong một dự án.
    """
    return await bot_service.get_bots(str(current_user.id), project_id)

@router.post("/", response_model=BotDetailResponse, status_code=status.HTTP_201_CREATED)
async def create_bot(
    bot_in: BotCreate,
    current_user: UserDetailResponse = Depends(get_current_user),
    bot_service: BotService = Depends(get_bot_service)
) -> Any:
    """
    Tạo một Bot mới.
    """
    return await bot_service.create_bot(str(current_user.id), bot_in)

@router.get("/{id}", response_model=BotDetailResponse)
async def get_bot(
    id: str,
    current_user: UserDetailResponse = Depends(get_current_user),
    bot_service: BotService = Depends(get_bot_service)
) -> Any:
    """
    Lấy thông tin chi tiết cấu hình của một Bot.
    """
    return await bot_service.get_bot_by_id(str(current_user.id), id)

@router.put("/{id}", response_model=BotDetailResponse)
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

@router.delete("/{id}", response_model=None)
async def delete_bot(
    id: str,
    current_user: UserDetailResponse = Depends(get_current_user),
    bot_service: BotService = Depends(get_bot_service)
) -> Any:
    """
    Xóa một Bot.
    """
    return await bot_service.delete_bot(str(current_user.id), id)

# --- Analytics & Leads Endpoints ---

@router.get("/{id}/chat-analytics", response_model=BotAnalyticsResponse)
async def get_bot_analytics(
    id: str,
    from_date: datetime = Query(..., alias="fromDate"),
    to_date: datetime = Query(..., alias="toDate"),
    current_user: UserDetailResponse = Depends(get_current_user),
    analytics_service: BotAnalyticsService = Depends(get_bot_analytics_service)
) -> Any:
    """
    Lấy thống kê chat của Bot (Aggregate theo ngày).
    """
    return await analytics_service.get_bot_analytics(
        str(current_user.id), id, from_date, to_date
    )

@router.get("/{id}/leads", response_model=List[LeadDetailResponse])
async def get_bot_leads(
    id: str,
    from_date: datetime | None = Query(None, alias="fromDate"),
    to_date: datetime | None = Query(None, alias="toDate"),
    current_user: UserDetailResponse = Depends(get_current_user),
    lead_service: LeadService = Depends(get_lead_service)
) -> Any:
    """
    Lấy danh sách khách hàng (Leads) đã thu thập được của Bot.
    """
    return await lead_service.get_bot_leads(
        str(current_user.id), id, from_date, to_date
    )

@router.post("/{id}/leads", response_model=LeadDetailResponse, status_code=status.HTTP_201_CREATED)
async def create_bot_lead(
    id: str,
    lead_in: LeadCreate,
    lead_service: LeadService = Depends(get_lead_service)
) -> Any:
    """
    Tạo một Lead mới (thường dùng cho API công khai/Widget chat).
    Không yêu cầu đăng nhập nếu là API công khai.
    """
    return await lead_service.create_lead(id, lead_in)

# --- Source & Training Endpoints ---

@router.get("/{id}/source", response_model=List[SourceResponse])
async def get_bot_sources(
    id: str,
    current_user: UserDetailResponse = Depends(get_current_user),
    source_service: BotSourceService = Depends(get_bot_source_service)
) -> Any:
    """
    Lấy danh sách các nguồn dữ liệu của Bot.
    """
    return await source_service.get_bot_sources(str(current_user.id), id)

@router.get("/{id}/training-history", response_model=List[TrainingHistoryResponse])
async def get_bot_training_history(
    id: str,
    current_user: UserDetailResponse = Depends(get_current_user),
    source_service: BotSourceService = Depends(get_bot_source_service)
) -> Any:
    """
    Lấy lịch sử các lần huấn luyện Bot.
    """
    return await source_service.get_training_history(str(current_user.id), id)

@router.post("/{id}/training", status_code=status.HTTP_200_OK)
async def trigger_bot_training(
    id: str,
    current_user: UserDetailResponse = Depends(get_current_user),
    source_service: BotSourceService = Depends(get_bot_source_service)
) -> Any:
    """
    Kích hoạt huấn luyện Bot thủ công.
    """
    return await source_service.trigger_training(str(current_user.id), id)
