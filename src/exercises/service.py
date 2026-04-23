from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.WorkoutModels import ExerciseModel
from src.repository.exercises import ExerciseRepository
from src.schemas.WorkoutSchemas import SExerciseUpdate, SExerciseCreate


async def get_exercises(
    session: AsyncSession,
) -> list[ExerciseModel]:
    try:
        return await ExerciseRepository.get_exercises(session=session)

    except SQLAlchemyError as e:
        raise ValueError("Не удалось получить список упражнений") from e


async def get_exercise_by_id(
    session: AsyncSession,
    id: int,
) -> ExerciseModel:
    try:
        exercise = await ExerciseRepository.get_exercise_by_id(
            id=id,
            session=session,
        )

    except SQLAlchemyError as e:
        raise ValueError("Не удалось получить упражнение") from e

    if exercise is None:
        raise ValueError("Упражнение не найдено")

    return exercise


async def create_exercise(
    session: AsyncSession,
    data: SExerciseCreate,
) -> ExerciseModel:
    try:
        return await ExerciseRepository.create_exercise(
            data=data,
            session=session,
        )

    except SQLAlchemyError as e:
        await session.rollback()
        raise ValueError("Не удалось создать упражнение") from e


async def update_exercise(
    session: AsyncSession,
    id: int,
    data: SExerciseUpdate,
) -> ExerciseModel:
    update_data = data.model_dump(exclude_unset=True)

    if not update_data:
        raise ValueError("Нет данных для обновления")

    try:
        exercise = await ExerciseRepository.update_exercise(
            id=id,
            data=data,
            session=session,
        )

    except SQLAlchemyError as e:
        await session.rollback()
        raise ValueError("Не удалось обновить упражнение") from e

    if exercise is None:
        raise ValueError("Упражнение не найдено")

    return exercise


async def delete_exercise(
    session: AsyncSession,
    id: int,
) -> ExerciseModel:
    try:
        exercise = await ExerciseRepository.delete_exercise(
            id=id,
            session=session,
        )

    except SQLAlchemyError as e:
        await session.rollback()
        raise ValueError("Не удалось удалить упражнение") from e

    if exercise is None:
        raise ValueError("Упражнение не найдено")

    return exercise