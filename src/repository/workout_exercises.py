from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from src.models.workout import WorkoutExercise, WorkoutModel, StatusTypes
from src.schemas.workout import SWorkoutExerciseCreate, SWorkoutExerciseUpdate


class WorkoutExerciseRepository:

    @classmethod
    async def check_workout_owner(cls, workout_id: int, user_id: int, session: AsyncSession) -> bool:
        """Return whether the workout belongs to the user."""
        stmt = select(WorkoutModel.id).where(
            WorkoutModel.id == workout_id,
            WorkoutModel.user_id == user_id,
        )
        result = await session.execute(stmt)
        return result.scalar_one_or_none() is not None

    @classmethod
    async def create_workout_exercise(
        cls,
        data: SWorkoutExerciseCreate,
        session: AsyncSession,
    ) -> WorkoutExercise:
        """Add an exercise to a workout owned by the user."""
        workout_exercise = WorkoutExercise(**data.model_dump())

        session.add(workout_exercise)
        await session.commit()
        await session.refresh(workout_exercise)

        return workout_exercise

    @classmethod
    async def get_workout_exercises(
        cls,
        user_id: int,
        session: AsyncSession,
    ) -> list[WorkoutExercise]:
        """Return workout exercise links for the current user."""
        stmt = (
            select(WorkoutExercise)
            .join(WorkoutModel, WorkoutExercise.workout_id == WorkoutModel.id)
            .where(WorkoutModel.user_id == user_id)
        )

        result = await session.execute(stmt)
        return list(result.scalars().all())

    @classmethod
    async def get_workout_exercises_by_status(
        cls,
        user_id: int,
        status: StatusTypes,
        session: AsyncSession,
    ) -> list[WorkoutExercise]:
        """Return workout exercise links with the requested status."""
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
    async def get_workout_exercises_by_workout(
        cls,
        workout_id: int,
        user_id: int,
        session: AsyncSession,
    ) -> list[WorkoutExercise]:
        """Return exercise links for a specific workout owned by the user."""
        stmt = (
            select(WorkoutExercise)
            .join(WorkoutModel, WorkoutExercise.workout_id == WorkoutModel.id)
            .where(
                WorkoutExercise.workout_id == workout_id,
                WorkoutModel.user_id == user_id,
            )
            .order_by(WorkoutExercise.order_index)
        )

        result = await session.execute(stmt)
        return list(result.scalars().all())

    @classmethod
    async def get_workout_exercise_by_ids(
        cls,
        workout_id: int,
        exercise_id: int,
        user_id: int,
        session: AsyncSession,
    ) -> WorkoutExercise | None:
        """Return one workout exercise link by workout and exercise ids."""
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
    async def update_workout_exercise(
        cls,
        workout_id: int,
        exercise_id: int,
        user_id: int,
        data: SWorkoutExerciseUpdate,
        session: AsyncSession,
    ) -> WorkoutExercise | None:
        """Update an exercise link in a workout owned by the user."""
        workout_exercise = await cls.get_workout_exercise_by_ids(
            workout_id=workout_id,
            exercise_id=exercise_id,
            user_id=user_id,
            session=session,
        )

        if workout_exercise is None:
            return None

        update_data = data.model_dump(exclude_unset=True)

        for field, value in update_data.items():
            setattr(workout_exercise, field, value)

        await session.commit()
        await session.refresh(workout_exercise)

        return workout_exercise

    @classmethod
    async def delete_workout_exercise(
        cls,
        workout_id: int,
        exercise_id: int,
        user_id: int,
        session: AsyncSession,
    ) -> WorkoutExercise | None:
        """Delete an exercise link from a workout owned by the user."""
        workout_exercise = await cls.get_workout_exercise_by_ids(
            workout_id=workout_id,
            exercise_id=exercise_id,
            user_id=user_id,
            session=session,
        )

        if workout_exercise is None:
            return None

        await session.delete(workout_exercise)
        await session.commit()

        return workout_exercise
