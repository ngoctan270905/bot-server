from pydantic import BaseModel, Field, ConfigDict

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

class TelegramUser(BaseModel):
    id: int
    is_bot: bool
    first_name: str
    last_name: str | None = None
    username: str | None = None
    language_code: str | None = None

class TelegramChat(BaseModel):
    id: int
    first_name: str | None = None
    last_name: str | None = None
    username: str | None = None
    type: str

class TelegramMessage(BaseModel):
    message_id: int
    from_user: TelegramUser = Field(..., alias="from")
    chat: TelegramChat
    date: int
    text: str | None = None

    model_config = ConfigDict(populate_by_name=True)

class TelegramUpdate(BaseModel):
    update_id: int
    message: TelegramMessage | None = None
