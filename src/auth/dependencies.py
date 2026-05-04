from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.security import decode_token
from src.database import get_db
from src.models.UserModels import User
from src.repository.users import UserRepository


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


def is_access_token(token: str) -> bool:
    claims = decode_token(token)
    return claims.get("token_type") == "access"


def is_refresh_token(token: str) -> bool:
    claims = decode_token(token)
    return claims.get("token_type") == "refresh"


async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    session: Annotated[AsyncSession, Depends(get_db)],
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Не удалось проверить учетные данные",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        claims = decode_token(token)
        if claims.get("token_type") != "access":
            raise credentials_exception

        subject = claims.get("sub")
        if subject is None:
            raise credentials_exception

        user_id = int(subject)

    except Exception:
        raise credentials_exception

    user = await UserRepository.get_user(user_id, session)
    if user is None:
        raise credentials_exception

    return user