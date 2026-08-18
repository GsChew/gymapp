from datetime import UTC, datetime

import pytest

from tests.factories import (
    ExerciseFactory,
    GoalFactory,
    TemplateFactory,
    UserFactory,
    WorkoutExerciseFactory,
    WorkoutFactory,
)
from tests.helpers.dates import future_datetime, past_datetime
from tests.helpers.safe_logging import redact


pytestmark = [pytest.mark.unit]


def test_factories_generate_unique_valid_payloads() -> None:
    first_user = UserFactory.build()
    second_user = UserFactory.build()
    workout = WorkoutFactory.build()
    exercise = ExerciseFactory.build()
    goal = GoalFactory.build()
    template = TemplateFactory.build(exercise_id=17)
    link = WorkoutExerciseFactory.build(workout_id=3, exercise_id=17)

    assert first_user["username"] != second_user["username"]
    assert first_user["email"] != second_user["email"]
    assert len(first_user["password"]) >= 8
    assert workout["status"] == "запланировано"
    assert exercise["train"] == "силовая_тренировка"
    assert goal["target_value"] > 0
    assert template["exercises"][0]["exercise_id"] == 17
    assert link["workout_id"] == 3
    assert link["sets"] > 0


def test_factory_overrides_only_requested_values() -> None:
    payload = WorkoutFactory.build(title="Custom", status="пропущено")

    assert payload["title"] == "Custom"
    assert payload["status"] == "пропущено"
    assert "planned_at" in payload


def test_date_helpers_return_timezone_aware_values() -> None:
    now = datetime.now(UTC)

    assert future_datetime(days=1).tzinfo is not None
    assert future_datetime(days=1) > now
    assert past_datetime(days=1) < now


def test_redaction_recursively_masks_secrets() -> None:
    source = {
        "password": "plain",
        "nested": {
            "Authorization": "Bearer token",
            "items": [{"refresh_token": "token"}, {"safe": "visible"}],
        },
    }

    sanitized = redact(source)

    assert sanitized["password"] == "***"
    assert sanitized["nested"]["Authorization"] == "***"
    assert sanitized["nested"]["items"][0]["refresh_token"] == "***"
    assert sanitized["nested"]["items"][1]["safe"] == "visible"
