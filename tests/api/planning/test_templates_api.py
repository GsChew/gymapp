import allure
import pytest
from sqlalchemy import func, select

from src.models.workout import WorkoutExercise, WorkoutModel, WorkoutTemplate
from tests.factories.template_factory import TemplateFactory
from tests.helpers.assertions import assert_error
from tests.helpers.dates import future_datetime, to_api_datetime


pytestmark = [pytest.mark.api]


@allure.feature("Workout templates")
@allure.story("Schedule from template")
@pytest.mark.positive
@pytest.mark.asyncio
async def test_template_copies_exercises_into_new_workout(
    user_account,
    make_exercise,
    db_session,
) -> None:
    exercise = await make_exercise()
    payload = TemplateFactory.build(exercise_id=exercise.id)

    created = await user_account.clients.templates.create_template(payload)
    assert created.status_code == 200, created.text
    template_id = created.json()["id"]

    scheduled = await user_account.clients.templates.create_workout(
        template_id,
        {"planned_at": to_api_datetime(future_datetime(days=3))},
    )
    assert scheduled.status_code == 200, scheduled.text
    workout_id = scheduled.json()["id"]
    assert scheduled.json()["title"] == payload["title"]
    link = await db_session.get(WorkoutExercise, (exercise.id, workout_id))
    assert link is not None
    assert link.sets == payload["exercises"][0]["sets"]
    assert link.scheduled_at == (
        await db_session.get(WorkoutModel, workout_id)
    ).planned_at

    listing = await user_account.clients.templates.list_templates()
    assert [item["id"] for item in listing.json()] == [template_id]

    deleted = await user_account.clients.templates.delete_template(template_id)
    assert deleted.status_code == 200
    assert await db_session.get(WorkoutTemplate, template_id) is None
    assert await db_session.get(WorkoutModel, workout_id) is not None


@pytest.mark.security
@pytest.mark.negative
@pytest.mark.asyncio
async def test_template_isolation_and_missing_resource(
    user_account,
    make_user,
    make_exercise,
) -> None:
    stranger = await make_user()
    exercise = await make_exercise()
    created = await user_account.clients.templates.create_template(
        TemplateFactory.build(exercise_id=exercise.id)
    )
    template_id = created.json()["id"]

    foreign_schedule = await stranger.clients.templates.create_workout(
        template_id,
        {"planned_at": to_api_datetime(future_datetime())},
    )
    foreign_delete = await stranger.clients.templates.delete_template(template_id)
    stranger_listing = await stranger.clients.templates.list_templates()
    missing = await user_account.clients.templates.create_workout(
        999_999,
        {"planned_at": to_api_datetime(future_datetime())},
    )

    assert_error(foreign_schedule, 404)
    assert_error(foreign_delete, 404)
    assert stranger_listing.json() == []
    assert_error(missing, 404)


@pytest.mark.negative
@pytest.mark.asyncio
async def test_template_validation_and_duplicate_link_roll_back(
    user_account,
    make_exercise,
    db_session,
) -> None:
    exercise = await make_exercise()
    exercise_id = exercise.id
    invalid_title = await user_account.clients.templates.create_template(
        TemplateFactory.build(title="")
    )
    invalid_fk = await user_account.clients.templates.create_template(
        TemplateFactory.build(exercise_id=999_999)
    )
    duplicate = await user_account.clients.templates.create_template(
        TemplateFactory.build(
            exercises=[
                {
                    "exercise_id": exercise_id,
                    "order_index": 0,
                    "sets": 1,
                    "reps": 1,
                },
                {
                    "exercise_id": exercise_id,
                    "order_index": 1,
                    "sets": 1,
                    "reps": 1,
                },
            ]
        )
    )

    assert_error(invalid_title, 422)
    assert_error(invalid_fk, 400)
    assert_error(duplicate, 400)
    template_count = await db_session.scalar(
        select(func.count()).select_from(WorkoutTemplate)
    )
    assert template_count == 0
