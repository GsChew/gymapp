from loguru import logger
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.WorkoutModels import ExerciseModel
from src.repository.exercises import ExerciseRepository
from src.schemas.WorkoutSchemas import (
    SExerciseUpdate,
    SExerciseCreate,
)


async def get_exercises(
    session: AsyncSession,
) -> list[ExerciseModel]:

    logger.info("Getting exercises")

    try:
        exercises = await ExerciseRepository.get_exercises(
            session=session
        )

    except SQLAlchemyError as e:

        logger.exception(
            "Database error while getting exercises"
        )

        raise ValueError(
            "Не удалось получить список упражнений"
        ) from e

    logger.info(
        f"Exercises retrieved successfully "
        f"count={len(exercises)}"
    )

    return exercises


async def get_exercise_by_id(
    session: AsyncSession,
    id: int,
) -> ExerciseModel:

    logger.info(
        f"Getting exercise "
        f"exercise_id={id}"
    )

    try:
        exercise = await ExerciseRepository.get_exercise_by_id(
            id=id,
            session=session,
        )

    except SQLAlchemyError as e:

        logger.exception(
            f"Database error while getting exercise "
            f"exercise_id={id}"
        )

        raise ValueError(
            "Не удалось получить упражнение"
        ) from e

    if exercise is None:

        logger.warning(
            f"Exercise not found "
            f"exercise_id={id}"
        )

        raise ValueError("Упражнение не найдено")

    logger.info(
        f"Exercise retrieved successfully "
        f"exercise_id={exercise.id}"
    )

    return exercise


async def create_exercise(
    session: AsyncSession,
    data: SExerciseCreate,
) -> ExerciseModel:

    logger.info(
        f"Creating exercise "
        f"title={data.title}"
    )

    try:
        exercise = await ExerciseRepository.create_exercise(
            data=data,
            session=session,
        )

    except SQLAlchemyError as e:

        await session.rollback()

        logger.exception(
            f"Database error while creating exercise "
            f"title={data.title}"
        )

        raise ValueError(
            "Не удалось создать упражнение"
        ) from e

    logger.info(
        f"Exercise created successfully "
        f"exercise_id={exercise.id} "
        f"title={exercise.title}"
    )

    return exercise


async def update_exercise(
    session: AsyncSession,
    id: int,
    data: SExerciseUpdate,
) -> ExerciseModel:

    logger.info(
        f"Updating exercise "
        f"exercise_id={id}"
    )

    update_data = data.model_dump(exclude_unset=True)

    if not update_data:

        logger.warning(
            f"Exercise update failed: no data provided "
            f"exercise_id={id}"
        )

        raise ValueError("Нет данных для обновления")

    try:
        exercise = await ExerciseRepository.update_exercise(
            id=id,
            data=data,
            session=session,
        )

    except SQLAlchemyError as e:

        await session.rollback()

        logger.exception(
            f"Database error while updating exercise "
            f"exercise_id={id}"
        )

        raise ValueError(
            "Не удалось обновить упражнение"
        ) from e

    if exercise is None:

        logger.warning(
            f"Exercise not found "
            f"exercise_id={id}"
        )

        raise ValueError("Упражнение не найдено")

    logger.info(
        f"Exercise updated successfully "
        f"exercise_id={exercise.id} "
        f"fields={list(update_data.keys())}"
    )

    return exercise


async def delete_exercise(
    session: AsyncSession,
    id: int,
) -> ExerciseModel:

    logger.info(
        f"Deleting exercise "
        f"exercise_id={id}"
    )

    try:
        exercise = await ExerciseRepository.delete_exercise(
            id=id,
            session=session,
        )

    except SQLAlchemyError as e:

        await session.rollback()

        logger.exception(
            f"Database error while deleting exercise "
            f"exercise_id={id}"
        )

        raise ValueError(
            "Не удалось удалить упражнение"
        ) from e

    if exercise is None:

        logger.warning(
            f"Exercise not found "
            f"exercise_id={id}"
        )

        raise ValueError("Упражнение не найдено")

    logger.info(
        f"Exercise deleted successfully "
        f"exercise_id={id}"
    )

    return exercise