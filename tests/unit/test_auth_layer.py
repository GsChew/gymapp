from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from src.auth import dependencies, service
from src.models.user import UserRole
from src.schemas.user import SUserCreate, SUserLogin


pytestmark = [pytest.mark.unit, pytest.mark.auth]


@pytest.mark.asyncio
async def test_register_service_hashes_password_and_returns_user(monkeypatch) -> None:
    created = SimpleNamespace(id=1, username="user")
    create = AsyncMock(return_value=created)
    monkeypatch.setattr(service.UserRepository, "create_user", create)
    monkeypatch.setattr(service, "hash_password", lambda value: f"hash:{value}")
    session = SimpleNamespace(rollback=AsyncMock())
    payload = SUserCreate(
        username="user",
        email="user@example.com",
        password="runtime-password",
    )

    result = await service.register_user(payload, session)

    assert result is created
    sent = create.await_args.args[0]
    assert sent["hashed_password"] == "hash:runtime-password"
    assert "password" not in sent
    session.rollback.assert_not_awaited()


@pytest.mark.parametrize(
    ("error", "message"),
    [
        (
            IntegrityError("insert", {}, Exception("duplicate")),
            "уже существует",
        ),
        (SQLAlchemyError("database"), "Ошибка при создании"),
    ],
)
@pytest.mark.asyncio
async def test_register_service_rolls_back_database_errors(
    monkeypatch,
    error,
    message: str,
) -> None:
    monkeypatch.setattr(
        service.UserRepository,
        "create_user",
        AsyncMock(side_effect=error),
    )
    monkeypatch.setattr(service, "hash_password", lambda _value: "hash")
    session = SimpleNamespace(rollback=AsyncMock())
    payload = SUserCreate(
        username="user",
        email="user@example.com",
        password="runtime-password",
    )

    with pytest.raises(ValueError, match=message):
        await service.register_user(payload, session)

    session.rollback.assert_awaited_once()


@pytest.mark.asyncio
async def test_login_service_issues_token_pair(monkeypatch) -> None:
    user = SimpleNamespace(id=7, hashed_password="hash")
    monkeypatch.setattr(
        service.UserRepository,
        "get_user_by_username",
        AsyncMock(return_value=user),
    )
    monkeypatch.setattr(service, "verify_password", lambda *_args: True)
    monkeypatch.setattr(service, "create_access_token", lambda value: f"a-{value}")
    monkeypatch.setattr(service, "create_refresh_token", lambda value: f"r-{value}")

    result = await service.login_user(
        SUserLogin(username="known", password="password"),
        SimpleNamespace(rollback=AsyncMock()),
    )

    assert result.access_token == "a-7"
    assert result.refresh_token == "r-7"


@pytest.mark.parametrize(
    ("repository_user", "valid_password"),
    [(None, True), (SimpleNamespace(id=1, hashed_password="hash"), False)],
)
@pytest.mark.asyncio
async def test_login_service_hides_unknown_user_and_wrong_password(
    monkeypatch,
    repository_user,
    valid_password: bool,
) -> None:
    monkeypatch.setattr(
        service.UserRepository,
        "get_user_by_username",
        AsyncMock(return_value=repository_user),
    )
    monkeypatch.setattr(
        service,
        "verify_password",
        lambda *_args: valid_password,
    )

    with pytest.raises(ValueError, match="Неверные учетные данные"):
        await service.login_user(
            SUserLogin(username="known", password="password"),
            SimpleNamespace(rollback=AsyncMock()),
        )


@pytest.mark.asyncio
async def test_login_service_rolls_back_sqlalchemy_error(monkeypatch) -> None:
    monkeypatch.setattr(
        service.UserRepository,
        "get_user_by_username",
        AsyncMock(side_effect=SQLAlchemyError("database")),
    )
    session = SimpleNamespace(rollback=AsyncMock())

    with pytest.raises(ValueError, match="Ошибка при входе"):
        await service.login_user(
            SUserLogin(username="known", password="password"),
            session,
        )

    session.rollback.assert_awaited_once()


@pytest.mark.asyncio
async def test_refresh_service_validates_type_and_subject(monkeypatch) -> None:
    monkeypatch.setattr(
        service,
        "decode_token",
        lambda _token: {"sub": "8", "token_type": "refresh"},
    )
    monkeypatch.setattr(service, "create_access_token", lambda value: f"a-{value}")
    monkeypatch.setattr(service, "create_refresh_token", lambda value: f"r-{value}")

    result = await service.refresh_tokens("valid")

    assert result.access_token == "a-8"
    assert result.refresh_token == "r-8"

    monkeypatch.setattr(
        service,
        "decode_token",
        lambda _token: {"sub": "8", "token_type": "access"},
    )
    with pytest.raises(ValueError, match="Некорректный refresh token"):
        await service.refresh_tokens("wrong-type")

    monkeypatch.setattr(
        service,
        "decode_token",
        lambda _token: {"token_type": "refresh"},
    )
    with pytest.raises(ValueError, match="отсутствует subject"):
        await service.refresh_tokens("missing-subject")


@pytest.mark.asyncio
async def test_current_user_and_role_dependencies(monkeypatch) -> None:
    user = SimpleNamespace(id=3, role=UserRole.trainer)
    monkeypatch.setattr(
        dependencies,
        "decode_token",
        lambda _token: {"sub": "3", "token_type": "access"},
    )
    monkeypatch.setattr(
        dependencies.UserRepository,
        "get_user",
        AsyncMock(return_value=user),
    )

    assert await dependencies.get_current_user("token", object()) is user
    checker = dependencies.require_roles(UserRole.trainer)
    assert await checker(user) is user

    denied = dependencies.require_roles(UserRole.admin)
    with pytest.raises(HTTPException) as error:
        await denied(user)
    assert error.value.status_code == 403


@pytest.mark.parametrize(
    "claims",
    [
        {"sub": "3", "token_type": "refresh"},
        {"token_type": "access"},
        {"sub": "not-int", "token_type": "access"},
    ],
)
@pytest.mark.asyncio
async def test_current_user_rejects_invalid_claims(monkeypatch, claims) -> None:
    monkeypatch.setattr(dependencies, "decode_token", lambda _token: claims)

    with pytest.raises(HTTPException) as error:
        await dependencies.get_current_user("token", object())

    assert error.value.status_code == 401


@pytest.mark.asyncio
async def test_current_user_rejects_deleted_user(monkeypatch) -> None:
    monkeypatch.setattr(
        dependencies,
        "decode_token",
        lambda _token: {"sub": "3", "token_type": "access"},
    )
    monkeypatch.setattr(
        dependencies.UserRepository,
        "get_user",
        AsyncMock(return_value=None),
    )

    with pytest.raises(HTTPException):
        await dependencies.get_current_user("token", object())


def test_token_type_helpers(monkeypatch) -> None:
    monkeypatch.setattr(
        dependencies,
        "decode_token",
        lambda token: {"token_type": token},
    )

    assert dependencies.is_access_token("access") is True
    assert dependencies.is_access_token("refresh") is False
    assert dependencies.is_refresh_token("refresh") is True
    assert dependencies.is_refresh_token("access") is False
