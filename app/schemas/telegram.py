from pydantic import BaseModel, Field

class TelegramConnectRequest(BaseModel):
    bot_token: str = Field(..., description="Telegram Bot Token từ BotFather")
    bot_id: str = Field(..., description="ID của Bot trong hệ thống (Bot ObjectId)")

class TelegramBotInfo(BaseModel):
    id: int
    first_name: str
    last_name: str | None = None
    username: str | None = None
    can_join_groups: bool
    can_read_all_group_messages: bool
    supports_inline_queries: bool
