from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError
from loguru import logger

from src.models.workout import WorkoutExercise, StatusTypes
from src.repository.workout_exercises import WorkoutExerciseRepository
from src.schemas.workout import (
    SWorkoutExerciseCreate,
    SWorkoutExerciseUpdate,
)


async def create_workout_exercise(
    session: AsyncSession,
    user_id: int,
    data: SWorkoutExerciseCreate,
) -> WorkoutExercise:

    """Add an exercise to a workout owned by the user."""
    logger.info(
        f"Creating workout exercise "
        f"user_id={user_id} "
        f"workout_id={data.workout_id} "
        f"exercise_id={data.exercise_id}"
    )

    try:
        is_owner = await WorkoutExerciseRepository.check_workout_owner(
            workout_id=data.workout_id,
            user_id=user_id,
            session=session,
        )

        if not is_owner:

            logger.warning(
                f"Workout not found or access denied "
                f"user_id={user_id} "
                f"workout_id={data.workout_id}"
            )

            raise ValueError(
                "Тренировка не найдена или не принадлежит пользователю"
            )

        created = await WorkoutExerciseRepository.create_workout_exercise(
            data=data,
            session=session,
        )

    except SQLAlchemyError as e:

        await session.rollback()

        logger.exception(
            f"Database error while creating workout exercise "
            f"user_id={user_id} "
            f"workout_id={data.workout_id} "
            f"exercise_id={data.exercise_id}"
        )

        raise ValueError(
            "Ошибка при создании упражнения в тренировке"
        ) from e

    logger.info(
        f"Workout exercise created successfully "
        f"user_id={user_id} "
        f"workout_id={created.workout_id} "
        f"exercise_id={created.exercise_id}"
    )

    return created


async def get_workout_exercises(
    session: AsyncSession,
    user_id: int,
) -> list[WorkoutExercise]:

    """Return workout exercise links for the current user."""
    logger.info(
        f"Getting workout exercises "
        f"user_id={user_id}"
    )

    try:
        exercises = await WorkoutExerciseRepository.get_workout_exercises(
            user_id=user_id,
            session=session,
        )

    except SQLAlchemyError as e:

        logger.exception(
            f"Database error while getting workout exercises "
            f"user_id={user_id}"
        )

        raise ValueError(
            "Не удалось получить список упражнений в тренировках"
        ) from e

    logger.info(
        f"Workout exercises retrieved successfully "
        f"user_id={user_id} "
        f"count={len(exercises)}"
    )

    return exercises


async def get_workout_exercises_by_status(
    session: AsyncSession,
    user_id: int,
    status: StatusTypes,
) -> list[WorkoutExercise]:

    """Return workout exercise links with the requested status."""
    logger.info(
        f"Getting workout exercises by status "
        f"user_id={user_id} "
        f"status={status}"
    )

    try:
        exercises = await WorkoutExerciseRepository.get_workout_exercises_by_status(
            user_id=user_id,
            status=status,
            session=session,
        )

    except SQLAlchemyError as e:

        logger.exception(
            f"Database error while getting workout exercises by status "
            f"user_id={user_id} "
            f"status={status}"
        )

        raise ValueError(
            "Не удалось получить список упражнений по статусу"
        ) from e

    logger.info(
        f"Workout exercises retrieved successfully "
        f"user_id={user_id} "
        f"status={status} "
        f"count={len(exercises)}"
    )

    return exercises


async def get_workout_exercise_by_ids(
    session: AsyncSession,
    user_id: int,
    workout_id: int,
    exercise_id: int,
) -> WorkoutExercise:

    """Return one workout exercise link by workout and exercise ids."""
    logger.info(
        f"Getting workout exercise "
        f"user_id={user_id} "
        f"workout_id={workout_id} "
        f"exercise_id={exercise_id}"
    )

    try:
        selected = await WorkoutExerciseRepository.get_workout_exercise_by_ids(
            workout_id=workout_id,
            exercise_id=exercise_id,
            user_id=user_id,
            session=session,
        )

    except SQLAlchemyError as e:

        logger.exception(
            f"Database error while getting workout exercise "
            f"user_id={user_id} "
            f"workout_id={workout_id} "
            f"exercise_id={exercise_id}"
        )

        raise ValueError(
            "Не удалось получить упражнение из тренировки"
        ) from e

    if selected is None:

        logger.warning(
            f"Workout exercise not found "
            f"user_id={user_id} "
            f"workout_id={workout_id} "
            f"exercise_id={exercise_id}"
        )

        raise ValueError("Упражнение в тренировке не найдено")

    logger.info(
        f"Workout exercise retrieved successfully "
        f"user_id={user_id} "
        f"workout_id={workout_id} "
        f"exercise_id={exercise_id}"
    )

    return selected


async def update_workout_exercise(
    session: AsyncSession,
    user_id: int,
    workout_id: int,
    exercise_id: int,
    data: SWorkoutExerciseUpdate,
) -> WorkoutExercise:

    """Update an exercise link in a workout owned by the user."""
    logger.info(
        f"Updating workout exercise "
        f"user_id={user_id} "
        f"workout_id={workout_id} "
        f"exercise_id={exercise_id}"
    )

    update_data = data.model_dump(exclude_unset=True)

    if not update_data:

        logger.warning(
            f"Workout exercise update failed: no data provided "
            f"user_id={user_id} "
            f"workout_id={workout_id} "
            f"exercise_id={exercise_id}"
        )

        raise ValueError("Нет данных для обновления")

    try:
        updated = await WorkoutExerciseRepository.update_workout_exercise(
            workout_id=workout_id,
            exercise_id=exercise_id,
            user_id=user_id,
            data=data,
            session=session,
        )

    except SQLAlchemyError as e:

        await session.rollback()

        logger.exception(
            f"Database error while updating workout exercise "
            f"user_id={user_id} "
            f"workout_id={workout_id} "
            f"exercise_id={exercise_id}"
        )

        raise ValueError(
            "Не удалось изменить упражнение в тренировке"
        ) from e

    if updated is None:

        logger.warning(
            f"Workout exercise not found "
            f"user_id={user_id} "
            f"workout_id={workout_id} "
            f"exercise_id={exercise_id}"
        )

        raise ValueError("Упражнение в тренировке не найдено")

    logger.info(
        f"Workout exercise updated successfully "
        f"user_id={user_id} "
        f"workout_id={workout_id} "
        f"exercise_id={exercise_id} "
        f"fields={list(update_data.keys())}"
    )

    return updated


async def delete_workout_exercise(
    session: AsyncSession,
    workout_id: int,
    exercise_id: int,
    user_id: int,
) -> WorkoutExercise:

    """Delete an exercise link from a workout owned by the user."""
    logger.info(
        f"Deleting workout exercise "
        f"user_id={user_id} "
        f"workout_id={workout_id} "
        f"exercise_id={exercise_id}"
    )

    try:
        deleted = await WorkoutExerciseRepository.delete_workout_exercise(
            workout_id=workout_id,
            exercise_id=exercise_id,
            user_id=user_id,
            session=session,
        )

    except SQLAlchemyError as e:

        await session.rollback()

        logger.exception(
            f"Database error while deleting workout exercise "
            f"user_id={user_id} "
            f"workout_id={workout_id} "
            f"exercise_id={exercise_id}"
        )

        raise ValueError(
            "Не удалось удалить упражнение из тренировки"
        ) from e

    if deleted is None:

        logger.warning(
            f"Workout exercise not found "
            f"user_id={user_id} "
            f"workout_id={workout_id} "
            f"exercise_id={exercise_id}"
        )

        raise ValueError("Упражнение в тренировке не найдено")

    logger.info(
        f"Workout exercise deleted successfully "
        f"user_id={user_id} "
        f"workout_id={workout_id} "
        f"exercise_id={exercise_id}"
    )

    return deleted
