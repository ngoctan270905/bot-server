from pydantic import BaseModel, Field, ConfigDict, BeforeValidator
from datetime import datetime
from typing import Annotated, Optional
from enum import Enum

PyObjectId = Annotated[str, BeforeValidator(str)]

class ChannelEnum(str, Enum):
    FACEBOOK = "fb"
    ZALO = "zalo"
    TELEGRAM = "telegram"
    WEB = "web"

class SocialPageBase(BaseModel):
    page_id: str = Field(..., alias="pageId")
    name: str
    bot_id: PyObjectId = Field(..., alias="botId")
    channel: ChannelEnum = Field(default=ChannelEnum.FACEBOOK)
    active: bool = True
    avatar: Optional[str] = None
    
    model_config = ConfigDict(alias_generator=None, populate_by_name=True)

class SocialPageCreate(SocialPageBase):
    page_access_token: str = Field(..., alias="pageAccessToken")
    page_refresh_token: Optional[str] = Field(None, alias="pageRefreshToken")

class SocialPageResponse(SocialPageBase):
    id: PyObjectId = Field(alias="_id", serialization_alias="id")
    created_at: datetime = Field(alias="createdAt")
    
    model_config = ConfigDict(alias_generator=None, populate_by_name=True)

class FacebookConnectResponse(BaseModel):
    url: str
