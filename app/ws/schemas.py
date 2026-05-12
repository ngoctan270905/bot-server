from pydantic import BaseModel, Field
from typing import Any, Optional, Dict

class WSMessage(BaseModel):
    """Cấu trúc tin nhắn chung Type/Payload."""
    type: str
    payload: Dict[str, Any]

# --- Client Messages (Tin nhắn từ Client gửi lên) ---

class ClientStartChatPayload(BaseModel):
    bot_id: str = Field(..., alias="botId")
    channel: str = Field("web")

class ClientSendMessagePayload(BaseModel):
    message: str

class ClientEndChatPayload(BaseModel):
    reason: Optional[str] = "Client closed"

# --- Server Messages (Tin nhắn từ Server gửi xuống) ---

class ServerConversationCreatedPayload(BaseModel):
    conversation_id: str = Field(..., alias="conversationId")

class ServerSendMessagePayload(BaseModel):
    conversation_id: str = Field(..., alias="conversationId")
    message: str
    is_customer_send: bool = Field(False, alias="isCustomerSend")
