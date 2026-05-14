from fastapi import APIRouter, Depends, Query, status
from typing import List, Optional
from app.services.chat_service import ChatService
from app.api.v1.dependencies import get_chat_service, get_current_user
from app.schemas.chat import (
    ConversationWithHistory, 
    ChatHistoryDetailResponse, 
    ConversationUpdate
)
from app.schemas.user import UserDetailResponse

router = APIRouter()

@router.get("/chatlogs", response_model=List[ConversationWithHistory])
async def get_chatlogs(
    bot_id: str = Query(..., alias="botId"),
    limit: int = 20,
    cursor: Optional[str] = None,
    from_date: Optional[str] = Query(None, alias="fromDate"),
    to_date: Optional[str] = Query(None, alias="toDate"),
    channels: Optional[str] = None,
    current_user: UserDetailResponse = Depends(get_current_user),
    chat_service: ChatService = Depends(get_chat_service)
):
    """
    Lấy danh sách các cuộc hội thoại (Chatlogs) cho Dashboard.
    """
    return await chat_service.get_chatlogs(
        user_id=str(current_user.id),
        bot_id=bot_id,
        limit=limit,
        cursor=cursor,
        from_date=from_date,
        to_date=to_date,
        channels=channels
    )

@router.get("/chatlogs/{id}", response_model=List[ChatHistoryDetailResponse])
async def get_chat_history(
    id: str,
    current_user: UserDetailResponse = Depends(get_current_user),
    chat_service: ChatService = Depends(get_chat_service)
):
    """
    Lấy chi tiết lịch sử tin nhắn của một cuộc hội thoại.
    """
    return await chat_service.get_history(conversation_id=id)

@router.put("/{id}", status_code=status.HTTP_200_OK)
async def update_conversation(
    id: str,
    update_in: ConversationUpdate,
    current_user: UserDetailResponse = Depends(get_current_user),
    chat_service: ChatService = Depends(get_chat_service)
):
    """
    Cập nhật thông tin cuộc hội thoại (ví dụ: bật/tắt autoReply).
    """
    await chat_service.update_conversation(conversation_id=id, update_in=update_in)
    return {"message": "Conversation updated successfully"}
