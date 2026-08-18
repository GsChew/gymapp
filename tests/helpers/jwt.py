from typing import Any

import jwt

from src.config import settings


def decode_jwt(token: str, *, verify_expiration: bool = True) -> dict[str, Any]:
    """Decode a JWT and propagate validation errors to the test."""
    return jwt.decode(
        token,
        settings.secret_key,
        algorithms=[settings.algorithm],
        options={"verify_exp": verify_expiration},
    )
