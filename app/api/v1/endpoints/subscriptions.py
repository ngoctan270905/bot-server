from fastapi import APIRouter, Depends
from typing import List
from app.services.subscription_service import get_all_subscriptions
from app.schemas.subscription import TokenSubscription

router = APIRouter()

@router.get("/", response_model=List[TokenSubscription])
async def list_subscriptions():
    """
    Lấy danh sách tất cả các gói cước (Pricing Table).
    """
    return await get_all_subscriptions()
