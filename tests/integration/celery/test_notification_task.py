from unittest.mock import AsyncMock

import pytest
from sqlalchemy import func, select

from src.models.notification import NotificationModel
from src.models.workout import StatusTypes
from src.tasks import workout_notifications
from tests.helpers.dates import future_datetime, past_datetime


pytestmark = [pytest.mark.integration, pytest.mark.celery]


def test_notification_task_is_registered_and_runs_in_eager_mode(
    celery_eager,
    monkeypatch,
) -> None:
    async_operation = AsyncMock(return_value=None)
    monkeypatch.setattr(
        workout_notifications,
        "_check_workout_notifications",
        async_operation,
    )

    result = celery_eager.tasks["check_workout_notifications"].apply()

    assert result.successful()
    assert result.result is None
    async_operation.assert_awaited_once_with()


def test_notification_task_rejects_unexpected_parameters(celery_eager) -> None:
    with pytest.raises(TypeError):
        celery_eager.tasks["check_workout_notifications"].apply(
            args=[123],
            throw=True,
        )


@pytest.mark.asyncio
async def test_due_workout_creates_one_idempotent_notification(
    user_account,
    make_workout,
    db_session,
    db_session_factory,
    monkeypatch,
) -> None:
    workout = await make_workout(
        user_id=user_account.user.id,
        planned_at=future_datetime(days=1),
        remind_at=past_datetime(days=1),
    )
    monkeypatch.setattr(
        workout_notifications,
        "new_session",
        db_session_factory,
    )

    await workout_notifications._check_workout_notifications()
    await workout_notifications._check_workout_notifications()

    await db_session.refresh(workout)
    notifications = (
        await db_session.execute(
            select(NotificationModel).where(
                NotificationModel.workout_id == workout.id
            )
        )
    ).scalars().all()
    assert workout.notification_sent is True
    assert len(notifications) == 1
    assert notifications[0].user_id == user_account.user.id
    assert workout.title in notifications[0].message


@pytest.mark.asyncio
async def test_task_ignores_future_reminder_and_non_planned_workout(
    user_account,
    make_workout,
    db_session,
    db_session_factory,
    monkeypatch,
) -> None:
    future = await make_workout(
        user_id=user_account.user.id,
        title="Future reminder",
        remind_at=future_datetime(days=2),
    )
    missed = await make_workout(
        user_id=user_account.user.id,
        title="Missed",
        remind_at=past_datetime(days=1),
        status=StatusTypes.missed.value,
    )
    done = await make_workout(
        user_id=user_account.user.id,
        title="Done",
        remind_at=past_datetime(days=1),
        status=StatusTypes.done.value,
    )
    monkeypatch.setattr(
        workout_notifications,
        "new_session",
        db_session_factory,
    )

    await workout_notifications._check_workout_notifications()

    count = await db_session.scalar(
        select(func.count()).select_from(NotificationModel)
    )
    assert count == 0
    for workout in (future, missed, done):
        await db_session.refresh(workout)
        assert workout.notification_sent is False


@pytest.mark.asyncio
async def test_task_rolls_back_when_notification_dependency_fails(
    monkeypatch,
) -> None:
    session = AsyncMock()

    class SessionContext:
        async def __aenter__(self):
            return session

        async def __aexit__(self, *_args):
            return None

    monkeypatch.setattr(
        workout_notifications,
        "new_session",
        lambda: SessionContext(),
    )
    monkeypatch.setattr(
        "src.tasks.workout_notifications."
        "WorkoutRepository.get_workouts_for_notifications",
        AsyncMock(side_effect=RuntimeError("dependency failed")),
    )

    with pytest.raises(RuntimeError, match="dependency failed"):
        await workout_notifications._check_workout_notifications()

    session.rollback.assert_awaited_once()
    session.commit.assert_not_awaited()
