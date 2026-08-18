from __future__ import annotations

from selenium.webdriver.common.by import By

from tests.factories.ui_factory import UiUserData
from tests.ui.selenium.pages.base_page import SeleniumBasePage
from tests.ui.selenium.pages.dashboard_page import SeleniumDashboardPage


class SeleniumAuthPage(SeleniumBasePage):
    auth_view = (By.ID, "auth-view")
    login_heading = (By.CSS_SELECTOR, "#login-form-wrap h2")
    register_heading = (By.CSS_SELECTOR, "#register-form-wrap h2")
    open_register_button = (By.CSS_SELECTOR, "[data-auth-mode='register']")
    open_login_button = (By.CSS_SELECTOR, "[data-auth-mode='login']")
    login_username = (By.CSS_SELECTOR, "#login-form input[name='username']")
    login_password = (By.CSS_SELECTOR, "#login-form input[name='password']")
    login_submit = (By.CSS_SELECTOR, "#login-form button[type='submit']")
    register_username = (By.CSS_SELECTOR, "#register-form input[name='username']")
    register_email = (By.CSS_SELECTOR, "#register-form input[name='email']")
    register_password = (By.CSS_SELECTOR, "#register-form input[name='password']")
    register_submit = (By.CSS_SELECTOR, "#register-form button[type='submit']")
    toast = (By.ID, "toast")

    def open_login(self) -> "SeleniumAuthPage":
        self.open()
        self.visible(self.login_heading)
        return self

    def show_register(self) -> None:
        self.clickable(self.open_register_button).click()
        self.visible(self.register_heading)

    def show_login(self) -> None:
        self.clickable(self.open_login_button).click()
        self.visible(self.login_heading)

    @property
    def visible_heading(self) -> str:
        for locator in (self.login_heading, self.register_heading):
            elements = self.driver.find_elements(*locator)
            if elements and elements[0].is_displayed():
                return elements[0].text
        return ""

    def login(self, username: str, password: str) -> None:
        self.fill(self.login_username, username)
        self.fill(self.login_password, password)
        self.clickable(self.login_submit).click()

    def register(self, user: UiUserData) -> SeleniumDashboardPage:
        self.show_register()
        self.fill(self.register_username, user.username)
        self.fill(self.register_email, user.email)
        self.fill(self.register_password, user.password)
        self.clickable(self.register_submit).click()
        dashboard = SeleniumDashboardPage(self.driver, self.base_url)
        dashboard.wait_until_loaded(user.username)
        return dashboard

    def wait_for_error(self, expected: str) -> str:
        self.text_is(self.toast, expected)
        return self.visible(self.toast).text

    @property
    def is_login_visible(self) -> bool:
        return self.visible(self.login_heading).is_displayed()
