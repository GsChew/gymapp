from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.workout import StatusTypes, WorkoutExercise, WorkoutModel, WorkoutTemplate, WorkoutTemplateExercise
from src.schemas.workout import SWorkoutFromTemplate, SWorkoutTemplateCreate


class TemplateRepository:
    @classmethod
    async def get_templates(
        cls,
        session: AsyncSession,
        user_id: int,
    ) -> list[WorkoutTemplate]:
        """Return templates owned by a user."""
        result = await session.execute(
            select(WorkoutTemplate)
            .where(WorkoutTemplate.user_id == user_id)
            .order_by(WorkoutTemplate.created_at.desc())
        )
        return list(result.scalars().all())

    @classmethod
    async def get_template(
        cls,
        session: AsyncSession,
        user_id: int,
        template_id: int,
        *,
        load_exercises: bool = False,
    ) -> WorkoutTemplate | None:
        """Return one template owned by a user."""
        result = await session.execute(
            select(WorkoutTemplate).where(
                WorkoutTemplate.id == template_id,
                WorkoutTemplate.user_id == user_id,
            )
        )
        template = result.scalar_one_or_none()
        if template is not None and load_exercises:
            await session.refresh(template, attribute_names=["exercises"])
        return template

    @classmethod
    async def create_template(
        cls,
        session: AsyncSession,
        user_id: int,
        data: SWorkoutTemplateCreate,
    ) -> WorkoutTemplate:
        """Create a workout template with exercise links."""
        template = WorkoutTemplate(
            user_id=user_id,
            title=data.title,
            description=data.description,
        )
        session.add(template)
        await session.flush()

        for item in data.exercises:
            session.add(
                WorkoutTemplateExercise(
                    template_id=template.id,
                    **item.model_dump(),
                )
            )

        await session.commit()
        await session.refresh(template)
        return template

    @classmethod
    async def create_workout_from_template(
        cls,
        session: AsyncSession,
        user_id: int,
        template: WorkoutTemplate,
        data: SWorkoutFromTemplate,
    ) -> WorkoutModel:
        """Create a workout and exercise links from a loaded template."""
        workout = WorkoutModel(
            user_id=user_id,
            title=template.title,
            planned_at=data.planned_at,
            remind_at=data.remind_at,
            status=StatusTypes.planned,
        )
        session.add(workout)
        await session.flush()

        for item in sorted(template.exercises, key=lambda link: link.order_index):
            session.add(
                WorkoutExercise(
                    workout_id=workout.id,
                    exercise_id=item.exercise_id,
                    order_index=item.order_index,
                    sets=item.sets,
                    reps=item.reps,
                    weight=item.weight,
                    notes=item.notes,
                    scheduled_at=data.planned_at,
                    status=StatusTypes.planned,
                )
            )

        await session.commit()
        await session.refresh(workout)
        return workout

    @classmethod
    async def delete_template(
        cls,
        session: AsyncSession,
        user_id: int,
        template_id: int,
    ) -> WorkoutTemplate | None:
        """Delete one template owned by a user."""
        template = await cls.get_template(
            session=session,
            user_id=user_id,
            template_id=template_id,
        )
        if template is None:
            return None

        await session.delete(template)
        await session.commit()
        return template
