from pydantic import BaseModel, Field, ConfigDict, BeforeValidator
from pydantic.alias_generators import to_camel
from datetime import datetime
from typing import Annotated

PyObjectId = Annotated[str, BeforeValidator(str)]

class WebhookEvent(BaseModel):
    id: str
    name: str

class WebhookCreate(BaseModel):
    app_id: str = Field(...)
    endpoints: list[str] = Field(default_factory=list)
    events: list[str] = Field(default_factory=list)
    bot_id: PyObjectId = Field(...)
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

class WebhookCreateResponse(BaseModel):
    id: PyObjectId = Field(alias="_id", serialization_alias="id")
    app_id: str
    message: str = "Webhook created successfully"
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

class WebhookUpdate(BaseModel):
    endpoints: list[str] | None = Field(None)
    events: list[str] | None = Field(None)
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

class WebhookUpdateResponse(BaseModel):
    id: PyObjectId = Field(alias="_id", serialization_alias="id")
    message: str = "Webhook updated successfully"
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

class WebhookDetailResponse(BaseModel):
    id: PyObjectId = Field(alias="_id", serialization_alias="id")
    app_id: str
    endpoints: list[str]
    events: list[str]
    bot_id: PyObjectId = Field(...)
    created_at: datetime = Field(...)
    updated_at: datetime = Field(...)
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)
