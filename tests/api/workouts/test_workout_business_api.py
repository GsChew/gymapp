import allure
import pytest

from src.models.workout import StatusTypes, WorkoutExercise
from tests.factories.workout_factory import WorkoutExerciseFactory, WorkoutFactory
from tests.helpers.assertions import assert_error


pytestmark = [pytest.mark.api]


@allure.feature("Workouts")
@allure.story("Starter plan")
@pytest.mark.positive
@pytest.mark.asyncio
async def test_starter_plan_is_idempotent_per_user(user_account) -> None:
    first = await user_account.clients.workouts.create_starter_plan()
    second = await user_account.clients.workouts.create_starter_plan()
    listing = await user_account.clients.workouts.list_workouts()
    links = await user_account.clients.workout_exercises.list_links()

    assert first.status_code == 200, first.text
    assert len(first.json()) == 4
    assert second.status_code == 200
    assert second.json() == []
    assert len(listing.json()) == 4
    assert len(links.json()) == 9
    assert all(item["status"] == StatusTypes.planned.value for item in links.json())


@allure.feature("Workouts")
@allure.story("Completion")
@allure.severity(allure.severity_level.CRITICAL)
@pytest.mark.positive
@pytest.mark.asyncio
async def test_complete_workout_saves_results_and_updates_all_links(
    user_account,
    make_exercise,
    db_session,
) -> None:
    workout_response = await user_account.clients.workouts.create_workout(
        WorkoutFactory.build()
    )
    exercise = await make_exercise()
    workout_id = workout_response.json()["id"]
    link_response = await user_account.clients.workout_exercises.create_link(
        WorkoutExerciseFactory.build(
            workout_id=workout_id,
            exercise_id=exercise.id,
        )
    )
    assert link_response.status_code == 200

    completed = await user_account.clients.workouts.complete_workout(
        workout_id,
        {
            "completed_at": "2030-01-05T18:00:00Z",
            "exercises": [
                {
                    "exercise_id": exercise.id,
                    "sets": 5,
                    "reps": 5,
                    "weight": 80,
                    "notes": "Personal best",
                }
            ],
            "wellness_energy": 5,
            "wellness_sleep": 1,
            "wellness_soreness": 3,
            "completion_notes": "Completed safely",
        },
    )

    assert completed.status_code == 200, completed.text
    assert completed.json()["status"] == StatusTypes.done.value
    assert completed.json()["notification_sent"] is True
    assert completed.json()["wellness_energy"] == 5
    link = await db_session.get(
        WorkoutExercise,
        (exercise.id, workout_id),
    )
    assert link is not None
    await db_session.refresh(link)
    assert link.status == StatusTypes.done
    assert link.sets == 5
    assert link.reps == 5
    assert link.weight == 80
    assert link.completed_at is not None


@pytest.mark.negative
@pytest.mark.asyncio
async def test_complete_workout_rejects_unknown_link_and_invalid_wellness(
    user_account,
) -> None:
    created = await user_account.clients.workouts.create_workout(
        WorkoutFactory.build()
    )
    workout_id = created.json()["id"]

    missing_link = await user_account.clients.workouts.complete_workout(
        workout_id,
        {"exercises": [{"exercise_id": 999_999, "sets": 3}]},
    )
    invalid_wellness = await user_account.clients.workouts.complete_workout(
        workout_id,
        {"wellness_energy": 6},
    )
    missing_workout = await user_account.clients.workouts.complete_workout(
        999_999,
        {},
    )

    assert_error(missing_link, 404, detail_contains="Упражнение")
    assert_error(invalid_wellness, 422)
    assert_error(missing_workout, 404)
