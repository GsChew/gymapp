from pydantic import BaseModel, ConfigDict, EmailStr
from datetime import  datetime

class SUserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str

class SUser(BaseModel):
    id: int
    username: str
    email: EmailStr
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class SUserUpdate(BaseModel):
    username: str | None

class SUserLogin(BaseModel):
    username: str
    password: str