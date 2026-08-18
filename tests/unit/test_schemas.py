from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from src.schemas.user import SUserCreate, SUserLogin
from src.schemas.workout import (
    SExerciseCreate,
    SUserGoalCreate,
    SWorkoutCreate,
    SWorkoutExerciseCreate,
    SWorkoutUpdate,
)


pytestmark = [pytest.mark.unit]


@pytest.mark.parametrize("password", ["", "short", "1234567"])
def test_registration_rejects_short_password(password: str) -> None:
    with pytest.raises(ValidationError):
        SUserCreate(username="valid_user", email="user@example.com", password=password)


@pytest.mark.parametrize("username", ["", "ab"])
def test_registration_rejects_short_username(username: str) -> None:
    with pytest.raises(ValidationError):
        SUserCreate(username=username, email="user@example.com", password="12345678")


def test_login_allows_one_character_password_for_safe_auth_failure() -> None:
    schema = SUserLogin(username="known_user", password="x")

    assert schema.password == "x"


@pytest.mark.parametrize(
    "schema_class,payload",
    [
        (
            SWorkoutCreate,
            {"title": "", "planned_at": datetime.now(UTC)},
        ),
        (
            SExerciseCreate,
            {"name": "Exercise", "train": "unknown"},
        ),
        (
            SUserGoalCreate,
            {"title": "Goal", "metric": "kg", "target_value": 0},
        ),
        (
            SWorkoutExerciseCreate,
            {
                "workout_id": 1,
                "exercise_id": 1,
                "order_index": -1,
                "sets": 0,
                "reps": -1,
                "scheduled_at": datetime.now(UTC),
            },
        ),
    ],
)
def test_domain_schemas_reject_invalid_boundaries(
    schema_class,
    payload: dict,
) -> None:
    with pytest.raises(ValidationError):
        schema_class.model_validate(payload)


@pytest.mark.parametrize(
    "field,value",
    [
        ("wellness_energy", 0),
        ("wellness_sleep", 6),
        ("wellness_soreness", -1),
        ("completion_notes", "x" * 1001),
    ],
)
def test_workout_update_rejects_wellness_and_text_boundaries(
    field: str,
    value,
) -> None:
    with pytest.raises(ValidationError):
        SWorkoutUpdate.model_validate({field: value})
