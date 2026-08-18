from __future__ import annotations

from selenium.webdriver.common.by import By

from tests.factories.ui_factory import UiWorkoutData
from tests.ui.selenium.pages.base_page import SeleniumBasePage


class SeleniumDashboardPage(SeleniumBasePage):
    app_view = (By.ID, "app-view")
    greeting = (By.ID, "greeting-name")
    open_workout_dialog = (
        By.CSS_SELECTOR,
        "#dashboard-view .page-heading [data-open-dialog='workout-dialog']",
    )
    workout_title = (By.CSS_SELECTOR, "#workout-form input[name='title']")
    workout_planned_at = (
        By.CSS_SELECTOR,
        "#workout-form input[name='planned_at']",
    )
    workout_submit = (
        By.CSS_SELECTOR,
        "#workout-form button[type='submit']",
    )
    dashboard_workouts = (By.ID, "dashboard-workouts")
    plan_navigation = (By.CSS_SELECTOR, ".main-nav [data-view='plan']")
    plan_view = (By.ID, "plan-view")
    plan_workouts = (By.ID, "plan-workouts")
    logout_button = (By.ID, "logout-button")
    auth_view = (By.ID, "auth-view")

    def wait_until_loaded(self, username: str) -> None:
        self.visible(self.app_view)
        self.text_is(self.greeting, username)

    @property
    def greeting_text(self) -> str:
        return self.visible(self.greeting).text

    @property
    def has_session_tokens(self) -> bool:
        return bool(
            self.driver.execute_script(
                "return Boolean("
                "localStorage.getItem('stride_access_token') && "
                "localStorage.getItem('stride_refresh_token')"
                ");"
            )
        )

    @property
    def auth_view_is_hidden(self) -> bool:
        auth_view = self.driver.find_element(By.ID, "auth-view")
        return not auth_view.is_displayed()

    def schedule_workout(self, workout: UiWorkoutData) -> None:
        self.clickable(self.open_workout_dialog).click()
        self.fill(self.workout_title, workout.title)
        self.set_dom_value(self.workout_planned_at, workout.planned_at)
        self.clickable(self.workout_submit).click()
        self.text_is(self.dashboard_workouts, workout.title)

    def open_plan(self) -> None:
        self.clickable(self.plan_navigation).click()
        self.visible(self.plan_view)

    def plan_contains(self, title: str) -> bool:
        self.text_is(self.plan_workouts, title)
        return title in self.visible(self.plan_workouts).text

    def logout(self) -> None:
        self.clickable(self.logout_button).click()
        self.visible(self.auth_view)

    @property
    def session_is_cleared(self) -> bool:
        return bool(
            self.driver.execute_script(
                "return !localStorage.getItem('stride_access_token') && "
                "!localStorage.getItem('stride_refresh_token');"
            )
        )
