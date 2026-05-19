from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError
from loguru import logger

from src.repository.workouts import WorkoutRepository
from src.models.WorkoutModels import WorkoutModel
from src.schemas.WorkoutSchemas import SWorkoutCreate, SWorkoutUpdate


async def create_workout(
    session: AsyncSession,
    data: SWorkoutCreate,
    user_id: int,
) -> WorkoutModel:
    logger.info(f"Creating workout user_id={user_id}")

    workout_data = data.model_dump()
    workout_data["user_id"] = user_id

    try:
        created_workout = await WorkoutRepository.create_workout(
            session=session,
            data=workout_data,
        )

        logger.info(
            f"Workout created successfully "
            f"workout_id={created_workout.id} "
            f"user_id={created_workout.user_id}"
        )

        return created_workout

    except SQLAlchemyError as e:
        await session.rollback()

        logger.exception(
            f"Database error while creating workout "
            f"user_id={user_id}"
        )

        raise ValueError("Ошибка при создании тренировки") from e


async def get_workouts(
    session: AsyncSession,
    user_id: int,
) -> list[WorkoutModel]:

    logger.info(f"Getting workouts user_id={user_id}")

    try:

        workouts = await WorkoutRepository.get_workouts(
            user_id=user_id,
            session=session,
        )

        logger.info(
            f"Workouts retrieved successfully "
            f"user_id={user_id} "
            f"count={len(workouts)}"
        )

        return workouts

    except SQLAlchemyError as e:

        logger.exception(
            f"Database error while getting workouts "
            f"user_id={user_id}"
        )

        raise ValueError("Не удалось получить список тренировок") from e


async def get_workout_by_id(
    session: AsyncSession,
    id: int,
    user_id: int,
) -> WorkoutModel:

    logger.info(
        f"Getting workout "
        f"user_id={user_id} "
        f"workout_id={id}"
    )

    try:

        workout = await WorkoutRepository.get_workout_by_id(
            user_id=user_id,
            id=id,
            session=session,
        )

    except SQLAlchemyError as e:

        logger.exception(
            f"Database error while getting workout "
            f"user_id={user_id} "
            f"workout_id={id}"
        )

        raise ValueError("Ошибка при получении тренировки") from e

    if workout is None:

        logger.warning(
            f"Workout not found "
            f"user_id={user_id} "
            f"workout_id={id}"
        )

        raise ValueError("Тренировка не найдена")

    logger.info(
        f"Workout retrieved successfully "
        f"user_id={user_id} "
        f"workout_id={workout.id}"
    )

    return workout


async def get_workout_by_name(
    session: AsyncSession,
    name: str,
    user_id: int,
) -> WorkoutModel:
    logger.info(
        f"Getting workout "
        f"user_id={user_id} "
        f"workout_name={name}"
    )
    try:
        workout = await WorkoutRepository.get_workout_by_name(
            user_id=user_id,
            name_of_workout=name,
            session=session,
        )

    except SQLAlchemyError as e:
        logger.exception(
            f"Database error while getting workout "
            f"user_id={user_id} "
            f"workout_name={name}"
        )
        raise ValueError("Ошибка при получении тренировки") from e

    if workout is None:
        logger.warning(
            f"Workout not found "
            f"user_id={user_id} "
            f"workout_name={name}"
        )
        raise ValueError("Тренировка не найдена")

    logger.info(
        f"Workout retrieved successfully "
        f"user_id={user_id} "
        f"workout_name={name}"
    )
    return workout


async def update_workout(
    session: AsyncSession,
    id: int,
    user_id: int,
    data: SWorkoutUpdate,
) -> WorkoutModel:
    logger.info(
        f"Updating workout "
        f"user_id={user_id} "
        f"workout_id={id}"
    )

    update_data = data.model_dump(exclude_unset=True)

    if not update_data:
        logger.warning(
            f"Workout update failed: no data provided "
            f"user_id={user_id} "
            f"workout_id={id}"
        )
        raise ValueError("Нет данных для обновления")

    try:
        workout = await WorkoutRepository.update_workout(
            id=id,
            user_id=user_id,
            data=update_data,
            session=session,
        )

    except SQLAlchemyError as e:
        await session.rollback()

        logger.exception(
            f"Database error while updating workout "
            f"user_id={user_id} "
            f"workout_id={id}"
        )

        raise ValueError("Не удалось изменить тренировку") from e

    if workout is None:
        logger.warning(
            f"Workout not found "
            f"user_id={user_id} "
            f"workout_id={id}"
        )
        raise ValueError("Тренировка не найдена")

    logger.info(
        f"Workout updated successfully "
        f"user_id={user_id} "
        f"workout_id={workout.id}"
    )

    return workout

async def delete_workout(
    session: AsyncSession,
    id: int,
    user_id: int,
) -> WorkoutModel:
    logger.info(
        f"Deleting workout "
        f"user_id={user_id} "
        f"workout_id={id}"
    )
    try:
        workout = await WorkoutRepository.delete_workout(
            id=id,
            user_id=user_id,
            session=session,
        )

    except SQLAlchemyError as e:
        await session.rollback()
        logger.exception(
            f"Database error while deleting workout "
            f"user_id={user_id} "
            f"workout_id={id}"
        )
        raise ValueError("Не удалось удалить тренировку") from e

    if workout is None:
        logger.warning(
            f"Workout not found "
            f"user_id={user_id} "
            f"workout_id={id}"
        )
        raise ValueError("Тренировка не найдена")

    logger.info(
        f"Workout deleted successfully "
        f"user_id={user_id} "
        f"workout_id={id}"
    )
    return workout