from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from src.models.user import UserRole

class SUserCreate(BaseModel):
    username: str = Field(min_length=3, max_length=255)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)

class SUser(BaseModel):
    id: int
    username: str
    email: EmailStr
    created_at: datetime
    role: UserRole

    model_config = ConfigDict(from_attributes=True)

class SUserUpdate(BaseModel):
    username: str | None = Field(
        default=None,
        min_length=3,
        max_length=255,
    )

class SUserLogin(BaseModel):
    username: str = Field(min_length=3, max_length=255)
    password: str = Field(min_length=1, max_length=128)
