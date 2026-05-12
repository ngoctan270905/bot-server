from pydantic import BaseModel, Field, ConfigDict, EmailStr, BeforeValidator
from pydantic.alias_generators import to_camel
from datetime import datetime
from typing import Annotated

PyObjectId = Annotated[str, BeforeValidator(str)]

# ==========================================
# 1. EmailPasswordUser Schemas
# ==========================================

class EmailPasswordUserCreate(BaseModel):
    email: EmailStr = Field(..., description="Email đăng nhập")
    password: str = Field(..., min_length=6)
    user_id: PyObjectId | None = Field(None, description="Liên kết tới User")

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        json_schema_extra={"example": {"email": "user@example.com", "password": "password123"}}
    )

class EmailPasswordUserDetailResponse(BaseModel):
    id: PyObjectId = Field(alias="_id", serialization_alias="id")
    email: EmailStr = Field(...)
    user_id: PyObjectId | None = Field(None)

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)


# ==========================================
# 2. FacebookUser Schemas
# ==========================================

class FacebookUserCreate(BaseModel):
    email: EmailStr = Field(...)
    profile_id: str = Field(...)
    access_token: str = Field(...)
    user_id: PyObjectId | None = Field(None)

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

class FacebookUserDetailResponse(BaseModel):
    id: PyObjectId = Field(alias="_id", serialization_alias="id")
    email: EmailStr = Field(...)
    profile_id: str = Field(...)
    user_id: PyObjectId | None = Field(None)

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)


# ==========================================
# 3. FirebaseUser Schemas
# ==========================================

class FirebaseUserCreate(BaseModel):
    email: EmailStr | None = Field(None)
    profile_id: str = Field(...)
    access_token: str = Field(...)
    user_id: PyObjectId | None = Field(None)

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

class FirebaseUserDetailResponse(BaseModel):
    id: PyObjectId = Field(alias="_id", serialization_alias="id")
    email: EmailStr | None = Field(None)
    profile_id: str = Field(...)
    user_id: PyObjectId | None = Field(None)

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)


# ==========================================
# 4. User Schemas (Main)
# ==========================================

class UserCreate(BaseModel):
    email: EmailStr = Field(..., description="Email đăng ký")
    password: str = Field(..., min_length=6, description="Mật khẩu (tối thiểu 6 ký tự)")

    model_config = ConfigDict(
        alias_generator=to_camel, 
        populate_by_name=True,
        json_schema_extra={
            "example": {
                "email": "user@example.com",
                "password": "password123"
            }
        }
    )

class UserCreateResponse(BaseModel):
    id: PyObjectId = Field(alias="_id", serialization_alias="id")
    name: str | None = Field(None)
    provider: str = Field(...)
    active: bool = Field(...)

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

class UserUpdate(BaseModel):
    name: str | None = Field(None, min_length=2, max_length=100)
    avatar: str | None = Field(None)

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

class UserUpdateResponse(BaseModel):
    id: PyObjectId = Field(alias="_id", serialization_alias="id")
    name: str | None = Field(None)

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

class UserListAll(BaseModel):
    id: PyObjectId = Field(alias="_id", serialization_alias="id")
    name: str | None = Field(None)
    provider: str = Field(...)
    active: bool = Field(...)
    created_at: datetime | None = Field(None)

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

class UserDetailResponse(BaseModel):
    id: PyObjectId = Field(alias="_id", serialization_alias="id")
    provider: str = Field(...)
    active: bool = Field(...)
    name: str | None = Field(None)
    avatar: str | None = Field(None)
    created_at: datetime | None = Field(None)
    last_login: datetime | None = Field(None)
    
    email_pw: EmailPasswordUserDetailResponse | None = Field(None)
    facebook: FacebookUserDetailResponse | None = Field(None)
    firebase: FirebaseUserDetailResponse | None = Field(None)

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)
