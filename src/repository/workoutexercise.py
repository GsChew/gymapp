from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from src.models.WorkoutModels import WorkoutExercise, WorkoutModel, StatusTypes
from src.schemas.WorkoutSchemas import SWorkoutExerciseCreate, SWorkoutExerciseUpdate


class WorkoutExerciseRepository:

    @classmethod
    async def check_workout_owner(cls, workout_id: int, user_id: int, session: AsyncSession) -> bool:
        stmt = select(WorkoutModel.id).where(
            WorkoutModel.id == workout_id,
            WorkoutModel.user_id == user_id,
        )
        result = await session.execute(stmt)
        return result.scalar_one_or_none() is not None

    @classmethod
    async def create_workoutexercise(
        cls,
        data: SWorkoutExerciseCreate,
        session: AsyncSession,
    ) -> WorkoutExercise:
        workoutexercise = WorkoutExercise(**data.model_dump())

        session.add(workoutexercise)
        await session.commit()
        await session.refresh(workoutexercise)

        return workoutexercise

    @classmethod
    async def get_workoutexercises(
        cls,
        user_id: int,
        session: AsyncSession,
    ) -> list[WorkoutExercise]:
        stmt = (
            select(WorkoutExercise)
            .join(WorkoutModel, WorkoutExercise.workout_id == WorkoutModel.id)
            .where(WorkoutModel.user_id == user_id)
        )

        result = await session.execute(stmt)
        return list(result.scalars().all())

    @classmethod
    async def get_workoutexercises_by_status(
        cls,
        user_id: int,
        status: StatusTypes,
        session: AsyncSession,
    ) -> list[WorkoutExercise]:
        stmt = (
            select(WorkoutExercise)
            .join(WorkoutModel, WorkoutExercise.workout_id == WorkoutModel.id)
            .where(
                WorkoutModel.user_id == user_id,
                WorkoutExercise.status == status,
            )
        )

        result = await session.execute(stmt)
        return list(result.scalars().all())

    @classmethod
    async def get_workoutexercise_by_ids(
        cls,
        workout_id: int,
        exercise_id: int,
        user_id: int,
        session: AsyncSession,
    ) -> WorkoutExercise | None:
        stmt = (
            select(WorkoutExercise)
            .join(WorkoutModel, WorkoutExercise.workout_id == WorkoutModel.id)
            .where(
                WorkoutExercise.workout_id == workout_id,
                WorkoutExercise.exercise_id == exercise_id,
                WorkoutModel.user_id == user_id,
            )
        )

        result = await session.execute(stmt)
        return result.scalar_one_or_none()

    @classmethod
    async def update_workoutexercise(
        cls,
        workout_id: int,
        exercise_id: int,
        user_id: int,
        data: SWorkoutExerciseUpdate,
        session: AsyncSession,
    ) -> WorkoutExercise | None:
        workoutexercise = await cls.get_workoutexercise_by_ids(
            workout_id=workout_id,
            exercise_id=exercise_id,
            user_id=user_id,
            session=session,
        )

        if workoutexercise is None:
            return None

        update_data = data.model_dump(exclude_unset=True)

        for field, value in update_data.items():
            setattr(workoutexercise, field, value)

        await session.commit()
        await session.refresh(workoutexercise)

        return workoutexercise

    @classmethod
    async def delete_workoutexercise(
        cls,
        workout_id: int,
        exercise_id: int,
        user_id: int,
        session: AsyncSession,
    ) -> WorkoutExercise | None:
        workoutexercise = await cls.get_workoutexercise_by_ids(
            workout_id=workout_id,
            exercise_id=exercise_id,
            user_id=user_id,
            session=session,
        )

        if workoutexercise is None:
            return None

        await session.delete(workoutexercise)
        await session.commit()

        return workoutexercise