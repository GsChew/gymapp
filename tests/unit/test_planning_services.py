from datetime import UTC, datetime
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from sqlalchemy.exc import SQLAlchemyError

from src.models.workout import StatusTypes
from src.progress import service as progress
from src.schemas.workout import SWorkoutFromTemplate, SWorkoutTemplateCreate
from src.templates import service as templates


pytestmark = [pytest.mark.unit]


class ScalarResult:
    def __init__(self, values) -> None:
        self._values = values

    def scalars(self):
        return self

    def all(self):
        return self._values


@pytest.mark.asyncio
async def test_template_service_success_and_not_found(monkeypatch) -> None:
    template = SimpleNamespace(id=1)
    workout = SimpleNamespace(id=2)
    session = SimpleNamespace(rollback=AsyncMock())
    monkeypatch.setattr(
        templates.TemplateRepository,
        "get_templates",
        AsyncMock(return_value=[template]),
    )
    monkeypatch.setattr(
        templates.TemplateRepository,
        "create_template",
        AsyncMock(return_value=template),
    )
    monkeypatch.setattr(
        templates.TemplateRepository,
        "get_template",
        AsyncMock(return_value=template),
    )
    monkeypatch.setattr(
        templates.TemplateRepository,
        "create_workout_from_template",
        AsyncMock(return_value=workout),
    )
    monkeypatch.setattr(
        templates.TemplateRepository,
        "delete_template",
        AsyncMock(return_value=template),
    )

    assert await templates.get_templates(session, 3) == [template]
    assert (
        await templates.create_template(
            session,
            3,
            SWorkoutTemplateCreate(title="Template"),
        )
        is template
    )
    assert (
        await templates.create_workout_from_template(
            session,
            3,
            1,
            SWorkoutFromTemplate(planned_at=datetime.now(UTC)),
        )
        is workout
    )
    assert await templates.delete_template(session, 3, 1) is template

    monkeypatch.setattr(
        templates.TemplateRepository,
        "get_template",
        AsyncMock(return_value=None),
    )
    with pytest.raises(ValueError, match="не найден"):
        await templates.create_workout_from_template(
            session,
            3,
            999,
            SWorkoutFromTemplate(planned_at=datetime.now(UTC)),
        )

    monkeypatch.setattr(
        templates.TemplateRepository,
        "delete_template",
        AsyncMock(return_value=None),
    )
    with pytest.raises(ValueError, match="не найден"):
        await templates.delete_template(session, 3, 999)


@pytest.mark.asyncio
async def test_template_service_rolls_back_database_error(monkeypatch) -> None:
    session = SimpleNamespace(rollback=AsyncMock())
    monkeypatch.setattr(
        templates.TemplateRepository,
        "create_template",
        AsyncMock(side_effect=SQLAlchemyError("db")),
    )

    with pytest.raises(ValueError, match="Не удалось создать"):
        await templates.create_template(
            session,
            3,
            SWorkoutTemplateCreate(title="Template"),
        )

    session.rollback.assert_awaited_once()


@pytest.mark.asyncio
async def test_progress_services_calculate_summary_records_and_history(
    monkeypatch,
) -> None:
    now = datetime.now(UTC)
    workout = SimpleNamespace(
        id=1,
        title="Workout",
        planned_at=now,
        status=StatusTypes.done,
    )
    exercise = SimpleNamespace(id=2, name="Deadlift")
    link = SimpleNamespace(
        sets=3,
        reps=5,
        weight=100.0,
        completed_at=now,
        status=StatusTypes.done,
    )
    rows = [(link, workout, exercise)]
    monkeypatch.setattr(progress, "_completed_rows", AsyncMock(return_value=rows))
    session = SimpleNamespace(
        execute=AsyncMock(return_value=ScalarResult([])),
    )

    summary = await progress.get_progress_summary(session, 7)
    weekly = await progress.get_weekly_volume(session, 7)
    record = await progress.get_exercise_record(session, 7, exercise.id)
    history = await progress.get_exercise_history(session, 7, exercise.id)

    assert summary.completed_workouts == 1
    assert summary.total_volume == 1500
    assert summary.current_streak_weeks == 1
    assert weekly[0].volume == 1500
    assert record.max_weight == 100
    assert record.max_volume == 1500
    assert history[0].workout_id == workout.id


def test_progress_date_and_volume_helpers() -> None:
    naive = datetime(2026, 7, 23, 12)
    workout = SimpleNamespace(planned_at=naive)
    link = SimpleNamespace(
        sets=2,
        reps=10,
        weight=None,
        completed_at=None,
    )

    assert progress._volume(link) == 0
    assert progress._completed_at(link, workout) == naive
    assert progress._week_start(naive).isoformat() == "2026-07-20"


@pytest.mark.asyncio
async def test_progress_record_rejects_empty_history(monkeypatch) -> None:
    monkeypatch.setattr(progress, "_completed_rows", AsyncMock(return_value=[]))

    with pytest.raises(ValueError, match="не найдены"):
        await progress.get_exercise_record(object(), 7, 2)


@pytest.mark.asyncio
async def test_progress_wraps_database_error(monkeypatch) -> None:
    monkeypatch.setattr(
        progress,
        "_completed_rows",
        AsyncMock(side_effect=SQLAlchemyError("db")),
    )

    with pytest.raises(ValueError, match="Не удалось получить прогресс"):
        await progress.get_progress_summary(object(), 7)
