from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    refresh_token: str | None = None

    model_config = ConfigDict(
        populate_by_name=True
    )

class TokenData(BaseModel):
    user_id: str | None = None
    type: str | None = None


class RefreshTokenRequest(BaseModel):
  refresh_token: str = Field(alias="refreshToken")
