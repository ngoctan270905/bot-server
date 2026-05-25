from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel

class Token(BaseModel):
    """
    Schema phản hồi token xác thực.
    """

    access_token: str
    token_type: str = "bearer"
    refresh_token: str | None = None


class TokenData(BaseModel):
    """
    Dữ liệu payload được giải mã từ JWT.
    """

    user_id: str | None = None
    type: str | None = None


class RefreshTokenRequest(BaseModel):
    """
    Schema request dùng để refresh access token.
    """

    refresh_token: str = Field(alias="refreshToken")