from pydantic import BaseModel, Field, ConfigDict, BeforeValidator
from pydantic.alias_generators import to_camel
from datetime import datetime
from typing import Annotated

PyObjectId = Annotated[str, BeforeValidator(str)]

class BotSettingSchema(BaseModel):
    temperature: float = Field(0.0)
    instructions: str | None = Field("")
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

class LeadsSettingSchema(BaseModel):
    title: str = Field(...)
    name: str | None = Field(None)
    email: str | None = Field(None)
    phone: str | None = Field(None)
    message: str | None = Field(None)
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

class BotCreate(BaseModel):
    name: str = Field(...)
    project_id: PyObjectId = Field(...)
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

class BotCreateResponse(BaseModel):
    id: PyObjectId = Field(alias="_id", serialization_alias="id")
    name: str
    message: str = "Bot created successfully"
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

class BotUpdate(BaseModel):
    name: str | None = Field(None)
    model: str | None = Field(None)
    settings: BotSettingSchema | None = Field(None)
    sk_key: str | None = Field(None)
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

class BotUpdateResponse(BaseModel):
    id: PyObjectId = Field(alias="_id", serialization_alias="id")
    name: str
    message: str = "Bot updated successfully"
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

class BotListAll(BaseModel):
    id: PyObjectId = Field(alias="_id", serialization_alias="id")
    name: str
    project_id: PyObjectId = Field(...)
    sk_key: str | None = Field(None)
    token_usage: int = Field(0)
    character_usage: int = Field(0)
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

class BotDetailResponse(BaseModel):
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
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

class BotPublicResponse(BaseModel):
    id: PyObjectId = Field(alias="_id", serialization_alias="id")
    name: str
    settings: BotSettingSchema | None = Field(None)
    leads_settings: LeadsSettingSchema | None = Field(None)
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

class SkKeyResponse(BaseModel):
    sk_key: str = Field(alias="skKey")
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

# --- Analytics Schemas ---

class ChatByChannelCount(BaseModel):
    channel: str
    total_chat: int
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

class ChatAnalyticsDetail(BaseModel):
    date: datetime
    total_chat: int
    total_message: int
    thumbs_up_message: int
    thumbs_down_message: int
    chats_by_channel: list[ChatByChannelCount] = Field(default_factory=list)
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

class BotAnalyticsTotal(BaseModel):
    total_chat: int
    total_message: int
    thumbs_up_message: int
    thumbs_down_message: int
    chats_by_channel: list[ChatByChannelCount] = Field(default_factory=list)
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

class BotAnalyticsResponse(BaseModel):
    bot_id: str
    total: BotAnalyticsTotal
    data: list[ChatAnalyticsDetail]
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

# --- Leads Schemas ---

class LeadCreate(BaseModel):
    conversation_id: str
    name: str | None = None
    email: str | None = None
    phone: str | None = None
    message: str | None = None
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

class LeadDetailResponse(BaseModel):
    id: PyObjectId = Field(alias="_id", serialization_alias="id")
    bot_id: str
    conversation_id: str | None = None
    name: str | None = None
    email: str | None = None
    phone: str | None = None
    message: str | None = None
    created_at: datetime
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)
