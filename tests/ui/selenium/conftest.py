from __future__ import annotations

import pytest
from selenium.webdriver.remote.webdriver import WebDriver

from tests.ui.selenium.pages import SeleniumAuthPage


@pytest.fixture
def selenium_auth_page(
    selenium_driver: WebDriver,
    ui_base_url: str,
    clean_ui_environment: None,
    ui_artifact_registry,
) -> SeleniumAuthPage:
    del clean_ui_environment
    page = SeleniumAuthPage(selenium_driver, ui_base_url)
    page.open_login()
    selenium_driver.execute_script("localStorage.clear(); sessionStorage.clear();")
    page.open_login()
    ui_artifact_registry(
        "selenium",
        selenium_driver.get_screenshot_as_png,
    )
    return page
