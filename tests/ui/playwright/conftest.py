from __future__ import annotations

import pytest
from playwright.sync_api import Page

from tests.ui.playwright.pages import PlaywrightAuthPage


@pytest.fixture
def playwright_auth_page(
    playwright_page: Page,
    ui_base_url: str,
    clean_ui_environment: None,
    ui_artifact_registry,
) -> PlaywrightAuthPage:
    del clean_ui_environment
    page = PlaywrightAuthPage(playwright_page, ui_base_url)
    page.open_login()
    ui_artifact_registry(
        "playwright",
        lambda: playwright_page.screenshot(full_page=True),
    )
    return page
