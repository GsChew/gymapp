from __future__ import annotations

from typing import Any


SENSITIVE_KEYS = {
    "authorization",
    "password",
    "hashed_password",
    "access_token",
    "refresh_token",
    "secret",
    "secret_key",
}


def redact(value: Any) -> Any:
    if isinstance(value, dict):
        return {
            key: "***" if key.lower() in SENSITIVE_KEYS else redact(item)
            for key, item in value.items()
        }
    if isinstance(value, list):
        return [redact(item) for item in value]
    if isinstance(value, tuple):
        return tuple(redact(item) for item in value)
    return value
