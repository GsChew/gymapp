import json

import pytest
from loguru import logger
from sqlalchemy import func, select

from src.models.user import User
from tests.factories.user_factory import UserFactory
from tests.factories.workout_factory import WorkoutFactory
from tests.helpers.assertions import assert_error


pytestmark = [pytest.mark.api, pytest.mark.security]


@pytest.mark.positive
@pytest.mark.asyncio
async def test_injection_strings_are_stored_as_data_not_executed(
    anonymous_clients,
    api_clients_factory,
    db_session,
) -> None:
    injection = "'; DROP TABLE users; --"
    payload = UserFactory.build(
        username=injection,
        email="injection@example.com",
    )
    registration = await anonymous_clients.auth.register(payload)
    assert registration.status_code == 200, registration.text
    login = await anonymous_clients.auth.login(
        UserFactory.login(injection, payload["password"])
    )
    assert login.status_code == 200
    clients = api_clients_factory(login.json()["access_token"])

    workout = await clients.workouts.create_workout(
        WorkoutFactory.build(title=injection)
    )
    assert workout.status_code == 200
    assert workout.json()["title"] == injection
    assert await db_session.scalar(select(func.count()).select_from(User)) == 1


@pytest.mark.negative
@pytest.mark.asyncio
async def test_auth_failures_do_not_log_password_or_tokens(
    anonymous_clients,
) -> None:
    messages: list[str] = []
    sink_id = logger.add(lambda message: messages.append(str(message)), level="DEBUG")
    payload = UserFactory.build()
    try:
        response = await anonymous_clients.auth.login(
            {"username": payload["username"], "password": payload["password"]}
        )
    finally:
        logger.remove(sink_id)

    assert_error(response, 401)
    combined = "\n".join(messages)
    assert payload["password"] not in combined
    assert "access_token" not in combined
    assert "refresh_token" not in combined
    assert json.dumps({"password": payload["password"]}) not in combined
