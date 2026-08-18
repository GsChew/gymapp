from __future__ import annotations

from tests.factories.ui_factory import UiWorkoutData
from tests.ui.playwright.pages.base_page import PlaywrightBasePage


class PlaywrightDashboardPage(PlaywrightBasePage):
    def wait_until_loaded(self, username: str) -> None:
        self.page.locator("#app-view").wait_for(state="visible")
        self.page.locator("#greeting-name").filter(has_text=username).wait_for()

    @property
    def greeting_text(self) -> str:
        return self.page.locator("#greeting-name").inner_text()

    @property
    def has_session_tokens(self) -> bool:
        return bool(
            self.page.evaluate(
                "() => Boolean("
                "localStorage.getItem('stride_access_token') && "
                "localStorage.getItem('stride_refresh_token')"
                ")"
            )
        )

    @property
    def auth_view_is_hidden(self) -> bool:
        return self.page.locator("#auth-view").is_hidden()

    def schedule_workout(self, workout: UiWorkoutData) -> None:
        self.page.locator(
            "#dashboard-view .page-heading "
            "[data-open-dialog='workout-dialog']"
        ).click()
        self.page.locator("#workout-form input[name='title']").fill(
            workout.title
        )
        self.page.locator("#workout-form input[name='planned_at']").fill(
            workout.planned_at
        )
        self.page.locator("#workout-form button[type='submit']").click()
        self.page.locator("#dashboard-workouts").filter(
            has_text=workout.title
        ).wait_for()

    def open_plan(self) -> None:
        self.page.locator(".main-nav [data-view='plan']").click()
        self.page.locator("#plan-view").wait_for(state="visible")

    def plan_contains(self, title: str) -> bool:
        plan = self.page.locator("#plan-workouts")
        plan.filter(has_text=title).wait_for()
        return title in plan.inner_text()

    def logout(self) -> None:
        self.page.locator("#logout-button").click()
        self.page.locator("#auth-view").wait_for(state="visible")

    @property
    def session_is_cleared(self) -> bool:
        return bool(
            self.page.evaluate(
                "() => !localStorage.getItem('stride_access_token') && "
                "!localStorage.getItem('stride_refresh_token')"
            )
        )
