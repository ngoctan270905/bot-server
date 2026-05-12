from pydantic import BaseModel, Field, ConfigDict, BeforeValidator
from pydantic.alias_generators import to_camel
from typing import Annotated

PyObjectId = Annotated[str, BeforeValidator(str)]

class CheckoutSessionCreate(BaseModel):
    user_id: str = Field(...)
    stripe_session_id: str = Field(...)
    product_id: str = Field(...)
    url: str = Field(...)
    project_id: PyObjectId = Field(...)
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

class CheckoutSessionDetailResponse(BaseModel):
    id: PyObjectId = Field(alias="_id", serialization_alias="id")
    user_id: str = Field(...)
    stripe_session_id: str = Field(...)
    status: str = "PENDING"
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

class StripeSubscriptionDetailResponse(BaseModel):
    id: str = Field(alias="_id")
    product_id: str = Field(...)
    project_id: PyObjectId = Field(...)
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)
