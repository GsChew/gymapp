from loguru import logger
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.user import UserRole, User
from src.repository.users import UserRepository


async def get_users(session: AsyncSession) -> list[User]:
    """Return users visible to trainers and administrators."""
    logger.info("Getting users for trainer dashboard")

    try:
        users = await UserRepository.get_users(session=session)
    except SQLAlchemyError as e:
        logger.exception("Database error while getting users for trainer dashboard")
        raise ValueError("Не удалось получить список пользователей") from e

    logger.info("Users retrieved for trainer dashboard count={}", len(users))
    return users


async def change_user_role(
    session: AsyncSession,
    user_id: int,
    role: UserRole,
) -> User:
    """Change a user role when requested by an administrator."""
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
        updated_user = await UserRepository.change_user_role(
            session=session,
            user_id=user_id,
            role=role,
        )
        if updated_user is None:
            logger.warning(
                "User disappeared while changing role: user_id={}",
                user_id,
            )
            raise ValueError("Пользователь не найден")

        logger.info(
            "User role changed successfully: user_id={}, old_role={}, new_role={}",
            user_id,
            old_role.value if old_role else None,
            role.value,
        )

        return updated_user

    except SQLAlchemyError as e:
        await session.rollback()

        logger.exception(
            "Database error while changing user role: user_id={}, new_role={}",
            user_id,
            role.value,
        )

        raise ValueError("Не удалось изменить роль пользователя") from e
