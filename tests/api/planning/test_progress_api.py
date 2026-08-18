from datetime import timedelta

import allure
import pytest

from src.models.workout import StatusTypes
from tests.helpers.assertions import assert_error
from tests.helpers.dates import to_api_datetime, utc_now


pytestmark = [pytest.mark.api]


@allure.feature("Progress")
@allure.story("Completed workout analytics")
@pytest.mark.positive
@pytest.mark.asyncio
async def test_progress_summary_volume_record_and_history(
    user_account,
    make_workout,
    make_exercise,
    make_workout_exercise,
) -> None:
    exercise = await make_exercise(name="QA deadlift")
    first_workout = await make_workout(user_id=user_account.user.id, title="First")
    second_workout = await make_workout(user_id=user_account.user.id, title="Second")
    await make_workout_exercise(
        workout_id=first_workout.id,
        exercise_id=exercise.id,
    )
    await user_account.clients.workouts.complete_workout(
        first_workout.id,
        {
            "completed_at": to_api_datetime(utc_now() - timedelta(days=1)),
            "exercises": [
                {"exercise_id": exercise.id, "sets": 3, "reps": 5, "weight": 100}
            ],
        },
    )
    await make_workout_exercise(
        workout_id=second_workout.id,
        exercise_id=exercise.id,
    )
    await user_account.clients.workouts.complete_workout(
        second_workout.id,
        {
            "completed_at": to_api_datetime(utc_now()),
            "exercises": [
                {"exercise_id": exercise.id, "sets": 4, "reps": 3, "weight": 120}
            ],
        },
    )

    summary = await user_account.clients.progress.summary()
    weekly = await user_account.clients.progress.weekly_volume()
    record = await user_account.clients.progress.exercise_record(exercise.id)
    history = await user_account.clients.progress.exercise_history(exercise.id)

    assert summary.status_code == 200
    assert summary.json()["completed_workouts"] == 2
    assert summary.json()["planned_workouts"] == 0
    assert summary.json()["total_volume"] == (3 * 5 * 100) + (4 * 3 * 120)
    assert summary.json()["best_exercise_name"] == "QA deadlift"
    assert weekly.status_code == 200
    assert sum(item["completed_workouts"] for item in weekly.json()) == 2
    assert record.json()["max_weight"] == 120
    assert record.json()["max_volume"] == 1500
    assert [item["workout_id"] for item in history.json()] == [
        second_workout.id,
        first_workout.id,
    ]


@pytest.mark.security
@pytest.mark.negative
@pytest.mark.asyncio
async def test_empty_and_foreign_progress_are_isolated(
    user_account,
    make_user,
    make_workout,
    make_exercise,
    make_workout_exercise,
) -> None:
    stranger = await make_user()
    exercise = await make_exercise()
    workout = await make_workout(user_id=user_account.user.id)
    await make_workout_exercise(
        workout_id=workout.id,
        exercise_id=exercise.id,
        status=StatusTypes.done,
        completed_at=utc_now(),
        weight=50,
    )

    summary = await stranger.clients.progress.summary()
    weekly = await stranger.clients.progress.weekly_volume()
    record = await stranger.clients.progress.exercise_record(exercise.id)
    history = await stranger.clients.progress.exercise_history(exercise.id)

    assert summary.status_code == 200
    assert summary.json()["completed_workouts"] == 0
    assert summary.json()["total_volume"] == 0
    assert weekly.json() == []
    assert_error(record, 404)
    assert history.status_code == 200
    assert history.json() == []
