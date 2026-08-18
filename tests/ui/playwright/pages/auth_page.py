from __future__ import annotations

from tests.factories.ui_factory import UiUserData
from tests.ui.playwright.pages.base_page import PlaywrightBasePage
from tests.ui.playwright.pages.dashboard_page import PlaywrightDashboardPage


class PlaywrightAuthPage(PlaywrightBasePage):
    login_heading = "#login-form-wrap h2"
    register_heading = "#register-form-wrap h2"

    def open_login(self) -> "PlaywrightAuthPage":
        self.open()
        self.page.locator(self.login_heading).wait_for(state="visible")
        return self

    def show_register(self) -> None:
        self.page.locator("[data-auth-mode='register']").click()
        self.page.locator(self.register_heading).wait_for(state="visible")

    def show_login(self) -> None:
        self.page.locator("[data-auth-mode='login']").click()
        self.page.locator(self.login_heading).wait_for(state="visible")

    @property
    def visible_heading(self) -> str:
        if self.page.locator(self.login_heading).is_visible():
            return self.page.locator(self.login_heading).inner_text()
        return self.page.locator(self.register_heading).inner_text()

    def login(self, username: str, password: str) -> None:
        self.page.locator("#login-form input[name='username']").fill(username)
        self.page.locator("#login-form input[name='password']").fill(password)
        self.page.locator("#login-form button[type='submit']").click()

    def register(self, user: UiUserData) -> PlaywrightDashboardPage:
        self.show_register()
        self.page.locator("#register-form input[name='username']").fill(
            user.username
        )
        self.page.locator("#register-form input[name='email']").fill(user.email)
        self.page.locator("#register-form input[name='password']").fill(
            user.password
        )
        self.page.locator("#register-form button[type='submit']").click()
        dashboard = PlaywrightDashboardPage(self.page, self.base_url)
        dashboard.wait_until_loaded(user.username)
        return dashboard

    def wait_for_error(self, expected: str) -> str:
        toast = self.page.locator("#toast")
        toast.wait_for(state="visible")
        toast.filter(has_text=expected).wait_for(state="visible")
        return toast.inner_text()

    @property
    def is_login_visible(self) -> bool:
        return self.page.locator(self.login_heading).is_visible()
