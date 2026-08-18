from __future__ import annotations

from collections.abc import Generator
from typing import Any

import allure
import pytest

from tests.clients.base_client import BaseClient


pytest_plugins = (
    "tests.fixtures.app",
    "tests.fixtures.database",
    "tests.fixtures.users",
    "tests.fixtures.resources",
    "tests.fixtures.celery",
    "tests.fixtures.ui",
)


@pytest.fixture
def client_registry(request: pytest.FixtureRequest):
    """Register API clients so failed tests receive sanitized HTTP attachments."""
    clients: list[BaseClient] = []
    setattr(request.node, "_qa_api_clients", clients)

    def register(client: BaseClient) -> BaseClient:
        clients.append(client)
        return client

    return register


@pytest.fixture
def ui_artifact_registry(request: pytest.FixtureRequest):
    """Register browser screenshot callbacks for failure-only Allure evidence."""
    screenshotters: list[tuple[str, Any]] = []
    setattr(request.node, "_qa_ui_screenshotters", screenshotters)

    def register(name: str, screenshotter: Any) -> None:
        screenshotters.append((name, screenshotter))

    return register


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(
    item: pytest.Item,
    call: pytest.CallInfo[Any],
) -> Generator[None, Any, None]:
    """Attach sanitized request/response history only when a test phase fails."""
    outcome = yield
    report = outcome.get_result()
    if report.when != "call" or not report.failed:
        return

    for index, client in enumerate(getattr(item, "_qa_api_clients", []), start=1):
        if client.exchanges:
            allure.attach(
                client.dump_exchanges(),
                name=f"http-exchanges-{index}",
                attachment_type=allure.attachment_type.JSON,
            )

    for name, screenshotter in getattr(item, "_qa_ui_screenshotters", []):
        try:
            screenshot = screenshotter()
        except Exception as error:  # pragma: no cover - diagnostic fallback
            allure.attach(
                str(error),
                name=f"{name}-screenshot-error",
                attachment_type=allure.attachment_type.TEXT,
            )
        else:
            allure.attach(
                screenshot,
                name=f"{name}-failure",
                attachment_type=allure.attachment_type.PNG,
            )
