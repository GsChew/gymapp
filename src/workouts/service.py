from datetime import UTC, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError
from loguru import logger

from src.models.workout import (
    ExerciseModel,
    MuscleTypes,
    StatusTypes,
    TrainTypes,
    WorkoutExercise,
)
from src.repository.workouts import WorkoutRepository
from src.models.workout import WorkoutModel
from src.schemas.workout import SWorkoutComplete, SWorkoutCreate, SWorkoutUpdate


STARTER_EXERCISES = (
    {
        "name": "Приседания со штангой",
        "description": "Контролируй глубину и сохраняй нейтральную спину.",
        "train": TrainTypes.strength_train,
        "muscle": MuscleTypes.quadriceps,
        "muscle_image_url": "/static/assets/exercise-strength.png",
    },
    {
        "name": "Румынская тяга",
        "description": "Веди таз назад и почувствуй работу задней поверхности бедра.",
        "train": TrainTypes.strength_train,
        "muscle": MuscleTypes.hamstrings,
        "muscle_image_url": "/static/assets/exercise-strength.png",
    },
    {
        "name": "Планка",
        "description": "Собери корпус в прямую линию и дыши ровно.",
        "train": TrainTypes.strength_train,
        "muscle": MuscleTypes.abdominal_muscles,
        "muscle_image_url": "/static/assets/exercise-strength.png",
    },
    {
        "name": "Жим гантелей лёжа",
        "description": "Опускай гантели под контролем, не своди плечи вперёд.",
        "train": TrainTypes.strength_train,
        "muscle": MuscleTypes.pectorals,
        "muscle_image_url": "/static/assets/exercise-strength.png",
    },
    {
        "name": "Тяга верхнего блока",
        "description": "Тяни локти вниз и не раскачивай корпус.",
        "train": TrainTypes.strength_train,
        "muscle": MuscleTypes.lats,
        "muscle_image_url": "/static/assets/exercise-strength.png",
    },
    {
        "name": "Интервальный бег",
        "description": "Чередуй быстрые отрезки и лёгкое восстановление.",
        "train": TrainTypes.cardio,
        "muscle": None,
        "muscle_image_url": "/static/assets/exercise-cardio.png",
    },
    {
        "name": "Мобильность таза",
        "description": "Мягкая подвижность перед восстановительной тренировкой.",
        "train": TrainTypes.stretching,
        "muscle": MuscleTypes.glutes,
        "muscle_image_url": "/static/assets/training-hero.png",
    },
    {
        "name": "Растяжка задней поверхности бедра",
        "description": "Двигайся плавно, без рывков и боли.",
        "train": TrainTypes.stretching,
        "muscle": MuscleTypes.hamstrings,
        "muscle_image_url": "/static/assets/training-hero.png",
    },
)

STARTER_WORKOUTS = (
    ("Ноги и корпус", 1, 18, ("Приседания со штангой", "Румынская тяга", "Планка")),
    ("Верх тела", 3, 18, ("Жим гантелей лёжа", "Тяга верхнего блока", "Планка")),
    ("Кардио: темп", 5, 10, ("Интервальный бег",)),
    ("Мобильность и восстановление", 6, 11, ("Мобильность таза", "Растяжка задней поверхности бедра")),
)


async def create_starter_plan(
    session: AsyncSession,
    user_id: int,
) -> list[WorkoutModel]:
    """Create a practical first training week without duplicating it for a user."""
    try:
        exercise_names = [exercise["name"] for exercise in STARTER_EXERCISES]
        exercises_result = await session.execute(
            select(ExerciseModel).where(ExerciseModel.name.in_(exercise_names))
        )
        exercises_by_name = {
            exercise.name: exercise
            for exercise in exercises_result.scalars().all()
        }

        for exercise_data in STARTER_EXERCISES:
            if exercise_data["name"] not in exercises_by_name:
                exercise = ExerciseModel(**exercise_data)
                session.add(exercise)
                exercises_by_name[exercise.name] = exercise

        await session.flush()

        workout_titles = [workout[0] for workout in STARTER_WORKOUTS]
        existing_result = await session.execute(
            select(WorkoutModel).where(
                WorkoutModel.user_id == user_id,
                WorkoutModel.title.in_(workout_titles),
            )
        )
        existing_titles = {
            workout.title
            for workout in existing_result.scalars().all()
        }

        now = datetime.now(UTC)
        created_workouts: list[WorkoutModel] = []

        for title, day_offset, hour, exercise_names in STARTER_WORKOUTS:
            if title in existing_titles:
                continue

            planned_at = (now + timedelta(days=day_offset)).replace(
                hour=hour,
                minute=0,
                second=0,
                microsecond=0,
            )
            workout = WorkoutModel(
                user_id=user_id,
                title=title,
                planned_at=planned_at,
                remind_at=planned_at - timedelta(hours=2),
                status=StatusTypes.planned,
            )
            session.add(workout)
            await session.flush()

            for order_index, exercise_name in enumerate(exercise_names):
                session.add(
                    WorkoutExercise(
                        workout_id=workout.id,
                        exercise_id=exercises_by_name[exercise_name].id,
                        order_index=order_index,
                        sets=3,
                        reps=10,
                        scheduled_at=planned_at,
                        status=StatusTypes.planned,
                    )
                )

            created_workouts.append(workout)

        await session.commit()

        for workout in created_workouts:
            await session.refresh(workout)

        return created_workouts

    except SQLAlchemyError as error:
        await session.rollback()
        logger.exception("Database error while creating starter plan user_id={}", user_id)
        raise ValueError("Не удалось добавить готовый план") from error


async def create_workout(
    session: AsyncSession,
    data: SWorkoutCreate,
    user_id: int,
) -> WorkoutModel:
    """Create a workout for the user."""
    logger.info(f"Creating workout user_id={user_id}")

    try:
        created_workout = await WorkoutRepository.create_workout(
            session=session,
            data=data,
            user_id=user_id,
        )

        logger.info(
            f"Workout created successfully "
            f"workout_id={created_workout.id} "
            f"user_id={created_workout.user_id}"
        )

        return created_workout

    except SQLAlchemyError as e:
        await session.rollback()

        logger.exception(
            f"Database error while creating workout "
            f"user_id={user_id}"
        )

        raise ValueError("Ошибка при создании тренировки") from e


async def get_workouts(
    session: AsyncSession,
    user_id: int,
    limit: int,
    offset: int,
    status: StatusTypes | None,
) -> list[WorkoutModel]:

    """Return workouts for the user with pagination and optional filters."""
    logger.info(
        f"Getting workouts "
        f"user_id={user_id} "
        f"limit={limit} "
        f"offset={offset} "
        f"status={status}"
    )

    try:
        workouts = await WorkoutRepository.get_workouts(
            user_id=user_id,
            session=session,
            limit=limit,
            offset=offset,
            status=status,
        )

        logger.info(
            f"Workouts retrieved successfully "
            f"user_id={user_id} "
            f"count={len(workouts)}"
        )

        return workouts

    except SQLAlchemyError as e:
        logger.exception(
            f"Database error while getting workouts "
            f"user_id={user_id}"
        )

        raise ValueError("Не удалось получить список тренировок") from e


async def get_workout_by_id(
    session: AsyncSession,
    id: int,
    user_id: int,
) -> WorkoutModel:

    """Return one workout by id for the user."""
    logger.info(
        f"Getting workout "
        f"user_id={user_id} "
        f"workout_id={id}"
    )

    try:

        workout = await WorkoutRepository.get_workout_by_id(
            user_id=user_id,
            id=id,
            session=session,
        )

    except SQLAlchemyError as e:

        logger.exception(
            f"Database error while getting workout "
            f"user_id={user_id} "
            f"workout_id={id}"
        )

        raise ValueError("Ошибка при получении тренировки") from e

    if workout is None:

        logger.warning(
            f"Workout not found "
            f"user_id={user_id} "
            f"workout_id={id}"
        )

        raise ValueError("Тренировка не найдена")

    logger.info(
        f"Workout retrieved successfully "
        f"user_id={user_id} "
        f"workout_id={workout.id}"
    )

    return workout


async def get_workout_by_name(
    session: AsyncSession,
    name: str,
    user_id: int,
) -> WorkoutModel:
    """Return one workout by title for the user."""
    logger.info(
        f"Getting workout "
        f"user_id={user_id} "
        f"workout_name={name}"
    )
    try:
        workout = await WorkoutRepository.get_workout_by_name(
            user_id=user_id,
            name_of_workout=name,
            session=session,
        )

    except SQLAlchemyError as e:
        logger.exception(
            f"Database error while getting workout "
            f"user_id={user_id} "
            f"workout_name={name}"
        )
        raise ValueError("Ошибка при получении тренировки") from e

    if workout is None:
        logger.warning(
            f"Workout not found "
            f"user_id={user_id} "
            f"workout_name={name}"
        )
        raise ValueError("Тренировка не найдена")

    logger.info(
        f"Workout retrieved successfully "
        f"user_id={user_id} "
        f"workout_name={name}"
    )
    return workout


async def update_workout(
    session: AsyncSession,
    id: int,
    user_id: int,
    data: SWorkoutUpdate,
) -> WorkoutModel:
    """Update a workout owned by the user."""
    logger.info(
        f"Updating workout "
        f"user_id={user_id} "
        f"workout_id={id}"
    )

    update_data = data.model_dump(exclude_unset=True)

    if not update_data:
        logger.warning(
            f"Workout update failed: no data provided "
            f"user_id={user_id} "
            f"workout_id={id}"
        )
        raise ValueError("Нет данных для обновления")

    try:
        workout = await WorkoutRepository.update_workout(
            id=id,
            user_id=user_id,
            data=data,
            session=session,
        )

    except SQLAlchemyError as e:
        await session.rollback()

        logger.exception(
            f"Database error while updating workout "
            f"user_id={user_id} "
            f"workout_id={id}"
        )

        raise ValueError("Не удалось изменить тренировку") from e

    if workout is None:
        logger.warning(
            f"Workout not found "
            f"user_id={user_id} "
            f"workout_id={id}"
        )
        raise ValueError("Тренировка не найдена")

    logger.info(
        f"Workout updated successfully "
        f"user_id={user_id} "
        f"workout_id={workout.id}"
    )

    return workout


async def complete_workout(
    session: AsyncSession,
    id: int,
    user_id: int,
    data: SWorkoutComplete,
) -> WorkoutModel:
    """Mark a workout and its exercises as completed with actual results."""
    logger.info(
        f"Completing workout "
        f"user_id={user_id} "
        f"workout_id={id}"
    )

    try:
        workout = await WorkoutRepository.get_workout_by_id(
            id=id,
            user_id=user_id,
            session=session,
        )

        if workout is None:
            logger.warning(
                f"Workout not found "
                f"user_id={user_id} "
                f"workout_id={id}"
            )
            raise ValueError("Тренировка не найдена")

        links_result = await session.execute(
            select(WorkoutExercise).where(WorkoutExercise.workout_id == workout.id)
        )
        links = list(links_result.scalars().all())
        links_by_exercise_id = {link.exercise_id: link for link in links}
        completed_at = data.completed_at or datetime.now(UTC)

        for entry in data.exercises:
            link = links_by_exercise_id.get(entry.exercise_id)
            if link is None:
                raise ValueError("Упражнение в тренировке не найдено")

            entry_data = entry.model_dump(exclude={"exercise_id"}, exclude_unset=True)
            for field, value in entry_data.items():
                setattr(link, field, value)

        for link in links:
            link.status = StatusTypes.done
            link.completed_at = completed_at

        workout.status = StatusTypes.done
        workout.notification_sent = True
        workout.wellness_energy = data.wellness_energy
        workout.wellness_sleep = data.wellness_sleep
        workout.wellness_soreness = data.wellness_soreness
        workout.completion_notes = data.completion_notes

        await session.commit()
        await session.refresh(workout)
        return workout

    except SQLAlchemyError as e:
        await session.rollback()
        logger.exception(
            f"Database error while completing workout "
            f"user_id={user_id} "
            f"workout_id={id}"
        )
        raise ValueError("Не удалось завершить тренировку") from e


async def delete_workout(
    session: AsyncSession,
    id: int,
    user_id: int,
) -> WorkoutModel:
    """Delete a workout owned by the user."""
    logger.info(
        f"Deleting workout "
        f"user_id={user_id} "
        f"workout_id={id}"
    )
    try:
        workout = await WorkoutRepository.delete_workout(
            id=id,
            user_id=user_id,
            session=session,
        )

    except SQLAlchemyError as e:
        await session.rollback()
        logger.exception(
            f"Database error while deleting workout "
            f"user_id={user_id} "
            f"workout_id={id}"
        )
        raise ValueError("Не удалось удалить тренировку") from e

    if workout is None:
        logger.warning(
            f"Workout not found "
            f"user_id={user_id} "
            f"workout_id={id}"
        )
        raise ValueError("Тренировка не найдена")

    logger.info(
        f"Workout deleted successfully "
        f"user_id={user_id} "
        f"workout_id={id}"
    )
    return workout
