from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.security import decode_token
from src.database import get_db
from src.models.user import User
from src.repository.users import UserRepository
from src.models.user import UserRole


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


def is_access_token(token: str) -> bool:
    """Return whether the token is an access token."""
    claims = decode_token(token)
    return claims.get("token_type") == "access"


def is_refresh_token(token: str) -> bool:
    """Return whether the token is a refresh token."""
    claims = decode_token(token)
    return claims.get("token_type") == "refresh"


async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    session: Annotated[AsyncSession, Depends(get_db)],
) -> User:
    """Resolve and return the authenticated user from a bearer token."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Не удалось проверить учетные данные",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        claims = decode_token(token)
        if claims.get("token_type") != "access":
            logger.warning(
                "Authentication failed: invalid token type token_type={}",
                claims.get("token_type"),
            )
            raise credentials_exception

        subject = claims.get("sub")
        if subject is None:
            logger.warning("Authentication failed: missing token subject")
            raise credentials_exception

        user_id = int(subject)

    except HTTPException:
        raise
    except Exception:
        logger.warning("Authentication failed: token decoding error")
        raise credentials_exception

    user = await UserRepository.get_user(user_id, session)
    if user is None:
        logger.warning("Authentication failed: user not found user_id={}", user_id)
        raise credentials_exception

    return user

def require_roles(*roles: UserRole):
    """Build a dependency that allows only users with the required roles."""
    async def role_checker(
        user: User = Depends(get_current_user),
    ) -> User:
        """Validate that the current user has one of the required roles."""
        if user.role not in roles:
            logger.warning(
                "Authorization denied user_id={} role={} required_roles={}",
                getattr(user, "id", "-"),
                user.role.value,
                [role.value for role in roles],
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Недостаточно прав",
            )

        return user

    return role_checker
