from pydantic import BaseModel, Field, ConfigDict, BeforeValidator
from pydantic.alias_generators import to_camel
from datetime import datetime
from typing import Annotated

PyObjectId = Annotated[str, BeforeValidator(str)]

class ProjectCreate(BaseModel):
    name: str = Field(...)
    url: str | None = Field("")
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

class ProjectCreateResponse(BaseModel):
    id: PyObjectId = Field(alias="_id", serialization_alias="id")
    name: str
    message: str = "Project created successfully"
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

class ProjectUpdate(BaseModel):
    name: str | None = Field(None)
    url: str | None = Field(None)
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

class ProjectUpdateResponse(BaseModel):
    id: PyObjectId = Field(alias="_id", serialization_alias="id")
    name: str
    message: str = "Project updated successfully"
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

class ProjectListAll(BaseModel):
    id: PyObjectId = Field(alias="_id", serialization_alias="id")
    name: str
    url: str
    created_at: datetime | None = Field(None)
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

class ProjectDetailResponse(BaseModel):
    id: PyObjectId = Field(alias="_id", serialization_alias="id")
    name: str
    url: str
    subscription_id: str | None = Field(None)
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

class BillingDetailResponse(BaseModel):
    id: PyObjectId = Field(alias="_id", serialization_alias="id")
    project_id: PyObjectId = Field(...)
    customer_id: str | None = Field(None)
    invoice_receiver_email: str | None = Field(None)
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

class MemberDetailResponse(BaseModel):
    id: PyObjectId = Field(alias="_id", serialization_alias="id")
    user_id: PyObjectId = Field(...)
    role: str | None = Field(None)
    project_id: PyObjectId = Field(...)
    is_creator: bool | None = Field(None)
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

class SubscriptionService(BaseModel):
    tokens_per_bot_per_month: int
    characters_per_bot: int
    team_members: int
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

class SubscriptionPrice(BaseModel):
    currency: str
    price: int
    reccuring_interval: str
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

class ProjectSubscriptionResponse(BaseModel):
    id: str
    name: str
    description: str
    is_free: bool = False
    prices: list[SubscriptionPrice]
    services: SubscriptionService
    features: list[str]
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

class MessagePerDay(BaseModel):
    date: str
    count: int

class MessagePerBot(BaseModel):
    bot_id: str
    count: int

class ProjectUsageResponse(BaseModel):
    total_messages: int
    message_per_days: list[MessagePerDay]
    message_per_bots: list[MessagePerBot]
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)
