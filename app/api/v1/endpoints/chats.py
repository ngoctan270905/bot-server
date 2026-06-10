from fastapi import APIRouter, Depends, status
from app.services.chat_service import ChatService
from app.api.v1.dependencies import get_chat_service
from app.schemas.chat import ChatSendMessage, ChatSendMessageResponse

router = APIRouter()

@router.post("/{bot_id}", response_model=ChatSendMessageResponse)
async def send_message_http(
    bot_id: str,
    payload: ChatSendMessage,
    chat_service: ChatService = Depends(get_chat_service)
):
    """
    API gửi tin nhắn tới Bot qua giao thức HTTP POST truyền thống.
    Được dùng bởi Chat Widget/Bong bóng chat.
    """
    result = await chat_service.send_message_http(
        bot_id=bot_id,
        message=payload.message,
        conversation_id=payload.conversation_id
    )
    return result
