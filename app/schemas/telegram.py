from pydantic import BaseModel, Field, ConfigDict


class TelegramConnectRequest(BaseModel):
    """Request kết nối Telegram Bot."""

    bot_token: str = Field(..., alias="botToken", description="Telegram Bot Token từ BotFather")
    bot_id: str = Field(..., alias="botId", description="ID của Bot trong hệ thống (Bot ObjectId)")

    model_config = ConfigDict(populate_by_name=True)


class TelegramBotInfo(BaseModel):
    """Thông tin Telegram Bot."""

    id: int
    first_name: str
    last_name: str | None = None
    username: str | None = None
    can_join_groups: bool
    can_read_all_group_messages: bool
    supports_inline_queries: bool


class TelegramUser(BaseModel):
    """Thông tin người dùng Telegram."""

    id: int
    is_bot: bool
    first_name: str
    last_name: str | None = None
    username: str | None = None
    language_code: str | None = None


class TelegramChat(BaseModel):
    """Thông tin cuộc trò chuyện Telegram."""

    id: int
    first_name: str | None = None
    last_name: str | None = None
    username: str | None = None
    type: str


class TelegramMessage(BaseModel):
    """Tin nhắn Telegram."""

    message_id: int
    from_user: TelegramUser = Field(..., alias="from")
    chat: TelegramChat
    date: int
    text: str | None = None

    model_config = ConfigDict(populate_by_name=True)


class TelegramUpdate(BaseModel):
    """Webhook update từ Telegram."""

    update_id: int
    message: TelegramMessage | None = None