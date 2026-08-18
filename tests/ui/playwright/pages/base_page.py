from __future__ import annotations

from playwright.sync_api import Page


class PlaywrightBasePage:
    timeout = 8_000

    def __init__(self, page: Page, base_url: str) -> None:
        self.page = page
        self.base_url = base_url.rstrip("/")
        self.page.set_default_timeout(self.timeout)

    def open(self, path: str = "/") -> None:
        self.page.goto(f"{self.base_url}{path}", wait_until="domcontentloaded")
