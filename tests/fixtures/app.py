from __future__ import annotations

from collections.abc import AsyncIterator, Callable

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from main import app
from src.database import get_db
from src.rate_limit import dependencies as rate_limit_dependencies
from src.schemas.rate_limit import SRateLimitResponse
from tests.clients.api import ApiClients
from tests.clients.base_client import BaseClient
from tests.fixtures.config import TestSettings


@pytest.fixture
def app_instance():
    return app


@pytest.fixture
def bypass_rate_limits(monkeypatch: pytest.MonkeyPatch) -> None:
    async def allowed(*_args, **_kwargs) -> SRateLimitResponse:
        return SRateLimitResponse(
            allowed=True,
            limit=999,
            remaining=998,
            retry_after=0,
        )

    monkeypatch.setattr(
        rate_limit_dependencies,
        "get_ratelimit_result",
        allowed,
    )


@pytest_asyncio.fixture
async def http_client(
    app_instance,
    db_session,
    bypass_rate_limits: None,
    test_settings: TestSettings,
) -> AsyncIterator[AsyncClient]:
    async def override_get_db():
        yield db_session

    app_instance.dependency_overrides[get_db] = override_get_db
    transport = ASGITransport(app=app_instance, raise_app_exceptions=False)
    async with AsyncClient(
        transport=transport,
        base_url="http://testserver",
        timeout=test_settings.api_timeout,
    ) as client:
        yield client
    app_instance.dependency_overrides.clear()


@pytest.fixture
def api_clients_factory(
    http_client: AsyncClient,
    client_registry,
    test_settings: TestSettings,
) -> Callable[[str | None], ApiClients]:
    def factory(token: str | None = None) -> ApiClients:
        base = BaseClient(
            http_client,
            token=token,
            timeout=test_settings.api_timeout,
        )
        client_registry(base)
        return ApiClients.build(base)

    return factory


@pytest.fixture
def anonymous_clients(api_clients_factory) -> ApiClients:
    return api_clients_factory()
