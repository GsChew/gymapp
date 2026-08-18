from __future__ import annotations

from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import Any

import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.security import (
    create_access_token,
    create_refresh_token,
    hash_password,
)
from src.models.user import User, UserRole
from tests.clients.api import ApiClients
from tests.factories.user_factory import UserFactory


@dataclass(slots=True)
class UserAccount:
    user: User
    password: str
    access_token: str
    refresh_token: str
    clients: ApiClients


@pytest_asyncio.fixture
async def make_user(
    db_session: AsyncSession,
    api_clients_factory,
) -> Callable[..., Awaitable[UserAccount]]:
    async def factory(
        *,
        role: UserRole = UserRole.user,
        **overrides: Any,
    ) -> UserAccount:
        payload = UserFactory.build(**overrides)
        user = User(
            username=payload["username"],
            email=payload["email"],
            hashed_password=hash_password(payload["password"]),
            role=role,
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)
        access_token = create_access_token(user.id)
        refresh_token = create_refresh_token(user.id)
        return UserAccount(
            user=user,
            password=payload["password"],
            access_token=access_token,
            refresh_token=refresh_token,
            clients=api_clients_factory(access_token),
        )

    return factory


@pytest_asyncio.fixture
async def user_account(make_user) -> UserAccount:
    return await make_user()


@pytest_asyncio.fixture
async def trainer_account(make_user) -> UserAccount:
    return await make_user(role=UserRole.trainer)


@pytest_asyncio.fixture
async def admin_account(make_user) -> UserAccount:
    return await make_user(role=UserRole.admin)
