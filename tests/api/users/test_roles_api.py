import allure
import pytest

from src.models.user import UserRole
from tests.helpers.assertions import assert_error


pytestmark = [pytest.mark.api, pytest.mark.security]


@allure.feature("Role based access")
@allure.story("User administration")
@pytest.mark.positive
@pytest.mark.asyncio
async def test_trainer_and_admin_can_list_users_but_user_cannot(
    user_account,
    trainer_account,
    admin_account,
) -> None:
    forbidden = await user_account.clients.users.list_users()
    trainer_listing = await trainer_account.clients.users.list_users()
    admin_listing = await admin_account.clients.users.list_users()

    assert_error(forbidden, 403, detail_contains="Недостаточно прав")
    assert trainer_listing.status_code == 200
    assert admin_listing.status_code == 200
    expected_ids = {
        user_account.user.id,
        trainer_account.user.id,
        admin_account.user.id,
    }
    assert expected_ids <= {item["id"] for item in trainer_listing.json()}
    assert expected_ids <= {item["id"] for item in admin_listing.json()}


@allure.feature("Role based access")
@allure.story("Role management")
@pytest.mark.positive
@pytest.mark.asyncio
async def test_admin_promotes_user_and_new_permission_takes_effect(
    user_account,
    admin_account,
) -> None:
    promoted = await admin_account.clients.users.change_role(
        user_account.user.id,
        UserRole.trainer.value,
    )
    create_exercise = await user_account.clients.exercises.create_exercise(
        {"name": "Role propagation exercise", "train": "силовая_тренировка"}
    )

    assert promoted.status_code == 200, promoted.text
    assert promoted.json()["role"] == "trainer"
    assert create_exercise.status_code == 200, create_exercise.text


@pytest.mark.negative
@pytest.mark.asyncio
async def test_non_admin_cannot_change_role_and_input_is_validated(
    user_account,
    trainer_account,
    admin_account,
) -> None:
    user_attempt = await user_account.clients.users.change_role(
        trainer_account.user.id,
        "admin",
    )
    trainer_attempt = await trainer_account.clients.users.change_role(
        user_account.user.id,
        "trainer",
    )
    invalid_role = await admin_account.clients.users.change_role(
        user_account.user.id,
        "superadmin",
    )
    missing_user = await admin_account.clients.users.change_role(
        999_999,
        "trainer",
    )

    assert_error(user_attempt, 403)
    assert_error(trainer_attempt, 403)
    assert_error(invalid_role, 422)
    assert_error(missing_user, 404, detail_contains="не найден")
