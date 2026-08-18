from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from loguru import logger

from src.schemas.user import SUserCreate, SUserLogin
from src.repository.users import UserRepository
from src.auth.security import hash_password, create_access_token, create_refresh_token, verify_password, decode_token
from src.schemas.token import STokenResponse

async def register_user(user: SUserCreate, session: AsyncSession):
    """Create a user after hashing the password and validating uniqueness."""
    logger.info(f"Trying to register user username={user.username}")

    user_data = user.model_dump()
    user_data["hashed_password"] = hash_password(user.password)
    user_data.pop("password")

    try:
        created_user = await UserRepository.create_user(user_data, session)

        logger.info(
            f"User created successfully "
            f"user_id={created_user.id} "
            f"username={created_user.username}"
        )

        return created_user

    except IntegrityError:
        await session.rollback()

        logger.warning(
            f"Registration failed: user with this username/email already exists "
            f"username={user.username} "
            f"email={user.email}"
        )

        raise ValueError("Пользователь с таким username или email уже существует")

    except SQLAlchemyError:
        await session.rollback()

        logger.exception(
            f"Database error while registering user "
            f"username={user.username} "
            f"email={user.email}"
        )

        raise ValueError("Ошибка при создании пользователя")

async def login_user(user: SUserLogin, session: AsyncSession) -> STokenResponse:
    """Authenticate user credentials and issue token pair."""
    logger.info(f"Trying to login user username={user.username}")

    try:
        curr_user = await UserRepository.get_user_by_username(user.username, session)

        if curr_user is None:
            logger.warning(
                f"Login failed: user not found "
                f"username={user.username}"
            )
            raise ValueError("Неверные учетные данные")

        if not verify_password(user.password, curr_user.hashed_password):
            logger.warning(
                f"Login failed: password mismatch "
                f"username={user.username} "
                f"user_id={curr_user.id}"
            )
            raise ValueError("Неверные учетные данные")

        access_token = create_access_token(curr_user.id)
        refresh_token = create_refresh_token(curr_user.id)

        logger.info(
            f"User logged in successfully "
            f"user_id={curr_user.id} "
            f"username={user.username}"
        )

        return STokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
        )

    except SQLAlchemyError:
        await session.rollback()

        logger.exception(
            f"Database error while login "
            f"username={user.username}"
        )

        raise ValueError("Ошибка при входе пользователя")

async def refresh_tokens(refresh_token: str) -> STokenResponse:

    """Validate a refresh token and issue a new token pair."""
    logger.info("Trying to refresh tokens")

    try:
        claims = decode_token(refresh_token)

    except Exception:

        logger.warning(
            "Refresh token decode failed"
        )

        raise ValueError("Некорректный refresh token")

    if claims.get("token_type") != "refresh":

        logger.warning(
            "Refresh token failed: invalid token type"
        )

        raise ValueError("Некорректный refresh token")

    subject = claims.get("sub")

    if subject is None:

        logger.warning(
            "Refresh token failed: subject not found"
        )

        raise ValueError("В токене отсутствует subject")

    logger.info(
        f"Tokens refreshed successfully "
        f"user_id={subject}"
    )

    return STokenResponse(
        access_token=create_access_token(subject),
        refresh_token=create_refresh_token(subject),
        token_type="bearer",
    )
