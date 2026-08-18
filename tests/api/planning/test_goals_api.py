import allure
import pytest

from src.models.workout import GoalStatus, UserGoal
from tests.factories.goal_factory import GoalFactory
from tests.helpers.assertions import assert_error


pytestmark = [pytest.mark.api]


@allure.feature("Goals")
@allure.story("Goal CRUD")
@pytest.mark.positive
@pytest.mark.asyncio
async def test_user_crud_goal_persists_expected_state(
    user_account,
    db_session,
) -> None:
    payload = GoalFactory.build(target_value=0.1, current_value=0)

    created = await user_account.clients.goals.create_goal(payload)
    assert created.status_code == 200, created.text
    goal_id = created.json()["id"]
    assert created.json()["status"] == GoalStatus.active.value

    updated = await user_account.clients.goals.update_goal(
        goal_id,
        {"current_value": 0.1, "status": GoalStatus.done.value},
    )
    listing = await user_account.clients.goals.list_goals()
    assert updated.status_code == 200
    assert updated.json()["status"] == GoalStatus.done.value
    assert [item["id"] for item in listing.json()] == [goal_id]
    persisted = await db_session.get(UserGoal, goal_id)
    assert persisted is not None
    await db_session.refresh(persisted)
    assert persisted.current_value == 0.1

    deleted = await user_account.clients.goals.delete_goal(goal_id)
    assert deleted.status_code == 200
    assert await db_session.get(UserGoal, goal_id) is None


@pytest.mark.security
@pytest.mark.negative
@pytest.mark.asyncio
async def test_goal_ownership_empty_update_and_missing_resource(
    user_account,
    make_user,
) -> None:
    stranger = await make_user()
    created = await user_account.clients.goals.create_goal(GoalFactory.build())
    goal_id = created.json()["id"]

    empty = await user_account.clients.goals.update_goal(goal_id, {})
    foreign_update = await stranger.clients.goals.update_goal(
        goal_id,
        {"current_value": 50},
    )
    foreign_delete = await stranger.clients.goals.delete_goal(goal_id)
    missing = await user_account.clients.goals.update_goal(
        999_999,
        {"current_value": 1},
    )

    assert_error(empty, 400, detail_contains="Нет данных")
    assert_error(foreign_update, 404)
    assert_error(foreign_delete, 404)
    assert_error(missing, 404)


@pytest.mark.parametrize(
    "payload",
    [
        {},
        {"title": "", "metric": "kg", "target_value": 1},
        {"title": "Goal", "metric": "", "target_value": 1},
        {"title": "Goal", "metric": "kg", "target_value": 0},
        {"title": "Goal", "metric": "kg", "target_value": -1},
        {"title": "Goal", "metric": "kg", "target_value": "many"},
        {
            "title": "Goal",
            "metric": "kg",
            "target_value": 1,
            "current_value": -1,
        },
    ],
)
@pytest.mark.negative
@pytest.mark.asyncio
async def test_goal_validation_boundaries(user_account, payload: dict) -> None:
    response = await user_account.clients.goals.create_goal(payload)

    assert_error(response, 422)
