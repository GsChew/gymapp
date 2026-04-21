from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.WorkoutModels import WorkoutModel
from src.schemas.WorkoutSchemas import SWorkoutCreate, SWorkoutUpdate


class WorkoutRepository:

    @classmethod
    async def get_workout_by_name(
        cls,
        user_id: int,
        name_of_workout: str,
        session: AsyncSession,
    ) -> WorkoutModel | None:
        stmt = select(WorkoutModel).where(
            WorkoutModel.user_id == user_id,
            WorkoutModel.title == name_of_workout,
        )
        result = await session.execute(stmt)
        return result.scalar_one_or_none()

    @classmethod
    async def get_workouts(
        cls,
        user_id: int,
        session: AsyncSession,
    ) -> list[WorkoutModel]:
        stmt = select(WorkoutModel).where(
            WorkoutModel.user_id == user_id
        )
        result = await session.execute(stmt)
        return list(result.scalars().all())

    @classmethod
    async def get_workout_by_id(
        cls,
        id: int,
        user_id: int,
        session: AsyncSession,
    ) -> WorkoutModel | None:
        stmt = select(WorkoutModel).where(
            WorkoutModel.id == id,
            WorkoutModel.user_id == user_id,
        )
        result = await session.execute(stmt)
        return result.scalar_one_or_none()

    @classmethod
    async def create_workout(
        cls,
        data: SWorkoutCreate,
        user_id: int,
        session: AsyncSession,
    ) -> WorkoutModel:
        workout = WorkoutModel(
            user_id=user_id,
            **data.model_dump()
        )
        session.add(workout)
        await session.commit()
        await session.refresh(workout)
        return workout

    @classmethod
    async def update_workout(
        cls,
        id: int,
        user_id: int,
        data: SWorkoutUpdate,
        session: AsyncSession,
    ) -> WorkoutModel | None:
        workout = await cls.get_workout_by_id(id, user_id, session)
        if workout is None:
            return None

        update_data = data.model_dump(exclude_unset=True)

        for field, value in update_data.items():
            setattr(workout, field, value)

        await session.commit()
        await session.refresh(workout)
        return workout

    @classmethod
    async def delete_workout(
        cls,
        id: int,
        user_id: int,
        session: AsyncSession,
    ) -> WorkoutModel | None:
        workout = await cls.get_workout_by_id(id, user_id, session)
        if workout is None:
            return None

        await session.delete(workout)
        await session.commit()
        return workout