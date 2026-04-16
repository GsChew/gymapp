from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from src.schemas.UserSchemas import SUserCreate, SUserLogin
from src.repository.users import UserRepository
from src.auth.security import hash_password, create_access_token, create_refresh_token, verify_password, decode_token
from src.schemas.TokenSchemas import STokenResponse

async def register_user(user: SUserCreate, session: AsyncSession):
    user_data = user.model_dump()
    user_data["password"] = hash_password(user.password)

    try:
        created_user = await UserRepository.create_user(user_data, session)
        return created_user

    except IntegrityError:
        await session.rollback()
        raise ValueError("Пользователь с таким username или email уже существует")

    except SQLAlchemyError:
        await session.rollback()
        raise ValueError("Ошибка при создании пользователя")

async def login_user(user: SUserLogin, session: AsyncSession) -> STokenResponse:
    try:
        curr_user = await UserRepository.get_user_by_username(user.username, session)

        if curr_user is None:
            raise ValueError("Пользователь не найден")

        if not verify_password(user.password, curr_user.hashed_password):
            raise ValueError("Неверный пароль")

        access_token = create_access_token(curr_user.id)
        refresh_token = create_refresh_token(curr_user.id)

        return STokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
        )

    except SQLAlchemyError:
        await session.rollback()
        raise ValueError("Ошибка при входе пользователя")

async def refresh_tokens(refresh_token: str) -> STokenResponse:
    claims = decode_token(refresh_token)

    if claims.get("token_type") != "refresh":
        raise ValueError("Некорректный refresh token")

    subject = claims.get("sub")
    if subject is None:
        raise ValueError("В токене отсутствует subject")

    return STokenResponse(
        access_token=create_access_token(subject),
        refresh_token=create_refresh_token(subject),
        token_type="bearer",
    )