from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock

import pytest
from sqlalchemy.exc import SQLAlchemyError

from src.models.workout import StatusTypes
from src.schemas.workout import (
    SWorkoutComplete,
    SWorkoutCreate,
    SWorkoutExerciseCreate,
    SWorkoutExerciseUpdate,
    SWorkoutUpdate,
)
from src.workout_exercises import service as links
from src.workouts import service as workouts
from tests.helpers.dates import future_datetime


pytestmark = [pytest.mark.unit]


class ScalarResult:
    def __init__(self, values) -> None:
        self._values = values

    def scalars(self):
        return self

    def all(self):
        return self._values


@pytest.mark.asyncio
async def test_workout_service_repository_paths(monkeypatch) -> None:
    model = SimpleNamespace(id=1, user_id=2)
    session = SimpleNamespace(rollback=AsyncMock())
    for name in (
        "create_workout",
        "get_workout_by_id",
        "get_workout_by_name",
        "update_workout",
        "delete_workout",
    ):
        monkeypatch.setattr(
            workouts.WorkoutRepository,
            name,
            AsyncMock(return_value=model),
        )
    monkeypatch.setattr(
        workouts.WorkoutRepository,
        "get_workouts",
        AsyncMock(return_value=[model]),
    )
    create = SWorkoutCreate(title="Workout", planned_at=future_datetime())

    assert await workouts.create_workout(session, create, 2) is model
    assert await workouts.get_workouts(session, 2, 10, 0, None) == [model]
    assert await workouts.get_workout_by_id(session, 1, 2) is model
    assert await workouts.get_workout_by_name(session, "Workout", 2) is model
    assert (
        await workouts.update_workout(
            session,
            1,
            2,
            SWorkoutUpdate(title="Updated"),
        )
        is model
    )
    assert await workouts.delete_workout(session, 1, 2) is model


@pytest.mark.asyncio
async def test_workout_service_not_found_empty_and_database_error(
    monkeypatch,
) -> None:
    session = SimpleNamespace(rollback=AsyncMock())
    monkeypatch.setattr(
        workouts.WorkoutRepository,
        "get_workout_by_id",
        AsyncMock(return_value=None),
    )
    with pytest.raises(ValueError, match="не найдена"):
        await workouts.get_workout_by_id(session, 1, 2)

    monkeypatch.setattr(
        workouts.WorkoutRepository,
        "get_workout_by_name",
        AsyncMock(return_value=None),
    )
    with pytest.raises(ValueError, match="не найдена"):
        await workouts.get_workout_by_name(session, "Missing", 2)

    with pytest.raises(ValueError, match="Нет данных"):
        await workouts.update_workout(session, 1, 2, SWorkoutUpdate())

    monkeypatch.setattr(
        workouts.WorkoutRepository,
        "create_workout",
        AsyncMock(side_effect=SQLAlchemyError("db")),
    )
    with pytest.raises(ValueError, match="Ошибка при создании"):
        await workouts.create_workout(
            session,
            SWorkoutCreate(title="Workout", planned_at=future_datetime()),
            2,
        )
    session.rollback.assert_awaited()


@pytest.mark.asyncio
async def test_complete_workout_updates_links_and_workout(monkeypatch) -> None:
    workout = SimpleNamespace(
        id=1,
        status=StatusTypes.planned,
        notification_sent=False,
        wellness_energy=None,
        wellness_sleep=None,
        wellness_soreness=None,
        completion_notes=None,
    )
    link = SimpleNamespace(
        exercise_id=4,
        status=StatusTypes.planned,
        completed_at=None,
        sets=1,
        reps=1,
        weight=None,
        notes=None,
    )
    monkeypatch.setattr(
        workouts.WorkoutRepository,
        "get_workout_by_id",
        AsyncMock(return_value=workout),
    )
    session = SimpleNamespace(
        execute=AsyncMock(return_value=ScalarResult([link])),
        commit=AsyncMock(),
        refresh=AsyncMock(),
        rollback=AsyncMock(),
    )
    data = SWorkoutComplete.model_validate(
        {
            "exercises": [
                {"exercise_id": 4, "sets": 5, "reps": 3, "weight": 100}
            ],
            "wellness_energy": 5,
        }
    )

    result = await workouts.complete_workout(session, 1, 2, data)

    assert result is workout
    assert workout.status == StatusTypes.done
    assert workout.notification_sent is True
    assert link.status == StatusTypes.done
    assert link.sets == 5
    assert link.completed_at is not None
    session.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_complete_workout_rejects_missing_workout_and_link(
    monkeypatch,
) -> None:
    session = SimpleNamespace(
        execute=AsyncMock(return_value=ScalarResult([])),
        rollback=AsyncMock(),
    )
    monkeypatch.setattr(
        workouts.WorkoutRepository,
        "get_workout_by_id",
        AsyncMock(return_value=None),
    )
    with pytest.raises(ValueError, match="Тренировка не найдена"):
        await workouts.complete_workout(session, 1, 2, SWorkoutComplete())

    monkeypatch.setattr(
        workouts.WorkoutRepository,
        "get_workout_by_id",
        AsyncMock(return_value=SimpleNamespace(id=1)),
    )
    with pytest.raises(ValueError, match="Упражнение"):
        await workouts.complete_workout(
            session,
            1,
            2,
            SWorkoutComplete.model_validate(
                {"exercises": [{"exercise_id": 999}]}
            ),
        )


@pytest.mark.asyncio
async def test_starter_plan_builds_four_workouts(monkeypatch) -> None:
    existing_exercises = [
        SimpleNamespace(id=index, name=item["name"])
        for index, item in enumerate(workouts.STARTER_EXERCISES, start=1)
    ]
    session = SimpleNamespace(
        execute=AsyncMock(
            side_effect=[
                ScalarResult(existing_exercises),
                ScalarResult([]),
            ]
        ),
        add=Mock(),
        flush=AsyncMock(),
        commit=AsyncMock(),
        refresh=AsyncMock(),
        rollback=AsyncMock(),
    )

    result = await workouts.create_starter_plan(session, user_id=2)

    assert len(result) == 4
    assert session.add.call_count == 13
    session.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_workout_exercise_service_crud_and_ownership(monkeypatch) -> None:
    model = SimpleNamespace(workout_id=1, exercise_id=2)
    session = SimpleNamespace(rollback=AsyncMock())
    monkeypatch.setattr(
        links.WorkoutExerciseRepository,
        "check_workout_owner",
        AsyncMock(return_value=True),
    )
    for method_name in (
        "create_workout_exercise",
        "get_workout_exercise_by_ids",
        "update_workout_exercise",
        "delete_workout_exercise",
    ):
        monkeypatch.setattr(
            links.WorkoutExerciseRepository,
            method_name,
            AsyncMock(return_value=model),
        )
    monkeypatch.setattr(
        links.WorkoutExerciseRepository,
        "get_workout_exercises",
        AsyncMock(return_value=[model]),
    )
    monkeypatch.setattr(
        links.WorkoutExerciseRepository,
        "get_workout_exercises_by_status",
        AsyncMock(return_value=[model]),
    )
    create = SWorkoutExerciseCreate(
        workout_id=1,
        exercise_id=2,
        order_index=0,
        sets=3,
        reps=10,
        scheduled_at=future_datetime(),
    )

    assert await links.create_workout_exercise(session, 3, create) is model
    assert await links.get_workout_exercises(session, 3) == [model]
    assert (
        await links.get_workout_exercises_by_status(
            session,
            3,
            StatusTypes.planned,
        )
        == [model]
    )
    assert await links.get_workout_exercise_by_ids(session, 3, 1, 2) is model
    assert (
        await links.update_workout_exercise(
            session,
            3,
            1,
            2,
            SWorkoutExerciseUpdate(sets=4),
        )
        is model
    )
    assert await links.delete_workout_exercise(session, 1, 2, 3) is model


@pytest.mark.asyncio
async def test_workout_exercise_service_rejects_non_owner_empty_and_missing(
    monkeypatch,
) -> None:
    session = SimpleNamespace(rollback=AsyncMock())
    monkeypatch.setattr(
        links.WorkoutExerciseRepository,
        "check_workout_owner",
        AsyncMock(return_value=False),
    )
    data = SWorkoutExerciseCreate(
        workout_id=1,
        exercise_id=2,
        order_index=0,
        sets=3,
        reps=10,
        scheduled_at=future_datetime(),
    )
    with pytest.raises(ValueError, match="не принадлежит"):
        await links.create_workout_exercise(session, 3, data)

    with pytest.raises(ValueError, match="Нет данных"):
        await links.update_workout_exercise(
            session,
            3,
            1,
            2,
            SWorkoutExerciseUpdate(),
        )

    monkeypatch.setattr(
        links.WorkoutExerciseRepository,
        "get_workout_exercise_by_ids",
        AsyncMock(return_value=None),
    )
    with pytest.raises(ValueError, match="не найдено"):
        await links.get_workout_exercise_by_ids(session, 3, 1, 2)
