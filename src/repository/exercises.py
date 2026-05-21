from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from models.WorkoutModels import MuscleTypes, TrainTypes
from src.models.WorkoutModels import ExerciseModel
from src.schemas.WorkoutSchemas import SExerciseCreate, SExerciseUpdate


class ExerciseRepository:

    @classmethod
    async def get_exercises(
            cls,
            session: AsyncSession,
            limit: int = 30,
            offset: int = 0,
            muscle: MuscleTypes | None = None,
            train_type: TrainTypes | None = None,
    ) -> list[ExerciseModel]:
        stmt = select(ExerciseModel)

        if muscle is not None:
            stmt = stmt.where(ExerciseModel.muscle == muscle)

        if train_type is not None:
            stmt = stmt.where(ExerciseModel.train_type == train_type)

        stmt = (
            stmt
            .order_by(ExerciseModel.id)
            .offset(offset)
            .limit(limit)
        )

        result = await session.execute(stmt)

        return list(result.scalars().all())

    @classmethod
    async def get_exercise_by_id(
        cls,
        id: int,
        session: AsyncSession,
    ) -> ExerciseModel | None:
        stmt = select(ExerciseModel).where(ExerciseModel.id == id)
        result = await session.execute(stmt)
        return result.scalar_one_or_none()

    @classmethod
    async def create_exercise(
        cls,
        data: SExerciseCreate,
        session: AsyncSession,
    ) -> ExerciseModel:
        exercise = ExerciseModel(**data.model_dump())
        session.add(exercise)
        await session.commit()
        await session.refresh(exercise)
        return exercise

    @classmethod
    async def update_exercise(
        cls,
        id: int,
        data: SExerciseUpdate,
        session: AsyncSession,
    ) -> ExerciseModel | None:
        exercise = await cls.get_exercise_by_id(id=id, session=session)
        if exercise is None:
            return None

        update_data = data.model_dump(exclude_unset=True)

        for field, value in update_data.items():
            setattr(exercise, field, value)

        await session.commit()
        await session.refresh(exercise)
        return exercise

    @classmethod
    async def delete_exercise(
        cls,
        id: int,
        session: AsyncSession,
    ) -> ExerciseModel | None:
        exercise = await cls.get_exercise_by_id(id=id, session=session)

        if exercise is None:
            return None

        await session.delete(exercise)
        await session.commit()
        return exercise