from collections import defaultdict
from datetime import UTC, date, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger

from src.models.workout import ExerciseModel, StatusTypes, WorkoutExercise, WorkoutModel
from src.schemas.progress import SExerciseHistoryItem, SExerciseRecord, SProgressSummary, SWeeklyVolume


def _volume(link: WorkoutExercise) -> float:
    """Calculate training volume for a workout exercise link."""
    return float(link.sets * link.reps * (link.weight or 0))


def _completed_at(link: WorkoutExercise, workout: WorkoutModel) -> datetime:
    """Return the completion timestamp used for progress calculations."""
    return link.completed_at or workout.planned_at


def _week_start(value: datetime) -> date:
    """Return the Monday date for the week containing the given datetime."""
    current = value.astimezone(UTC).date() if value.tzinfo else value.date()
    return current - timedelta(days=current.weekday())


async def _completed_rows(
    session: AsyncSession,
    user_id: int,
) -> list[tuple[WorkoutExercise, WorkoutModel, ExerciseModel]]:
    """Load completed workout exercise rows for a user with related entities."""
    stmt = (
        select(WorkoutExercise, WorkoutModel, ExerciseModel)
        .join(WorkoutModel, WorkoutExercise.workout_id == WorkoutModel.id)
        .join(ExerciseModel, WorkoutExercise.exercise_id == ExerciseModel.id)
        .where(
            WorkoutModel.user_id == user_id,
            WorkoutExercise.status == StatusTypes.done,
        )
        .order_by(WorkoutExercise.completed_at.desc().nullslast(), WorkoutModel.planned_at.desc())
    )
    result = await session.execute(stmt)
    return list(result.all())


async def get_progress_summary(
    session: AsyncSession,
    user_id: int,
) -> SProgressSummary:
    """Return aggregate progress metrics for a user."""
    logger.info("Getting progress summary user_id={}", user_id)

    try:
        rows = await _completed_rows(session=session, user_id=user_id)
        planned_result = await session.execute(
            select(WorkoutModel.id).where(
                WorkoutModel.user_id == user_id,
                WorkoutModel.status == StatusTypes.planned,
            )
        )
    except SQLAlchemyError as error:
        logger.exception("Database error while getting progress summary user_id={}", user_id)
        raise ValueError("Не удалось получить прогресс") from error

    planned_workouts = len(planned_result.scalars().all())
    completed_workout_ids = {workout.id for _, workout, _ in rows}
    today_week = _week_start(datetime.now(UTC))
    total_volume = sum(_volume(link) for link, _, _ in rows)
    weekly_volume = sum(
        _volume(link)
        for link, workout, _ in rows
        if _week_start(_completed_at(link, workout)) == today_week
    )
    completed_this_week = len(
        {
            workout.id
            for link, workout, _ in rows
            if _week_start(_completed_at(link, workout)) == today_week
        }
    )

    volume_by_exercise: dict[int, tuple[str, float]] = {}
    for link, _, exercise in rows:
        name, current_volume = volume_by_exercise.get(exercise.id, (exercise.name, 0))
        volume_by_exercise[exercise.id] = (name, current_volume + _volume(link))

    best_exercise_name = None
    best_exercise_volume = 0.0
    if volume_by_exercise:
        best_exercise_name, best_exercise_volume = max(
            volume_by_exercise.values(),
            key=lambda item: item[1],
        )

    weeks_with_workouts = {
        _week_start(_completed_at(link, workout))
        for link, workout, _ in rows
    }
    current_streak = 0
    cursor = today_week if today_week in weeks_with_workouts else (
        max(weeks_with_workouts) if weeks_with_workouts else today_week
    )
    while cursor in weeks_with_workouts:
        current_streak += 1
        cursor = cursor - timedelta(days=7)

    summary = SProgressSummary(
        completed_workouts=len(completed_workout_ids),
        completed_this_week=completed_this_week,
        planned_workouts=planned_workouts,
        total_volume=round(total_volume, 2),
        weekly_volume=round(weekly_volume, 2),
        current_streak_weeks=current_streak,
        best_exercise_name=best_exercise_name,
        best_exercise_volume=round(best_exercise_volume, 2),
    )
    logger.info(
        "Progress summary calculated user_id={} completed_workouts={} total_volume={} weekly_volume={}",
        user_id,
        summary.completed_workouts,
        summary.total_volume,
        summary.weekly_volume,
    )
    return summary


async def get_weekly_volume(
    session: AsyncSession,
    user_id: int,
) -> list[SWeeklyVolume]:
    """Return completed training volume grouped by week."""
    logger.info("Getting weekly volume user_id={}", user_id)

    try:
        rows = await _completed_rows(session=session, user_id=user_id)
    except SQLAlchemyError as error:
        logger.exception("Database error while getting weekly volume user_id={}", user_id)
        raise ValueError("Не удалось получить недельный объем") from error

    volume_by_week: dict[date, float] = defaultdict(float)
    workouts_by_week: dict[date, set[int]] = defaultdict(set)

    for link, workout, _ in rows:
        week = _week_start(_completed_at(link, workout))
        volume_by_week[week] += _volume(link)
        workouts_by_week[week].add(workout.id)

    result = [
        SWeeklyVolume(
            week_start=week,
            volume=round(volume_by_week[week], 2),
            completed_workouts=len(workouts_by_week[week]),
        )
        for week in sorted(volume_by_week)
    ]
    logger.info("Weekly volume calculated user_id={} weeks={}", user_id, len(result))
    return result


async def get_exercise_record(
    session: AsyncSession,
    user_id: int,
    exercise_id: int,
) -> SExerciseRecord:
    """Return personal records for one exercise."""
    logger.info(
        "Getting exercise record user_id={} exercise_id={}",
        user_id,
        exercise_id,
    )

    try:
        rows = [
            row
            for row in await _completed_rows(session=session, user_id=user_id)
            if row[2].id == exercise_id
        ]
    except SQLAlchemyError as error:
        logger.exception(
            "Database error while getting exercise record user_id={} exercise_id={}",
            user_id,
            exercise_id,
        )
        raise ValueError("Не удалось получить рекорд упражнения") from error

    if not rows:
        logger.warning(
            "Exercise record not found user_id={} exercise_id={}",
            user_id,
            exercise_id,
        )
        raise ValueError("Завершенные подходы для упражнения не найдены")

    exercise = rows[0][2]
    max_weight_row = max(
        rows,
        key=lambda row: ((row[0].weight or 0), _completed_at(row[0], row[1])),
    )
    max_volume_row = max(
        rows,
        key=lambda row: (_volume(row[0]), _completed_at(row[0], row[1])),
    )
    best_set_row = max(
        rows,
        key=lambda row: (row[0].reps, (row[0].weight or 0), _completed_at(row[0], row[1])),
    )
    last_row = max(rows, key=lambda row: _completed_at(row[0], row[1]))

    max_weight = max_weight_row[0].weight
    record = SExerciseRecord(
        exercise_id=exercise.id,
        exercise_name=exercise.name,
        max_weight=max_weight,
        max_weight_at=_completed_at(max_weight_row[0], max_weight_row[1]) if max_weight is not None else None,
        max_volume=round(_volume(max_volume_row[0]), 2),
        max_volume_at=_completed_at(max_volume_row[0], max_volume_row[1]),
        best_set_reps=best_set_row[0].reps,
        best_set_weight=best_set_row[0].weight,
        last_completed_at=_completed_at(last_row[0], last_row[1]),
    )
    logger.info(
        "Exercise record calculated user_id={} exercise_id={} max_weight={} max_volume={}",
        user_id,
        exercise_id,
        record.max_weight,
        record.max_volume,
    )
    return record


async def get_exercise_history(
    session: AsyncSession,
    user_id: int,
    exercise_id: int,
) -> list[SExerciseHistoryItem]:
    """Return completed history entries for one exercise."""
    logger.info(
        "Getting exercise history user_id={} exercise_id={}",
        user_id,
        exercise_id,
    )
    try:
        rows = [
            row
            for row in await _completed_rows(session=session, user_id=user_id)
            if row[2].id == exercise_id
        ]
    except SQLAlchemyError as error:
        logger.exception(
            "Database error while getting exercise history user_id={} exercise_id={}",
            user_id,
            exercise_id,
        )
        raise ValueError("Не удалось получить историю упражнения") from error

    return [
        SExerciseHistoryItem(
            workout_id=workout.id,
            workout_title=workout.title,
            completed_at=_completed_at(link, workout),
            sets=link.sets,
            reps=link.reps,
            weight=link.weight,
            volume=round(_volume(link), 2),
        )
        for link, workout, _ in sorted(rows, key=lambda row: _completed_at(row[0], row[1]), reverse=True)
    ]
