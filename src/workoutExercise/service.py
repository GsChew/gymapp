from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError

from src.models.WorkoutModels import WorkoutExercise, StatusTypes
from src.repository.workoutexercise import WorkoutExerciseRepository
from src.schemas.WorkoutSchemas import SWorkoutExerciseCreate, SWorkoutExerciseUpdate


async def create_workoutexercise(
    session: AsyncSession,
    user_id: int,
    data: SWorkoutExerciseCreate,
) -> WorkoutExercise:
    try:
        is_owner = await WorkoutExerciseRepository.check_workout_owner(
            workout_id=data.workout_id,
            user_id=user_id,
            session=session,
        )

        if not is_owner:
            raise ValueError("Тренировка не найдена или не принадлежит пользователю")

        return await WorkoutExerciseRepository.create_workoutexercise(
            data=data,
            session=session,
        )

    except SQLAlchemyError as e:
        await session.rollback()
        raise ValueError("Ошибка при создании упражнения в тренировке") from e


async def get_workoutexercises(
    session: AsyncSession,
    user_id: int,
) -> list[WorkoutExercise]:
    try:
        return await WorkoutExerciseRepository.get_workoutexercises(
            user_id=user_id,
            session=session,
        )

    except SQLAlchemyError as e:
        raise ValueError("Не удалось получить список упражнений в тренировках") from e


async def get_workoutexercises_by_status(
    session: AsyncSession,
    user_id: int,
    status: StatusTypes,
) -> list[WorkoutExercise]:
    try:
        return await WorkoutExerciseRepository.get_workoutexercises_by_status(
            user_id=user_id,
            status=status,
            session=session,
        )

    except SQLAlchemyError as e:
        raise ValueError("Не удалось получить список упражнений по статусу") from e


async def get_workoutexercise_by_ids(
    session: AsyncSession,
    user_id: int,
    workout_id: int,
    exercise_id: int,
) -> WorkoutExercise:
    try:
        selected = await WorkoutExerciseRepository.get_workoutexercise_by_ids(
            workout_id=workout_id,
            exercise_id=exercise_id,
            user_id=user_id,
            session=session,
        )

    except SQLAlchemyError as e:
        raise ValueError("Не удалось получить упражнение из тренировки") from e

    if selected is None:
        raise ValueError("Упражнение в тренировке не найдено")

    return selected


async def update_workoutexercise(
    session: AsyncSession,
    user_id: int,
    workout_id: int,
    exercise_id: int,
    data: SWorkoutExerciseUpdate,
) -> WorkoutExercise:
    update_data = data.model_dump(exclude_unset=True)

    if not update_data:
        raise ValueError("Нет данных для обновления")

    try:
        updated = await WorkoutExerciseRepository.update_workoutexercise(
            workout_id=workout_id,
            exercise_id=exercise_id,
            user_id=user_id,
            data=data,
            session=session,
        )

    except SQLAlchemyError as e:
        await session.rollback()
        raise ValueError("Не удалось изменить упражнение в тренировке") from e

    if updated is None:
        raise ValueError("Упражнение в тренировке не найдено")

    return updated


async def delete_workoutexercise(
    session: AsyncSession,
    workout_id: int,
    exercise_id: int,
    user_id: int,
) -> WorkoutExercise:
    try:
        deleted = await WorkoutExerciseRepository.delete_workoutexercise(
            workout_id=workout_id,
            exercise_id=exercise_id,
            user_id=user_id,
            session=session,
        )

    except SQLAlchemyError as e:
        await session.rollback()
        raise ValueError("Не удалось удалить упражнение из тренировки") from e

    if deleted is None:
        raise ValueError("Упражнение в тренировке не найдено")

    return deleted