from pydantic import BaseModel, Field, ConfigDict, BeforeValidator
from pydantic.alias_generators import to_camel
from datetime import datetime
from typing import Annotated, Optional

PyObjectId = Annotated[str, BeforeValidator(str)]


class BotSettingSchema(BaseModel):
    """
    Cấu hình AI của bot.
    """

    temperature: float = Field(0.0)
    instructions: str | None = Field("")

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True
    )


class LeadsSettingSchema(BaseModel):
    """
    Cấu hình thông tin lead cần thu thập.
    """

    title: str = Field(...)
    name: str | None = Field(None)
    email: str | None = Field(None)
    phone: str | None = Field(None)
    message: str | None = Field(None)

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True
    )


class BotCreate(BaseModel):
    """
    Schema tạo bot mới.
    """

    name: str = Field(...)
    project_id: PyObjectId = Field(...)

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True
    )


class BotCreateResponse(BaseModel):
    """
    Schema phản hồi sau khi tạo bot.
    """

    id: PyObjectId = Field(alias="_id", serialization_alias="id")
    name: str
    message: str = "Bot created successfully"

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True
    )


class BotUpdate(BaseModel):
    """
    Schema cập nhật thông tin bot.
    """

    name: str | None = Field(None)
    model: str | None = Field(None)
    settings: BotSettingSchema | None = Field(None)
    sk_key: str | None = Field(None)
    temperature: float | None = Field(None)
    instructions: str | None = Field(None)
    is_public: bool | None = Field(None)
    leads_settings: Optional[dict] = Field(None)

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True
    )


class BotUpdateResponse(BaseModel):
    """
    Schema phản hồi sau khi cập nhật bot.
    """

    id: PyObjectId = Field(alias="_id", serialization_alias="id")
    name: str
    message: str = "Bot updated successfully"

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True
    )


class BotListAll(BaseModel):
    """
    Schema danh sách bot.
    """

    id: PyObjectId = Field(alias="_id", serialization_alias="id")
    name: str
    project_id: PyObjectId = Field(...)
    sk_key: str | None = Field(None)
    token_usage: int = Field(0)
    character_usage: int = Field(0)

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True
    )


class BotDetailResponse(BaseModel):
    """
    Schema chi tiết bot.
    """

    id: PyObjectId = Field(alias="_id", serialization_alias="id")
    name: str
    project_id: PyObjectId = Field(...)
    user_id: PyObjectId = Field(...)
    model: str | None = Field(None)
    sk_key: str | None = Field(None)
    settings: BotSettingSchema | None = Field(None)
    leads_settings: LeadsSettingSchema | None = Field(None)
    token_usage: int = Field(0)
    character_usage: int = Field(0)

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True
    )


class BotPublicResponse(BaseModel):
    """
    Schema public của bot.
    """

    id: PyObjectId = Field(alias="_id", serialization_alias="id")
    name: str
    settings: BotSettingSchema | None = Field(None)
    leads_settings: LeadsSettingSchema | None = Field(None)

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True
    )


class SkKeyResponse(BaseModel):
    """
    Schema phản hồi API key của bot.
    """

    sk_key: str = Field(alias="skKey")

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True
    )


class ChatByChannelCount(BaseModel):
    """
    Thống kê số chat theo kênh.
    """

    channel: str
    total_chat: int

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True
    )


class ChatAnalyticsDetail(BaseModel):
    """
    Thống kê chi tiết chat theo ngày.
    """

    date: datetime
    total_chat: int
    total_message: int
    thumbs_up_message: int
    thumbs_down_message: int
    chats_by_channel: list[ChatByChannelCount] = Field(default_factory=list)

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True
    )


class BotAnalyticsTotal(BaseModel):
    """
    Tổng thống kê chat của bot.
    """

    total_chat: int
    total_message: int
    thumbs_up_message: int
    thumbs_down_message: int
    chats_by_channel: list[ChatByChannelCount] = Field(default_factory=list)

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True
    )


class BotAnalyticsResponse(BaseModel):
    """
    Schema phản hồi analytics của bot.
    """

    bot_id: str
    total: BotAnalyticsTotal
    data: list[ChatAnalyticsDetail]

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True
    )


class LeadCreate(BaseModel):
    """
    Schema tạo lead mới.
    """

    conversation_id: str
    name: str | None = None
    email: str | None = None
    phone: str | None = None
    message: str | None = None

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True
    )


class LeadDetailResponse(BaseModel):
    """
    Schema chi tiết lead.
    """

    id: PyObjectId = Field(alias="_id", serialization_alias="id")
    bot_id: str
    conversation_id: str | None = None
    name: str | None = None
    email: str | None = None
    phone: str | None = None
    message: str | None = None
    created_at: datetime

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True
    )