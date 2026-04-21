from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError

from src.repository.workouts import WorkoutRepository
from src.models.WorkoutModels import WorkoutModel
from src.schemas.WorkoutSchemas import SWorkoutCreate, SWorkoutUpdate


async def create_workout(
    session: AsyncSession,
    data: SWorkoutCreate,
    user_id: int,
) -> WorkoutModel:
    workout_data = data.model_dump()
    workout_data["user_id"] = user_id

    try:
        created_workout = await WorkoutRepository.create_workout(
            session=session,
            data=workout_data,
        )
        return created_workout

    except SQLAlchemyError as e:
        await session.rollback()
        raise ValueError("Ошибка при создании тренировки") from e


async def get_workouts(
    session: AsyncSession,
    user_id: int,
) -> list[WorkoutModel]:
    try:
        workouts = await WorkoutRepository.get_workouts(
            user_id=user_id,
            session=session,
        )
        return workouts

    except SQLAlchemyError as e:
        raise ValueError("Не удалось получить список тренировок") from e


async def get_workout_by_id(
    session: AsyncSession,
    id: int,
    user_id: int,
) -> WorkoutModel:
    try:
        workout = await WorkoutRepository.get_workout_by_id(
            user_id=user_id,
            id=id,
            session=session,
        )

    except SQLAlchemyError as e:
        raise ValueError("Ошибка при получении тренировки") from e

    if workout is None:
        raise ValueError("Тренировка не найдена")

    return workout


async def get_workout_by_name(
    session: AsyncSession,
    name: str,
    user_id: int,
) -> WorkoutModel:
    try:
        workout = await WorkoutRepository.get_workout_by_name(
            user_id=user_id,
            name_of_workout=name,
            session=session,
        )

    except SQLAlchemyError as e:
        raise ValueError("Ошибка при получении тренировки") from e

    if workout is None:
        raise ValueError("Тренировка не найдена")

    return workout


async def update_workout(
    session: AsyncSession,
    id: int,
    user_id: int,
    data: SWorkoutUpdate,
) -> WorkoutModel:
    update_data = data.model_dump(exclude_unset=True)

    if not update_data:
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
        raise ValueError("Не удалось изменить тренировку") from e

    if workout is None:
        raise ValueError("Тренировка не найдена")

    return workout


async def delete_workout(
    session: AsyncSession,
    id: int,
    user_id: int,
) -> WorkoutModel:
    try:
        workout = await WorkoutRepository.delete_workout(
            id=id,
            user_id=user_id,
            session=session,
        )

    except SQLAlchemyError as e:
        await session.rollback()
        raise ValueError("Не удалось удалить тренировку") from e

    if workout is None:
        raise ValueError("Тренировка не найдена")

    return workout