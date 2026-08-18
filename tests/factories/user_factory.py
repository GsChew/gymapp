from __future__ import annotations

import secrets
from typing import Any

from tests.helpers.generators import unique_email, unique_username


class UserFactory:
    @staticmethod
    def build(**overrides: Any) -> dict[str, Any]:
        username = overrides.pop("username", unique_username())
        payload = {
            "username": username,
            "email": overrides.pop("email", unique_email(username[:12])),
            "password": overrides.pop("password", secrets.token_urlsafe(18)),
        }
        payload.update(overrides)
        return payload

    @staticmethod
    def login(username: str, password: str, **overrides: Any) -> dict[str, Any]:
        payload = {"username": username, "password": password}
        payload.update(overrides)
        return payload
