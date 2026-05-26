from loguru import logger
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.UserModels import UserRole, User
from src.repository.users import UserRepository


async def change_user_role(
    session: AsyncSession,
    user_id: int,
    role: UserRole,
) -> User:
    logger.info(
        "Changing user role: user_id={}, new_role={}",
        user_id,
        role.value,
    )

    try:
        user = await UserRepository.get_user(
            session=session,
            user_id=user_id,
        )

        if user is None:
            logger.warning(
                "User not found while changing role: user_id={}",
                user_id,
            )
            raise ValueError("Пользователь не найден")

        old_role = user.role

        user.role = role

        await session.commit()
        await session.refresh(user)

        logger.info(
            "User role changed successfully: user_id={}, old_role={}, new_role={}",
            user_id,
            old_role.value if old_role else None,
            role.value,
        )

        return user

    except SQLAlchemyError as e:
        await session.rollback()

        logger.exception(
            "Database error while changing user role: user_id={}, new_role={}",
            user_id,
            role.value,
        )

        raise ValueError("Не удалось изменить роль пользователя") from e