from fastapi import APIRouter, Depends
from loguru import logger

from src.models.user import User
from src.schemas.token import STokenResponse, SRefreshTokenRequest
from src.schemas.user import SUser, SUserCreate, SUserLogin
from src.database import SessionDep
from src.auth.service import register_user, login_user, refresh_tokens
from src.auth.dependencies import get_current_user
from src.rate_limit.dependencies import limit_by_user, limit_by_ip
from src.rate_limit.config import AUTH_REGISTER_IP, AUTH_LOGIN_IP

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post(
    "/register",
    response_model=SUser,
    dependencies=[Depends(limit_by_ip(AUTH_REGISTER_IP))],
)
async def register(
    user: SUserCreate,
    session: SessionDep,
):
    """Register a new user account."""
    our_user = await register_user(user, session)
    return our_user


@router.post(
    "/login",
    response_model=STokenResponse,
    dependencies=[Depends(limit_by_ip(AUTH_LOGIN_IP))],
)
async def login(
    user: SUserLogin,
    session: SessionDep,
):
    """Authenticate a user and return access and refresh tokens."""
    return await login_user(user, session)
@router.post("/refresh", response_model=STokenResponse)
async def refresh(token_data: SRefreshTokenRequest):
    """Refresh an access token using a valid refresh token."""
    logger.info("Token refresh requested")
    return await refresh_tokens(token_data.refresh_token)


@router.get("/me", response_model=SUser)
async def get_me(current_user: User = Depends(get_current_user)):
    """Return the currently authenticated user."""
    logger.info("Current user requested user_id={}", current_user.id)
    return current_user
