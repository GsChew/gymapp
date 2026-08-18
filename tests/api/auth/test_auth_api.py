from datetime import timedelta

import allure
import pytest

from src.auth.security import create_access_token, create_jwt, create_refresh_token
from tests.factories.user_factory import UserFactory
from tests.helpers.assertions import assert_error, assert_has_fields
from tests.helpers.jwt import decode_jwt


pytestmark = [pytest.mark.api, pytest.mark.auth]


@allure.feature("Authentication")
@allure.story("Registration and login")
@allure.title("New user can register, log in, and read own profile")
@allure.severity(allure.severity_level.CRITICAL)
@pytest.mark.positive
@pytest.mark.asyncio
async def test_register_login_refresh_and_me(
    anonymous_clients,
    api_clients_factory,
) -> None:
    payload = UserFactory.build()

    with allure.step("Register a unique user"):
        registration = await anonymous_clients.auth.register(payload)
    assert registration.status_code == 200, registration.text
    assert_has_fields(
        registration.json(),
        {"id", "username", "email", "created_at", "role"},
    )
    assert registration.json()["username"] == payload["username"]
    assert registration.json()["email"] == payload["email"]
    assert registration.json()["role"] == "user"
    assert "password" not in registration.json()
    assert "hashed_password" not in registration.json()

    with allure.step("Authenticate with the registered credentials"):
        login = await anonymous_clients.auth.login(
            UserFactory.login(payload["username"], payload["password"])
        )
    assert login.status_code == 200, login.text
    assert_has_fields(login.json(), {"access_token", "refresh_token", "token_type"})
    assert login.json()["token_type"] == "bearer"
    assert decode_jwt(login.json()["access_token"])["token_type"] == "access"
    assert decode_jwt(login.json()["refresh_token"])["token_type"] == "refresh"

    authenticated = api_clients_factory(login.json()["access_token"])
    profile = await authenticated.auth.me()

    assert profile.status_code == 200, profile.text
    assert profile.json()["id"] == registration.json()["id"]

    with allure.step("Rotate both tokens using the refresh token"):
        refreshed = await anonymous_clients.auth.refresh(
            login.json()["refresh_token"]
        )
    assert refreshed.status_code == 200, refreshed.text
    assert refreshed.json()["access_token"] != login.json()["access_token"]
    assert refreshed.json()["refresh_token"] != login.json()["refresh_token"]


@allure.feature("Authentication")
@allure.story("Registration validation")
@pytest.mark.negative
@pytest.mark.asyncio
async def test_duplicate_username_and_email_are_rejected(
    anonymous_clients,
) -> None:
    original = UserFactory.build()
    created = await anonymous_clients.auth.register(original)
    assert created.status_code == 200

    duplicate_username = UserFactory.build(username=original["username"])
    duplicate_email = UserFactory.build(email=original["email"])

    username_response = await anonymous_clients.auth.register(duplicate_username)
    email_response = await anonymous_clients.auth.register(duplicate_email)

    assert_error(username_response, 409, detail_contains="уже существует")
    assert_error(email_response, 409, detail_contains="уже существует")


@pytest.mark.parametrize(
    "payload",
    [
        {},
        {"username": "ab", "email": "valid@example.com", "password": "12345678"},
        {"username": "valid_name", "email": "not-email", "password": "12345678"},
        {"username": "valid_name", "email": "valid@example.com", "password": "short"},
        {"username": 42, "email": "valid@example.com", "password": "12345678"},
        {"username": "valid_name", "email": None, "password": "12345678"},
    ],
)
@pytest.mark.negative
@pytest.mark.asyncio
async def test_registration_rejects_invalid_payloads(
    anonymous_clients,
    payload: dict,
) -> None:
    response = await anonymous_clients.auth.register(payload)

    assert_error(response, 422)


@pytest.mark.negative
@pytest.mark.asyncio
async def test_login_rejects_unknown_user_and_wrong_password(
    anonymous_clients,
) -> None:
    payload = UserFactory.build()
    created = await anonymous_clients.auth.register(payload)
    assert created.status_code == 200

    wrong_password = await anonymous_clients.auth.login(
        UserFactory.login(payload["username"], "definitely-wrong")
    )
    unknown = await anonymous_clients.auth.login(
        UserFactory.login("unknown_user", "some-password")
    )

    assert_error(wrong_password, 401, detail_contains="учетные данные")
    assert_error(unknown, 401, detail_contains="учетные данные")
    assert wrong_password.json()["detail"] == unknown.json()["detail"]


@pytest.mark.parametrize(
    "token_factory",
    [
        lambda: "not-a-jwt",
        lambda: create_access_token(1),
        lambda: create_jwt(
            1,
            expires_delta=timedelta(seconds=-1),
            token_type="refresh",
        ),
    ],
)
@pytest.mark.negative
@pytest.mark.asyncio
async def test_refresh_rejects_malformed_wrong_type_and_expired_tokens(
    anonymous_clients,
    token_factory,
) -> None:
    response = await anonymous_clients.auth.refresh(token_factory())

    assert_error(response, 400, detail_contains="refresh token")


@pytest.mark.negative
@pytest.mark.security
@pytest.mark.asyncio
async def test_me_rejects_missing_malformed_refresh_and_wrong_scheme(
    anonymous_clients,
    user_account,
) -> None:
    missing = await anonymous_clients.auth.me()
    malformed = await anonymous_clients.auth.me(
        headers={"Authorization": "Bearer malformed"}
    )
    refresh = await anonymous_clients.auth.me(
        headers={"Authorization": f"Bearer {user_account.refresh_token}"}
    )
    basic = await anonymous_clients.auth.me(
        headers={"Authorization": "Basic dXNlcjpwYXNz"}
    )

    for response in (missing, malformed, refresh, basic):
        assert_error(response, 401)
        assert "traceback" not in response.text.lower()


@pytest.mark.xfail(
    reason=(
        "DEFECT AUTH-001: refresh_tokens validates signature and token type "
        "but does not verify that token subject still references a user"
    ),
    strict=True,
)
@pytest.mark.security
@pytest.mark.negative
@pytest.mark.asyncio
async def test_refresh_token_for_nonexistent_user_is_rejected(
    anonymous_clients,
) -> None:
    response = await anonymous_clients.auth.refresh(create_refresh_token(999_999))

    assert response.status_code == 401
