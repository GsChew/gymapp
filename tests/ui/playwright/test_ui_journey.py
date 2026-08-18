from __future__ import annotations

import allure
import pytest

from tests.factories.ui_factory import UiUserData, UiWorkoutData
from tests.ui.playwright.pages import PlaywrightAuthPage


pytestmark = [
    pytest.mark.ui,
    pytest.mark.playwright,
    pytest.mark.e2e,
    pytest.mark.slow,
]


@allure.feature("Web UI")
@allure.story("Authentication")
@allure.title("Playwright: переключение между login и registration")
def test_auth_mode_switches(
    playwright_auth_page: PlaywrightAuthPage,
) -> None:
    assert playwright_auth_page.visible_heading == "Войди в свой ритм"

    playwright_auth_page.show_register()
    assert playwright_auth_page.visible_heading == "Создай аккаунт"

    playwright_auth_page.show_login()
    assert playwright_auth_page.visible_heading == "Войди в свой ритм"


@allure.feature("Web UI")
@allure.story("Authentication")
@allure.title("Playwright: неизвестный пользователь видит безопасную ошибку")
@pytest.mark.negative
def test_invalid_login_shows_safe_error(
    playwright_auth_page: PlaywrightAuthPage,
) -> None:
    playwright_auth_page.login("unknown_ui_user", "wrong-password")

    assert (
        playwright_auth_page.wait_for_error("Неверные учетные данные")
        == "Неверные учетные данные"
    )
    assert playwright_auth_page.is_login_visible


@allure.feature("Web UI")
@allure.story("Workout planning")
@allure.title(
    "Playwright: регистрация, создание тренировки и завершение сессии"
)
@allure.severity(allure.severity_level.CRITICAL)
@pytest.mark.positive
def test_user_registers_creates_workout_and_logs_out(
    playwright_auth_page: PlaywrightAuthPage,
    ui_user_data: UiUserData,
    ui_workout_data: UiWorkoutData,
) -> None:
    with allure.step("Зарегистрировать пользователя через UI"):
        dashboard = playwright_auth_page.register(ui_user_data)
        assert dashboard.greeting_text == ui_user_data.username
        assert dashboard.has_session_tokens

    with allure.step("Создать тренировку и проверить её в плане"):
        dashboard.schedule_workout(ui_workout_data)
        dashboard.open_plan()
        assert dashboard.plan_contains(ui_workout_data.title)

    with allure.step("Выйти и проверить очистку browser storage"):
        dashboard.logout()
        assert playwright_auth_page.visible_heading == "Создай аккаунт"
        assert dashboard.session_is_cleared


@allure.feature("Web UI")
@allure.story("Authentication")
@allure.title("Playwright: authenticated view скрывает форму авторизации")
@pytest.mark.xfail(
    strict=True,
    reason=(
        "DEFECT UI-001: .auth-layout display:grid overrides the HTML hidden "
        "attribute, so auth and application views render together"
    ),
)
def test_authenticated_view_hides_auth_form(
    playwright_auth_page: PlaywrightAuthPage,
    ui_user_data: UiUserData,
) -> None:
    dashboard = playwright_auth_page.register(ui_user_data)

    assert dashboard.auth_view_is_hidden
