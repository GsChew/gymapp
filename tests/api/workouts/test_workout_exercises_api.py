import allure
import pytest
from sqlalchemy import func, select

from src.models.workout import StatusTypes, WorkoutExercise
from tests.factories.workout_factory import WorkoutExerciseFactory, WorkoutFactory
from tests.helpers.assertions import assert_error


pytestmark = [pytest.mark.api]


@allure.feature("Workout composition")
@allure.story("Workout exercise CRUD")
@pytest.mark.positive
@pytest.mark.asyncio
async def test_owner_can_create_read_update_filter_and_delete_link(
    user_account,
    make_exercise,
    db_session,
) -> None:
    workout = await user_account.clients.workouts.create_workout(
        WorkoutFactory.build()
    )
    exercise = await make_exercise()
    workout_id = workout.json()["id"]
    payload = WorkoutExerciseFactory.build(
        workout_id=workout_id,
        exercise_id=exercise.id,
    )

    created = await user_account.clients.workout_exercises.create_link(payload)
    assert created.status_code == 200, created.text
    assert created.json()["sets"] == 3

    detail = await user_account.clients.workout_exercises.get_link(
        workout_id,
        exercise.id,
    )
    listing = await user_account.clients.workout_exercises.list_links()
    filtered = await user_account.clients.workout_exercises.list_by_status(
        StatusTypes.planned.value
    )
    assert detail.status_code == 200
    assert [item["exercise_id"] for item in listing.json()] == [exercise.id]
    assert [item["exercise_id"] for item in filtered.json()] == [exercise.id]

    updated = await user_account.clients.workout_exercises.update_link(
        workout_id,
        exercise.id,
        {
            "sets": 5,
            "reps": 6,
            "weight": 75,
            "status": StatusTypes.done.value,
            "notes": "Controlled reps",
        },
    )
    assert updated.status_code == 200, updated.text
    assert updated.json()["sets"] == 5
    assert updated.json()["status"] == StatusTypes.done.value
    link = await db_session.get(WorkoutExercise, (exercise.id, workout_id))
    assert link is not None
    await db_session.refresh(link)
    assert link.weight == 75

    deleted = await user_account.clients.workout_exercises.delete_link(
        workout_id,
        exercise.id,
    )
    missing = await user_account.clients.workout_exercises.get_link(
        workout_id,
        exercise.id,
    )
    assert deleted.status_code == 200
    assert_error(missing, 404)
    assert await db_session.get(WorkoutExercise, (exercise.id, workout_id)) is None


@pytest.mark.security
@pytest.mark.negative
@pytest.mark.asyncio
async def test_link_operations_do_not_cross_user_boundary(
    user_account,
    make_user,
    make_exercise,
) -> None:
    stranger = await make_user()
    workout = await user_account.clients.workouts.create_workout(
        WorkoutFactory.build()
    )
    exercise = await make_exercise()
    workout_id = workout.json()["id"]

    foreign_create = await stranger.clients.workout_exercises.create_link(
        WorkoutExerciseFactory.build(
            workout_id=workout_id,
            exercise_id=exercise.id,
        )
    )
    owner_create = await user_account.clients.workout_exercises.create_link(
        WorkoutExerciseFactory.build(
            workout_id=workout_id,
            exercise_id=exercise.id,
        )
    )
    foreign_read = await stranger.clients.workout_exercises.get_link(
        workout_id,
        exercise.id,
    )
    foreign_update = await stranger.clients.workout_exercises.update_link(
        workout_id,
        exercise.id,
        {"sets": 100},
    )
    foreign_delete = await stranger.clients.workout_exercises.delete_link(
        workout_id,
        exercise.id,
    )

    assert_error(foreign_create, 404)
    assert owner_create.status_code == 200
    for response in (foreign_read, foreign_update, foreign_delete):
        assert_error(response, 404)


@pytest.mark.negative
@pytest.mark.asyncio
async def test_duplicate_and_invalid_foreign_key_leave_single_valid_link(
    user_account,
    make_exercise,
    db_session,
) -> None:
    workout = await user_account.clients.workouts.create_workout(
        WorkoutFactory.build()
    )
    exercise = await make_exercise()
    workout_id = workout.json()["id"]
    payload = WorkoutExerciseFactory.build(
        workout_id=workout_id,
        exercise_id=exercise.id,
    )

    first = await user_account.clients.workout_exercises.create_link(payload)
    duplicate = await user_account.clients.workout_exercises.create_link(payload)
    invalid_fk = await user_account.clients.workout_exercises.create_link(
        WorkoutExerciseFactory.build(
            workout_id=workout_id,
            exercise_id=999_999,
        )
    )

    assert first.status_code == 200
    assert_error(duplicate, 400)
    assert_error(invalid_fk, 400)
    count = await db_session.scalar(
        select(func.count()).select_from(WorkoutExercise)
    )
    assert count == 1


@pytest.mark.parametrize(
    "changes",
    [
        {"order_index": -1},
        {"sets": 0},
        {"reps": -1},
        {"weight": -0.01},
        {"status": "invalid"},
        {"scheduled_at": "not-a-date"},
        {"notes": "x" * 1001},
    ],
)
@pytest.mark.negative
@pytest.mark.asyncio
async def test_workout_exercise_rejects_invalid_boundaries(
    user_account,
    make_exercise,
    changes: dict,
) -> None:
    workout = await user_account.clients.workouts.create_workout(
        WorkoutFactory.build()
    )
    exercise = await make_exercise()
    payload = WorkoutExerciseFactory.build(
        workout_id=workout.json()["id"],
        exercise_id=exercise.id,
        **changes,
    )

    response = await user_account.clients.workout_exercises.create_link(payload)

    assert_error(response, 422)
