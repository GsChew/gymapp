import allure
import pytest

from src.models.workout import StatusTypes, WorkoutModel
from tests.factories.workout_factory import WorkoutFactory
from tests.helpers.assertions import assert_error
from tests.helpers.dates import past_datetime, to_api_datetime


pytestmark = [pytest.mark.api]


@allure.feature("Workouts")
@allure.story("CRUD")
@allure.title("Workout owner can create, read, update, and delete a workout")
@allure.severity(allure.severity_level.CRITICAL)
@pytest.mark.positive
@pytest.mark.asyncio
async def test_workout_crud_updates_postgresql_state(
    user_account,
    db_session,
) -> None:
    payload = WorkoutFactory.build(
        remind_at=to_api_datetime(past_datetime(days=-5)),
    )

    with allure.step("Create a planned workout"):
        created = await user_account.clients.workouts.create_workout(payload)
    assert created.status_code == 200, created.text
    workout_id = created.json()["id"]
    assert created.json()["user_id"] == user_account.user.id
    assert created.json()["title"] == payload["title"]
    assert created.json()["status"] == StatusTypes.planned.value

    persisted = await db_session.get(WorkoutModel, workout_id)
    assert persisted is not None
    assert persisted.title == payload["title"]

    detail = await user_account.clients.workouts.get_workout(workout_id)
    by_name = await user_account.clients.workouts.get_by_name(payload["title"])
    assert detail.status_code == 200
    assert by_name.status_code == 200
    assert detail.json()["id"] == by_name.json()["id"] == workout_id

    with allure.step("Partially update one field"):
        updated = await user_account.clients.workouts.update_workout(
            workout_id,
            {"title": "Updated workout", "wellness_energy": 5},
        )
    assert updated.status_code == 200, updated.text
    assert updated.json()["title"] == "Updated workout"
    assert updated.json()["wellness_energy"] == 5
    await db_session.refresh(persisted)
    assert persisted.title == "Updated workout"

    with allure.step("Delete and verify absence"):
        deleted = await user_account.clients.workouts.delete_workout(workout_id)
        missing = await user_account.clients.workouts.get_workout(workout_id)
    assert deleted.status_code == 200
    assert_error(missing, 404, detail_contains="не найдена")
    assert await db_session.get(WorkoutModel, workout_id) is None


@pytest.mark.positive
@pytest.mark.asyncio
async def test_workout_list_supports_status_filter_and_pagination(
    user_account,
) -> None:
    clients = user_account.clients.workouts
    payloads = [
        WorkoutFactory.build(title="A", status=StatusTypes.planned.value),
        WorkoutFactory.build(title="B", status=StatusTypes.done.value),
        WorkoutFactory.build(title="C", status=StatusTypes.planned.value),
    ]
    for payload in payloads:
        response = await clients.create_workout(payload)
        assert response.status_code == 200

    planned = await clients.list_workouts(status=StatusTypes.planned.value)
    page_one = await clients.list_workouts(limit=1, offset=0)
    page_two = await clients.list_workouts(limit=1, offset=1)
    empty = await clients.list_workouts(offset=100)

    assert planned.status_code == 200
    assert {item["title"] for item in planned.json()} == {"A", "C"}
    assert len(page_one.json()) == 1
    assert len(page_two.json()) == 1
    assert page_one.json()[0]["id"] != page_two.json()[0]["id"]
    assert empty.json() == []


@pytest.mark.security
@pytest.mark.negative
@pytest.mark.asyncio
async def test_workout_data_is_isolated_between_users(
    user_account,
    make_user,
) -> None:
    stranger = await make_user()
    created = await user_account.clients.workouts.create_workout(
        WorkoutFactory.build()
    )
    workout_id = created.json()["id"]

    detail = await stranger.clients.workouts.get_workout(workout_id)
    update = await stranger.clients.workouts.update_workout(
        workout_id,
        {"title": "Stolen"},
    )
    delete = await stranger.clients.workouts.delete_workout(workout_id)
    listing = await stranger.clients.workouts.list_workouts()
    owner_detail = await user_account.clients.workouts.get_workout(workout_id)

    for response in (detail, update, delete):
        assert_error(response, 404)
    assert listing.json() == []
    assert owner_detail.status_code == 200
    assert owner_detail.json()["title"] != "Stolen"


@pytest.mark.parametrize(
    ("payload", "status_code"),
    [
        ({}, 422),
        ({"title": "", "planned_at": "2030-01-01T00:00:00Z"}, 422),
        ({"title": "Valid", "planned_at": None}, 422),
        ({"title": "Valid", "planned_at": "not-a-date"}, 422),
        ({"title": "Valid", "planned_at": "2030-01-01T00:00:00Z", "status": "x"}, 422),
        ({"title": "x" * 256, "planned_at": "2030-01-01T00:00:00Z"}, 422),
    ],
)
@pytest.mark.negative
@pytest.mark.asyncio
async def test_create_workout_rejects_invalid_payloads(
    user_account,
    payload: dict,
    status_code: int,
) -> None:
    response = await user_account.clients.workouts.create_workout(payload)

    assert_error(response, status_code)


@pytest.mark.negative
@pytest.mark.asyncio
async def test_workout_update_and_paths_validate_edge_cases(
    user_account,
) -> None:
    created = await user_account.clients.workouts.create_workout(
        WorkoutFactory.build()
    )
    workout_id = created.json()["id"]

    empty = await user_account.clients.workouts.update_workout(workout_id, {})
    invalid_type = await user_account.clients.workouts.update_workout(
        workout_id,
        {"wellness_sleep": "high"},
    )
    invalid_id = await user_account.clients.workouts.get_workout("not-an-int")
    missing = await user_account.clients.workouts.update_workout(
        999_999,
        {"title": "Missing"},
    )
    repeated_delete = await user_account.clients.workouts.delete_workout(workout_id)
    second_delete = await user_account.clients.workouts.delete_workout(workout_id)

    assert_error(empty, 400, detail_contains="Нет данных")
    assert_error(invalid_type, 422)
    assert_error(invalid_id, 422)
    assert_error(missing, 404)
    assert repeated_delete.status_code == 200
    assert_error(second_delete, 404)


@pytest.mark.positive
@pytest.mark.asyncio
async def test_past_planned_date_is_accepted_because_code_has_no_date_rule(
    user_account,
) -> None:
    payload = WorkoutFactory.build(planned_at=past_datetime(days=30))

    response = await user_account.clients.workouts.create_workout(payload)

    assert response.status_code == 200, response.text
    assert response.json()["planned_at"].startswith(
        past_datetime(days=30).date().isoformat()
    )


@pytest.mark.xfail(
    reason=(
        "DEFECT VALIDATION-001: title uses min_length only and accepts "
        "whitespace-only workout names"
    ),
    strict=True,
)
@pytest.mark.negative
@pytest.mark.asyncio
async def test_whitespace_only_workout_title_is_rejected(user_account) -> None:
    response = await user_account.clients.workouts.create_workout(
        WorkoutFactory.build(title="   ")
    )

    assert response.status_code == 422
