from __future__ import annotations

from collections.abc import Awaitable, Callable
from datetime import UTC, datetime
from typing import Any

import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.notification import NotificationModel
from src.models.workout import (
    ExerciseModel,
    MuscleTypes,
    StatusTypes,
    TrainTypes,
    WorkoutExercise,
    WorkoutModel,
)
from tests.factories.exercise_factory import ExerciseFactory
from tests.factories.workout_factory import WorkoutFactory
from tests.helpers.dates import future_datetime


@pytest_asyncio.fixture
async def make_workout(
    db_session: AsyncSession,
) -> Callable[..., Awaitable[WorkoutModel]]:
    async def factory(*, user_id: int, **overrides: Any) -> WorkoutModel:
        payload = WorkoutFactory.build(**overrides)
        planned_at = payload["planned_at"]
        if isinstance(planned_at, str):
            planned_at = datetime.fromisoformat(planned_at.replace("Z", "+00:00"))
        workout = WorkoutModel(
            user_id=user_id,
            title=payload["title"],
            planned_at=planned_at,
            status=StatusTypes(payload["status"]),
            remind_at=overrides.get("remind_at"),
            notification_sent=overrides.get("notification_sent", False),
        )
        db_session.add(workout)
        await db_session.commit()
        await db_session.refresh(workout)
        return workout

    return factory


@pytest_asyncio.fixture
async def make_exercise(
    db_session: AsyncSession,
) -> Callable[..., Awaitable[ExerciseModel]]:
    async def factory(**overrides: Any) -> ExerciseModel:
        payload = ExerciseFactory.build(**overrides)
        exercise = ExerciseModel(
            name=payload["name"],
            description=payload.get("description"),
            train=TrainTypes(payload["train"]),
            muscle=(
                MuscleTypes(payload["muscle"])
                if payload.get("muscle") is not None
                else None
            ),
            video_url=payload.get("video_url"),
            muscle_image_url=payload.get("muscle_image_url"),
        )
        db_session.add(exercise)
        await db_session.commit()
        await db_session.refresh(exercise)
        return exercise

    return factory


@pytest_asyncio.fixture
async def make_workout_exercise(
    db_session: AsyncSession,
) -> Callable[..., Awaitable[WorkoutExercise]]:
    async def factory(
        *,
        workout_id: int,
        exercise_id: int,
        **overrides: Any,
    ) -> WorkoutExercise:
        link = WorkoutExercise(
            workout_id=workout_id,
            exercise_id=exercise_id,
            order_index=overrides.get("order_index", 0),
            sets=overrides.get("sets", 3),
            reps=overrides.get("reps", 10),
            weight=overrides.get("weight", 20.0),
            notes=overrides.get("notes"),
            scheduled_at=overrides.get("scheduled_at", future_datetime()),
            status=overrides.get("status", StatusTypes.planned),
            completed_at=overrides.get("completed_at"),
        )
        db_session.add(link)
        await db_session.commit()
        await db_session.refresh(link)
        return link

    return factory


@pytest_asyncio.fixture
async def make_notification(
    db_session: AsyncSession,
) -> Callable[..., Awaitable[NotificationModel]]:
    async def factory(*, user_id: int, **overrides: Any) -> NotificationModel:
        notification = NotificationModel(
            user_id=user_id,
            workout_id=overrides.get("workout_id"),
            title=overrides.get("title", "QA notification"),
            message=overrides.get("message", "Scheduled workout reminder"),
            is_read=overrides.get("is_read", False),
            created_at=overrides.get("created_at", datetime.now(UTC)),
        )
        db_session.add(notification)
        await db_session.commit()
        await db_session.refresh(notification)
        return notification

    return factory
