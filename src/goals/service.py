from loguru import logger
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.workout import UserGoal
from src.repository.goals import GoalRepository
from src.schemas.workout import SUserGoalCreate, SUserGoalUpdate


async def get_goals(session: AsyncSession, user_id: int) -> list[UserGoal]:
    """Return goals owned by the current user."""
    logger.info("Getting goals user_id={}", user_id)
    try:
        return await GoalRepository.get_goals(session=session, user_id=user_id)
    except SQLAlchemyError as error:
        logger.exception("Database error while getting goals user_id={}", user_id)
        raise ValueError("Не удалось получить цели") from error


async def create_goal(
    session: AsyncSession,
    user_id: int,
    data: SUserGoalCreate,
) -> UserGoal:
    """Create a user goal."""
    logger.info("Creating goal user_id={} title={}", user_id, data.title)
    try:
        return await GoalRepository.create_goal(
            session=session,
            user_id=user_id,
            data=data,
        )
    except SQLAlchemyError as error:
        await session.rollback()
        logger.exception("Database error while creating goal user_id={}", user_id)
        raise ValueError("Не удалось создать цель") from error


async def update_goal(
    session: AsyncSession,
    user_id: int,
    goal_id: int,
    data: SUserGoalUpdate,
) -> UserGoal:
    """Update a user goal."""
    update_data = data.model_dump(exclude_unset=True)
    if not update_data:
        raise ValueError("Нет данных для обновления")

    logger.info("Updating goal user_id={} goal_id={}", user_id, goal_id)
    try:
        goal = await GoalRepository.update_goal(
            session=session,
            user_id=user_id,
            goal_id=goal_id,
            data=data,
        )
    except SQLAlchemyError as error:
        await session.rollback()
        logger.exception("Database error while updating goal user_id={} goal_id={}", user_id, goal_id)
        raise ValueError("Не удалось обновить цель") from error

    if goal is None:
        raise ValueError("Цель не найдена")
    return goal


async def delete_goal(session: AsyncSession, user_id: int, goal_id: int) -> UserGoal:
    """Delete a user goal."""
    logger.info("Deleting goal user_id={} goal_id={}", user_id, goal_id)
    try:
        goal = await GoalRepository.delete_goal(
            session=session,
            user_id=user_id,
            goal_id=goal_id,
        )
    except SQLAlchemyError as error:
        await session.rollback()
        logger.exception("Database error while deleting goal user_id={} goal_id={}", user_id, goal_id)
        raise ValueError("Не удалось удалить цель") from error

    if goal is None:
        raise ValueError("Цель не найдена")
    return goal
