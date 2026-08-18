from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from sqlalchemy.exc import SQLAlchemyError

from src.exercises import service as exercises
from src.goals import service as goals
from src.models.user import UserRole
from src.models.workout import GoalStatus
from src.notifications import service as notifications
from src.schemas.notification import SNotificationCreate
from src.schemas.workout import (
    SExerciseCreate,
    SExerciseUpdate,
    SUserGoalCreate,
    SUserGoalUpdate,
)
from src.users import service as users


pytestmark = [pytest.mark.unit]


@pytest.mark.asyncio
async def test_exercise_service_success_paths(monkeypatch) -> None:
    model = SimpleNamespace(id=1, name="Exercise")
    monkeypatch.setattr(
        exercises.ExerciseRepository,
        "get_exercises",
        AsyncMock(return_value=[model]),
    )
    monkeypatch.setattr(
        exercises.ExerciseRepository,
        "get_exercise_by_id",
        AsyncMock(return_value=model),
    )
    monkeypatch.setattr(
        exercises.ExerciseRepository,
        "create_exercise",
        AsyncMock(return_value=model),
    )
    monkeypatch.setattr(
        exercises.ExerciseRepository,
        "update_exercise",
        AsyncMock(return_value=model),
    )
    monkeypatch.setattr(
        exercises.ExerciseRepository,
        "delete_exercise",
        AsyncMock(return_value=model),
    )
    session = SimpleNamespace(rollback=AsyncMock())

    assert await exercises.get_exercises(session) == [model]
    assert await exercises.get_exercise_by_id(session, 1) is model
    assert (
        await exercises.create_exercise(
            session,
            SExerciseCreate(name="Exercise", train="силовая_тренировка"),
        )
        is model
    )
    assert (
        await exercises.update_exercise(
            session,
            1,
            SExerciseUpdate(name="Updated"),
        )
        is model
    )
    assert await exercises.delete_exercise(session, 1) is model


@pytest.mark.asyncio
async def test_exercise_service_not_found_empty_and_database_errors(
    monkeypatch,
) -> None:
    session = SimpleNamespace(rollback=AsyncMock())
    monkeypatch.setattr(
        exercises.ExerciseRepository,
        "get_exercise_by_id",
        AsyncMock(return_value=None),
    )
    with pytest.raises(ValueError, match="не найдено"):
        await exercises.get_exercise_by_id(session, 1)

    with pytest.raises(ValueError, match="Нет данных"):
        await exercises.update_exercise(session, 1, SExerciseUpdate())

    monkeypatch.setattr(
        exercises.ExerciseRepository,
        "delete_exercise",
        AsyncMock(return_value=None),
    )
    with pytest.raises(ValueError, match="не найдено"):
        await exercises.delete_exercise(session, 1)

    monkeypatch.setattr(
        exercises.ExerciseRepository,
        "create_exercise",
        AsyncMock(side_effect=SQLAlchemyError("db")),
    )
    with pytest.raises(ValueError, match="Не удалось создать"):
        await exercises.create_exercise(
            session,
            SExerciseCreate(name="Exercise", train="кардио"),
        )
    session.rollback.assert_awaited()


@pytest.mark.asyncio
async def test_notification_service_success_paths(monkeypatch) -> None:
    model = SimpleNamespace(id=1, user_id=4)
    monkeypatch.setattr(
        notifications.NotificationsRepository,
        "create_notification",
        AsyncMock(return_value=model),
    )
    monkeypatch.setattr(
        notifications.NotificationsRepository,
        "get_notifications",
        AsyncMock(return_value=[model]),
    )
    monkeypatch.setattr(
        notifications.NotificationsRepository,
        "get_notification_by_id",
        AsyncMock(return_value=model),
    )
    monkeypatch.setattr(
        notifications.NotificationsRepository,
        "mark_notification_as_read",
        AsyncMock(return_value=model),
    )
    monkeypatch.setattr(
        notifications.NotificationsRepository,
        "delete_notification",
        AsyncMock(return_value=model),
    )
    monkeypatch.setattr(
        notifications.NotificationsRepository,
        "get_unread_count_by_user_id",
        AsyncMock(return_value=2),
    )
    session = SimpleNamespace(rollback=AsyncMock())

    data = SNotificationCreate(user_id=4, title="Title", message="Message")
    assert await notifications.create_notification(session, data) is model
    assert await notifications.get_notifications(session, 4, 10, 0, None) == [model]
    assert await notifications.get_notification_by_id(session, 4, 1) is model
    assert await notifications.mark_notification_as_read(session, 4, 1) is model
    assert await notifications.delete_notification(session, 4, 1) is model
    assert await notifications.get_unread_count_by_user_id(session, 4) == 2


@pytest.mark.asyncio
async def test_notification_service_not_found_and_database_error(
    monkeypatch,
) -> None:
    session = SimpleNamespace(rollback=AsyncMock())
    for method_name, operation in (
        ("get_notification_by_id", notifications.get_notification_by_id),
        ("mark_notification_as_read", notifications.mark_notification_as_read),
        ("delete_notification", notifications.delete_notification),
    ):
        monkeypatch.setattr(
            notifications.NotificationsRepository,
            method_name,
            AsyncMock(return_value=None),
        )
        with pytest.raises(ValueError, match="не найдено"):
            await operation(session, 4, 1)

    monkeypatch.setattr(
        notifications.NotificationsRepository,
        "create_notification",
        AsyncMock(side_effect=SQLAlchemyError("db")),
    )
    with pytest.raises(ValueError, match="Не удалось создать"):
        await notifications.create_notification(
            session,
            SNotificationCreate(user_id=4, title="Title", message="Message"),
        )
    session.rollback.assert_awaited()


@pytest.mark.asyncio
async def test_goal_and_user_services_cover_success_and_not_found(
    monkeypatch,
) -> None:
    goal = SimpleNamespace(id=1)
    user = SimpleNamespace(id=2, role=UserRole.user)
    session = SimpleNamespace(rollback=AsyncMock())
    monkeypatch.setattr(
        goals.GoalRepository,
        "get_goals",
        AsyncMock(return_value=[goal]),
    )
    monkeypatch.setattr(
        goals.GoalRepository,
        "create_goal",
        AsyncMock(return_value=goal),
    )
    monkeypatch.setattr(
        goals.GoalRepository,
        "update_goal",
        AsyncMock(return_value=goal),
    )
    monkeypatch.setattr(
        goals.GoalRepository,
        "delete_goal",
        AsyncMock(return_value=goal),
    )

    assert await goals.get_goals(session, 2) == [goal]
    assert (
        await goals.create_goal(
            session,
            2,
            SUserGoalCreate(title="Goal", metric="kg", target_value=1),
        )
        is goal
    )
    assert (
        await goals.update_goal(
            session,
            2,
            1,
            SUserGoalUpdate(status=GoalStatus.done),
        )
        is goal
    )
    assert await goals.delete_goal(session, 2, 1) is goal

    monkeypatch.setattr(
        users.UserRepository,
        "get_users",
        AsyncMock(return_value=[user]),
    )
    monkeypatch.setattr(
        users.UserRepository,
        "get_user",
        AsyncMock(return_value=user),
    )
    monkeypatch.setattr(
        users.UserRepository,
        "change_user_role",
        AsyncMock(return_value=user),
    )
    assert await users.get_users(session) == [user]
    assert await users.change_user_role(session, 2, UserRole.trainer) is user

    monkeypatch.setattr(
        goals.GoalRepository,
        "update_goal",
        AsyncMock(return_value=None),
    )
    with pytest.raises(ValueError, match="не найдена"):
        await goals.update_goal(
            session,
            2,
            999,
            SUserGoalUpdate(current_value=1),
        )
    with pytest.raises(ValueError, match="Нет данных"):
        await goals.update_goal(session, 2, 1, SUserGoalUpdate())

    monkeypatch.setattr(
        users.UserRepository,
        "get_user",
        AsyncMock(return_value=None),
    )
    with pytest.raises(ValueError, match="не найден"):
        await users.change_user_role(session, 999, UserRole.trainer)
