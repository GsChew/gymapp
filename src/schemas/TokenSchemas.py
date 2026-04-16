from typing import Literal
from pydantic import BaseModel, Field


class STokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: Literal["bearer"] = "bearer"


class SRefreshTokenRequest(BaseModel):
    refresh_token: str


class STokenPayload(BaseModel):
    sub: str = Field(..., description="Идентификатор пользователя внутри JWT")
    exp: int = Field(..., description="Время истечения токена в формате timestamp")
    token_type: Literal["access", "refresh"]


class STokenData(BaseModel):
    sub: str
    token_type: Literal["access", "refresh"]