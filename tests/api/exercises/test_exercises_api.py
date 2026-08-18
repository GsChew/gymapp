import allure
import pytest

from src.models.workout import ExerciseModel, MuscleTypes, TrainTypes
from tests.factories.exercise_factory import ExerciseFactory
from tests.helpers.assertions import assert_error


pytestmark = [pytest.mark.api]


@allure.feature("Exercises")
@allure.story("Role-protected CRUD")
@pytest.mark.positive
@pytest.mark.asyncio
async def test_trainer_creates_and_updates_exercise_admin_deletes_it(
    trainer_account,
    admin_account,
    db_session,
) -> None:
    payload = ExerciseFactory.build(
        video_url="https://example.test/video",
        muscle_image_url="/static/assets/exercise-strength.png",
    )

    created = await trainer_account.clients.exercises.create_exercise(payload)
    assert created.status_code == 200, created.text
    exercise_id = created.json()["id"]
    assert created.json()["name"] == payload["name"]
    assert created.json()["train"] == TrainTypes.strength_train.value

    detail = await trainer_account.clients.exercises.get_exercise(exercise_id)
    updated = await trainer_account.clients.exercises.update_exercise(
        exercise_id,
        {
            "description": "Updated description",
            "train": TrainTypes.cardio.value,
            "muscle": None,
        },
    )
    assert detail.status_code == 200
    assert updated.status_code == 200, updated.text
    assert updated.json()["description"] == "Updated description"
    assert updated.json()["train"] == TrainTypes.cardio.value
    assert updated.json()["muscle"] is None

    deleted = await admin_account.clients.exercises.delete_exercise(exercise_id)
    missing = await admin_account.clients.exercises.get_exercise(exercise_id)
    assert deleted.status_code == 200
    assert_error(missing, 404)
    assert await db_session.get(ExerciseModel, exercise_id) is None


@pytest.mark.security
@pytest.mark.negative
@pytest.mark.asyncio
async def test_exercise_write_permissions_are_enforced(
    user_account,
    trainer_account,
    make_exercise,
) -> None:
    exercise = await make_exercise()
    create = await user_account.clients.exercises.create_exercise(
        ExerciseFactory.build()
    )
    update = await user_account.clients.exercises.update_exercise(
        exercise.id,
        {"name": "Unauthorized"},
    )
    trainer_delete = await trainer_account.clients.exercises.delete_exercise(
        exercise.id
    )

    assert_error(create, 403)
    assert_error(update, 403)
    assert_error(trainer_delete, 403)


@pytest.mark.positive
@pytest.mark.asyncio
async def test_exercise_list_filters_and_paginates(
    user_account,
    make_exercise,
) -> None:
    strength = await make_exercise(
        name="Strength",
        train=TrainTypes.strength_train.value,
        muscle=MuscleTypes.quadriceps.value,
    )
    await make_exercise(
        name="Cardio",
        train=TrainTypes.cardio.value,
        muscle=None,
    )
    await make_exercise(
        name="Stretch",
        train=TrainTypes.stretching.value,
        muscle=MuscleTypes.hamstrings.value,
    )

    by_train = await user_account.clients.exercises.list_exercises(
        train_type=TrainTypes.strength_train.value
    )
    by_muscle = await user_account.clients.exercises.list_exercises(
        muscle=MuscleTypes.quadriceps.value
    )
    first_page = await user_account.clients.exercises.list_exercises(
        limit=1,
        offset=0,
    )
    second_page = await user_account.clients.exercises.list_exercises(
        limit=1,
        offset=1,
    )

    assert [item["id"] for item in by_train.json()] == [strength.id]
    assert [item["id"] for item in by_muscle.json()] == [strength.id]
    assert len(first_page.json()) == len(second_page.json()) == 1
    assert first_page.json()[0]["id"] != second_page.json()[0]["id"]


@pytest.mark.parametrize(
    "payload",
    [
        {},
        {"name": "", "train": "силовая_тренировка"},
        {"name": None, "train": "силовая_тренировка"},
        {"name": "x" * 256, "train": "силовая_тренировка"},
        {"name": "Valid", "train": "unknown"},
        {"name": "Valid", "train": 42},
        {
            "name": "Valid",
            "train": "силовая_тренировка",
            "description": "x" * 1001,
        },
    ],
)
@pytest.mark.negative
@pytest.mark.asyncio
async def test_exercise_create_validation(trainer_account, payload: dict) -> None:
    response = await trainer_account.clients.exercises.create_exercise(payload)

    assert_error(response, 422)


@pytest.mark.negative
@pytest.mark.asyncio
async def test_exercise_update_delete_and_query_edge_cases(
    trainer_account,
    admin_account,
    make_exercise,
) -> None:
    exercise = await make_exercise()

    empty_update = await trainer_account.clients.exercises.update_exercise(
        exercise.id,
        {},
    )
    missing_update = await trainer_account.clients.exercises.update_exercise(
        999_999,
        {"name": "Missing"},
    )
    invalid_id = await trainer_account.clients.exercises.get_exercise("uuid-like")
    invalid_limit = await trainer_account.clients.exercises.list_exercises(limit=0)
    first_delete = await admin_account.clients.exercises.delete_exercise(exercise.id)
    second_delete = await admin_account.clients.exercises.delete_exercise(exercise.id)

    assert_error(empty_update, 400, detail_contains="Нет данных")
    assert_error(missing_update, 404)
    assert_error(invalid_id, 422)
    assert_error(invalid_limit, 422)
    assert first_delete.status_code == 200
    assert_error(second_delete, 404)


@pytest.mark.positive
@pytest.mark.asyncio
async def test_duplicate_exercise_names_are_allowed_by_current_model(
    trainer_account,
) -> None:
    payload = ExerciseFactory.build(name="Duplicate allowed")

    first = await trainer_account.clients.exercises.create_exercise(payload)
    second = await trainer_account.clients.exercises.create_exercise(payload)

    assert first.status_code == 200
    assert second.status_code == 200
    assert first.json()["id"] != second.json()["id"]
