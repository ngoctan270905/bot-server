from pydantic import BaseModel, Field, ConfigDict, BeforeValidator
from pydantic.alias_generators import to_camel
from datetime import datetime
from typing import Annotated

PyObjectId = Annotated[str, BeforeValidator(str)]

class AttachmentSchema(BaseModel):
    type: str = Field(...)
    payload: str | None = Field(None)
    payload_object: dict | None = Field(None)
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

class CustomerDetailResponse(BaseModel):
    id: PyObjectId = Field(alias="_id")
    cid: str = Field(...)
    name: str | None = Field(None)
    avatar: str | None = Field(None)
    channel: str | None = Field(None)
    created_at: datetime = Field(...)
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

class ConversationListAll(BaseModel):
    id: PyObjectId = Field(alias="_id")
    customer_id: PyObjectId = Field(...)
    channel: str = Field(...)
    bot_id: PyObjectId = Field(...)
    created_at: datetime = Field(...)
    updated_at: datetime = Field(...)
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

class ConversationDetailResponse(BaseModel):
    id: PyObjectId = Field(alias="_id")
    customer_id: PyObjectId = Field(...)
    channel: str = Field(...)
    bot_id: PyObjectId = Field(...)
    auto_reply: bool = Field(True)
    created_at: datetime = Field(...)
    updated_at: datetime = Field(...)
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

class ChatHistoryCreate(BaseModel):
    role: str = Field("agent")
    bot_id: PyObjectId = Field(...)
    content: str | None = Field(None)
    conversation_id: PyObjectId = Field(...)
    attachments: list[AttachmentSchema] = Field(default_factory=list)
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

class ChatHistoryDetailResponse(BaseModel):
    id: PyObjectId = Field(alias="_id")
    role: str
    content: str | None
    thumb: str = "Unspecified"
    attachments: list[AttachmentSchema] = Field(default_factory=list)
    conversation_id: PyObjectId = Field(...)
    created_at: datetime = Field(...)
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)
