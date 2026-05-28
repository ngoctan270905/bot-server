import json
import hmac
import hashlib
from fastapi import APIRouter, Depends, Query, Request, Header, HTTPException
from fastapi.responses import RedirectResponse, Response
from app.api.v1.dependencies import get_social_service, get_current_user
from app.services.social_service import SocialService
from app.schemas.social import FacebookConnectResponse
from app.schemas.user import UserDetailResponse
from app.core.config import settings
from loguru import logger

router = APIRouter()

@router.get("/facebook/connect", response_model=FacebookConnectResponse)
async def get_facebook_connect_url(
    bot_id: str = Query(..., alias="botId"),
    project_id: str = Query(..., alias="projectId"),
    redirect_url: str = Query(None, alias="redirectUrl"),
    current_user: UserDetailResponse = Depends(get_current_user),
    social_service: SocialService = Depends(get_social_service)
):
    """Lấy URL đăng nhập Facebook để kết nối Page."""
    url = social_service.get_facebook_login_url(bot_id, project_id, redirect_url)
    return FacebookConnectResponse(url=url)

@router.get("/facebook/connect/callback")
async def facebook_connect_callback(
    code: str,
    state: str,
    social_service: SocialService = Depends(get_social_service)
):
    """Xử lý callback từ Facebook"""
    try:
        state_data = json.loads(state)
        bot_id = state_data.get("botId")
        # URL đích mặc định nếu không có redirectUrl trong state
        final_redirect_url = state_data.get("redirectUrl") or f"{settings.FRONTEND_URL}/dashboard"
        
        # 1. Đổi code lấy access token
        access_token = await social_service.get_facebook_access_token(code)
        
        # 2. Lấy danh sách pages
        pages = await social_service.get_facebook_pages_info(access_token)
        
        if not pages:
            logger.bind(context="Social").warning("No pages found for this user.")
            return RedirectResponse(url=final_redirect_url)

        # 3. Đăng ký webhook và lưu vào DB cho TẤT CẢ các trang
        for page in pages:
            try:
                await social_service.subscribe_page_to_webhook(page["id"], page["access_token"])
                await social_service.save_or_update_social_page(page, bot_id)
                logger.bind(context="Social").success(f"Connected page {page.get('name')}")
            except Exception as page_err:
                # Log lỗi nhưng không chặn tiến trình của các trang khác
                logger.bind(context="Social").error(f"Error processing page {page.get('id')}: {page_err}")
            
        # 4. Redirect về mà không kèm status
        return RedirectResponse(url=final_redirect_url)
        
    except Exception as e:
        logger.bind(context="Social").error(f"Facebook Connect Callback Error: {str(e)}")
        fallback_url = f"{settings.FRONTEND_URL}/dashboard"
        return RedirectResponse(url=fallback_url)
