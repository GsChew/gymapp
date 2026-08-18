from __future__ import annotations

import asyncio
import os
import socket
import subprocess
import sys
from collections.abc import AsyncIterator, Iterator
from pathlib import Path
from typing import Any

import httpx
import psycopg
import pytest
import pytest_asyncio
from playwright.sync_api import Browser, BrowserContext, Page, Playwright
from playwright.sync_api import sync_playwright
from psycopg import sql
from redis import Redis
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.remote.webdriver import WebDriver

import src.models  # noqa: F401
from src.database import Model
from tests.factories.ui_factory import UiDataFactory, UiUserData, UiWorkoutData
from tests.fixtures.config import TestSettings


def _free_local_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
        server_socket.bind(("127.0.0.1", 0))
        return int(server_socket.getsockname()[1])


def _is_headless() -> bool:
    return os.getenv("UI_HEADLESS", "1").lower() not in {"0", "false", "no"}


@pytest_asyncio.fixture(scope="session")
async def ui_base_url(
    db_engine: Any,
    test_settings: TestSettings,
    tmp_path_factory: pytest.TempPathFactory,
) -> AsyncIterator[str]:
    """Run the real application on an ephemeral loopback port for browser tests."""
    del db_engine
    port = _free_local_port()
    base_url = f"http://127.0.0.1:{port}"
    log_path = tmp_path_factory.mktemp("ui-server") / "uvicorn.log"
    environment = os.environ.copy()
    environment.update(
        {
            "DATABASE_URL": test_settings.database_url,
            "ALEMBIC_DATABASE_URL": test_settings.alembic_database_url,
            "REDIS_URL": test_settings.redis_url,
            "CELERY_BROKER_URL": test_settings.rabbitmq_url,
            "CELERY_RESULT_BACKEND": test_settings.redis_url,
            "SECRET_KEY": os.getenv(
                "SECRET_KEY",
                "ui-tests-only-secret-not-for-production",
            ),
            "ALGORITHM": os.getenv("ALGORITHM", "HS256"),
            "ACCESS_TOKEN_EXPIRE_MINUTES": "30",
            "REFRESH_TOKEN_EXPIRE_DAYS": "7",
            "LOG_LEVEL": "WARNING",
            "LOG_DIR": str(log_path.parent),
            "LOG_JSON": "false",
            "PYTHONUNBUFFERED": "1",
        }
    )

    with log_path.open("w+", encoding="utf-8") as log_file:
        process = subprocess.Popen(
            [
                sys.executable,
                "-m",
                "uvicorn",
                "main:app",
                "--host",
                "127.0.0.1",
                "--port",
                str(port),
                "--log-level",
                "warning",
            ],
            cwd=Path(__file__).resolve().parents[2],
            env=environment,
            stdout=log_file,
            stderr=subprocess.STDOUT,
        )

        try:
            async with httpx.AsyncClient(timeout=0.5) as client:
                for _ in range(200):
                    if process.poll() is not None:
                        break
                    try:
                        response = await client.get(f"{base_url}/health")
                        if response.status_code == 200:
                            yield base_url
                            return
                    except httpx.HTTPError:
                        pass
                    await asyncio.sleep(0.05)

            log_file.flush()
            log_file.seek(0)
            pytest.fail(
                "UI test server did not become ready. Uvicorn output:\n"
                f"{log_file.read()}"
            )
        finally:
            if process.poll() is None:
                process.terminate()
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait(timeout=5)


def _truncate_ui_database(test_settings: TestSettings) -> None:
    test_settings.validate_database_safety()
    url = test_settings.parsed_database_url
    table_names = [table.name for table in Model.metadata.sorted_tables]
    statement = sql.SQL("TRUNCATE TABLE {} RESTART IDENTITY CASCADE").format(
        sql.SQL(", ").join(sql.Identifier(name) for name in table_names)
    )
    with psycopg.connect(
        host=url.host,
        port=url.port,
        user=url.username,
        password=url.password,
        dbname=url.database,
    ) as connection:
        connection.execute(statement)
        connection.commit()


@pytest.fixture
def clean_ui_environment(
    ui_base_url: str,
    test_settings: TestSettings,
) -> Iterator[None]:
    """Reset dedicated Redis rate-limit state around every browser scenario."""
    del ui_base_url
    redis = Redis.from_url(test_settings.redis_url, decode_responses=True)
    try:
        _truncate_ui_database(test_settings)
        redis.flushdb()
        yield
    finally:
        _truncate_ui_database(test_settings)
        redis.flushdb()
        redis.close()


@pytest.fixture
def ui_user_data() -> UiUserData:
    return UiDataFactory.user()


@pytest.fixture
def ui_workout_data() -> UiWorkoutData:
    return UiDataFactory.workout()


@pytest.fixture(scope="session")
def selenium_driver() -> Iterator[WebDriver]:
    options = Options()
    if _is_headless():
        options.add_argument("--headless=new")
    options.add_argument("--window-size=1440,1200")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--no-sandbox")

    browser_binary = os.getenv("UI_BROWSER_BINARY")
    if browser_binary:
        options.binary_location = browser_binary

    driver_binary = os.getenv("UI_DRIVER_BINARY")
    service = Service(executable_path=driver_binary) if driver_binary else Service()
    driver = webdriver.Chrome(service=service, options=options)
    driver.execute_cdp_cmd("Network.enable", {})
    driver.execute_cdp_cmd(
        "Network.setBlockedURLs",
        {"urls": ["https://unpkg.com/*"]},
    )
    try:
        yield driver
    finally:
        driver.quit()


@pytest.fixture
def playwright_runtime(
    clean_ui_environment: None,
) -> Iterator[Playwright]:
    del clean_ui_environment
    with sync_playwright() as runtime:
        yield runtime


@pytest.fixture
def playwright_browser(playwright_runtime: Playwright) -> Iterator[Browser]:
    launch_options: dict[str, Any] = {"headless": _is_headless()}
    browser_binary = os.getenv("UI_BROWSER_BINARY")
    if browser_binary:
        launch_options["executable_path"] = browser_binary
    browser = playwright_runtime.chromium.launch(**launch_options)
    try:
        yield browser
    finally:
        browser.close()


@pytest.fixture
def playwright_context(
    playwright_browser: Browser,
) -> Iterator[BrowserContext]:
    context = playwright_browser.new_context(viewport={"width": 1440, "height": 1200})
    context.route("https://unpkg.com/**", lambda route: route.abort())
    try:
        yield context
    finally:
        context.close()


@pytest.fixture
def playwright_page(playwright_context: BrowserContext) -> Iterator[Page]:
    page = playwright_context.new_page()
    try:
        yield page
    finally:
        page.close()
