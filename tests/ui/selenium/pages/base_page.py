from __future__ import annotations

from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support import expected_conditions as conditions
from selenium.webdriver.support.ui import WebDriverWait


class SeleniumBasePage:
    timeout = 8.0

    def __init__(self, driver: WebDriver, base_url: str) -> None:
        self.driver = driver
        self.base_url = base_url.rstrip("/")
        self.wait = WebDriverWait(driver, self.timeout)

    def open(self, path: str = "/") -> None:
        self.driver.get(f"{self.base_url}{path}")

    def visible(self, locator: tuple[str, str]) -> WebElement:
        return self.wait.until(conditions.visibility_of_element_located(locator))

    def clickable(self, locator: tuple[str, str]) -> WebElement:
        return self.wait.until(conditions.element_to_be_clickable(locator))

    def text_is(self, locator: tuple[str, str], expected: str) -> None:
        self.wait.until(conditions.text_to_be_present_in_element(locator, expected))

    def hidden(self, locator: tuple[str, str]) -> None:
        self.wait.until(conditions.invisibility_of_element_located(locator))

    def fill(self, locator: tuple[str, str], value: str) -> None:
        field = self.visible(locator)
        field.clear()
        field.send_keys(value)

    def set_dom_value(self, locator: tuple[str, str], value: str) -> None:
        """Set browser-native fields that WebDriver cannot type portably."""
        field = self.visible(locator)
        self.driver.execute_script(
            "arguments[0].value = arguments[1];"
            "arguments[0].dispatchEvent(new Event('input', {bubbles: true}));"
            "arguments[0].dispatchEvent(new Event('change', {bubbles: true}));",
            field,
            value,
        )
